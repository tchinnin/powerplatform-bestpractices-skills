# Global Choices in solutions — Web API guide

## The problem

A `POST GlobalOptionSetDefinitions` call creates the choice in the environment but **outside any solution**. The choice will not be exported and is effectively unmanaged unless you explicitly attach it.

## Correct procedure — 2 mandatory calls

### Step 1 — Create the choice

```http
POST /api/data/v9.2/GlobalOptionSetDefinitions
{
  "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata",
  "IsGlobal": true,
  "Name": "prefix_choice_name",
  "DisplayName": { "LocalizedLabels": [{ "Label": "My Choice", "LanguageCode": 1033 }] },
  "OptionSetType": "Picklist",
  "Options": [
    { "Value": 100000000, "Label": { "LocalizedLabels": [{ "Label": "Option A", "LanguageCode": 1033 }] } }
  ]
}
```

Extract the `MetadataId` from the response header:

```python
entity_id = response.headers["OData-EntityId"]
# "https://.../GlobalOptionSetDefinitions(xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)"
metadata_id = entity_id.split("(")[-1].rstrip(")")
```

### Step 2 — Attach to the solution

`ComponentType 9` = Global OptionSet.

```http
POST /api/data/v9.2/AddSolutionComponent
{
  "ComponentId": "<metadata_id>",
  "ComponentType": 9,
  "SolutionUniqueName": "<solution_unique_name>",
  "AddRequiredComponents": false
}
```

## Binding a Picklist column to a Global Choice

Use `GlobalOptionSet@odata.bind` — anything else raises `0x80048403`.

```python
# Resolve the MetadataId (always fetch fresh — see execution order below)
resp = session.get(
    f"{base_url}/GlobalOptionSetDefinitions(Name='prefix_choice_name')?$select=MetadataId"
)
metadata_id = resp.json()["MetadataId"]

# Create the column
payload = {
    "@odata.type": "Microsoft.Dynamics.CRM.PicklistAttributeMetadata",
    "SchemaName": "prefix_StatusCode",
    "DisplayName": { "LocalizedLabels": [{ "Label": "Status", "LanguageCode": 1033 }] },
    "RequiredLevel": { "Value": "None", "ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings" },
    "GlobalOptionSet@odata.bind": f"/GlobalOptionSetDefinitions({metadata_id})"
}
session.post(f"{base_url}/EntityDefinitions(LogicalName='prefix_table')/Attributes", json=payload)
```

**Wrong syntaxes that all raise `0x80048403`:**

| Syntax | Why it fails |
|---|---|
| `"OptionSet": {"IsGlobal": true, ...}` | Creates a local option set — `IsGlobal` is ignored on nested objects |
| `"OptionSet": {"MetadataId": "..."}` | Same error |
| `"OptionSet@odata.bind": "..."` | Wrong navigation property name |

## Execution order in an idempotent script

```
Phase 0 — Create Global Choices  →  AddSolutionComponent (ComponentType 9)
Phase 1 — Create Tables          →  AddSolutionComponent (ComponentType 1)
           ↓ sleep 20 s  (metadata propagation)
Phase 2 — Resolve choice MetadataIds fresh
       →  Create Columns (GlobalOptionSet@odata.bind)
```

Always resolve `MetadataId` values **at the start of Phase 2**, after the propagation pause. Do not cache them from Phase 0 — they may not be available yet in Phase 2 if the script is restarted mid-run.

## Complete idempotent example

