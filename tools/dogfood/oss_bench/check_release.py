#!/usr/bin/env python3
"""Release trigger for the two-arm OSS benchmark.

Exit codes speak for the nightly loop:
  0 UP-TO-DATE   — benched version equals pyproject version (or newer)
  3 BENCH-READY  — a new release is unbenched AND model+budget are configured
  4 SKIPPED      — a new release is unbenched but prerequisites are missing
                   (reason printed; never fabricate results instead)

Reads only real files: pyproject.toml, this directory's state.json, and the
environment for the configured API key variable.
"""

from __future__ import annotations

import json
import os
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]


def current_version() -> str:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def main() -> int:
    state = json.loads((HERE / "state.json").read_text())
    version = current_version()
    benched = state.get("last_benched_version")
    if benched == version:
        print(f"UP-TO-DATE benched={benched} current={version}")
        return 0
    missing = []
    if not state.get("model"):
        missing.append("state.json model is unset (owner decision)")
    if not state.get("budget_cap_usd"):
        missing.append("state.json budget_cap_usd is unset")
    key_env = state.get("api_key_env", "VULCAN_MODEL_API_KEY")
    if os.environ.get(key_env):
        pass  # env wins; nothing missing
    else:
        key_file = state.get("api_key_file")
        if key_file and Path(key_file).is_file():
            lines = Path(key_file).read_text().splitlines()
            line_no = state.get("api_key_file_line")
            value = lines[line_no - 1] if isinstance(line_no, int) and 0 < line_no <= len(lines) \
                else next((ln for ln in lines if ln.strip() and " " not in ln), "")
            if not value.strip():
                missing.append(f"{key_env} unset and {key_file} has no key line")
        else:
            missing.append(f"${key_env} is not set and no api_key_file exists")
    if missing:
        print(f"SKIPPED current={version} benched={benched} reasons={missing}")
        return 4
    print(f"BENCH-READY current={version} benched={benched} "
          f"model={state['model']} cap=${state['budget_cap_usd']}")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
