#!/usr/bin/env python3
"""
dv_metadata.py — Dataverse metadata as code
===========================================

Reads a model described in ``*.dv.metadata.yaml`` files::

    dataverse/metadata/
    ├── _meta.dv.metadata.yaml          # publisher, project code, solution, locale
    ├── choices.dv.metadata.yaml        # global Choices
    └── tables/<key>.dv.metadata.yaml   # one table per file

and reconciles it with a Dataverse **dev** environment, Terraform style:

    doctor              check tooling, az session, dev guard, solution
    validate <path>     offline structural + semantic validation
    plan <model-dir>    read-only diff: create / update / blocked / unmanaged
    apply <model-dir> --plan-file <f>
                        execute exactly the saved plan (aborts if stale)

Never deletes anything. Components present on the server but absent from the
model are reported as "unmanaged" and left untouched.

Authentication: Azure CLI token (``az login``). Target: ``<repo-root>/.env.dev``
only — the script refuses to run against anything that is not a dev
environment holding the target solution as unmanaged.

Exit codes:
    0  no changes (plan) / success (validate, doctor, apply)
    1  error, validation failure, guard failure, or blocked changes
    2  plan has pending changes

Do not edit this script per project — edit the model files.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:  # reported by doctor / validate
    yaml = None

try:
    import jsonschema
except ImportError:
    jsonschema = None

SKILL_DIR = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = SKILL_DIR / "references" / "schemas"
REQUIREMENTS = Path(__file__).resolve().parent / "requirements.txt"

EXT = ".dv.metadata.yaml"
META_FILE = "_meta" + EXT
CHOICES_FILE = "choices" + EXT
TABLES_DIR = "tables"
PLAN_DIR = ".dv-metadata"
PLAN_VERSION = 1
API_VERSION = "v9.2"
CUSTOM_CHOICE_MIN = 100000000

LOCALE_LCID = {"en": 1033, "fr": 1036, "es": 3082, "de": 1031, "it": 1040, "pt": 2070, "nl": 1043}
BOOL_LABELS = {
    "en": ("Yes", "No"), "fr": ("Oui", "Non"), "es": ("Sí", "No"), "de": ("Ja", "Nein"),
    "it": ("Sì", "No"), "pt": ("Sim", "Não"), "nl": ("Ja", "Nee"),
}

STRING_TYPES = {"text", "email", "url", "phone", "autonumber"}
NUMERIC_TYPES = {"integer", "decimal", "money"}
CHOICE_TYPES = {"choice", "multichoice"}

# Model type -> Web API metadata type
ODATA_TYPE = {
    "text": "StringAttributeMetadata", "email": "StringAttributeMetadata",
    "url": "StringAttributeMetadata", "phone": "StringAttributeMetadata",
    "autonumber": "StringAttributeMetadata", "multiline": "MemoAttributeMetadata",
    "integer": "IntegerAttributeMetadata", "decimal": "DecimalAttributeMetadata",
    "money": "MoneyAttributeMetadata", "boolean": "BooleanAttributeMetadata",
    "date": "DateTimeAttributeMetadata", "datetime": "DateTimeAttributeMetadata",
    "choice": "PicklistAttributeMetadata", "multichoice": "MultiSelectPicklistAttributeMetadata",
    "lookup": "LookupAttributeMetadata", "file": "FileAttributeMetadata",
    "image": "ImageAttributeMetadata",
}
TYPED_SELECT = {
    "StringAttributeMetadata": "MaxLength,FormatName",
    "MemoAttributeMetadata": "MaxLength",
    "IntegerAttributeMetadata": "MinValue,MaxValue",
    "DecimalAttributeMetadata": "MinValue,MaxValue,Precision",
    "MoneyAttributeMetadata": "MinValue,MaxValue,Precision",
    "BooleanAttributeMetadata": "DefaultValue",
    "DateTimeAttributeMetadata": "Format,DateTimeBehavior",
    "PicklistAttributeMetadata": "DefaultFormValue",
    "MultiSelectPicklistAttributeMetadata": "DefaultFormValue",
    "LookupAttributeMetadata": "Targets",
    "FileAttributeMetadata": "MaxSizeInKB",
    "ImageAttributeMetadata": "MaxSizeInKB",
}
TYPED_EXPAND = {
    "PicklistAttributeMetadata": "GlobalOptionSet($select=Name)",
    "MultiSelectPicklistAttributeMetadata": "GlobalOptionSet($select=Name)",
}

REQ_TO_API = {"none": "None", "recommended": "Recommended", "required": "ApplicationRequired"}
REQ_FROM_API = {"None": "none", "Recommended": "recommended",
                "ApplicationRequired": "required", "SystemRequired": "system"}
CASCADE_TO_API = {"removelink": "RemoveLink", "cascade": "Cascade", "restrict": "Restrict"}
CASCADE_FROM_API = {v: k for k, v in CASCADE_TO_API.items()}
BEHAVIOR_TO_API = {"userlocal": "UserLocal", "dateonly": "DateOnly",
                   "timezoneindependent": "TimeZoneIndependent"}
BEHAVIOR_FROM_API = {v: k for k, v in BEHAVIOR_TO_API.items()}
STRING_FORMAT_TO_API = {"text": "Text", "email": "Email", "url": "Url", "phone": "Phone",
                        "autonumber": "Text"}
STRING_FORMAT_FROM_API = {"Text": "text", "Email": "email", "Url": "url", "Phone": "phone"}
TYPE_FROM_API = {
    "MemoType": "multiline", "IntegerType": "integer", "DecimalType": "decimal",
    "MoneyType": "money", "BooleanType": "boolean", "PicklistType": "choice",
    "MultiSelectPicklistType": "multichoice", "LookupType": "lookup",
    "FileType": "file", "ImageType": "image",
}

# Phase order used to sort plan actions.
PHASE = {"choice": 0, "option": 1, "table": 2, "column": 3, "lookup": 4, "key": 5}


class GuardError(Exception):
    """Raised when the dev-only guard refuses to run."""


class ApiError(Exception):
    def __init__(self, status, code, message, path):
        super().__init__(f"{status} {code or ''} {path}: {message}".strip())
        self.status = status
        self.code = code
        self.message = message


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
_TTY = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if _TTY else text


def green(t): return _c("92", t)
def yellow(t): return _c("93", t)
def red(t): return _c("91", t)
def grey(t): return _c("90", t)
def bold(t): return _c("1", t)


# --------------------------------------------------------------------------- #
# Model loading
# --------------------------------------------------------------------------- #
def _require_yaml():
    if yaml is None:
        raise SystemExit(f"ERROR: PyYAML is not installed — pip install -r {REQUIREMENTS}")


def load_yaml(path: Path):
    _require_yaml()
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def find_model_dir(start: Path):
    """Return the folder holding _meta.dv.metadata.yaml for a dir or file path."""
    p = start.resolve()
    if p.is_file():
        p = p.parent
    for candidate in [p, *p.parents][:4]:
        if (candidate / META_FILE).is_file():
            return candidate
    return None


def table_files(model_dir: Path):
    tdir = model_dir / TABLES_DIR
    return sorted(tdir.glob("*" + EXT)) if tdir.is_dir() else []


def file_key(path: Path):
    return path.name[: -len(EXT)]


def load_model(model_dir: Path):
    meta = load_yaml(model_dir / META_FILE) or {}
    choices = {}
    cpath = model_dir / CHOICES_FILE
    if cpath.is_file():
        choices = (load_yaml(cpath) or {}).get("choices") or {}
    tables = []
    for tf in table_files(model_dir):
        data = load_yaml(tf)
        if isinstance(data, dict):
            tables.append(data)
    return meta, choices, tables


def prefixes(meta):
    pub = meta.get("publisher") or {}
    prefix = (pub.get("prefix") or "").lower()
    pc = (pub.get("project_code") or "").lower()
    scope = f"{prefix}_{pc}_" if pc else f"{prefix}_"
    return prefix, pc, scope, scope + "choice_"


def model_lcid(meta):
    return LOCALE_LCID.get((meta.get("locale") or "en").lower(), 1033)


# --------------------------------------------------------------------------- #
# Validation (offline)
# --------------------------------------------------------------------------- #
class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, msg):
        self.errors.append(f"[{where}] {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"[{where}] {msg}")


def _structural(report, data, schema_name, where):
    if jsonschema is None:
        report.warn(where, "jsonschema not installed — structural validation skipped")
        return
    with open(SCHEMAS_DIR / schema_name, "r", encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft7Validator(schema)
    for e in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        field = " > ".join(str(p) for p in e.absolute_path) or "(root)"
        report.error(where, f"{e.message} (at {field})")


APPLICABLE = {
    "max_length": STRING_TYPES | {"multiline"},
    "min": NUMERIC_TYPES, "max": NUMERIC_TYPES, "precision": {"decimal", "money"},
    "behavior": {"datetime"}, "format": {"autonumber"},
    "max_size_kb": {"file", "image"}, "default": {"boolean", "choice"},
    "choice": CHOICE_TYPES, "target": {"lookup"}, "on_delete": {"lookup"},
}


def validate_model(model_dir: Path) -> Report:
    r = Report()
    meta_path = model_dir / META_FILE
    meta = load_yaml(meta_path)
    if not isinstance(meta, dict):
        r.error(META_FILE, "root must be a YAML mapping")
        return r
    _structural(r, meta, "meta.schema.json", META_FILE)
    prefix, pc, table_prefix, choice_prefix = prefixes(meta)
    if not prefix:
        return r

    for f in sorted(model_dir.glob("*" + EXT)):
        if f.name not in (META_FILE, CHOICES_FILE):
            r.warn(f.name, f"unexpected file — only {META_FILE}, {CHOICES_FILE} and {TABLES_DIR}/*{EXT} are read")

    # ── Choices ──────────────────────────────────────────────────────────────
    choice_values = {}
    cpath = model_dir / CHOICES_FILE
    if cpath.is_file():
        cdata = load_yaml(cpath)
        if not isinstance(cdata, dict):
            r.error(CHOICES_FILE, "root must be a YAML mapping")
            cdata = {}
        _structural(r, cdata, "choices.schema.json", CHOICES_FILE)
        for ckey, spec in (cdata.get("choices") or {}).items():
            where = f"{CHOICES_FILE}:{ckey}"
            spec = spec or {}
            if ckey.lower() in choice_values:
                r.error(where, "duplicate global Choice (names are case-insensitive)")
            if not ckey.lower().startswith(choice_prefix):
                r.error(where, f"global Choice must start with '{choice_prefix}'")
            label = (spec.get("label") or "").strip()
            if label and not label.endswith(" Choice"):
                r.warn(where, f"Display Name should end with ' Choice' (e.g. '{label} Choice')")
            values, labels = set(), set()
            for opt in spec.get("options") or []:
                v = opt.get("value")
                if not isinstance(v, int):
                    continue
                if v in values:
                    r.error(where, f"duplicate option value {v}")
                values.add(v)
                if v < CUSTOM_CHOICE_MIN:
                    r.warn(where, f"option value {v} < {CUSTOM_CHOICE_MIN} — custom values start at {CUSTOM_CHOICE_MIN}")
                lab = (opt.get("label") or "").lower()
                if lab in labels:
                    r.warn(where, f"duplicate option label '{opt.get('label')}'")
                labels.add(lab)
            choice_values[ckey.lower()] = values

    # ── Tables ───────────────────────────────────────────────────────────────
    loaded = []
    seen_tables = set()
    for tf in table_files(model_dir):
        where = f"{TABLES_DIR}/{tf.name}"
        data = load_yaml(tf)
        if not isinstance(data, dict):
            r.error(where, "root must be a YAML mapping")
            continue
        _structural(r, data, "table.schema.json", where)
        key = data.get("key") or ""
        if key != file_key(tf):
            r.error(where, f"'key: {key}' must equal the file name ('{file_key(tf)}{EXT}')")
        if key.lower() in seen_tables:
            r.error(where, f"duplicate table '{key}' (names are case-insensitive)")
        seen_tables.add(key.lower())
        if key and not key.lower().startswith(table_prefix):
            r.error(where, f"table must start with '{table_prefix}'")
        loaded.append((where, data))

    for where, t in loaded:
        columns = t.get("columns") or {}
        if t.get("ownership") == "org":
            r.warn(where, "ownership: org — requires explicit double confirmation from the user (irreversible)")
        if t.get("auditing") is True:
            r.warn(where, "auditing: true — requires explicit double confirmation (Dataverse storage cost)")
        if not t.get("description"):
            r.warn(where, "table has no description")

        primaries = [c for c, cd in columns.items() if (cd or {}).get("primary")]
        if len(primaries) != 1:
            r.error(where, f"exactly one column must have 'primary: true' (found {len(primaries)})")

        lowered = set()
        for cname, col in columns.items():
            col = col or {}
            cw = f"{where}:{cname}"
            low = cname.lower()
            ctype = col.get("type") or ""
            if low in lowered:
                r.error(cw, "duplicate column (names are case-insensitive)")
            lowered.add(low)
            if not low.startswith(prefix + "_"):
                r.error(cw, f"column must start with '{prefix}_'")
            if pc and low.startswith(table_prefix):
                r.error(cw, f"columns never carry the project code — use '{prefix}_<Name>'")
            local = low[len(prefix) + 1:] if low.startswith(prefix + "_") else low

            for attr, types in APPLICABLE.items():
                if attr in col and ctype and ctype not in types:
                    r.error(cw, f"'{attr}' does not apply to type '{ctype}'")
            if col.get("required") is not None and col.get("required_level"):
                r.error(cw, "use either 'required' or 'required_level', not both")
            if col.get("primary") and ctype not in ("text", "autonumber"):
                r.error(cw, "primary column must be of type text or autonumber")
            if col.get("primary") and ctype == "autonumber" and (col.get("required") or col.get("required_level") == "required"):
                r.warn(cw, "an AutoNumber primary column should be optional — the value is generated")
            if ctype == "text" and col.get("max_length", 0) > 4000:
                r.error(cw, "text max_length cannot exceed 4000 — use multiline")
            if ctype == "money":
                r.warn(cw, "money column — requires explicit double confirmation (currency machinery); prefer decimal")
            if ctype == "datetime" and col.get("behavior") == "dateonly":
                r.warn(cw, "datetime with behavior dateonly — use type: date")
            if col.get("auditing") is True:
                r.warn(cw, "column auditing: true — requires explicit double confirmation")

            if ctype in CHOICE_TYPES:
                ref = (col.get("choice") or "").lower()
                if ref and ref not in choice_values:
                    r.error(cw, f"'choice: {col.get('choice')}' is not defined in {CHOICES_FILE}")
                elif ref and "default" in col and col["default"] not in choice_values[ref]:
                    r.error(cw, f"default {col['default']} is not an option of {col.get('choice')}")
                if not local.endswith("code"):
                    r.warn(cw, "choice column should end with 'Code' (e.g. prfx_StatusCode)")
            if ctype == "lookup":
                target = (col.get("target") or "").lower()
                if target.startswith(prefix + "_") and target not in seen_tables:
                    r.error(cw, f"'target: {col.get('target')}' is not a table of the model")
                if not local.endswith("id"):
                    r.warn(cw, "lookup column should end with 'Id' (e.g. prfx_CustomerId)")
            elif local.endswith("id"):
                r.warn(cw, "non-lookup column ending in 'Id' collides with lookup navigation properties — use another stem (e.g. SourceRef)")
            if ctype == "boolean" and not (local.startswith("is") or local.startswith("has")):
                r.warn(cw, "boolean column should start with 'Is' or 'Has'")
            if ctype in CHOICE_TYPES | {"lookup"} and not col.get("description"):
                r.warn(cw, "non-trivial column (choice/lookup) has no description")

        for i, k in enumerate(t.get("keys") or []):
            kw = f"{where}:keys[{i}]"
            for kc in k.get("columns") or []:
                if kc.lower() not in lowered:
                    r.error(kw, f"key column '{kc}' is not a column of the table")
    return r


def validate_path(path: Path) -> Report:
    model_dir = find_model_dir(path)
    if model_dir is not None:
        return validate_model(model_dir)
    r = Report()
    data = load_yaml(path)
    name = path.name
    if not isinstance(data, dict):
        r.error(name, "root must be a YAML mapping")
        return r
    if "choices" in data:
        _structural(r, data, "choices.schema.json", name)
    elif "key" in data:
        _structural(r, data, "table.schema.json", name)
    elif "publisher" in data:
        _structural(r, data, "meta.schema.json", name)
    else:
        r.error(name, "unrecognised file (not _meta, choices nor table)")
    r.warn(name, f"no {META_FILE} found above this file — cross-file checks skipped")
    return r


# --------------------------------------------------------------------------- #
# Dev-only guard
# --------------------------------------------------------------------------- #
def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    for candidate in [p, *p.parents]:
        if (candidate / ".env.dev").is_file() or (candidate / ".git").exists():
            return candidate
    raise GuardError("cannot find the repository root (no .env.dev or .git above the model)")


def read_dotenv(path: Path):
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        if k.startswith("export "):
            k = k[7:].strip()
        v = v.strip()
        if " #" in v:
            v = v.split(" #", 1)[0].strip()
        values[k] = v.strip("'\"")
    return values


def _norm_url(u):
    return (u or "").strip().lower().rstrip("/")


def dev_environment(repo_root: Path):
    """Local half of the guard: .env.dev only, stage=dev, URL distinct from uat/prod."""
    env_path = repo_root / ".env.dev"
    if not env_path.is_file():
        raise GuardError(f"{env_path} not found — this tool only runs against the dev environment "
                         f"described in .env.dev (see ppbp-init)")
    env = read_dotenv(env_path)
    if (env.get("ENVIRONMENT_STAGE") or "").lower() != "dev":
        raise GuardError(f".env.dev must declare ENVIRONMENT_STAGE=dev (found "
                         f"'{env.get('ENVIRONMENT_STAGE', '')}') — refusing to run")
    url = _norm_url(env.get("DATAVERSE_URL"))
    if not url.startswith("https://"):
        raise GuardError(".env.dev must declare DATAVERSE_URL=https://<org>.crm<n>.dynamics.com")
    for other in (".env.uat", ".env.prod"):
        op = repo_root / other
        if op.is_file() and _norm_url(read_dotenv(op).get("DATAVERSE_URL")) == url:
            raise GuardError(f"DATAVERSE_URL in .env.dev is the same as in {other} — refusing to run")
    return {"url": url, "tenant": env.get("TENANT_ID") or None, "env_file": str(env_path)}


# --------------------------------------------------------------------------- #
# Azure CLI auth + Web API client
# --------------------------------------------------------------------------- #
def az_path():
    return shutil.which("az") or shutil.which("az.cmd")


def az_json(args):
    exe = az_path()
    if not exe:
        raise GuardError("Azure CLI (az) not found — install it, then run: az login")
    proc = subprocess.run([exe, *args, "-o", "json"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise GuardError("az " + " ".join(args) + " failed: " + (proc.stderr.strip() or proc.stdout.strip())
                         + "\n  → run: az login" + (" --tenant <TENANT_ID>" if "--tenant" in args else ""))
    return json.loads(proc.stdout or "null")


class Api:
    def __init__(self, env):
        self.url = env["url"]
        self.tenant = env["tenant"]
        self.base = f"{self.url}/api/data/{API_VERSION}"
        self._token = None
        self._expires = 0.0

    def token(self):
        if self._token and time.time() < self._expires - 120:
            return self._token
        args = ["account", "get-access-token", "--resource", self.url]
        if self.tenant:
            args += ["--tenant", self.tenant]
        data = az_json(args)
        self._token = data["accessToken"]
        exp = data.get("expires_on")
        self._expires = float(exp) if exp else time.time() + 1800
        return self._token

    def _headers(self, extra=None):
        h = {
            "Authorization": f"Bearer {self.token()}",
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "User-Agent": "ppbp-dv-metadata",
        }
        h.update(extra or {})
        return h

    def _url(self, path):
        if path.startswith("http"):
            return path
        if "?" in path:
            p, q = path.split("?", 1)
            path = p + "?" + urllib.parse.quote(q, safe="=&$(),'/;")
        return f"{self.base}/{path}"

    def request(self, method, path, body=None, headers=None, return_id=False):
        """Send a Web API request. With return_id, return the MetadataId/GUID from the
        OData-EntityId response header instead of the body (no read-after-write)."""
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        for attempt in range(6):
            req = urllib.request.Request(self._url(path), data=data, method=method,
                                         headers=self._headers(headers))
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    raw = resp.read().decode("utf-8")
                    if return_id:
                        entity = resp.headers.get("OData-EntityId") or ""
                        return entity.rsplit("(", 1)[-1].rstrip(")") if "(" in entity else None
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as e:
                raw = e.read().decode("utf-8", "replace")
                code, msg = None, raw
                try:
                    err = json.loads(raw).get("error", {})
                    code, msg = err.get("code"), err.get("message", raw)
                except ValueError:
                    pass
                low = (msg or "").lower()
                transient = (
                    e.code == 429
                    or code in ("0x80072560", "0x80040216", "0x80060891", "0x80060888")
                    or ("another" in low and ("customization" in low or "running" in low))
                )
                if transient and attempt < 5:
                    wait = int(e.headers.get("Retry-After") or 0) or 10 * (attempt + 1)
                    print(grey(f"    … transient error {code or e.code}, retrying in {wait}s"), flush=True)
                    time.sleep(wait)
                    continue
                raise ApiError(e.code, code, msg, path) from None
        raise ApiError(0, None, "retries exhausted", path)

    def get(self, path):
        return self.request("GET", path)

    def get_all(self, path):
        items, data = [], self.get(path)
        while True:
            items.extend(data.get("value", []))
            nxt = data.get("@odata.nextLink")
            if not nxt:
                return items
            data = self.get(nxt)

    def get_or_none(self, path):
        try:
            return self.get(path)
        except ApiError as e:
            if e.status == 404:
                return None
            raise


def check_solution(api, solution):
    """Server half of the guard: the solution exists and is unmanaged."""
    rows = api.get_all("solutions?$select=solutionid,uniquename,ismanaged"
                       f"&$filter=uniquename eq '{solution}'")
    if not rows:
        raise GuardError(f"solution '{solution}' not found in {api.url} — create it first "
                         f"(official skill: dataverse:dv-solution)")
    if rows[0].get("ismanaged"):
        raise GuardError(f"solution '{solution}' is MANAGED in {api.url} — this is not a dev "
                         f"environment. Metadata changes are only allowed on an unmanaged dev solution.")
    return rows[0]["solutionid"]


# --------------------------------------------------------------------------- #
# Server state (normalised to the model vocabulary)
# --------------------------------------------------------------------------- #
def label_of(label_obj, lcid):
    if not isinstance(label_obj, dict):
        return None
    for loc in label_obj.get("LocalizedLabels") or []:
        if loc.get("LanguageCode") == lcid:
            return loc.get("Label")
    user = label_obj.get("UserLocalizedLabel") or {}
    return user.get("Label")


def _managed_bool(prop):
    return bool((prop or {}).get("Value")) if isinstance(prop, dict) else None


def normalise_column(attr, typed, lcid):
    tname = ((attr.get("AttributeTypeName") or {}).get("Value")) or attr.get("AttributeType") or ""
    col = {
        "label": label_of(attr.get("DisplayName"), lcid),
        "description": label_of(attr.get("Description"), lcid) or "",
        "required_level": REQ_FROM_API.get((attr.get("RequiredLevel") or {}).get("Value"), "none"),
        "auditing": _managed_bool(attr.get("IsAuditEnabled")),
        "searchable": _managed_bool(attr.get("IsValidForAdvancedFind")),
        "metadata_id": attr.get("MetadataId"),
    }
    t = typed or {}
    if tname == "StringType":
        if attr.get("AutoNumberFormat"):
            col["type"] = "autonumber"
            col["format"] = attr.get("AutoNumberFormat")
        else:
            fmt = (t.get("FormatName") or {}).get("Value", "Text")
            col["type"] = STRING_FORMAT_FROM_API.get(fmt, f"string:{fmt}")
        col["max_length"] = t.get("MaxLength")
    elif tname == "DateTimeType":
        behavior = BEHAVIOR_FROM_API.get((t.get("DateTimeBehavior") or {}).get("Value"), "userlocal")
        col["type"] = "date" if behavior == "dateonly" else "datetime"
        col["behavior"] = behavior
    else:
        col["type"] = TYPE_FROM_API.get(tname, tname.replace("Type", "").lower() or "unknown")
    if col["type"] == "multiline":
        col["max_length"] = t.get("MaxLength")
    if col["type"] in NUMERIC_TYPES:
        col["min"], col["max"] = t.get("MinValue"), t.get("MaxValue")
        if col["type"] != "integer":
            col["precision"] = t.get("Precision")
    if col["type"] == "boolean":
        col["default"] = t.get("DefaultValue")
    if col["type"] in CHOICE_TYPES:
        col["choice"] = ((t.get("GlobalOptionSet") or {}).get("Name") or "").lower() or None
        if col["type"] == "choice":
            col["default"] = t.get("DefaultFormValue")
    if col["type"] == "lookup":
        targets = t.get("Targets") or []
        col["target"] = targets[0].lower() if len(targets) == 1 else ",".join(sorted(targets))
    if col["type"] in ("file", "image"):
        col["max_size_kb"] = t.get("MaxSizeInKB")
    return col


def read_server(api, meta, choices, tables):
    lcid = model_lcid(meta)
    prefix, pc, scope, choice_prefix = prefixes(meta)
    solution = meta["publisher"]["solution"]
    state = {"solution_id": check_solution(api, solution), "components": set(),
             "choices": {}, "tables": {}, "scope_choices": [], "scope_tables": []}

    for row in api.get_all("solutioncomponents?$select=objectid,componenttype"
                           f"&$filter=_solutionid_value eq {state['solution_id']} "
                           "and (componenttype eq 1 or componenttype eq 9)"):
        state["components"].add(row["objectid"].lower())

    # Global Choices
    wanted = {c.lower() for c in choices}
    for row in api.get_all("GlobalOptionSetDefinitions?$select=Name,MetadataId"):
        name = (row.get("Name") or "").lower()
        if name.startswith(scope):
            state["scope_choices"].append(name)
        if name in wanted or name.startswith(scope):
            full = api.get(f"GlobalOptionSetDefinitions({row['MetadataId']})")
            state["choices"][name] = {
                "metadata_id": row["MetadataId"],
                "label": label_of(full.get("DisplayName"), lcid),
                "description": label_of(full.get("Description"), lcid) or "",
                "options": {o["Value"]: {"label": label_of(o.get("Label"), lcid)}
                            for o in full.get("Options") or []},
            }

    # Tables
    custom = api.get_all("EntityDefinitions?$select=LogicalName,MetadataId"
                         "&$filter=IsCustomEntity eq true")
    existing = {row["LogicalName"].lower(): row["MetadataId"] for row in custom}
    state["scope_tables"] = sorted(n for n in existing if n.startswith(scope))
    for t in tables:
        logical = t["key"].lower()
        exists = logical in existing or api.get_or_none(
            f"EntityDefinitions(LogicalName='{logical}')?$select=MetadataId") is not None
        if not exists:
            continue
        state["tables"][logical] = read_table(api, logical, t, lcid, prefix)
    return state


def read_table(api, logical, model_table, lcid, prefix):
    base = f"EntityDefinitions(LogicalName='{logical}')"
    e = api.get(base + "?$select=MetadataId,LogicalName,DisplayName,DisplayCollectionName,"
                       "Description,OwnershipType,IsActivity,TableType,IsAuditEnabled,PrimaryNameAttribute")
    ownership = {"UserOwned": "user", "TeamOwned": "user",
                 "OrganizationOwned": "org"}.get(e.get("OwnershipType"), str(e.get("OwnershipType")).lower())
    ttype = "activity" if e.get("IsActivity") else (e.get("TableType") or "Standard").lower()
    table = {
        "metadata_id": e["MetadataId"],
        "label": label_of(e.get("DisplayName"), lcid),
        "label_plural": label_of(e.get("DisplayCollectionName"), lcid),
        "description": label_of(e.get("Description"), lcid) or "",
        "ownership": ownership,
        "table_type": ttype,
        "auditing": _managed_bool(e.get("IsAuditEnabled")),
        "primary": (e.get("PrimaryNameAttribute") or "").lower(),
        "columns": {}, "unmanaged_columns": [], "keys": {},
    }
    attrs = api.get_all(base + "/Attributes?$select=LogicalName,MetadataId,AttributeType,"
                               "AttributeTypeName,DisplayName,Description,RequiredLevel,IsAuditEnabled,"
                               "IsValidForAdvancedFind,IsCustomAttribute,AttributeOf,AutoNumberFormat")
    model_cols = {c.lower(): spec for c, spec in (model_table.get("columns") or {}).items()}
    present = {a["LogicalName"].lower(): a for a in attrs}

    needed = {}
    for name in model_cols:
        if name not in present:
            continue
        tname = ((present[name].get("AttributeTypeName") or {}).get("Value")) or ""
        odata = {"StringType": "StringAttributeMetadata", "MemoType": "MemoAttributeMetadata",
                 "IntegerType": "IntegerAttributeMetadata", "DecimalType": "DecimalAttributeMetadata",
                 "MoneyType": "MoneyAttributeMetadata", "BooleanType": "BooleanAttributeMetadata",
                 "DateTimeType": "DateTimeAttributeMetadata", "PicklistType": "PicklistAttributeMetadata",
                 "MultiSelectPicklistType": "MultiSelectPicklistAttributeMetadata",
                 "LookupType": "LookupAttributeMetadata", "FileType": "FileAttributeMetadata",
                 "ImageType": "ImageAttributeMetadata"}.get(tname)
        if odata:
            needed.setdefault(odata, set()).add(name)
    typed = {}
    for odata, names in needed.items():
        q = f"{base}/Attributes/Microsoft.Dynamics.CRM.{odata}?$select=LogicalName,{TYPED_SELECT[odata]}"
        if odata in TYPED_EXPAND:
            q += f"&$expand={TYPED_EXPAND[odata]}"
        for row in api.get_all(q):
            if row["LogicalName"].lower() in names:
                typed[row["LogicalName"].lower()] = row

    rels = api.get_all(base + "/ManyToOneRelationships?$select=SchemaName,ReferencingAttribute,"
                              "ReferencedEntity,CascadeConfiguration,MetadataId")
    rel_by_attr = {(r.get("ReferencingAttribute") or "").lower(): r for r in rels}

    for name, a in present.items():
        if name in model_cols:
            col = normalise_column(a, typed.get(name), lcid)
            if col["type"] == "lookup" and name in rel_by_attr:
                rel = rel_by_attr[name]
                col["on_delete"] = CASCADE_FROM_API.get(
                    (rel.get("CascadeConfiguration") or {}).get("Delete"),
                    str((rel.get("CascadeConfiguration") or {}).get("Delete")).lower())
                col["relationship"] = rel.get("SchemaName")
            table["columns"][name] = col
        elif (a.get("IsCustomAttribute") and not a.get("AttributeOf")
              and name.startswith(prefix + "_") and name != table["primary"]):
            tname = ((a.get("AttributeTypeName") or {}).get("Value")) or a.get("AttributeType")
            table["unmanaged_columns"].append({"name": name, "type": tname})

    for k in api.get_all(base + "/Keys?$select=SchemaName,LogicalName,KeyAttributes,MetadataId"):
        table["keys"][(k.get("SchemaName") or k.get("LogicalName")).lower()] = {
            "columns": sorted(c.lower() for c in k.get("KeyAttributes") or []),
        }
    return table


# --------------------------------------------------------------------------- #
# Diff (pure — no I/O)
# --------------------------------------------------------------------------- #
def _req_level(col):
    if col.get("required_level"):
        return col["required_level"]
    return "required" if col.get("required") else "none"


def _same(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a)), abs(float(b)))
    return a == b


def desired_column(col):
    """Model column → dict of the fields this tool manages for it."""
    ctype = col["type"]
    if ctype == "datetime" and col.get("behavior") == "dateonly":
        ctype = "date"
    d = {"type": ctype, "label": col["label"], "required_level": _req_level(col)}
    for f in ("description", "auditing", "searchable", "max_length", "min", "max",
              "precision", "format", "default", "max_size_kb"):
        if f in col:
            d[f] = col[f]
    if ctype == "datetime" and "behavior" in col:
        d["behavior"] = col["behavior"]
    if ctype in CHOICE_TYPES:
        d["choice"] = col["choice"].lower()
    if ctype == "lookup":
        d["target"] = col["target"].lower()
        d["on_delete"] = col["on_delete"]
    return d


# Fields whose change cannot be applied in place.
IMMUTABLE_COLUMN = {
    "type": "column type cannot be changed in place (needs a new column + data migration)",
    "choice": "the global Choice bound to a column cannot be changed in place",
    "target": "a lookup target cannot be changed in place",
    "max_size_kb": "file/image max size cannot be changed after creation",
}


def diff(model, server):
    """Compare the model with the normalised server state.

    Returns {"actions": [...], "blocked": [...], "unmanaged": [...]}. Pure function —
    unit-testable with hand-built dicts.
    """
    meta, choices, tables = model["meta"], model["choices"], model["tables"]
    components = server.get("components", set())
    actions, blocked, unmanaged = [], [], []

    def act(op, kind, name, table=None, **extra):
        a = {"op": op, "kind": kind, "name": name}
        if table:
            a["table"] = table
        a.update(extra)
        actions.append(a)

    # ── Global Choices ───────────────────────────────────────────────────────
    model_choice_names = set()
    for cname, spec in choices.items():
        low = cname.lower()
        model_choice_names.add(low)
        srv = server["choices"].get(low)
        if srv is None:
            act("create", "choice", cname, detail=f"{len(spec['options'])} options")
            continue
        changes = {}
        if srv["label"] != spec["label"]:
            changes["label"] = [srv["label"], spec["label"]]
        if "description" in spec and srv["description"] != spec["description"]:
            changes["description"] = [srv["description"], spec["description"]]
        if changes:
            act("update", "choice", cname, changes=changes)
        if srv.get("metadata_id") and srv["metadata_id"].lower() not in components:
            act("update", "choice", cname, changes={"solution": ["absent", "present"]},
                solution_component=9)
        model_values = set()
        for opt in spec["options"]:
            v = opt["value"]
            model_values.add(v)
            so = srv["options"].get(v)
            if so is None:
                act("create", "option", f"{cname}:{v}", choice=cname, value=v, label=opt["label"],
                    detail=f"\"{opt['label']}\"")
            elif so["label"] != opt["label"]:
                act("update", "option", f"{cname}:{v}", choice=cname, value=v,
                    changes={"label": [so["label"], opt["label"]]})
        for v in sorted(set(srv["options"]) - model_values):
            unmanaged.append({"kind": "option", "name": f"{cname}:{v}",
                              "detail": srv["options"][v]["label"]})
    for name in server.get("scope_choices", []):
        if name not in model_choice_names:
            unmanaged.append({"kind": "choice", "name": name})

    # ── Tables / columns / lookups / keys ────────────────────────────────────
    model_table_names = set()
    for t in tables:
        key = t["key"]
        low = key.lower()
        model_table_names.add(low)
        cols = t.get("columns") or {}
        primary = next(c for c, s in cols.items() if (s or {}).get("primary"))
        srv = server["tables"].get(low)
        if srv is None:
            act("create", "table", key, detail=f"primary {primary}: {cols[primary]['type']}")
            for cname, spec in cols.items():
                if cname == primary:
                    continue
                kind = "lookup" if spec["type"] == "lookup" else "column"
                detail = (f"→ {spec['target']} (on_delete {spec['on_delete']})" if kind == "lookup"
                          else spec["type"])
                act("create", kind, cname, table=key, detail=detail)
            for k in t.get("keys") or []:
                act("create", "key", k["schema_name"], table=key, detail="(" + ", ".join(k["columns"]) + ")")
            continue

        # immutable table properties
        for field, want in (("ownership", t.get("ownership", "user")),
                            ("table_type", t.get("table_type", "standard"))):
            if srv[field] != want:
                blocked.append({"kind": "table", "name": key, "field": field, "server": srv[field],
                                "model": want, "reason": f"table {field} cannot be changed after creation"})
        if srv["primary"] != primary.lower():
            blocked.append({"kind": "table", "name": key, "field": "primary", "server": srv["primary"],
                            "model": primary.lower(), "reason": "the primary name column cannot be changed"})
        changes = {}
        if srv["label"] != t["label"]:
            changes["label"] = [srv["label"], t["label"]]
        if "label_plural" in t and srv["label_plural"] != t["label_plural"]:
            changes["label_plural"] = [srv["label_plural"], t["label_plural"]]
        if "description" in t and srv["description"] != t["description"]:
            changes["description"] = [srv["description"], t["description"]]
        want_audit = bool(t.get("auditing", False))
        if srv["auditing"] is not None and srv["auditing"] != want_audit:
            changes["auditing"] = [srv["auditing"], want_audit]
        if changes:
            act("update", "table", key, changes=changes)
        if srv.get("metadata_id") and srv["metadata_id"].lower() not in components:
            act("update", "table", key, changes={"solution": ["absent", "present"]},
                solution_component=1)

        for cname, spec in cols.items():
            want = desired_column(spec)
            have = srv["columns"].get(cname.lower())
            kind = "lookup" if want["type"] == "lookup" else "column"
            if have is None:
                detail = (f"→ {spec['target']} (on_delete {spec['on_delete']})" if kind == "lookup"
                          else want["type"])
                act("create", kind, cname, table=key, detail=detail)
                continue
            col_changes, col_blocked = {}, False
            for field, reason in IMMUTABLE_COLUMN.items():
                if field in want and not _same(have.get(field), want[field]):
                    blocked.append({"kind": kind, "name": f"{key}.{cname}", "field": field,
                                    "server": have.get(field), "model": want[field], "reason": reason})
                    col_blocked = True
            if col_blocked:
                continue
            if "behavior" in want and have.get("behavior") != want["behavior"]:
                if have.get("behavior") == "userlocal":
                    col_changes["behavior"] = [have.get("behavior"), want["behavior"]]
                else:
                    blocked.append({"kind": kind, "name": f"{key}.{cname}", "field": "behavior",
                                    "server": have.get("behavior"), "model": want["behavior"],
                                    "reason": "DateTime behavior can only change once, from userlocal"})
            for field in ("label", "description", "required_level", "auditing", "searchable",
                          "max_length", "min", "max", "precision", "format", "default"):
                if field not in want:
                    continue
                if field == "required_level" and have.get(field) == "system":
                    continue
                if not _same(have.get(field), want[field]):
                    col_changes[field] = [have.get(field), want[field]]
            if col_changes:
                act("update", "column", cname, table=key, changes=col_changes, type=want["type"])
            if kind == "lookup" and have.get("on_delete") != want["on_delete"]:
                act("update", "lookup", cname, table=key, relationship=have.get("relationship"),
                    changes={"on_delete": [have.get("on_delete"), want["on_delete"]]})

        for u in srv.get("unmanaged_columns", []):
            unmanaged.append({"kind": "column", "name": f"{key}.{u['name']}", "detail": u["type"]})

        model_keys = set()
        for k in t.get("keys") or []:
            klow = k["schema_name"].lower()
            model_keys.add(klow)
            sk = srv["keys"].get(klow)
            want_cols = sorted(c.lower() for c in k["columns"])
            if sk is None:
                act("create", "key", k["schema_name"], table=key, detail="(" + ", ".join(k["columns"]) + ")")
            elif sk["columns"] != want_cols:
                blocked.append({"kind": "key", "name": f"{key}.{k['schema_name']}", "field": "columns",
                                "server": sk["columns"], "model": want_cols,
                                "reason": "alternate key columns cannot be changed in place"})
        for kname in sorted(set(srv["keys"]) - model_keys):
            unmanaged.append({"kind": "key", "name": f"{key}.{kname}",
                              "detail": "(" + ", ".join(srv["keys"][kname]["columns"]) + ")"})

    for name in server.get("scope_tables", []):
        if name not in model_table_names:
            unmanaged.append({"kind": "table", "name": name})

    actions.sort(key=lambda a: PHASE[a["kind"]])  # stable: keeps model order within a phase
    return {"actions": actions, "blocked": blocked, "unmanaged": unmanaged}


# --------------------------------------------------------------------------- #
# Plan rendering
# --------------------------------------------------------------------------- #
def _fmt(v):
    return json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else f'"{v}"'


def render_plan(plan):
    print(bold("Dataverse metadata plan"))
    print(f"  env      : {plan['env_url']} ({plan['env_file']})")
    print(f"  solution : {plan['solution']} (unmanaged)")
    if plan.get("az_account"):
        print(f"  az user  : {plan['az_account']}")
    acts = plan["actions"]
    if acts:
        print()
    for a in acts:
        target = f"{a['table']}.{a['name']}" if a.get("table") else a["name"]
        if a["op"] == "create":
            print(f"  {green('+ create')}  {a['kind']:<7} {target}" + (f"  {grey(a['detail'])}" if a.get("detail") else ""))
        else:
            print(f"  {yellow('~ update')}  {a['kind']:<7} {target}")
            for field, (old, new) in a.get("changes", {}).items():
                print(f"              {field}: {_fmt(old)} → {_fmt(new)}")
    if plan["blocked"]:
        print("\n" + red("Blocked — never applied; align the model with the server or change it manually:"))
        for b in plan["blocked"]:
            print(f"  {red('!')} {b['kind']:<7} {b['name']}  {b['field']}: {_fmt(b['server'])} → {_fmt(b['model'])}")
            print(grey(f"              {b['reason']}"))
    if plan["unmanaged"]:
        print("\n" + grey("Unmanaged — on the server but not in the model (reported only, never deleted):"))
        for u in plan["unmanaged"]:
            print(f"  ? {u['kind']:<7} {u['name']}" + (f"  {grey(str(u['detail']))}" if u.get("detail") else ""))
    creates = sum(1 for a in acts if a["op"] == "create")
    updates = len(acts) - creates
    print(f"\nSummary: {creates} to create, {updates} to update, "
          f"{len(plan['blocked'])} blocked, {len(plan['unmanaged'])} unmanaged.")
    if not acts and not plan["blocked"]:
        print(green("No changes — the environment matches the model."))


def _model_hash(model_dir: Path):
    h = hashlib.sha256()
    for f in [model_dir / META_FILE, model_dir / CHOICES_FILE, *table_files(model_dir)]:
        if f.is_file():
            h.update(f.name.encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def _canonical(plan):
    return json.dumps({"env_url": plan["env_url"], "solution": plan["solution"],
                       "actions": plan["actions"], "blocked": plan["blocked"]},
                      sort_keys=True, ensure_ascii=False, default=str)


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def _validated_model(model_arg):
    model_dir = find_model_dir(Path(model_arg))
    if model_dir is None:
        raise SystemExit(f"ERROR: no {META_FILE} found at or above {model_arg}")
    report = validate_model(model_dir)
    if report.errors:
        for e in report.errors:
            print(red("  ✗ ") + e, file=sys.stderr)
        raise SystemExit(f"ERROR: the model is invalid ({len(report.errors)} error(s)) — run validate and fix it first")
    meta, choices, tables = load_model(model_dir)
    return model_dir, {"meta": meta, "choices": choices, "tables": tables}


def compute_plan(model_arg):
    model_dir, model = _validated_model(model_arg)
    env = dev_environment(find_repo_root(model_dir))
    api = Api(env)
    account = az_json(["account", "show"])
    state = read_server(api, model["meta"], model["choices"], model["tables"])
    result = diff(model, state)
    plan = {
        "plan_version": PLAN_VERSION,
        "created": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "env_url": env["url"], "env_file": env["env_file"],
        "az_account": f"{(account or {}).get('user', {}).get('name', '?')} (tenant {(account or {}).get('tenantId', '?')})",
        "solution": model["meta"]["publisher"]["solution"],
        "model_dir": str(model_dir), "model_hash": _model_hash(model_dir),
        **result,
    }
    return model_dir, model, env, api, plan


def plan_exit_code(plan):
    if plan["blocked"]:
        return 1
    return 2 if plan["actions"] else 0


def cmd_validate(args):
    report = validate_path(Path(args.path))
    for w in report.warnings:
        print(yellow("  ⚠ ") + w)
    for e in report.errors:
        print(red("  ✗ ") + e)
    if report.errors:
        print(red(f"\nInvalid — {len(report.errors)} error(s), {len(report.warnings)} warning(s)."))
        return 1
    print(green(f"Valid — {len(report.warnings)} warning(s)."))
    return 0


def cmd_plan(args):
    model_dir, _model, _env, _api, plan = compute_plan(args.model)
    out = Path(args.out) if args.out else find_repo_root(model_dir) / PLAN_DIR / "plan.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    if args.json:
        print(json.dumps({**plan, "plan_file": str(out)}, indent=2, ensure_ascii=False, default=str))
    else:
        render_plan(plan)
        print(grey(f"\nPlan saved to {out}"))
        if plan["actions"] and not plan["blocked"]:
            print(grey(f"Apply it with: dv_metadata.py apply {args.model} --plan-file {out}"))
    return plan_exit_code(plan)


def cmd_doctor(args):
    ok = True

    def line(passed, label, fix=""):
        nonlocal ok
        print(("  " + green("✓") if passed else "  " + red("✗")) + f" {label}")
        if not passed:
            ok = False
            if fix:
                print(grey(f"      → {fix}"))

    print(bold("dv_metadata doctor"))
    line(sys.version_info >= (3, 9), f"Python ≥ 3.9 ({sys.version.split()[0]})", "install Python 3.9+")
    line(yaml is not None, "pyyaml installed", f"pip install -r {REQUIREMENTS}")
    line(jsonschema is not None, "jsonschema installed", f"pip install -r {REQUIREMENTS}")
    line(az_path() is not None, "Azure CLI (az) on PATH", "install the Azure CLI")
    model_dir = find_model_dir(Path(args.model)) if args.model else None
    try:
        root = find_repo_root(model_dir or Path.cwd())
        env = dev_environment(root)
        line(True, f"dev guard: {env['env_file']} → {env['url']}")
    except GuardError as e:
        line(False, "dev guard", str(e))
        return 1
    try:
        account = az_json(["account", "show"])
        line(True, f"az session: {account.get('user', {}).get('name')} (tenant {account.get('tenantId')})")
        if env["tenant"] and account.get("tenantId", "").lower() != env["tenant"].lower():
            print(yellow(f"      ⚠ active az tenant differs from TENANT_ID in .env.dev — the token is requested for {env['tenant']}"))
        api = Api(env)
        api.token()
        line(True, "access token for the dev environment")
        who = api.get("WhoAmI")
        line(True, f"WhoAmI: user {who.get('UserId')}")
        if model_dir:
            meta = load_yaml(model_dir / META_FILE)
            sol = meta["publisher"]["solution"]
            check_solution(api, sol)
            line(True, f"solution '{sol}' exists and is unmanaged")
    except GuardError as e:
        line(False, "Dataverse access", str(e))
    except ApiError as e:
        line(False, "Dataverse access", str(e))
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
# Apply
# --------------------------------------------------------------------------- #
def make_label(text, lcid):
    return {"@odata.type": "Microsoft.Dynamics.CRM.Label",
            "LocalizedLabels": [{"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel",
                                 "Label": text, "LanguageCode": lcid}]}


def _bool_prop(value):
    return {"Value": bool(value), "CanBeChanged": True}


class Applier:
    def __init__(self, api, model):
        self.api = api
        self.meta = model["meta"]
        self.choices = {k.lower(): (k, v) for k, v in model["choices"].items()}
        self.tables = {t["key"].lower(): t for t in model["tables"]}
        self.lcid = model_lcid(self.meta)
        self.locale = (self.meta.get("locale") or "en").lower()
        self.prefix = prefixes(self.meta)[0]
        self.solution = self.meta["publisher"]["solution"]
        self.touched_tables, self.touched_choices = set(), set()

    # -- helpers --------------------------------------------------------------
    def post(self, path, body, solution=True, return_id=False):
        h = {"MSCRM.SolutionName": self.solution} if solution else {}
        return self.api.request("POST", path, body, h, return_id=return_id)

    def put(self, path, body):
        body = {k: v for k, v in body.items() if not k.startswith("@odata.context")}
        return self.api.request("PUT", path, body,
                                {"MSCRM.MergeLabels": "true", "MSCRM.SolutionName": self.solution})

    def add_component(self, component_id, component_type):
        self.post("AddSolutionComponent", {
            "ComponentId": component_id, "ComponentType": component_type,
            "SolutionUniqueName": self.solution, "AddRequiredComponents": False,
            "DoNotIncludeSubcomponents": False,
        }, solution=False)

    def choice_id(self, name):
        return self.api.get(f"GlobalOptionSetDefinitions(Name='{name}')?$select=MetadataId")["MetadataId"]

    def table_id(self, logical):
        return self.api.get(f"EntityDefinitions(LogicalName='{logical.lower()}')?$select=MetadataId")["MetadataId"]

    def column_spec(self, table, column):
        cols = self.tables[table.lower()]["columns"]
        return next(spec for name, spec in cols.items() if name.lower() == column.lower())

    # -- payloads -------------------------------------------------------------
    def attr_payload(self, name, col):
        ctype = col["type"]
        if ctype == "datetime" and col.get("behavior") == "dateonly":
            ctype = "date"
        p = {"@odata.type": f"Microsoft.Dynamics.CRM.{ODATA_TYPE[ctype]}",
             "SchemaName": name,
             "DisplayName": make_label(col["label"], self.lcid),
             "RequiredLevel": {"Value": REQ_TO_API[_req_level(col)]}}
        if col.get("description"):
            p["Description"] = make_label(col["description"], self.lcid)
        if "auditing" in col:
            p["IsAuditEnabled"] = _bool_prop(col["auditing"])
        if "searchable" in col:
            p["IsValidForAdvancedFind"] = _bool_prop(col["searchable"])
        if ctype in STRING_TYPES:
            p["MaxLength"] = col.get("max_length", 200 if ctype in ("text", "url") else 100)
            p["FormatName"] = {"Value": STRING_FORMAT_TO_API[ctype]}
            if ctype == "autonumber":
                p["AutoNumberFormat"] = col["format"]
        elif ctype == "multiline":
            p["MaxLength"] = col.get("max_length", 4000)
            p["Format"] = "Text"
        elif ctype == "integer":
            p["Format"] = "None"
            p["MinValue"] = int(col.get("min", -2147483648))
            p["MaxValue"] = int(col.get("max", 2147483647))
        elif ctype in ("decimal", "money"):
            p["Precision"] = col.get("precision", 2)
            p["MinValue"] = float(col.get("min", -100000000000 if ctype == "decimal" else 0))
            p["MaxValue"] = float(col.get("max", 100000000000 if ctype == "decimal" else 1000000000))
            if ctype == "money":
                p["PrecisionSource"] = 2
        elif ctype == "boolean":
            yes, no = BOOL_LABELS.get(self.locale, BOOL_LABELS["en"])
            p["DefaultValue"] = bool(col.get("default", False))
            p["OptionSet"] = {"@odata.type": "Microsoft.Dynamics.CRM.BooleanOptionSetMetadata",
                              "TrueOption": {"Value": 1, "Label": make_label(yes, self.lcid)},
                              "FalseOption": {"Value": 0, "Label": make_label(no, self.lcid)},
                              "IsGlobal": False}
        elif ctype in ("date", "datetime"):
            behavior = "dateonly" if ctype == "date" else col.get("behavior", "userlocal")
            p["Format"] = "DateOnly" if behavior == "dateonly" else "DateAndTime"
            p["DateTimeBehavior"] = {"Value": BEHAVIOR_TO_API[behavior]}
            p["ImeMode"] = "Inactive"
        elif ctype in CHOICE_TYPES:
            # Bind by MetadataId — see ppbp-dv-global-choices.
            p["GlobalOptionSet@odata.bind"] = f"GlobalOptionSetDefinitions({self.choice_id(col['choice'])})"
            if ctype == "choice" and col.get("default") is not None:
                p["DefaultFormValue"] = int(col["default"])
        elif ctype in ("file", "image"):
            if "max_size_kb" in col:
                p["MaxSizeInKB"] = col["max_size_kb"]
            if ctype == "file" and "max_size_kb" not in col:
                p["MaxSizeInKB"] = 32768
            if ctype == "image":
                p["IsPrimaryImage"] = False
        return p

    # -- executors ------------------------------------------------------------
    def create_choice(self, a):
        name, spec = self.choices[a["name"].lower()]
        options = []
        for o in spec["options"]:
            opt = {"Value": o["value"], "Label": make_label(o["label"], self.lcid)}
            if o.get("color"):
                opt["Color"] = o["color"]
            options.append(opt)
        choice_id = self.post("GlobalOptionSetDefinitions", {
            "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata",
            "Name": name, "OptionSetType": "Picklist", "IsGlobal": True,
            "DisplayName": make_label(spec["label"], self.lcid),
            "Description": make_label(spec.get("description", spec["label"]), self.lcid),
            "Options": options,
        }, return_id=True)
        # MSCRM.SolutionName does not attach global Choices — add explicitly (type 9),
        # using the id from the create response: a lookup right after creation can 404.
        self.add_component(choice_id or self.choice_id(name), 9)
        self.touched_choices.add(name)

    def update_choice(self, a):
        name, spec = self.choices[a["name"].lower()]
        if a.get("solution_component"):
            self.add_component(self.choice_id(name), 9)
            return
        mid = self.choice_id(name)
        body = self.api.get(f"GlobalOptionSetDefinitions({mid})")
        body.pop("Options", None)
        if "label" in a["changes"]:
            body["DisplayName"] = make_label(spec["label"], self.lcid)
        if "description" in a["changes"]:
            body["Description"] = make_label(spec["description"], self.lcid)
        self.put(f"GlobalOptionSetDefinitions({mid})", body)
        self.touched_choices.add(name)

    def create_option(self, a):
        self.post("InsertOptionValue", {
            "OptionSetName": a["choice"], "Value": a["value"],
            "Label": make_label(a["label"], self.lcid), "SolutionUniqueName": self.solution,
        }, solution=False)
        self.touched_choices.add(a["choice"])

    def update_option(self, a):
        self.post("UpdateOptionValue", {
            "OptionSetName": a["choice"], "Value": a["value"],
            "Label": make_label(a["changes"]["label"][1], self.lcid),
            "MergeLabels": True, "SolutionUniqueName": self.solution,
        }, solution=False)
        self.touched_choices.add(a["choice"])

    def create_table(self, a):
        t = self.tables[a["name"].lower()]
        pname, pcol = next((n, c) for n, c in t["columns"].items() if c.get("primary"))
        primary = {"@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
                   "SchemaName": pname, "DisplayName": make_label(pcol["label"], self.lcid),
                   "RequiredLevel": {"Value": REQ_TO_API[_req_level(pcol)]},
                   "MaxLength": pcol.get("max_length", 100), "FormatName": {"Value": "Text"},
                   "IsPrimaryName": True}
        if pcol["type"] == "autonumber":
            primary["AutoNumberFormat"] = pcol["format"]
        if pcol.get("description"):
            primary["Description"] = make_label(pcol["description"], self.lcid)
        ttype = t.get("table_type", "standard")
        body = {
            "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
            "SchemaName": t["key"],
            "DisplayName": make_label(t["label"], self.lcid),
            "DisplayCollectionName": make_label(t.get("label_plural", t["label"] + "s"), self.lcid),
            "Description": make_label(t.get("description", t["label"]), self.lcid),
            "OwnershipType": "OrganizationOwned" if t.get("ownership") == "org" else "UserOwned",
            "IsActivity": ttype == "activity",
            "HasActivities": False, "HasNotes": True,
            "IsAuditEnabled": _bool_prop(t.get("auditing", False)),
            "Attributes": [primary],
        }
        if ttype == "elastic":
            body["TableType"] = "Elastic"
        # Created directly in the solution through the MSCRM.SolutionName header — no
        # read-after-write lookup (the new table is not queryable immediately: 0x80060888).
        self.post("EntityDefinitions", body)
        self.touched_tables.add(t["key"].lower())

    def update_table(self, a):
        t = self.tables[a["name"].lower()]
        if a.get("solution_component"):
            self.add_component(self.table_id(t["key"]), 1)
            return
        body = self.api.get(f"EntityDefinitions(LogicalName='{t['key'].lower()}')")
        ch = a["changes"]
        if "label" in ch:
            body["DisplayName"] = make_label(t["label"], self.lcid)
        if "label_plural" in ch:
            body["DisplayCollectionName"] = make_label(t["label_plural"], self.lcid)
        if "description" in ch:
            body["Description"] = make_label(t["description"], self.lcid)
        if "auditing" in ch:
            body["IsAuditEnabled"] = {**(body.get("IsAuditEnabled") or {}), "Value": ch["auditing"][1]}
        self.put(f"EntityDefinitions({body['MetadataId']})", body)
        self.touched_tables.add(t["key"].lower())

    def create_column(self, a):
        spec = self.column_spec(a["table"], a["name"])
        self.post(f"EntityDefinitions(LogicalName='{a['table'].lower()}')/Attributes",
                  self.attr_payload(a["name"], spec))
        self.touched_tables.add(a["table"].lower())

    def update_column(self, a):
        odata = ODATA_TYPE[a["type"]]
        tbase = f"EntityDefinitions(LogicalName='{a['table'].lower()}')"
        body = self.api.get(f"{tbase}/Attributes(LogicalName='{a['name'].lower()}')/Microsoft.Dynamics.CRM.{odata}")
        body["@odata.type"] = f"Microsoft.Dynamics.CRM.{odata}"
        for field, (_old, new) in a["changes"].items():
            if field == "label":
                body["DisplayName"] = make_label(new, self.lcid)
            elif field == "description":
                body["Description"] = make_label(new, self.lcid)
            elif field == "required_level":
                body["RequiredLevel"] = {**(body.get("RequiredLevel") or {}), "Value": REQ_TO_API[new]}
            elif field == "auditing":
                body["IsAuditEnabled"] = {**(body.get("IsAuditEnabled") or {}), "Value": new}
            elif field == "searchable":
                body["IsValidForAdvancedFind"] = {**(body.get("IsValidForAdvancedFind") or {}), "Value": new}
            elif field == "max_length":
                body["MaxLength"] = new
            elif field == "min":
                body["MinValue"] = new
            elif field == "max":
                body["MaxValue"] = new
            elif field == "precision":
                body["Precision"] = new
            elif field == "format":
                body["AutoNumberFormat"] = new
            elif field == "default":
                body["DefaultValue" if a["type"] == "boolean" else "DefaultFormValue"] = new
            elif field == "behavior":
                body["DateTimeBehavior"] = {"Value": BEHAVIOR_TO_API[new]}
                body["Format"] = "DateOnly" if new == "dateonly" else "DateAndTime"
        attr_id = body["MetadataId"]
        self.put(f"{tbase}/Attributes({attr_id})", body)
        self.touched_tables.add(a["table"].lower())

    def create_lookup(self, a):
        spec = self.column_spec(a["table"], a["name"])
        lookup = {"@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
                  "SchemaName": a["name"],
                  "DisplayName": make_label(spec["label"], self.lcid),
                  "RequiredLevel": {"Value": REQ_TO_API[_req_level(spec)]}}
        if spec.get("description"):
            lookup["Description"] = make_label(spec["description"], self.lcid)
        local = a["name"].split("_", 1)[1]
        rel_name = f"{a['table']}_{local}"  # deterministic, always publisher-prefixed
        self.post("RelationshipDefinitions", {
            "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata",
            "SchemaName": rel_name,
            "ReferencedEntity": spec["target"].lower(),
            "ReferencingEntity": a["table"].lower(),
            "CascadeConfiguration": {"Assign": "NoCascade", "Delete": CASCADE_TO_API[spec["on_delete"]],
                                     "Merge": "NoCascade", "Reparent": "NoCascade",
                                     "Share": "NoCascade", "Unshare": "NoCascade"},
            "Lookup": lookup,
        })
        self.touched_tables.add(a["table"].lower())

    def update_lookup(self, a):
        rel = a.get("relationship")
        if not rel:
            raise RuntimeError(f"relationship for {a['table']}.{a['name']} not found on the server")
        body = self.api.get(f"RelationshipDefinitions(SchemaName='{rel}')"
                            "/Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata")
        body["@odata.type"] = "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata"
        body["CascadeConfiguration"]["Delete"] = CASCADE_TO_API[a["changes"]["on_delete"][1]]
        self.put(f"RelationshipDefinitions({body['MetadataId']})", body)
        self.touched_tables.add(a["table"].lower())

    def create_key(self, a):
        t = self.tables[a["table"].lower()]
        k = next(k for k in t.get("keys") or [] if k["schema_name"].lower() == a["name"].lower())
        # Index is built asynchronously by Dataverse.
        self.post(f"EntityDefinitions(LogicalName='{a['table'].lower()}')/Keys", {
            "SchemaName": k["schema_name"],
            "DisplayName": make_label(k.get("label", k["schema_name"]), self.lcid),
            "KeyAttributes": [c.lower() for c in k["columns"]],
        })

    def run(self, a):
        handler = getattr(self, f"{a['op']}_{a['kind']}")
        handler(a)

    def publish(self):
        if not (self.touched_tables or self.touched_choices):
            return
        xml = "<importexportxml>"
        if self.touched_tables:
            xml += "<entities>" + "".join(f"<entity>{t}</entity>" for t in sorted(self.touched_tables)) + "</entities>"
        if self.touched_choices:
            xml += "<optionsets>" + "".join(f"<optionset>{c.lower()}</optionset>"
                                            for c in sorted(self.touched_choices)) + "</optionsets>"
        xml += "</importexportxml>"
        self.post("PublishXml", {"ParameterXml": xml}, solution=False)


def cmd_apply(args):
    saved = json.loads(Path(args.plan_file).read_text(encoding="utf-8"))
    if saved.get("plan_version") != PLAN_VERSION:
        print(red("ERROR: unsupported plan file version — re-run plan."), file=sys.stderr)
        return 1
    _model_dir, model, _env, api, fresh = compute_plan(args.model)
    if _canonical(fresh) != _canonical(saved):
        print(red("ERROR: stale plan — the model or the server changed since it was computed.\n"
                  "Re-run plan, review it again, and apply the new plan file."), file=sys.stderr)
        return 1
    if fresh["blocked"]:
        print(red("ERROR: the plan contains blocked changes — fix the model, re-plan, then apply."), file=sys.stderr)
        return 1
    if not fresh["actions"]:
        print(green("No changes to apply."))
        return 0

    applier = Applier(api, model)
    done, failure = 0, None
    print(bold(f"Applying {len(fresh['actions'])} change(s) to {fresh['env_url']} ({fresh['solution']})"))
    for a in fresh["actions"]:
        target = f"{a['table']}.{a['name']}" if a.get("table") else a["name"]
        try:
            applier.run(a)
            done += 1
            print(f"  {green('✓')} {a['op']:<6} {a['kind']:<7} {target}", flush=True)
        except (ApiError, RuntimeError, KeyError, StopIteration) as e:
            failure = e
            print(f"  {red('✗')} {a['op']:<6} {a['kind']:<7} {target}\n      {e}", flush=True)
            break
    try:
        applier.publish()
        print(f"  {green('✓')} publish")
    except ApiError as e:
        print(f"  {red('✗')} publish: {e}")
        failure = failure or e

    print(f"\n{done}/{len(fresh['actions'])} change(s) applied.")
    if failure:
        print(red("Stopped at the first failure. Fix the cause, re-run plan, then apply the new plan."))
        return 1
    _, _, _, _, after = compute_plan(args.model)
    if after["actions"] or after["blocked"]:
        print(yellow("Post-apply plan is not empty (metadata propagation can lag) — re-run plan in a minute:"))
        render_plan(after)
        return 1
    print(green("Post-apply plan is empty — the environment matches the model."))
    return 0


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(prog="dv_metadata.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("doctor", help="check tooling, az session, dev guard and solution")
    p.add_argument("model", nargs="?", help="model dir (enables the solution check)")
    p = sub.add_parser("validate", help="offline validation of the model or one file")
    p.add_argument("path")
    p = sub.add_parser("plan", help="read-only diff against the dev environment")
    p.add_argument("model")
    p.add_argument("--out", help=f"plan file (default <repo-root>/{PLAN_DIR}/plan.json)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p = sub.add_parser("apply", help="execute a saved plan (aborts if stale)")
    p.add_argument("model")
    p.add_argument("--plan-file", required=True)
    args = ap.parse_args(argv)
    try:
        return {"doctor": cmd_doctor, "validate": cmd_validate,
                "plan": cmd_plan, "apply": cmd_apply}[args.cmd](args)
    except GuardError as e:
        print(red(f"REFUSED: {e}"), file=sys.stderr)
        return 1
    except ApiError as e:
        print(red(f"Dataverse error: {e}"), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
