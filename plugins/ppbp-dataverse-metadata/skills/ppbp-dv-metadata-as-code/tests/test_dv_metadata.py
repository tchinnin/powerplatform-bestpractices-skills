"""Offline tests for dv_metadata.py — validator, diff engine, dev guard, hook.

Run:  python3 -m unittest discover -s <skill>/tests -v
"""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
import dv_metadata as dv  # noqa: E402

SAMPLES = SKILL / "references" / "samples"


def load_samples():
    meta, choices, tables = dv.load_model(SAMPLES)
    return {"meta": meta, "choices": choices, "tables": tables}


def mirror_server(model):
    """Server state identical to the model (what read_server would return after apply)."""
    choices = {}
    for name, spec in model["choices"].items():
        choices[name.lower()] = {
            "metadata_id": f"c-{name}", "label": spec["label"],
            "description": spec.get("description", ""),
            "options": {o["value"]: {"label": o["label"]} for o in spec["options"]},
        }
    tables = {}
    for t in model["tables"]:
        cols = {}
        primary = ""
        for cname, spec in t["columns"].items():
            want = dv.desired_column(spec)
            have = dict(want)
            have.setdefault("description", "")
            have.setdefault("auditing", True)
            have.setdefault("searchable", True)
            if want["type"] == "lookup":
                have["relationship"] = f"{t['key']}_{cname}"
            cols[cname.lower()] = have
            if spec.get("primary"):
                primary = cname.lower()
        tables[t["key"].lower()] = {
            "metadata_id": f"t-{t['key']}", "label": t["label"],
            "label_plural": t.get("label_plural"), "description": t.get("description", ""),
            "ownership": t.get("ownership", "user"), "table_type": t.get("table_type", "standard"),
            "auditing": t.get("auditing", False), "primary": primary,
            "columns": cols, "unmanaged_columns": [],
            "keys": {k["schema_name"].lower(): {"columns": sorted(c.lower() for c in k["columns"])}
                     for k in t.get("keys") or []},
        }
    components = {c["metadata_id"].lower() for c in choices.values()} | \
                 {t["metadata_id"].lower() for t in tables.values()}
    return {"components": components, "choices": choices, "tables": tables,
            "scope_choices": list(choices), "scope_tables": list(tables)}