```python
"""
Idempotent script — Global Choices + Tables + Columns in a solution.
Set DATAVERSE_TOKEN, BASE_URL, and SOLUTION_NAME before running.
"""

import os
import time
import requests

BASE_URL = "https://yourorg.crm.dynamics.com/api/data/v9.2"
SOLUTION_NAME = "YourSolutionUniqueName"
PFX = "prfx"
LANG = 1033


def label(text):
    return {"LocalizedLabels": [{"Label": text, "LanguageCode": LANG}]}


def session_from_token(token):
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    return s


def add_to_solution(s, component_id, component_type):
    s.post(f"{BASE_URL}/AddSolutionComponent", json={
        "ComponentId": component_id,
        "ComponentType": component_type,
        "SolutionUniqueName": SOLUTION_NAME,
        "AddRequiredComponents": False,
    }).raise_for_status()


# ── Phase 0 ──────────────────────────────────────────────────────────────────

CHOICES = [
    {"name": f"{PFX}_choice_ProjectStatus", "display": "Project Status Choice",
     "options": [(100000000, "Draft"), (100000001, "Active"), (100000002, "Closed")]},
    {"name": f"{PFX}_choice_InvoiceType", "display": "Invoice Type Choice",
     "options": [(100000000, "Standard"), (100000001, "Credit Note")]},
]


def phase_0(s):
    print("Phase 0 — Global Choices")
    for c in CHOICES:
        exists = s.get(
            f"{BASE_URL}/GlobalOptionSetDefinitions(Name='{c['name']}')?$select=MetadataId",
            headers={"Prefer": "return=minimal"},
        ).status_code == 200
        if exists:
            print(f"  SKIP  {c['name']}")
            continue
        resp = s.post(f"{BASE_URL}/GlobalOptionSetDefinitions", json={
            "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata",
            "IsGlobal": True,
            "Name": c["name"],
            "DisplayName": label(c["display"]),
            "OptionSetType": "Picklist",
            "Options": [
                {"Value": v, "Label": label(lbl)} for v, lbl in c["options"]
            ],
        })
        resp.raise_for_status()
        metadata_id = resp.headers["OData-EntityId"].split("(")[-1].rstrip(")")
        add_to_solution(s, metadata_id, component_type=9)
        print(f"  OK    {c['name']}  ({metadata_id})")


# ── Phase 1 ──────────────────────────────────────────────────────────────────

TABLES = [
    {"schema": f"{PFX}_Project", "display": "Project", "plural": "Projects"},
    {"schema": f"{PFX}_Invoice", "display": "Invoice", "plural": "Invoices"},
]


def phase_1(s):
    print("Phase 1 — Tables")
    for t in TABLES:
        logical = t["schema"].lower()
        exists = s.get(
            f"{BASE_URL}/EntityDefinitions(LogicalName='{logical}')?$select=LogicalName",
            headers={"Prefer": "return=minimal"},
        ).status_code == 200
        if exists:
            print(f"  SKIP  {t['schema']}")
            continue
        resp = s.post(f"{BASE_URL}/EntityDefinitions", json={
            "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata",
            "SchemaName": t["schema"],
            "DisplayName": label(t["display"]),
            "DisplayCollectionName": label(t["plural"]),
            "OwnershipType": "UserOwned",
            "HasActivities": False,
            "HasNotes": False,
            "PrimaryNameAttribute": f"{logical}_name",
            "Attributes": [{
                "@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata",
                "IsPrimaryName": True,
                "SchemaName": f"{t['schema']}_Name",
                "DisplayName": label("Name"),
                "RequiredLevel": {"Value": "None", "ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings"},
                "MaxLength": 100,
            }],
        })
        resp.raise_for_status()
        metadata_id = resp.headers["OData-EntityId"].split("(")[-1].rstrip(")")
        add_to_solution(s, metadata_id, component_type=1)
        print(f"  OK    {t['schema']}  ({metadata_id})")

    print("  Waiting 20 s for metadata propagation...")
    time.sleep(20)


# ── Phase 2 ──────────────────────────────────────────────────────────────────

COLUMNS = [
    {"table": f"{PFX}_project", "schema": f"{PFX}_StatusCode",
     "display": "Project Status", "type": "picklist", "choice": f"{PFX}_choice_ProjectStatus"},
    {"table": f"{PFX}_invoice", "schema": f"{PFX}_TypeCode",
     "display": "Invoice Type", "type": "picklist", "choice": f"{PFX}_choice_InvoiceType"},
    {"table": f"{PFX}_invoice", "schema": f"{PFX}_ProjectId",
     "display": "Project", "type": "lookup", "target": f"{PFX}_project"},
]


def resolve_choice_ids(s, columns):
    names = {c["choice"] for c in columns if c["type"] == "picklist"}
    ids = {}
    for name in names:
        resp = s.get(f"{BASE_URL}/GlobalOptionSetDefinitions(Name='{name}')?$select=MetadataId")
        resp.raise_for_status()
        ids[name] = resp.json()["MetadataId"]
        print(f"  Resolved {name} → {ids[name]}")
    return ids


def phase_2(s):
    print("Phase 2 — Columns")
    choice_ids = resolve_choice_ids(s, COLUMNS)

    for col in COLUMNS:
        exists = s.get(
            f"{BASE_URL}/EntityDefinitions(LogicalName='{col['table']}')"
            f"/Attributes(LogicalName='{col['schema'].lower()}')?$select=LogicalName",
            headers={"Prefer": "return=minimal"},
        ).status_code == 200
        if exists:
            print(f"  SKIP  {col['table']}.{col['schema']}")
            continue

        if col["type"] == "picklist":
            payload = {
                "@odata.type": "Microsoft.Dynamics.CRM.PicklistAttributeMetadata",
                "SchemaName": col["schema"],
                "DisplayName": label(col["display"]),
                "RequiredLevel": {"Value": "None", "ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings"},
                "GlobalOptionSet@odata.bind": f"/GlobalOptionSetDefinitions({choice_ids[col['choice']]})",
            }
        else:  # lookup
            payload = {
                "@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata",
                "SchemaName": col["schema"],
                "DisplayName": label(col["display"]),
                "RequiredLevel": {"Value": "None", "ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings"},
                "Targets": [col["target"]],
            }

        s.post(
            f"{BASE_URL}/EntityDefinitions(LogicalName='{col['table']}')/Attributes",
            json=payload,
        ).raise_for_status()
        print(f"  OK    {col['table']}.{col['schema']}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    s = session_from_token(os.environ["DATAVERSE_TOKEN"])
    phase_0(s)
    phase_1(s)
    phase_2(s)
    print("Done.")
```
