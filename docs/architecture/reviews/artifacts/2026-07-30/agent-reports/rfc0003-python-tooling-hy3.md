[0m
> build · tencent/hy3
[0m
[0m$ [0mpwd && ls
/home/soultransit/devtony/ranex
architecture
decisions
docs
legal
LICENSE
LICENSE-RANEX.md
NOTICE.md
README.md
schemas
scripts
[0m
[0m✱ [0mGlob "docs/architecture/rfcs/*.md"[90m 4 matches[0m
[0m→ [0mRead docs/architecture/rfcs/RFC-0003-deterministic-session-continuity-and-drift-tripwires.md
[0m→ [0mRead LICENSE-RANEX.md
[0m
[0m# [0mTodos
[✓] Read RFC and licence (done), plan work
[•] Build prototype in /tmp: cog span, cog -c, --check pass/fail exit codes
[ ] Prototype: pre-commit config firing on drift
[ ] Prototype: staleness rule (HEAD-recorded file, fails when HEAD moves)
[ ] Verify externally: cogapp, pre-commit, reviewdog, danger-js/danger-python, PyGithub, ghapi, githubkit, gh CLI — licence, version, release date, adopters
[ ] Q1 answer: pick Python combination, state what is lost vs danger-js
[ ] Q2 answer: pre-commit worth having despite bypass; labelling recommendation
[ ] Write final report: Q1, Q2, transcript, licence table, losses, inferences, unverified
[0m
[0m% [0mWebFetch https://pypi.org/pypi/cogapp/json
Setting up the prototype environment in `/tmp` (read-only with respect to the Ranex repo), and starting external verification in parallel.
[0m
[0m$ [0mmkdir -p /tmp/opencode/rfc0003-proto && cd /tmp/opencode/rfc0003-proto && python3 -m venv .venv && .venv/bin/pip -q install cogapp pre-commit && .venv/bin/cog --version; .venv/bin/pre-commit --version
[notice] A new release of pip is available: 26.1.2 -> 26.2
[notice] To update, run: /tmp/opencode/rfc0003-proto/.venv/bin/python3 -m pip install --upgrade pip
option --version not recognized
(for help use --help)
pre-commit 4.6.1
[0m
[0m$ [0mmkdir -p proto && git -C proto init -q && git -C proto config user.email proto@example.com && git -C proto config user.name Proto && mkdir -p proto/registry proto/tools
(no output)
[0m
[0m% [0mWebFetch https://pypi.org/pypi/pre-commit/json
[0m
[0m$ [0mpython3 -c "
import json
d=json.load(open('/home/soultransit/.local/share/opencode/tool-output/tool_fb32b1f99001AJxbJ4S17psTHM'))
i=d['info']
print(i['name'], i['version'], i.get('license_expression') or i.get('license'))
v=i['version']
print('released:', d['releases'][v][0]['upload_time'])
"
pre-commit 4.6.1 MIT
released: 2026-07-21T20:56:57
[0m
[0m← [0mWrite /tmp/opencode/rfc0003-proto/proto/tools/doc_values.py
Wrote file successfully.
[0m
[0m← [0mWrite /tmp/opencode/rfc0003-proto/proto/registry/adrs.json
Wrote file successfully.
[0m
[0m← [0mWrite /tmp/opencode/rfc0003-proto/proto/STATUS.md
Wrote file successfully.
[0m
[0m$ [0m.venv/bin/python -m cogapp -r -c proto/STATUS.md && echo "--- file after generation ---" && cat proto/STATUS.md
Cogging proto/STATUS.md  (changed)
--- file after generation ---
# Prototype project status

<!-- [[[cog
import sys, pathlib
sys.path.insert(0, str(pathlib.Path("proto/tools")))
import doc_values
cog.outl(f"Accepted ADRs: **{doc_values.accepted_adr_count()}**")
]]] -->
Accepted ADRs: **3**
<!-- [[[end]]] (sum: 0KH/J+dsLV) -->
[0m
[0m$ [0mecho '== 1. cog --check while current =='; .venv/bin/python -m cogapp --check -c proto/STATUS.md; echo "exit code: $?"
echo; echo '== 2. Registry drifts (ADR-0004 becomes ACCEPTED) but doc not regenerated =='
python3 - <<'EOF'
import json,pathlib
p=pathlib.Path('proto/registry/adrs.json'); d=json.loads(p.read_text())
d['adrs'][3]['status']='ACCEPTED'; p.write_text(json.dumps(d,indent=2)+'\n')
EOF
.venv/bin/python -m cogapp --check -c --diff proto/STATUS.md; echo "exit code: $?"
echo; echo '== 3. Restore registry, then hand-tamper the generated value =='
python3 - <<'EOF'
import json,pathlib
p=pathlib.Path('proto/registry/adrs.json'); d=json.loads(p.read_text())
d['adrs'][3]['status']='DRAFT'; p.write_text(json.dumps(d,indent=2)+'\n')
EOF
sed -i 's/Accepted ADRs: \*\*3\*\*/Accepted ADRs: **13**/' proto/STATUS.md
.venv/bin/python -m cogapp --check -c proto/STATUS.md; echo "exit code: $?"
echo; echo '== 4. Repair by regenerating; check passes again =='
sed -i 's/Accepted ADRs: \*\*13\*\*/Accepted ADRs: **3**/' proto/STATUS.md
.venv/bin/python -m cogapp --check -c proto/STATUS.md; echo "exit code: $?"
== 1. cog --check while current ==
Checking proto/STATUS.md
exit code: 0

== 2. Registry drifts (ADR-0004 becomes ACCEPTED) but doc not regenerated ==
Check failed
Checking proto/STATUS.md  (changed)
--- current proto/STATUS.md
+++ changed proto/STATUS.md
@@ -6,5 +6,5 @@
 import doc_values
 cog.outl(f"Accepted ADRs: **{doc_values.accepted_adr_count()}**")
 ]]] -->
-Accepted ADRs: **3**
-<!-- [[[end]]] (sum: 0KH/J+dsLV) -->
+Accepted ADRs: **4**
+<!-- [[[end]]] (sum: iUpU2U2emJ) -->
exit code: 5

== 3. Restore registry, then hand-tamper the generated value ==
proto/STATUS.md(10): Output has been edited! Delete old checksum to unprotect.
Checking proto/STATUS.md
exit code: 1

== 4. Repair by regenerating; check passes again ==
Checking proto/STATUS.md
exit code: 0
[0m
[0m← [0mWrite /tmp/opencode/rfc0003-proto/proto/.pre-commit-config.yaml
Wrote file successfully.
[0m
[0m← [0mWrite /tmp/opencode/rfc0003-proto/proto/tools/check_continuity.py
Wrote file successfully.
[0m
[0m$ [0mgit add -A && git commit -qm "initial prototype" && cat > AGENTS.md <<EOF
# AGENTS.md (prototype)

<!-- generated continuity span -->
describes_commit: $(git rev-parse HEAD)

## Authored handoff (fixed field list)
- attempted / outcome: ...
EOF
git add AGENTS.md && git commit -qm "continuity artifact for current HEAD" && echo "committed; HEAD=$(git rev-parse --short HEAD)"
committed; HEAD=cb12a73
[0m
[0m$ [0msed -i "s/describes_commit: .*/describes_commit: $(git rev-parse HEAD)/" AGENTS.md
echo '== staleness check right after generation =='; ../.venv/bin/python tools/check_continuity.py; echo "exit code: $?"
echo; echo '== now HEAD moves (any commit) =='
echo "note" > scratch.txt && git add scratch.txt && git commit -qm "unrelated work"
../.venv/bin/python tools/check_continuity.py; echo "exit code: $?"
echo; echo '== absent artifact also blocks =='
mv AGENTS.md /tmp/opencode/rfc0003-proto/AGENTS.md.bak
../.venv/bin/python tools/check_continuity.py; echo "exit code: $?"
mv /tmp/opencode/rfc0003-proto/AGENTS.md.bak AGENTS.md
== staleness check right after generation ==
<frozen site>:101: RuntimeWarning: Unexpected value in sys.prefix, expected /tmp/opencode/rfc0003-proto/.venv, got /tmp/opencode/rfc0003-proto/proto/../.venv
<frozen site>:101: RuntimeWarning: Unexpected value in sys.exec_prefix, expected /tmp/opencode/rfc0003-proto/.venv, got /tmp/opencode/rfc0003-proto/proto/../.venv
OK: AGENTS.md is current for HEAD cb12a73b0558.
exit code: 0

== now HEAD moves (any commit) ==
<frozen site>:101: RuntimeWarning: Unexpected value in sys.prefix, expected /tmp/opencode/rfc0003-proto/.venv, got /tmp/opencode/rfc0003-proto/proto/../.venv
<frozen site>:101: RuntimeWarning: Unexpected value in sys.exec_prefix, expected /tmp/opencode/rfc0003-proto/.venv, got /tmp/opencode/rfc0003-proto/proto/../.venv
FAIL: AGENTS.md is STALE. It describes cb12a73b0558 but HEAD is 0fd6dd323f08. Regenerate the continuity artifact.
exit code: 1

== absent artifact also blocks ==
<frozen site>:101: RuntimeWarning: Unexpected value in sys.prefix, expected /tmp/opencode/rfc0003-proto/.venv, got /tmp/opencode/rfc0003-proto/proto/../.venv
<frozen site>:101: RuntimeWarning: Unexpected value in sys.exec_prefix, expected /tmp/opencode/rfc0003-proto/.venv, got /tmp/opencode/rfc0003-proto/proto/../.venv
FAIL: continuity artifact AGENTS.md is absent.
exit code: 1
[0m
[0m$ [0msed -i 's|proto/tools|tools|' STATUS.md && sed -i 's|proto/STATUS.md|STATUS.md|' .pre-commit-config.yaml && sed -i 's|entry: python |entry: /tmp/opencode/rfc0003-proto/.venv/bin/python |' .pre-commit-config.yaml && /tmp/opencode/rfc0003-proto/.venv/bin/python -m cogapp -r -c STATUS.md && sed -i "s/describes_commit: .*/describes_commit: PLACEHOLDER/" AGENTS.md && git add -A && git commit -qm "fix paths for pre-commit run from repo root" && sed -i "s/describes_commit: .*/describes_commit: $(git rev-parse HEAD)/" AGENTS.md && git add AGENTS.md && git commit -q --amend --no-edit && sed -i "s/describes_commit: .*/describes_commit: $(git rev-parse HEAD)/" AGENTS.md && git update-index --refresh -q; git status --short; git rev-parse --short HEAD
Cogging STATUS.md
AGENTS.md: needs update
 M AGENTS.md
5cb2507
[0m
[0m$ [0mexport PATH=/tmp/opencode/rfc0003-proto/.venv/bin:$PATH
pre-commit install
echo; echo '== A. drift the registry, stage it, attempt to commit =='
python3 - <<'EOF'
import json,pathlib
p=pathlib.Path('registry/adrs.json'); d=json.loads(p.read_text())
d['adrs'][3]['status']='ACCEPTED'; p.write_text(json.dumps(d,indent=2)+'\n')
EOF
git add -A
git commit -m "accept ADR-0004 without regenerating docs"; echo "commit exit code: $?"
pre-commit installed at .git/hooks/pre-commit

== A. drift the registry, stage it, attempt to commit ==
CONVENIENCE (not a control): cog --check on doc spans...............................Failed
- hook id: cog-drift-check
- exit code: 5

Check failed
Checking STATUS.md  (changed)
--- current STATUS.md
+++ changed STATUS.md
@@ -6,5 +6,5 @@
 import doc_values
 cog.outl(f"Accepted ADRs: **{doc_values.accepted_adr_count()}**")
 ]]] -->
-Accepted ADRs: **3**
-<!-- [[[end]]] (sum: 0KH/J+dsLV) -->
+Accepted ADRs: **4**
+<!-- [[[end]]] (sum: iUpU2U2emJ) -->

CONVENIENCE (not a control): continuity artifact matches HEAD.......................Passed
commit exit code: 1
[0m
[0m$ [0mexport PATH=/tmp/opencode/rfc0003-proto/.venv/bin:$PATH
echo '== B. regenerate span, refresh continuity, commit passes =='
python -m cogapp -r -c STATUS.md && git add -A && git commit -m "accept ADR-0004 WITH regenerated docs"; echo "commit exit code: $?"
sed -i "s/describes_commit: .*/describes_commit: $(git rev-parse HEAD)/" AGENTS.md
echo; echo '== C. the bypass: same drift, --no-verify sails through =='
python3 - <<'EOF'
import json,pathlib
p=pathlib.Path('registry/adrs.json'); d=json.loads(p.read_text())
d['adrs'][2]['status']='DRAFT'; p.write_text(json.dumps(d,indent=2)+'\n')
EOF
git add -A && git commit --no-verify -m "drifting commit, hooks skipped"; echo "commit exit code: $?"
echo; echo '== D. but the same check in CI-position still catches it =='
python -m cogapp --check -c STATUS.md; echo "cog --check exit code: $?"
== B. regenerate span, refresh continuity, commit passes ==
Cogging STATUS.md  (changed)
CONVENIENCE (not a control): cog --check on doc spans...............................Passed
CONVENIENCE (not a control): continuity artifact matches HEAD.......................Passed
[master 49fee9b] accept ADR-0004 WITH regenerated docs
 3 files changed, 4 insertions(+), 4 deletions(-)
commit exit code: 0

== C. the bypass: same drift, --no-verify sails through ==
[master 5d661c0] drifting commit, hooks skipped
 2 files changed, 2 insertions(+), 2 deletions(-)
commit exit code: 0

== D. but the same check in CI-position still catches it ==
Check failed
Checking STATUS.md  (changed)
cog --check exit code: 5
[0m
[0m# [0mTodos
[✓] Read RFC and licence (done), plan work
[✓] Build prototype in /tmp: cog span, cog -c, --check pass/fail exit codes
[✓] Prototype: pre-commit config firing on drift
[✓] Prototype: staleness rule (HEAD-recorded file, fails when HEAD moves)
[•] Verify externally: reviewdog, danger-js, danger-python, PyGithub, ghapi, githubkit, gh CLI — licence, version, release date, adopters
[ ] Q1 answer: pick Python combination, state what is lost vs danger-js
[ ] Q2 answer: pre-commit worth having despite bypass; labelling recommendation
[ ] Write final report: Q1, Q2, transcript, licence table, losses, inferences, unverified
[0m
All four prototype requirements are demonstrated, plus the bypass evidence for Q2. Now completing external verification for the remaining tools:
[0m$ [0mfor repo in reviewdog/reviewdog danger/danger-js danger/python cli/cli PyGithub/PyGithub yukinarit/pyserde; do
  echo "=== $repo ==="
  curl -s "https://api.github.com/repos/$repo" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('license:', (d.get('license') or {}).get('spdx_id'))
print('stars:', d.get('stargazers_count'), '| archived:', d.get('archived'), '| pushed_at:', d.get('pushed_at'))
"
  curl -s "https://api.github.com/repos/$repo/releases/latest" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('latest release:', d.get('tag_name'), '|', d.get('published_at'))
"
done
=== reviewdog/reviewdog ===
license: MIT
stars: 9488 | archived: False | pushed_at: 2026-07-29T18:07:50Z
latest release: v0.21.0 | 2025-09-03T15:41:12Z
=== danger/danger-js ===
license: MIT
stars: 5495 | archived: False | pushed_at: 2026-07-27T17:23:48Z
latest release: 13.0.10 | 2026-06-25T13:03:48Z
=== danger/python ===
license: MIT
stars: 114 | archived: False | pushed_at: 2026-07-27T06:30:38Z
latest release: v0.1 | 2020-02-14T10:39:33Z
=== cli/cli ===
license: MIT
stars: 45509 | archived: False | pushed_at: 2026-07-30T11:46:04Z
latest release: v2.96.0 | 2026-07-02T21:31:04Z
=== PyGithub/PyGithub ===
license: LGPL-3.0
stars: 7756 | archived: False | pushed_at: 2026-07-29T21:41:38Z
latest release: v2.9.1 | 2026-04-14T07:25:38Z
=== yukinarit/pyserde ===
license: MIT
stars: 853 | archived: False | pushed_at: 2026-07-29T12:21:36Z
latest release: v0.31.8 | 2026-07-29T12:21:14Z
[0m
[0m$ [0mfor pkg in ghapi githubkit; do
  echo "=== $pkg ==="
  curl -s "https://pypi.org/pypi/$pkg/json" | python3 -c "
import json,sys
d=json.load(sys.stdin); i=d['info']
print('version:', i['version'], '| license:', i.get('license_expression') or (i.get('license') or '')[:60])
print('released:', d['releases'][i['version']][0]['upload_time'])
"
done
echo "=== named adopters: .pre-commit-config.yaml present at HEAD? ==="
for repo in django/django pandas-dev/pandas psf/black fastapi/fastapi; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "https://raw.githubusercontent.com/$repo/HEAD/.pre-commit-config.yaml")
  echo "$repo: HTTP $code"
done
=== ghapi ===
version: 2.0.4 | license: Apache-2.0
released: 2026-07-24T12:20:08
=== githubkit ===
version: 0.16.0 | license: MIT
released: 2026-06-14T09:48:43
=== named adopters: .pre-commit-config.yaml present at HEAD? ===
django/django: HTTP 200
pandas-dev/pandas: HTTP 200
psf/black: HTTP 200
fastapi/fastapi: HTTP 200
[0m
[0m$ [0mecho "=== danger-python README: runtime requirement ==="
curl -s "https://raw.githubusercontent.com/danger/python/HEAD/README.md" | grep -in -m5 -E "danger-js|node|npm|prerequi|install"
echo; echo "=== danger-js README: adopters section ==="
curl -s "https://raw.githubusercontent.com/danger/danger-js/HEAD/README.md" | grep -in -m10 -E "who uses|used by|apollo|microsoft|react"
=== danger-python README: runtime requirement ===
16:* danger-js 9.2 (tested under danger-js 9.2.10)
18:### Installation
23:# install danger-js
24:npm install -g danger
25:# install danger-python

=== danger-js README: adopters section ===
128:[rxjs]: https://github.com/ReactiveX/rxjs/blob/master/dangerfile.js
[0m
[0m$ [0mecho "=== cog docs: named users ==="
curl -sL https://cog.readthedocs.io/en/latest/index.html | grep -io -m10 -E "used[^<.]{0,120}" 
curl -sL https://nedbat.com/code/cog/ -o /dev/null -w 'nedbat page: %{http_code}\n'
echo; echo "=== reviewdog README: adopters ==="
curl -s https://raw.githubusercontent.com/reviewdog/reviewdog/HEAD/README.md | grep -in -m8 -E "who uses|used by|adopt"
echo; echo "=== GitHub docs URLs reachable ==="
for u in "https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-job-summary" "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches" "https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-github-cli"; do
  curl -sL -o /dev/null -w "%{http_code} $u\n" "$u"
done
=== cog docs: named users ===
nedbat page: 429

=== reviewdog README: adopters ===
53:    <img alt="Contributor Covenant" src="https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg">

=== GitHub docs URLs reachable ===
200 https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-job-summary
200 https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
200 https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-github-cli
[0m
[0m$ [0mcurl -s https://raw.githubusercontent.com/nedbat/cog/master/docs/index.rst | grep -in -B2 -A8 -E "who|uses|used" | head -60
(no output)
[0m
[0m$ [0mcurl -s "https://api.github.com/repos/nedbat/cog/contents/docs" | python3 -c "import json,sys; [print(x['name']) for x in json.load(sys.stdin)]" 2>/dev/null || curl -s https://raw.githubusercontent.com/nedbat/cog/main/docs/index.rst | head -5
Makefile
changes.rst
conf.py
design.rst
index.rst
module.rst
running.rst
source.rst
[0m
[0m$ [0mcurl -s https://raw.githubusercontent.com/nedbat/cog/master/docs/index.rst | grep -in -A12 -E "people have|use cog|using cog" | head -40
(no output)
[0m
[0m$ [0mcurl -s https://raw.githubusercontent.com/nedbat/cog/master/docs/index.rst | wc -l && curl -s https://raw.githubusercontent.com/nedbat/cog/master/docs/index.rst | grep -in -E "sqlite|python-requests|urllib3|example" | head
130
47:For example, if you run this file through cog:
[0m
[0m$ [0mfor f in "nedbat/coveragepy/master/doc/cmd.rst" "urllib3/urllib3/main/pyproject.toml"; do
  echo "=== $f ==="
  curl -s "https://raw.githubusercontent.com/$f" | grep -in -m3 "cog" 
done
=== nedbat/coveragepy/master/doc/cmd.rst ===
=== urllib3/urllib3/main/pyproject.toml ===
[0m
[0m$ [0mcurl -s "https://raw.githubusercontent.com/nedbat/coveragepy/master/doc/cmd.rst" -o /dev/null -w '%{http_code}\n'
curl -s "https://api.github.com/search/code?q=cogapp+repo:nedbat/coveragepy" -o /dev/null -w 'code search: %{http_code}\n'
curl -s "https://raw.githubusercontent.com/nedbat/coveragepy/master/requirements/dev.pip" | grep -in cog
curl -s "https://raw.githubusercontent.com/nedbat/coveragepy/master/Makefile" | grep -in -m3 cog
404
code search: 401
241:cogapp==3.6.0 \
180:workflows:				#- Run cog on the workflows to keep them up-to-date.
181:	python -m cogapp -crP .github/workflows/*.yml
183:prebuild: css workflows cogdoc		#- One command for all source prep.
[0m
[0m$ [0mcurl -s -o /dev/null -w 'rxjs dangerfile: %{http_code}\n' "https://raw.githubusercontent.com/ReactiveX/rxjs/master/dangerfile.js"; curl -s "https://api.github.com/repos/danger/danger-js/releases/latest" -o /dev/null -w 'ok\n'; curl -s "https://registry.npmjs.org/danger/latest" | python3 -c "import json,sys; d=json.load(sys.stdin); print('npm danger:', d['version'], '| license:', d.get('license'))"
rxjs dangerfile: 404
ok
npm danger: 13.0.10 | license: MIT
[0m
[0m$ [0mfor b in master main; do curl -s -o /dev/null -w "rxjs $b dangerfile: %{http_code}\n" "https://raw.githubusercontent.com/ReactiveX/rxjs/$b/dangerfile.js"; done
curl -s "https://danger.systems/js/" | grep -io -m6 -E "(used on over [^<]{0,60}|[0-9,]+ projects)" 
rxjs master dangerfile: 404
rxjs main dangerfile: 404
[0m
For Question 2 evidence — how real projects treat local hooks vs required CI — verifying that major adopters re-run the *same* hooks in CI:
[0m$ [0mecho "=== pandas: pre-commit as a CI workflow ==="
curl -s "https://api.github.com/repos/pandas-dev/pandas/contents/.github/workflows" | python3 -c "import json,sys; [print(x['name']) for x in json.load(sys.stdin) if 'commit' in x['name'] or 'check' in x['name']]"
echo "=== django: pre-commit/linters in CI? ==="
curl -s "https://raw.githubusercontent.com/django/django/HEAD/.github/workflows/linters.yml" | grep -in -m6 -E "pre-commit|black|flake8"
echo "=== pre-commit.com CI usage section ==="
curl -s -o /dev/null -w '%{http_code}\n' "https://pre-commit.com/"
curl -s "https://pre-commit.com/" | grep -io -m4 -E "continuous integration|pre-commit run --all-files|pre-commit.ci"
echo "=== githooks docs ==="
curl -s "https://git-scm.com/docs/githooks" | grep -io -m3 -E "hooks[^<.]{0,90}no-verify|not copied[^<.]{0,80}|--no-verify"
=== pandas: pre-commit as a CI workflow ===
code-checks.yml
package-checks.yml
=== django: pre-commit/linters in CI? ===
21:  flake8:
22:    name: flake8
34:      - run: python -m pip install flake8
35:      - name: flake8
39:          linters: flake8
40:          run: flake8
=== pre-commit.com CI usage section ===
200
pre-commit.ci
pre-commit.ci
pre-commit.ci
pre-commit run --all-files
pre-commit run --all-files
=== githooks docs ===
--no-verify
--no-verify
--no-verify
[0m
[0m$ [0mecho "=== pandas code-checks.yml: runs pre-commit in CI? ==="
curl -s "https://raw.githubusercontent.com/pandas-dev/pandas/main/.github/workflows/code-checks.yml" | grep -in -m6 -E "pre-commit"
echo "=== pre-commit.ci homepage ==="
curl -sL "https://pre-commit.ci" | grep -io -m3 -E "pre-commit ci[^<]{0,80}|fixes and[^<]{0,60}"
=== pandas code-checks.yml: runs pre-commit in CI? ===
=== pre-commit.ci homepage ===
pre-commit ci
[0m
[0m$ [0mcurl -s "https://raw.githubusercontent.com/pandas-dev/pandas/main/.github/workflows/code-checks.yml" | head -40; echo ---; curl -s "https://api.github.com/repos/pandas-dev/pandas/contents/.pre-commit-config.yaml" -o /dev/null -w '%{http_code}\n'; curl -s "https://raw.githubusercontent.com/pandas-dev/pandas/main/.pre-commit-config.yaml" | grep -in -m4 -E "pre-commit.ci|ci:"
name: Code Checks

on:
  push:
    branches:
      - main
      - 3.0.x
  pull_request:
    branches:
      - main
      - 3.0.x

defaults:
  run:
    shell: bash -euox pipefail {0}

permissions: {}

jobs:
  doctest:
    name: Doctests
    runs-on: ubuntu-24.04
    permissions:
      contents: read

    concurrency:
      # https://github.community/t/concurrecy-not-work-for-push/183068/7
      group: ${{ github.event_name == 'push' && github.run_number || github.ref }}-doctests
      cancel-in-progress: true

    steps:
    - name: Checkout
      uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      with:
        fetch-depth: 0

    - name: Create virtual environment with Pixi
      uses: ./.github/actions/setup-pixi
      with:
        environment: "doctests"
---
200
15:ci:
[0m
[0m$ [0mcurl -sL "https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-github-cli" | grep -io -m2 -E "preinstalled on all GitHub-hosted runners|pre-installed[^<]{0,60}"; curl -sL "https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands" | grep -io -m2 "GITHUB_STEP_SUMMARY"
preinstalled on all GitHub-hosted runners
preinstalled on all GitHub-hosted runners
preinstalled on all GitHub-hosted runners
GITHUB_STEP_SUMMARY
GITHUB_STEP_SUMMARY
[0m
[0m$ [0mgit status --porcelain && echo "(empty = Ranex repo untouched)"
(empty = Ranex repo untouched)
[0m
[0m# [0mTodos
[✓] Read RFC and licence (done), plan work
[✓] Build prototype in /tmp: cog span, cog -c, --check pass/fail exit codes
[✓] Prototype: pre-commit config firing on drift
[✓] Prototype: staleness rule (HEAD-recorded file, fails when HEAD moves)
[✓] Verify externally: reviewdog, danger-js, danger-python, PyGithub, ghapi, githubkit, gh CLI — licence, version, release date, adopters
[•] Q1 answer: pick Python combination, state what is lost vs danger-js
[ ] Q2 answer: pre-commit worth having despite bypass; labelling recommendation
[ ] Write final report: Q1, Q2, transcript, licence table, losses, inferences, unverified
[0m
All work is complete. The Ranex repository was not modified (`git status` clean). Full report follows.

---

# Question 1 answer — the Python way to fill the `danger-js` role

## Candidates surveyed (verification detail in the Licence table)

| Candidate | What it actually is | Verdict for the nagging role |
|---|---|---|
| **`pre-commit`** (Python, already adopted) | Hook *framework*. Runs deterministic checks; in CI via `pre-commit run --all-files` it fails a build. Cannot post PR comments — that is out of scope for it by design. | Keep for the local layer and as the CI entry point for lint-class hooks; it is not the reminder mechanism. |
| **Plain GitHub Actions steps** | A workflow step running any Python command; a non-zero exit fails the job; a job made a *required status check* via branch protection blocks the PR; `$GITHUB_STEP_SUMMARY` renders Markdown on the run page ([workflow commands docs](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-job-summary), fetched 2026-07-30; [required checks docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)). | **Selected.** Zero new dependencies for the fail-the-PR part. |
| **`reviewdog`** | Go binary, MIT, v0.21.0 (2025-09-03). Posts linter findings as inline PR comments. | Rejected: it is a **third toolchain** (Go, self-managed binary) — the exact objection to `danger-js`, minus the ecosystem. Its strength (inline diff comments from linter output) is not the shape of Ranex's checks, which are whole-repo pass/fail. |
| **`danger-python` (danger/python)** | Python bindings for Danger. Last release **v0.1, 2020-02-14**; its own README instructs `npm install -g danger` first — it **requires the Node `danger-js` runtime** ([README](https://github.com/danger/python)). | Rejected twice over: does not remove Node, and release cadence is dormant. |
| **`PyGithub`** | Python PR-comment-capable API client. v2.9.1 (2026-04-14). **LGPL-3.0 — copyleft, flagged.** | Rejected on licence posture (see table). |
| **`ghapi`** (fast.ai) | Python GitHub API client, Apache-2.0, 2.0.4 (2026-07-24). | Acceptable fallback if comment logic ever needs to live in Python. |
| **`githubkit`** | Python GitHub API client, MIT, 0.16.0 (2026-06-14). | Acceptable fallback, same condition. |
| **`gh` CLI** | MIT, v2.96.0 (2026-07-02), **preinstalled on all GitHub-hosted runners** ([docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-github-cli), page states "preinstalled on all GitHub-hosted runners", fetched 2026-07-30). `gh pr comment` posts the visible reminder with `GITHUB_TOKEN`. | **Selected** for the comment step. |

## The single combination Ranex should use

**A GitHub Actions workflow, made a required status check, whose steps are:**

1. Run the existing Python validator path: `python -m cogapp --check -c --diff <doc set>` plus the staleness script (both prototyped below). Non-zero exit fails the PR. This is the enforcement — it is layer 4's "cannot be defeated locally" property, and it needs no library at all.
2. Always write the result (including the `--diff` output on failure) to `$GITHUB_STEP_SUMMARY` — the zero-dependency visible report.
3. On failure only, post/update one PR comment via `gh pr comment` (preinstalled on the runner; no package added). The comment body is produced by the same Python script that already knows what failed — the "you forgot to regenerate the docs / refresh AGENTS.md" nag.

`pre-commit` remains the local mirror of step 1 only (Question 2). If comment logic ever outgrows `gh`, adopt `githubkit` (MIT) — not `PyGithub`.

This satisfies `LANG-PRIMARY-001`: every check and every message is computed by Python; the only non-Python pieces are the CI platform itself and a platform-provided binary, the same status as `git`.

## What is lost versus `danger-js` (the honest cost)

See **What is lost** section below — five concrete capabilities, none free to reimplement.

---

# Question 2 answer — is a bypassable pre-commit hook worth having?

## The case against (steelmanned)

- Bypass is a **designed feature** of git, not a defect to patch: `githooks` documentation explicitly documents `--no-verify` ([git-scm.com/docs/githooks](https://git-scm.com/docs/githooks), fetched 2026-07-30), and hooks are per-clone — a fresh clone has none until `pre-commit install` runs. My prototype committed *known-drifted state* through the hook with `--no-verify` and got exit code 0 (transcript, step C).
- False confidence is the specific recorded concern, and it is legitimate: a green local hook proves only that *this clone, this commit, hook installed, no bypass flag* passed. For an AI agent, worse: an agent can be *instructed* to bypass, or can delete `.git/hooks/pre-commit` — and the RFC's own Assumption 2 says any file an agent can write, an agent can neutralize.

## The case for (from how real projects actually behave)

- The ecosystem's settled answer to bypassability is **not** to drop local hooks but to **re-run the identical hooks server-side**: `pre-commit.com` itself documents CI usage (`pre-commit run --all-files` in CI) and the existence of `pre-commit.ci` ([pre-commit.com](https://pre-commit.com/), fetched 2026-07-30). django, pandas, black, and fastapi all carry `.pre-commit-config.yaml` at HEAD (all four verified HTTP 200 on raw.githubusercontent.com, 2026-07-30), and pandas' config carries a `ci:` block — the pre-commit.ci convention. These projects keep the local hook for *latency* and put *enforcement* in CI. Nobody serious treats the local hook as a control, and nobody serious deletes it either.
- Measured in the prototype: the hook caught an honest omission **at the moment of the commit**, printed the exact drift diff into the terminal, and blocked (transcript, step A). For an AI agent this is the highest-value property: the failure and its diff are injected into the agent's context *during the session that caused it*, when the agent can still fix it at zero marginal cost. CI catches the same defect minutes later — possibly after the session has ended and the context that understood the change is gone, which is precisely the continuity failure this RFC exists to prevent.
- Removing the hook does not reduce false confidence; it only delays first detection. The false-confidence risk is a *labelling* problem, and the RFC has already stated the doctrine ("Useful; not a control, and must not be described as one").

## Recommendation

**Keep layer 3, with mandatory labelling so the artifact itself carries its own epistemic status:**

1. Every hook `name:` in `.pre-commit-config.yaml` begins with a fixed prefix, e.g.
   `ADVISORY (bypassable by design; enforcement = required CI check): <check name>` — the prototype used `CONVENIENCE (not a control): …` and the label is what appears in every hook run's output (visible in the transcript).
2. A comment block at the top of `.pre-commit-config.yaml` stating: *stops honest omission; bypassed by `--no-verify`, uninstall, or fresh clone; the control is the CI required check running the identical command.*
3. The hook `entry:` must be **byte-identical to the CI command** so the two layers cannot drift apart, and so a local pass predicts a CI pass — the hook's only legitimate promise.
4. The word **"control"** is reserved, in all Ranex documentation, for the CI required check. The pre-commit layer may never be cited as evidence in any assurance or compliance claim.

---

# Prototype transcript

All run in `/tmp/opencode/rfc0003-proto` (git repo at `proto/`), Ranex repo untouched (`git status --porcelain` in the Ranex repo: empty). Tools actually installed and executed: `cogapp 3.6.0`, `pre-commit 4.6.1` in a venv.

**Setup.** `registry/adrs.json` (3 ACCEPTED, 1 DRAFT), `tools/doc_values.py` (`accepted_adr_count()`), and `STATUS.md` containing a cog span calling that function.

**1. Generation with checksum** — `python -m cogapp -r -c proto/STATUS.md`:

```
Cogging proto/STATUS.md  (changed)
...
Accepted ADRs: **3**
<!-- [[[end]]] (sum: 0KH/J+dsLV) -->
```

**2. `cog --check` pass and both failure modes, real exit codes:**

```
== 1. cog --check while current ==
Checking proto/STATUS.md
exit code: 0

== 2. Registry drifts (ADR-0004 becomes ACCEPTED) but doc not regenerated ==
Check failed
Checking proto/STATUS.md  (changed)
--- current proto/STATUS.md
+++ changed proto/STATUS.md
-Accepted ADRs: **3**
-<!-- [[[end]]] (sum: 0KH/J+dsLV) -->
+Accepted ADRs: **4**
+<!-- [[[end]]] (sum: iUpU2U2emJ) -->
exit code: 5

== 3. Restore registry, then hand-tamper the generated value (**3** -> **13**) ==
proto/STATUS.md(10): Output has been edited! Delete old checksum to unprotect.
exit code: 1

== 4. Repair by regenerating; check passes again ==
exit code: 0
```

Note step 3 is a literal replay of the RFC's measured defect class ("13 accepted ADRs" hand-written over a true 3) — caught by the `-c` checksum with a distinct exit code and message.

**3. `pre-commit` fires.** Config with two local hooks (labelled `CONVENIENCE (not a control): …`), `pre-commit install` → `pre-commit installed at .git/hooks/pre-commit`. Then: drift the registry, stage, `git commit`:

```
CONVENIENCE (not a control): cog --check on doc spans...............Failed
- hook id: cog-drift-check
- exit code: 5
Check failed
...(-Accepted ADRs: **3** / +Accepted ADRs: **4** diff printed)...
CONVENIENCE (not a control): continuity artifact matches HEAD.......Passed
commit exit code: 1
```

After regenerating: both hooks `Passed`, `commit exit code: 0`.

**The bypass, demonstrated** (Question 2 evidence): same drift, `git commit --no-verify` → `commit exit code: 0` with drifted state committed; the identical check run afterwards in CI-position: `cog --check exit code: 5`. The local layer folded; the check itself did not.

**4. Staleness rule.** `AGENTS.md` carries `describes_commit: <40-hex sha>`; `tools/check_continuity.py` compares it to `git rev-parse HEAD` — one string comparison, no heuristic:

```
== right after generation ==
OK: AGENTS.md is current for HEAD cb12a73b0558.        exit code: 0
== HEAD moves (any commit) ==
FAIL: AGENTS.md is STALE. It describes cb12a73b0558 but HEAD is 0fd6dd323f08.
Regenerate the continuity artifact.                    exit code: 1
== absent artifact ==
FAIL: continuity artifact AGENTS.md is absent.         exit code: 1
```

This also demonstrates RFC acceptance tests 3 and 4 (stale blocks; absent blocks rather than passing silently). Every command above was actually run; nothing in this transcript is reconstructed.

---

# Licence table

Reference licence: `LICENSE-RANEX.md` — source-available, all rights reserved, commercial optionality preserved. All tools below are **development-time dependencies, not distributed as part of the Ranex Material**, so no licence below imposes terms on Ranex's own licence; the copyleft flag is a posture/optionality flag, not a present legal conflict.

| Tool | Licence | Copyleft? | Version | Released | Named adopter(s) | Verified via |
|---|---|---|---|---|---|---|
| `cogapp` | MIT | No | 3.6.0 | 2025-09-21 | coverage.py — pins `cogapp==3.6.0` in `requirements/dev.pip`, runs `python -m cogapp -crP` in its Makefile (verified 2026-07-30) | [PyPI JSON](https://pypi.org/pypi/cogapp/json); raw.githubusercontent.com nedbat/coveragepy |
| `pre-commit` | MIT | No | 4.6.1 | 2026-07-21 | django, pandas, black, fastapi (config at HEAD, all HTTP 200, 2026-07-30) | [PyPI JSON](https://pypi.org/pypi/pre-commit/json) |
| GitHub Actions (platform) | n/a (service) | n/a | n/a | n/a | n/a | [Workflow commands](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-job-summary); [required checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) |
| `gh` CLI | MIT | No | v2.96.0 | 2026-07-02 | Preinstalled on all GitHub-hosted runners (GitHub's own statement) | GitHub API [cli/cli](https://github.com/cli/cli); [Actions docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-github-cli) |
| `reviewdog` | MIT | No | v0.21.0 | 2025-09-03 | UNVERIFIED (9,488 stars; active, pushed 2026-07-29) | GitHub API [reviewdog/reviewdog](https://github.com/reviewdog/reviewdog) |
| `danger-js` | MIT | No | 13.0.10 | 2026-06-25 (GitHub release; npm `latest` agrees) | UNVERIFIED — README's rxjs dangerfile link is dead (404 on master and main) | GitHub API + [npm registry](https://registry.npmjs.org/danger/latest) |
| `danger-python` | MIT | No | v0.1 | **2020-02-14** | UNVERIFIED | GitHub API [danger/python](https://github.com/danger/python); README requires `npm install -g danger` |
| `PyGithub` | **LGPL-3.0** | **Yes — flagged** | v2.9.1 | 2026-04-14 | UNVERIFIED | GitHub API [PyGithub/PyGithub](https://github.com/PyGithub/PyGithub) |
| `ghapi` | Apache-2.0 | No | 2.0.4 | 2026-07-24 | fast.ai (author org); others UNVERIFIED | [PyPI JSON](https://pypi.org/pypi/ghapi/json) |
| `githubkit` | MIT | No | 0.16.0 | 2026-06-14 | UNVERIFIED | [PyPI JSON](https://pypi.org/pypi/githubkit/json) |

**Copyleft flag:** `PyGithub` (LGPL-3.0) is the only copyleft item surveyed. Used-not-distributed in CI it would trigger no obligation, but MIT/Apache alternatives (`githubkit`, `ghapi`) exist at zero capability cost, so there is no reason to carry the flag.

---

# What is lost (versus `danger-js`)

1. **The rule DSL over a structured PR object.** Danger exposes `danger.git.modified_files`, PR title/body/labels, and the diff, making rules like "`src/` changed but no test changed" one-liners. The Python combination must hand-roll this: `git diff --name-only origin/main...HEAD` plus parsing the `GITHUB_EVENT_PATH` payload. Each new *PR-shaped* rule (as opposed to repo-state rule) costs bespoke code.
2. **Sticky comment lifecycle.** Danger maintains exactly one comment per PR, updates it in place, and removes it when issues resolve. `gh pr comment` is append-only; find-and-update logic must be written (roughly 20 lines against the API, but it is Ranex code to maintain).
3. **Inline per-line diff comments.** Danger and reviewdog can annotate specific lines. Step summaries and PR comments cannot. Mitigation exists at zero cost for *file/line* pointers — Actions [workflow commands](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands) `::error file=…,line=…::` produce annotations — but not full inline review threads.
4. **CI portability.** A Dangerfile runs across many CI providers; the selected combination is GitHub-specific. If Ranex ever leaves GitHub, the workflow and comment steps are rewritten (the Python checks themselves are portable).
5. **A plugin ecosystem** of prebuilt rules. Ranex's rules are few and bespoke (drift, staleness), so this loss is small *for the current rule set* — but it is a real ceiling if the nag list grows.

None of these losses touch the HIGH-importance purpose: failing the PR on drift/staleness and making the reason visible needs none of the five.

---

# Inferences (each marked, separately)

1. **Inference:** `gh` CLI does not constitute a "second toolchain" under `LANG-PRIMARY-001`, because it is platform-provided on the runner (like `git` itself) rather than a managed dependency. The owner may rule otherwise; the fallback is `githubkit` (MIT, Python).
2. **Inference:** `danger-python` is dormant. Based on release history (single release, v0.1, 2020-02-14). The repo's `pushed_at` is 2026-07-27, so *some* activity exists; "dormant" is my reading of the release cadence, not a verified project statement.
3. **Inference:** pandas uses pre-commit.ci, based on the `ci:` block in its `.pre-commit-config.yaml` (that block is the pre-commit.ci configuration convention). I did not verify a pre-commit.ci run on a pandas PR.
4. **Inference:** an AI agent that has not been prompted about hooks will run plain `git commit` and therefore be caught by the local hook. Plausible default behaviour; not measured.
5. **Inference:** the semantic meaning of cog's exit codes (5 = would-change, 1 = checksum-protected edit) is derived from observed behaviour and messages in the prototype, not from a documented exit-code table.
6. **Inference:** the in-session context injection of a hook failure is more valuable to a memoryless agent than the same failure surfacing in CI after session end. This follows from the RFC's own continuity premise but is an argument, not a measurement.

# Unverified

- Named adopters of `reviewdog`, `danger-python`, `githubkit`, and (beyond the author org) `ghapi` — marked UNVERIFIED in the table.
- Named adopters of `danger-js`: the RFC accepts danger.systems' self-description; the one concrete adopter link in its README (ReactiveX/rxjs `dangerfile.js`) returned 404 on both `master` and `main` on 2026-07-30, so I can name **no currently verified adopter**.
- Whether GitHub branch protection / required checks will actually be available to Ranex — this is the RFC's Unknown 1 (does a remote CI service exist?) and remains open; my Q1 recommendation is conditional on it exactly as layer 4 already is.
- pre-commit's popularity *statistics* (download counts etc.) — I verified four named adopters instead.
- I did not run the `gh pr comment` / `$GITHUB_STEP_SUMMARY` steps — they require a live GitHub PR and runner, which the read-only, local constraint precludes. The enforcement and check layers of the prototype **were** run; only the two GitHub-side reporting steps rest on the cited documentation rather than execution.
