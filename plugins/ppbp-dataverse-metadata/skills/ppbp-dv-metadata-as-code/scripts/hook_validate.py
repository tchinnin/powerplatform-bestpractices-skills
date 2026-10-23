#!/usr/bin/env python3
"""
PostToolUse hook — validates the Dataverse metadata model after an agent writes
or edits a *.dv.metadata.yaml file.

* Any other file: exits 0 immediately (cost = Python start-up only).
* Errors: printed to stderr, exit 2 — the agent sees them and fixes the file.
* Warnings only: returned as additional context, exit 0.
* Missing pyyaml/jsonschema: one-line notice, exit 0 — never blocks a developer.
"""
import json
import sys
from pathlib import Path

EXT = ".dv.metadata.yaml"


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path.endswith(EXT):
        return 0

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dv_metadata as dv  # noqa: E402

    if dv.yaml is None or dv.jsonschema is None:
        print(f"dv-metadata hook: pyyaml/jsonschema not installed — validation skipped "
              f"(pip install -r {dv.REQUIREMENTS})", file=sys.stderr)
        return 0
    path = Path(file_path)
    if not path.is_file():
        return 0
    try:
        report = dv.validate_path(path)
    except Exception as e:  # malformed YAML, unreadable file…
        print(f"dv-metadata validation failed on {path.name}: {e}", file=sys.stderr)
        return 2
    if report.errors:
        print(f"dv-metadata model invalid after editing {path.name} — fix before planning:", file=sys.stderr)
        for e in report.errors:
            print(f"  ✗ {e}", file=sys.stderr)
        for w in report.warnings:
            print(f"  ⚠ {w}", file=sys.stderr)
        return 2
    if report.warnings:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "dv-metadata model valid with warnings:\n"
                                 + "\n".join(f"- {w}" for w in report.warnings),
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
