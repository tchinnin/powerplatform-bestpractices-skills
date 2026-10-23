# Prerequisites for `dv_metadata.py`

`validate` runs offline and only needs the Python dependencies. `doctor`, `plan` and `apply` also need an Azure CLI session and the dev environment descriptor.

## 1. Python + dependencies

Python ≥ 3.9 in a virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r <plugin>/skills/ppbp-dv-metadata-as-code/scripts/requirements.txt
```

`pyyaml` reads the model and `jsonschema` validates it. No Dataverse SDK or auth package is needed.

## 2. Azure CLI session (recommended for any Python run against Dataverse)

The tool asks the Azure CLI for a token (`az account get-access-token --resource <DATAVERSE_URL>`). It never stores credentials. Sign in once per session:

```sh
az login --tenant <TENANT_ID>
```

When `TENANT_ID` is set in `.env.dev`, the token is requested for that tenant even if the active `az` subscription belongs to another one.

## 3. `.env.dev` at the repo root

Created by `ppbp-init`, committed, and free of secrets:

```dotenv
ENVIRONMENT_STAGE=dev
DATAVERSE_URL=https://<org>-dev.crm4.dynamics.com
TENANT_ID=<tenant-guid>
```

The tool reads **only** this file. It ignores `.env`, the local file `dataverse:dv-connect` writes for its own tooling. It refuses to run if `ENVIRONMENT_STAGE` is not `dev`, or if the URL matches `.env.uat` or `.env.prod`.

## 4. Unmanaged solution in dev

`publisher.solution` in `_meta.dv.metadata.yaml` must exist in the dev environment as an **unmanaged** solution whose publisher uses `publisher.prefix`. Create it with `dataverse:dv-solution`.

## 5. Check

```sh
python3 <plugin>/skills/ppbp-dv-metadata-as-code/scripts/dv_metadata.py doctor dataverse/metadata
```

Every line must show ✓ before you run `plan`.

## 6. Offline tests (tool maintainers)

```sh
python3 -m unittest discover -s <plugin>/skills/ppbp-dv-metadata-as-code/tests -v
```
