[0m
> build · x-ai/grok-4.5
[0m
[0m→ [0mRead LICENSE-RANEX.md[90m [limit=80][0m
[0m→ [0mRead docs/architecture/rfcs/RFC-0003-deterministic-session-continuity-and-drift-tripwires.md
[0m✱ [0mGlob "**/ADR-0014*"[90m 1 match[0m
[0m
[0m$ [0mls /tmp/opencode && which python3 cog pre-commit 2>/dev/null; python3 --version; pip show cogapp pre-commit 2>/dev/null | grep -E '^(Name|Version|Location)'
dagu.json
lock.db
prior-art-c
rfc0003-proto
seqtest.db
v
vacuous_test.py
/home/soultransit/.local/bin/python3
Python 3.14.6
[0m
I'll read the RFC and licence constraints first, then research Python CI options and build the external prototype.
[0m% [0mWebFetch https://pypi.org/pypi/cogapp/json
[0m% [0mWebFetch https://pypi.org/pypi/pre-commit/json
[0m
[0m$ [0mpip index versions cogapp 2>/dev/null | head -3; pip index versions pre-commit 2>/dev/null | head -3; python3 -m pip install --user -q cogapp pre-commit 2>&1 | tail -5; which cog; cog --version 2>&1; pre-commit --version 2>&1
cogapp (3.6.0)
Available versions: 3.6.0, 3.5.1, 3.5.0, 3.4.1, 3.4.0, 3.3.0, 3.2.0, 3.1.0, 3.0.0, 2.5.1, 2.5, 2.4, 2.3, 2.2
pre-commit (4.6.1)
Available versions: 4.6.1, 4.6.0, 4.5.1, 4.5.0, 4.4.0, 4.3.0, 4.2.0, 4.1.0, 4.0.1, 4.0.0, 3.8.0, 3.7.1, 3.7.0, 3.6.2, 3.6.1, 3.6.0, 3.5.0, 3.4.0, 3.3.3, 3.3.2, 3.3.1, 3.3.0, 3.2.2, 3.2.1, 3.2.0, 3.1.1, 3.1.0, 3.0.4, 3.0.3, 3.0.2, 3.0.1, 3.0.0, 2.21.0, 2.20.0, 2.19.0, 2.18.1, 2.18.0, 2.17.0, 2.16.0, 2.15.0, 2.14.1, 2.14.0, 2.13.0, 2.12.1, 2.12.0, 2.11.1, 2.11.0, 2.10.1, 2.10.0, 2.9.3, 2.9.2, 2.9.1, 2.9.0, 2.8.2, 2.8.1, 2.8.0, 2.7.1, 2.7.0, 2.6.0, 2.5.1, 2.5.0, 2.4.0, 2.3.0, 2.2.0, 2.1.1, 2.1.0, 2.0.1, 2.0.0, 1.21.0, 1.20.0, 1.19.0, 1.18.3, 1.18.2, 1.18.1, 1.18.0, 1.17.0, 1.16.1, 1.16.0, 1.15.2, 1.15.1, 1.15.0, 1.14.4, 1.14.3, 1.14.2, 1.14.1, 1.14.0, 1.13.0, 1.12.0, 1.11.2, 1.11.1, 1.11.0, 1.10.5, 1.10.4, 1.10.3, 1.10.2, 1.10.1, 1.10.0, 1.9.0, 1.8.2, 1.8.1, 1.8.0, 1.7.0, 1.6.0, 1.5.1, 1.5.0, 1.4.5, 1.4.4, 1.4.3, 1.4.2, 1.4.1, 1.4.0, 1.3.0, 1.2.0, 1.1.2, 1.1.1, 1.1.0, 1.0.1, 1.0.0, 0.18.3, 0.18.2, 0.18.1, 0.18.0, 0.17.0, 0.16.3, 0.16.2, 0.16.1, 0.16.0, 0.15.4, 0.15.3, 0.15.2, 0.15.1, 0.15.0, 0.14.3, 0.14.2, 0.14.1, 0.14.0, 0.13.6, 0.13.5, 0.13.4, 0.13.3, 0.13.2, 0.13.1, 0.13.0, 0.12.2, 0.12.1, 0.12.0, 0.11.0, 0.10.1, 0.10.0, 0.9.4, 0.9.3, 0.9.2, 0.9.1, 0.9.0, 0.8.2, 0.8.1, 0.8.0, 0.7.6, 0.7.5, 0.7.4, 0.7.3, 0.7.2, 0.7.1, 0.7.0, 0.6.8, 0.6.7, 0.6.6, 0.6.5, 0.6.4, 0.6.3, 0.6.2, 0.6.1, 0.6.0, 0.5.5, 0.5.4, 0.5.3, 0.5.2, 0.5.1, 0.5.0, 0.4.4, 0.4.3, 0.4.2, 0.4.1, 0.4.0, 0.3.6, 0.3.5, 0.3.4, 0.3.3, 0.3.2, 0.3.1, 0.3.0, 0.2.11, 0.2.10, 0.2.9, 0.2.8, 0.2.7, 0.2.6, 0.2.5, 0.2.4, 0.2.3, 0.2.2, 0.2.1, 0.2.0
× This environment is externally managed
╰─> This Python installation is managed by uv and should not be modified.

note: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.
hint: See PEP 668 for the detailed specification.
/bin/bash: line 1: cog: command not found
/bin/bash: line 1: pre-commit: command not found
[0m
[0m✗ [0mWebFetch https://pypi.org/pypi/reviewdog/json failed
[91m[1mError: [0mStatusCode: non 2xx status code (404 GET https://pypi.org/pypi/reviewdog/json)
Researching tool versions/licences and building the prototype in parallel.
[0m% [0mWebFetch https://pypi.org/pypi/danger-python/json
[0m% [0mWebFetch https://api.github.com/repos/reviewdog/reviewdog/releases/latest
Gathering release dates and PR-comment libraries, then building the prototype.
[0m% [0mWebFetch https://pre-commit.com/#usage-in-continuous-integration
[0m% [0mWebFetch https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks
[0m
[0m$ [0mpython3 - <<'PY'
import json,urllib.request
for pkg in ['pre-commit','PyGithub','github3.py','danger-python','cogapp']:
    data=json.load(urllib.request.urlopen(f'https://pypi.org/pypi/{pkg}/json'))
    info=data['info']
    ver=info['version']
    urls=data['releases'].get(ver,[])
    ut=urls[0]['upload_time_iso_8601'] if urls else '?'
    lic=info.get('license_expression') or info.get('license') or '?'
    print(f"{pkg}\t{ver}\t{ut}\t{lic[:80]!r}\t{info.get('home_page') or info.get('project_url')}")
PY
# reviewdog license from github
curl -sL https://raw.githubusercontent.com/reviewdog/reviewdog/master/LICENSE | head -5
curl -sL https://api.github.com/repos/reviewdog/reviewdog | python3 -c "import sys,json;d=json.load(sys.stdin);print('stars',d['stargazers_count'],'license',d.get('license'))"
curl -sL https://api.github.com/repos/danger/danger-js/releases/latest | python3 -c "import sys,json;d=json.load(sys.stdin);print('danger-js',d.get('tag_name'),d.get('published_at'))"
curl -sL https://api.github.com/repos/pre-commit/pre-commit | python3 -c "import sys,json;d=json.load(sys.stdin);print('pre-commit stars',d['stargazers_count'],'license',d.get('license'))"
curl -sL https://api.github.com/repos/nedbat/cog | python3 -c "import sys,json;d=json.load(sys.stdin);print('cog stars',d['stargazers_count'],'license',d.get('license'))"
curl -sL https://api.github.com/repos/PyGithub/PyGithub | python3 -c "import sys,json;d=json.load(sys.stdin);print('PyGithub stars',d['stargazers_count'],'license',d.get('license'))"
curl -sL https://api.github.com/repos/danger/python | python3 -c "import sys,json;d=json.load(sys.stdin);print('danger-python repo',d.get('stargazers_count'),d.get('pushed_at'),d.get('license'),d.get('archived'))" 2>/dev/null || curl -sL https://api.github.com/repos/danger/danger-python | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('full_name'),d.get('stargazers_count'),d.get('pushed_at'),d.get('license'),d.get('archived'),d.get('message'))"
# docs on pre-commit skip
curl -sL https://pre-commit.com/#Skipping-git-hooks | head -c 2000
echo '---'
# danger systems
curl -sL https://raw.githubusercontent.com/danger/danger-js/master/package.json | python3 -c "import sys,json;d=json.load(sys.stdin);print('danger-js version',d.get('version'),'license',d.get('license'))"

pre-commit	4.6.1	2026-07-21T20:56:57.064358Z	'MIT'	https://github.com/pre-commit/pre-commit
PyGithub	2.9.1	2026-04-14T07:26:12.382245Z	'?'	https://pypi.org/project/PyGithub/
github3.py	4.0.1	2023-04-26T17:56:25.015888Z	'?'	https://pypi.org/project/github3.py/
danger-python	0.1.0	2020-02-14T10:24:21.616876Z	'MIT'	https://pypi.org/project/danger-python/
cogapp	3.6.0	2025-09-21T15:54:12.205420Z	'MIT'	https://pypi.org/project/cogapp/
MIT License

Copyright (c) 2016 haya14busa

Permission is hereby granted, free of charge, to any person obtaining a copy
stars 9488 license {'key': 'mit', 'name': 'MIT License', 'spdx_id': 'MIT', 'url': 'https://api.github.com/licenses/mit', 'node_id': 'MDc6TGljZW5zZTEz'}
danger-js 13.0.10 2026-06-25T13:03:48Z
pre-commit stars 15464 license {'key': 'mit', 'name': 'MIT License', 'spdx_id': 'MIT', 'url': 'https://api.github.com/licenses/mit', 'node_id': 'MDc6TGljZW5zZTEz'}
cog stars 407 license {'key': 'mit', 'name': 'MIT License', 'spdx_id': 'MIT', 'url': 'https://api.github.com/licenses/mit', 'node_id': 'MDc6TGljZW5zZTEz'}
PyGithub stars 7756 license {'key': 'lgpl-3.0', 'name': 'GNU Lesser General Public License v3.0', 'spdx_id': 'LGPL-3.0', 'url': 'https://api.github.com/licenses/lgpl-3.0', 'node_id': 'MDc6TGljZW5zZTEy'}
danger-python repo 114 2026-07-27T06:30:38Z {'key': 'mit', 'name': 'MIT License', 'spdx_id': 'MIT', 'url': 'https://api.github.com/licenses/mit', 'node_id': 'MDc6TGljZW5zZTEz'} False
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

        <link rel="shortcut icon" type="image/x-icon" href="favicon.ico">

        <link rel="stylesheet" href="build/main_bs5.css">

        <title>pre-commit</title>
    </head>
    <body data-bs-spy="scroll" data-bs-target="#content-navigation">
        <nav class="navbar navbar-expand-md navbar-dark bg-primary">
            <div class="container-md">
                <a class="navbar-brand" href="/">
                    <img src="logo.svg" width="55" height="55" alt="" loading="lazy">
                </a>

                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbar" aria-controls="navbar" aria-expanded="false" >
                    <span class="navbar-toggler-icon"></span>
                </button>

                <div class="collapse navbar-collapse" id="navbar">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link active" href="index.html">Documentation</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="hooks.html">Supported hooks</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="https://github.com/pre-commit/demo-repo#readme">Demo</a>
                        </li>
                    </ul>

                    <ul class="navbar-nav ms-auto">
                        <li class="nav-item">
                            <a href="https://github.com/pre-commit/pre-commit" role="button" class="btn btn-outline-info my-2 my-sm-0">Download on GitHub</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <header class="bg-light">
            <div c---
danger-js version 13.0.10 license MIT
[0m
Building and running the full prototype outside the repo.
[0m$ [0mset -euo pipefail
PROTO=/tmp/rfc0003-proto
rm -rf "$PROTO"
mkdir -p "$PROTO"
cd "$PROTO"

# isolated venv
python3 -m venv .venv
. .venv/bin/activate
pip install -q 'cogapp==3.6.0' 'pre-commit==4.6.1'
echo "=== TOOL VERSIONS ==="
cog --version
pre-commit --version
python --version

# project layout
mkdir -p checks scripts
cat > checks/values.py << 'EOF'
"""Tiny value functions a cog span can call."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COUNT_FILE = ROOT / "data" / "accepted_adrs.txt"


def accepted_adr_count() -> int:
    text = COUNT_FILE.read_text(encoding="utf-8")
    return sum(1 for line in text.splitlines() if line.strip() and not line.startswith("#"))


def described_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
EOF

mkdir -p data
printf '%s\n' 'ADR-0001' 'ADR-0002' 'ADR-0014' > data/accepted_adrs.txt

cat > CONTINUITY.md << 'EOF'
# Continuity prototype

<!-- DO NOT EDIT generated spans by hand. Regenerate with: cog -rc CONTINUITY.md -->

## Generated state
<!-- [[[cog
import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))
from checks.values import accepted_adr_count, described_commit
cog.outl(f"described_commit: {described_commit()}")
cog.outl(f"accepted_adrs: {accepted_adr_count()}")
]]] -->
<!-- [[[end]]] -->

## Authored next action
Prove that cog --check fails when the count drifts.
EOF

git init -q
git config user.email 'proto@example.com'
git config user.name 'Proto'
# initial commit so HEAD exists for described_commit
git add data CONTINUITY.md checks
# generate cog span first - need commit for HEAD
git add -A
git commit -q -m 'seed empty' --allow-empty
# now generate with real HEAD
cog -c -r CONTINUITY.md
echo "=== AFTER cog -cr ==="
cat CONTINUITY.md

echo "=== cog --check when current ==="
set +e
cog --check CONTINUITY.md
EC_OK=$?
set -e
echo "exit_code=$EC_OK"

# stage continuity and commit
git add CONTINUITY.md checks data
git commit -q -m 'add continuity with cog spans'

# re-generate at this commit (HEAD moved... wait, after commit HEAD is the commit)
# Continuity was generated before final commit, so described_commit is wrong?
# For continuity artifact nature: generate AT a commit, then if HEAD moves need regen.
# Prototype staleness: record commit, then make another commit.

echo "=== Persist commit snapshot after generation ==="
# Regenerate at current HEAD and commit so it matches
cog -c -r CONTINUITY.md
git add CONTINUITY.md
git commit -q -m 'sync continuity to HEAD'
echo "file shows:"
grep described_commit CONTINUITY.md
echo "HEAD is: $(git rev-parse HEAD)"

echo "=== cog --check still pass ==="
set +e
cog --check CONTINUITY.md; echo "exit_code=$?"
set -e

echo "=== DRIFT: hand-edit accepted count claim ==="
# Corrupt the generated span (change number but leave checksum wrong / or just change visible value)
python3 - <<'PY'
from pathlib import Path
p = Path('CONTINUITY.md')
t = p.read_text()
t2 = t.replace('accepted_adrs: 3', 'accepted_adrs: 13')
assert t2 != t, 'expected to change'
p.write_text(t2)
print(p.read_text())
PY

echo "===-coggroup- cog --check when drifted ==="
set +e
cog --check --diff CONTINUITY.md
EC_DRIFT=$?
set -e
echo "exit_code_drift=$EC_DRIFT"

# restore for pre-commit demo
cog -c -r CONTINUITY.md

# staleness check script
cat > scripts/check_continuity_fresh.py << 'EOF'
#!/usr/bin/env python3
"""Fail when CONTINUITY.md describes a commit other than HEAD."""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "CONTINUITY.md"
text = path.read_text(encoding="utf-8")
m = re.search(r"^described_commit:\s*([0-9a-f]{7,40})\s*$", text, re.M)
if not m:
    print("FAIL: no described_commit field in CONTINUITY.md", file=sys.stderr)
    sys.exit(1)
described = m.group(1)
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
# allow short or full match
if not (head == described or head.startswith(described) or described.startswith(head[: len(described)])):
    # strict full equality preferred
    if head != described and not head.startswith(described):
        print(f"FAIL: CONTINUITY.md is stale by construction", file=sys.stderr)
        print(f"  described_commit: {described}", file=sys.stderr)
        print(f"  HEAD:             {head}", file=sys.stderr)
        print("  Regenerate with: cog -crc CONTINUITY.md", file=sys.stderr)
        sys.exit(1)
print(f"OK: CONTINUITY.md matches HEAD {head[:12]}")
sys.exit(0)
EOF
chmod +x scripts/check_continuity_fresh.py

echo "=== staleness: fresh after regen ==="
# need described_commit full hash - cog used full from rev-parse
python3 scripts/check_continuity_fresh.py; echo "exit=$?"

echo "=== move HEAD ==="
echo 'ADR-0015' >> data/accepted_adrs.txt
# before changing count in continuity - commit data only with --no-verify later
# First fix continuity count and commit a "sync" - actually for staleness we commit ANYTHING without regenerating continuity

# save current described
DESC=$(grep described_commit CONTINUITY.md)
git add data/accepted_adrs.txt
# use --no-verify for this commit so we can stage HEAD move without hook yet
git commit -q --no-verify -m 'move HEAD without regenerating continuity'
echo "=== staleness after HEAD moved ==="
echo "file: $DESC"
echo "HEAD: $(git rev-parse HEAD)"
set +e
python3 scripts/check_continuity_fresh.py
EC_STALE=$?
set -e
echo "exit_code_stale=$EC_STALE"

# pre-commit config
cat > .pre-commit-config.yaml << 'EOF'
# LOCAL CONVENIENCE ONLY — not an enforcement control.
# Bypass: git commit --no-verify, SKIP=..., uninstall hooks.
# Enforcement is required CI (GitHub Actions required check).
repos:
  - repo: local
    hooks:
      - id: cog-check-continuity
        name: "cog --check CONTINUITY.md (local convenience)"
        entry: bash -c 'cog --check CONTINUITY.md'
        language: system
        pass_filenames: false
        always_run: true
      - id: continuity-freshness
        name: "continuity stale-by-construction (local convenience)"
        entry: python3 scripts/check_continuity_fresh.py
        language: system
        pass_filenames: false
        always_run: true
EOF

# restore continuity for pre-commit fire demo
cog -c -r CONTINUITY.md
# update count - 4 adrs now
python3 scripts/check_continuity_fresh.py

pre-commit install
echo "=== pre-commit run --all-files (should pass) ==="
set +e
pre-commit run --all-files
EC_PC_OK=$?
set -e
echo "exit_pre_commit_ok=$EC_PC_OK"

echo "=== pre-commit fires on drift ==="
# corrupt
python3 - <<'PY'
from pathlib import Path
p=Path('CONTINUITY.md')
p.write_text(p.read_text().replace('accepted_adrs: 4','accepted_adrs: 99'))
PY
set +e
pre-commit run --all-files
EC_PC_FAIL=$?
set -e
echo "exit_pre_commit_fail=$EC_PC_FAIL"

# restore and commit to test commit path
cog -c -r CONTINUITY.md
git add CONTINUITY.md data
git commit -q -m 'regenerate continuity'

echo "=== commit path: install hook, make bad commit attempt ==="
# drift again stage it
python3 - <<'PY'
from pathlib import Path
p=Path('CONTINUITY.md')
p.write_text(p.read_text().replace('accepted_adrs: 4','accepted_adrs: 42'))
PY
git add CONTINUITY.md
set +e
git commit -m 'should be blocked by pre-commit'
EC_COMMIT_BLOCK=$?
set -e
echo "exit_commit_blocked=$EC_COMMIT_BLOCK"

echo "=== PROOF SUMMARY END ==="
echo "EC_OK=$EC_OK EC_DRIFT=$EC_DRIFT EC_STALE=$EC_STALE EC_PC_OK=$EC_PC_OK EC_PC_FAIL=$EC_PC_FAIL EC_COMMIT_BLOCK=$EC_COMMIT_BLOCK"
ls -la

[notice] A new release of pip is available: 26.1.2 -> 26.2
[notice] To update, run: pip install --upgrade pip
=== TOOL VERSIONS ===
option --version not recognized
(for help use --help)
[0m
Retrying the prototype; `cog --version` is unsupported.
[0m$ [0mset -euo pipefail
PROTO=/tmp/rfc0003-proto
rm -rf "$PROTO"
mkdir -p "$PROTO"
cd "$PROTO"

python3 -m venv .venv
. .venv/bin/activate
pip install -q 'cogapp==3.6.0' 'pre-commit==4.6.1'
echo "=== TOOL VERSIONS ==="
python -c "import cogapp; print('cogapp', getattr(cogapp,'__version__', 'import-ok'))"
cog --help 2>&1 | head -2
pre-commit --version
python --version

mkdir -p checks scripts data
cat > checks/values.py << 'EOF'
"""Tiny value functions a cog span can call."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COUNT_FILE = ROOT / "data" / "accepted_adrs.txt"


def accepted_adr_count() -> int:
    text = COUNT_FILE.read_text(encoding="utf-8")
    return sum(1 for line in text.splitlines() if line.strip() and not line.startswith("#"))


def described_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
EOF

printf '%s\n' 'ADR-0001' 'ADR-0002' 'ADR-0014' > data/accepted_adrs.txt

cat > CONTINUITY.md << 'EOF'
# Continuity prototype

## Generated state
<!-- [[[cog
import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))
from checks.values import accepted_adr_count, described_commit
cog.outl(f"described_commit: {described_commit()}")
cog.outl(f"accepted_adrs: {accepted_adr_count()}")
]]] -->
<!-- [[[end]]] -->

## Authored next action
Prove that cog --check fails when the count drifts.
EOF

git init -q
git config user.email 'proto@example.com'
git config user.name 'Proto'
git commit -q -m 'seed empty' --allow-empty

echo "=== 1) cog -c -r (checksum generate) ==="
cog -c -r CONTINUITY.md
cat CONTINUITY.md

echo "=== 2a) cog --check when current ==="
set +e
cog --check CONTINUITY.md
EC_OK=$?
set -e
echo "exit_code=$EC_OK"

git add CONTINUITY.md checks data
git commit -q -m 'add continuity with cog spans'

# re-sync so described_commit == this HEAD
cog -c -r CONTINUITY.md
git add CONTINUITY.md
git commit -q -m 'sync continuity to HEAD'
echo "file:"
grep -E 'described_commit|accepted_adrs' CONTINUITY.md
echo "HEAD: $(git rev-parse HEAD)"

set +e
cog --check CONTINUITY.md; echo "exit_after_sync=$?"
set -e

echo "=== 2b) DRIFT hand-edit ==="
python3 - <<'PY'
from pathlib import Path
p = Path('CONTINUITY.md')
t = p.read_text()
t2 = t.replace('accepted_adrs: 3', 'accepted_adrs: 13')
assert t2 != t
p.write_text(t2)
print(p.read_text())
PY

set +e
echo "--- cog --check --diff output ---"
cog --check --diff CONTINUITY.md
EC_DRIFT=$?
set -e
echo "exit_code_drift=$EC_DRIFT"

cog -c -r CONTINUITY.md

cat > scripts/check_continuity_fresh.py << 'EOF'
#!/usr/bin/env python3
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "CONTINUITY.md"
text = path.read_text(encoding="utf-8")
m = re.search(r"^described_commit:\s*([0-9a-f]{7,40})\s*$", text, re.M)
if not m:
    print("FAIL: no described_commit field in CONTINUITY.md", file=sys.stderr)
    sys.exit(1)
described = m.group(1)
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
if head != described:
    print("FAIL: CONTINUITY.md is stale by construction", file=sys.stderr)
    print(f"  described_commit: {described}", file=sys.stderr)
    print(f"  HEAD:             {head}", file=sys.stderr)
    print("  Regenerate with: cog -crc CONTINUITY.md", file=sys.stderr)
    sys.exit(1)
print(f"OK: CONTINUITY.md matches HEAD {head[:12]}")
sys.exit(0)
EOF
chmod +x scripts/check_continuity_fresh.py

echo "=== 4a) staleness when fresh ==="
python3 scripts/check_continuity_fresh.py; echo "exit_fresh=$?"

echo 'ADR-0015' >> data/accepted_adrs.txt
git add data/accepted_adrs.txt
git commit -q --no-verify -m 'move HEAD without regenerating continuity'
echo "=== 4b) staleness after HEAD moved ==="
grep described_commit CONTINUITY.md
echo "HEAD: $(git rev-parse HEAD)"
set +e
python3 scripts/check_continuity_fresh.py
EC_STALE=$?
set -e
echo "exit_code_stale=$EC_STALE"

cat > .pre-commit-config.yaml << 'EOF'
# LOCAL CONVENIENCE ONLY — not an enforcement control.
# Bypass: git commit --no-verify, SKIP=..., uninstall hooks.
# Enforcement is required CI (GitHub Actions required check).
repos:
  - repo: local
    hooks:
      - id: cog-check-continuity
        name: "cog --check CONTINUITY.md (local convenience)"
        entry: bash -c 'cog --check CONTINUITY.md'
        language: system
        pass_filenames: false
        always_run: true
      - id: continuity-freshness
        name: "continuity stale-by-construction (local convenience)"
        entry: python3 scripts/check_continuity_fresh.py
        language: system
        pass_filenames: false
        always_run: true
EOF

# fix continuity for community (4 adrs now, and new HEAD)
cog -c -r CONTINUITY.md
python3 scripts/check_continuity_fresh.py

# pre-commit needs PATH to cog from venv
export PATH="$PROTO/.venv/bin:$PATH"
pre-commit install
echo "=== 3a) pre-commit run --all-files pass ==="
set +e
pre-commit run --all-files
EC_PC_OK=$?
set -e
echo "exit_pre_commit_ok=$EC_PC_OK"

echo "=== 3b) pre-commit fires on drift ==="
python3 - <<'PY'
from pathlib import Path
p=Path('CONTINUITY.md')
p.write_text(p.read_text().replace('accepted_adrs: 4','accepted_adrs: 99'))
PY
set +e
pre-commit run --all-files
EC_PC_FAIL=$?
set -e
echo "exit_pre_commit_fail=$EC_PC_FAIL"

cog -c -r CONTINUITY.md
git add CONTINUITY.md data scripts .pre-commit-config.yaml checks
git commit -q -m 'regenerate continuity and hooks'

echo "=== 3c) git commit blocked by hook ==="
python3 - <<'PY'
from pathlib import Path
p=Path('CONTINUITY.md')
p.write_text(p.read_text().replace('accepted_adrs: 4','accepted_adrs: 42'))
PY
git add CONTINUITY.md
set +e
git commit -m 'should be blocked by pre-commit'
EC_COMMIT_BLOCK=$?
set -e
echo "exit_commit_blocked=$EC_COMMIT_BLOCK"

echo "=== FINAL CODES ==="
echo "EC_OK=$EC_OK EC_DRIFT=$EC_DRIFT EC_STALE=$EC_STALE EC_PC_OK=$EC_PC_OK EC_PC_FAIL=$EC_PC_FAIL EC_COMMIT_BLOCK=$EC_COMMIT_BLOCK"

[notice] A new release of pip is available: 26.1.2 -> 26.2
[notice] To update, run: pip install --upgrade pip
=== TOOL VERSIONS ===
cogapp import-ok
cog - generate content with inlined Python code.

pre-commit 4.6.1
Python 3.14.6
=== 1) cog -c -r (checksum generate) ===
Cogging CONTINUITY.md  (changed)
# Continuity prototype

## Generated state
<!-- [[[cog
import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))
from checks.values import accepted_adr_count, described_commit
cog.outl(f"described_commit: {described_commit()}")
cog.outl(f"accepted_adrs: {accepted_adr_count()}")
]]] -->
described_commit: b320a0ffcf7a3f9064dfd5990b8cd6a93bf355a8
accepted_adrs: 3
<!-- [[[end]]] (sum: pcjdNG90j5) -->

## Authored next action
Prove that cog --check fails when the count drifts.
=== 2a) cog --check when current ===
Check failed
Checking CONTINUITY.md  (changed)
exit_code=5
Cogging CONTINUITY.md  (changed)
file:
from checks.values import accepted_adr_count, described_commit
cog.outl(f"described_commit: {described_commit()}")
cog.outl(f"accepted_adrs: {accepted_adr_count()}")
described_commit: 563b72a70aefa35da8268c9567b5a4481b8152c3
accepted_adrs: 3
HEAD: e70a0d23f47917d49e28d34589cc77e245f08810
Check failed
Checking CONTINUITY.md  (changed)
exit_after_sync=5
=== 2b) DRIFT hand-edit ===
# Continuity prototype

## Generated state
<!-- [[[cog
import sys
from pathlib import Path
sys.path.insert(0, str(Path(".").resolve()))
from checks.values import accepted_adr_count, described_commit
cog.outl(f"described_commit: {described_commit()}")
cog.outl(f"accepted_adrs: {accepted_adr_count()}")
]]] -->
described_commit: 563b72a70aefa35da8268c9567b5a4481b8152c3
accepted_adrs: 13
<!-- [[[end]]] (sum: lBBw3QjUoG) -->

## Authored next action
Prove that cog --check fails when the count drifts.

--- cog --check --diff output ---
Check failed
Checking CONTINUITY.md  (changed)
--- current CONTINUITY.md
+++ changed CONTINUITY.md
@@ -9,9 +9,9 @@
 cog.outl(f"described_commit: {described_commit()}")
 cog.outl(f"accepted_adrs: {accepted_adr_count()}")
 ]]] -->
-described_commit: 563b72a70aefa35da8268c9567b5a4481b8152c3
-accepted_adrs: 13
-<!-- [[[end]]] (sum: lBBw3QjUoG) -->
+described_commit: e70a0d23f47917d49e28d34589cc77e245f08810
+accepted_adrs: 3
+<!-- [[[end]]] -->
 
 ## Authored next action
 Prove that cog --check fails when the count drifts.
exit_code_drift=5
CONTINUITY.md(14): Output has been edited! Delete old checksum to unprotect.
Cogging CONTINUITY.md
[0m
[93m[1m! [0mpermission requested: external_directory (/tmp/*); auto-rejecting
[0m✗ [0mset -euo pipefail
cd /tmp
rm -rf cogtest && mkdir cogtest && cd cogtest
python3 -m venv .venv && . .venv/bin/activate
pip install -q cogapp==3.6.0

cat > t.md << 'EOF'
# t
<!-- [[[cog
cog.outl("n = 3")
]]] -->
<!-- [[[end]]] -->
EOF

echo "=== generate plain ==="
cog -r t.md
cat t.md
echo "=== check plain OK ==="
set +e; cog --check t.md; echo ec=$?; set -e

echo "=== generate with -c ==="
# reset
cat > t.md << 'EOF'
# t
<!-- [[[cog
cog.outl("n = 3")
]]] -->
<!-- [[[end]]] -->
EOF
cog -c -r t.md
cat t.md
echo "=== check -c OK ==="
set +e; cog --check t.md; echo ec=$?; set -e
set +e; cog --check -c t.md; echo ec_c=$?; set -e

echo "=== drift body ==="
python3 - <<'PY'
from pathlib import Path
p=Path('t.md')
p.write_text(p.read_text().replace('n = 3','n = 99'))
print(p.read_text())
PY
set +e; cog --check t.md; echo ec_drift=$?; set -e
set +e; cog --check -c t.md; echo ec_drift_c=$?; set -e
set +e; cog --check --diff t.md; echo; set -e

echo "=== restore with delete checksum ==="
python3 - <<'PY'
from pathlib import Path
import re
p=Path('t.md')
t=p.read_text()
t=re.sub(r'<!-- \[\[\[end\]\]\] \(sum: [^)]+\) -->','<!-- [[[end]]] -->',t)
t=t.replace('n = 99','n = 3')
p.write_text(t)
print(p.read_text())
PY
cog -c -r t.md
cog --check t.md; echo ec_restored=$?

# dynamic head
echo "=== dynamic ==="
git init -q
git config user.email a@b.c && git config user.name a
git commit -q --allow-empty -m seed
cat > d.md << 'EOF'
<!-- [[[cog
import subprocess
h=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
cog.outl(f"commit: {h}")
]]] -->
<!-- [[[end]]] -->
EOF
cog -c -r d.md
cat d.md
set +e; cog --check d.md; echo ec1=$?; set -e
git commit -q --allow-empty -m move
set +e; cog --check d.md; echo ec2_after_head_move=$?; set -e
cog --check --diff d.md || true
 failed
[91m[1mError: [0mThe user rejected permission to use this specific tool call.
Investigating cog checksum/`--check` behaviour — first run hit checksum quirks.