class TestValidate(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.model = self.tmp / "dataverse" / "metadata"
        shutil.copytree(SAMPLES, self.model)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def edit(self, rel, old, new):
        p = self.model / rel
        text = p.read_text(encoding="utf-8")
        self.assertIn(old, text)
        p.write_text(text.replace(old, new, 1), encoding="utf-8")

    def errors(self):
        return "\n".join(dv.validate_model(self.model).errors)

    def test_samples_are_valid(self):
        self.assertEqual(dv.validate_model(SAMPLES).errors, [])

    def test_wrong_table_prefix(self):
        self.edit("tables/prfx_crm_Order.dv.metadata.yaml", "key: prfx_crm_Order", "key: prfx_Order")
        self.assertIn("must start with 'prfx_crm_'", self.errors())

    def test_column_with_project_code(self):
        self.edit("tables/prfx_crm_Order.dv.metadata.yaml", "  prfx_Amount:", "  prfx_crm_Amount:")
        self.assertIn("never carry the project code", self.errors())

    def test_missing_choice_reference(self):
        self.edit("tables/prfx_crm_Order.dv.metadata.yaml",
                  "choice: prfx_crm_choice_OrderStatus", "choice: prfx_crm_choice_Missing")
        self.assertIn("is not defined", self.errors())

    def test_two_primary_columns(self):
        self.edit("tables/prfx_crm_Order.dv.metadata.yaml", "    precision: 2", "    precision: 2\n    primary: true")
        self.assertIn("exactly one column", self.errors())

    def test_key_must_match_file_name(self):
        self.edit("tables/prfx_crm_Order.dv.metadata.yaml", "key: prfx_crm_Order", "key: prfx_crm_Orders")
        self.assertIn("must equal the file name", self.errors())

    def test_lookup_requires_on_delete(self):
        self.edit("tables/prfx_crm_Order.dv.metadata.yaml", "    on_delete: restrict", "")
        self.assertIn("'on_delete' is a required property", self.errors())

    def test_non_lookup_ending_in_id_warns(self):
        self.edit("tables/prfx_crm_Order.dv.metadata.yaml", "  prfx_Amount:", "  prfx_SourceId:")
        warnings = "\n".join(dv.validate_model(self.model).warnings)
        self.assertIn("non-lookup column ending in 'Id'", warnings)

    def test_attribute_not_applicable(self):
        self.edit("tables/prfx_crm_Order.dv.metadata.yaml", "    precision: 2", "    precision: 2\n    max_length: 10")
        self.assertIn("'max_length' does not apply to type 'decimal'", self.errors())


class TestDiff(unittest.TestCase):
    def setUp(self):
        self.model = load_samples()
        self.server = mirror_server(self.model)

    def test_empty_server_creates_everything(self):
        empty = {"components": set(), "choices": {}, "tables": {}, "scope_choices": [], "scope_tables": []}
        plan = dv.diff(self.model, empty)
        kinds = [a["kind"] for a in plan["actions"]]
        self.assertTrue(all(a["op"] == "create" for a in plan["actions"]))
        self.assertEqual(kinds, sorted(kinds, key=lambda k: dv.PHASE[k]))
        self.assertEqual(kinds.count("choice"), 3)
        self.assertEqual(kinds.count("table"), 2)
        self.assertIn("lookup", kinds)
        self.assertEqual(plan["blocked"], [])

    def test_identical_server_has_no_changes(self):
        plan = dv.diff(self.model, self.server)
        self.assertEqual(plan, {"actions": [], "blocked": [], "unmanaged": []})

    def test_label_change_is_an_update_with_before_after(self):
        self.server["tables"]["prfx_crm_order"]["columns"]["prfx_amount"]["label"] = "Total"
        plan = dv.diff(self.model, self.server)
        self.assertEqual(len(plan["actions"]), 1)
        a = plan["actions"][0]
        self.assertEqual((a["op"], a["kind"], a["name"]), ("update", "column", "prfx_Amount"))
        self.assertEqual(a["changes"], {"label": ["Total", "Amount"]})

    def test_new_option_is_created(self):
        del self.server["choices"]["prfx_crm_choice_orderstatus"]["options"][100000003]
        plan = dv.diff(self.model, self.server)
        self.assertEqual([(a["op"], a["kind"], a["value"]) for a in plan["actions"]],
                         [("create", "option", 100000003)])

    def test_type_change_is_blocked(self):
        self.server["tables"]["prfx_crm_order"]["columns"]["prfx_amount"]["type"] = "integer"
        plan = dv.diff(self.model, self.server)
        self.assertEqual(plan["actions"], [])
        self.assertEqual(plan["blocked"][0]["field"], "type")

    def test_ownership_change_is_blocked(self):
        self.server["tables"]["prfx_crm_order"]["ownership"] = "org"
        plan = dv.diff(self.model, self.server)
        self.assertEqual(plan["blocked"][0]["field"], "ownership")

    def test_server_only_components_are_unmanaged(self):
        self.server["tables"]["prfx_crm_order"]["unmanaged_columns"].append({"name": "prfx_legacy", "type": "StringType"})
        self.server["choices"]["prfx_crm_choice_orderstatus"]["options"][100000099] = {"label": "Old"}
        self.server["scope_tables"].append("prfx_crm_legacytable")
        plan = dv.diff(self.model, self.server)
        self.assertEqual(plan["actions"], [])
        self.assertEqual(sorted(u["kind"] for u in plan["unmanaged"]), ["column", "option", "table"])

    def test_cascade_change_updates_relationship(self):
        self.server["tables"]["prfx_crm_order"]["columns"]["prfx_customerid"]["on_delete"] = "removelink"
        plan = dv.diff(self.model, self.server)
        a = plan["actions"][0]
        self.assertEqual((a["kind"], a["changes"]), ("lookup", {"on_delete": ["removelink", "restrict"]}))

    def test_missing_solution_membership_is_an_update(self):
        self.server["components"].discard("t-prfx_crm_order")
        plan = dv.diff(self.model, self.server)
        self.assertEqual(plan["actions"][0]["changes"], {"solution": ["absent", "present"]})

    def test_datetime_behavior_only_from_userlocal(self):
        col = self.server["tables"]["prfx_crm_order"]["columns"]["prfx_orderedon"]
        col["behavior"] = "dateonly"
        plan = dv.diff(self.model, self.server)
        self.assertEqual(plan["blocked"][0]["field"], "behavior")


class TestDevGuard(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, name, body):
        (self.root / name).write_text(body, encoding="utf-8")

    def test_missing_env_dev(self):
        with self.assertRaises(dv.GuardError):
            dv.dev_environment(self.root)

    def test_stage_must_be_dev(self):
        self.write(".env.dev", "ENVIRONMENT_STAGE=uat\nDATAVERSE_URL=https://a.crm4.dynamics.com\n")
        with self.assertRaisesRegex(dv.GuardError, "ENVIRONMENT_STAGE=dev"):
            dv.dev_environment(self.root)

    def test_same_url_as_prod(self):
        self.write(".env.dev", "ENVIRONMENT_STAGE=dev\nDATAVERSE_URL=https://a.crm4.dynamics.com/\n")
        self.write(".env.prod", "ENVIRONMENT_STAGE=prod\nDATAVERSE_URL=https://A.crm4.dynamics.com\n")
        with self.assertRaisesRegex(dv.GuardError, ".env.prod"):
            dv.dev_environment(self.root)

    def test_valid_dev(self):
        self.write(".env.dev", "# dev\nENVIRONMENT_STAGE=dev\nDATAVERSE_URL=\"https://a-dev.crm4.dynamics.com\"\nTENANT_ID=t1\n")
        self.write(".env.prod", "ENVIRONMENT_STAGE=prod\nDATAVERSE_URL=https://a.crm4.dynamics.com\n")
        env = dv.dev_environment(self.root)
        self.assertEqual((env["url"], env["tenant"]), ("https://a-dev.crm4.dynamics.com", "t1"))

    def test_managed_solution_is_refused(self):
        class FakeApi:
            url = "https://a-dev.crm4.dynamics.com"

            def get_all(self, path):
                return [{"solutionid": "s1", "uniquename": "x", "ismanaged": True}]
        with self.assertRaisesRegex(dv.GuardError, "MANAGED"):
            dv.check_solution(FakeApi(), "x")


class TestHook(unittest.TestCase):
    HOOK = SKILL / "scripts" / "hook_validate.py"

    def run_hook(self, path):
        payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(path)}})
        return subprocess.run([sys.executable, str(self.HOOK)], input=payload,
                              capture_output=True, text=True)

    def test_ignores_other_files(self):
        res = self.run_hook("/somewhere/app.tsx")
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))

    def test_blocks_invalid_model(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            model = tmp / "metadata"
            shutil.copytree(SAMPLES, model)
            f = model / "tables" / "prfx_crm_Order.dv.metadata.yaml"
            f.write_text(f.read_text(encoding="utf-8").replace("key: prfx_crm_Order", "key: wrong_Order"),
                         encoding="utf-8")
            res = self.run_hook(f)
            self.assertEqual(res.returncode, 2)
            self.assertIn("must equal the file name", res.stderr)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
