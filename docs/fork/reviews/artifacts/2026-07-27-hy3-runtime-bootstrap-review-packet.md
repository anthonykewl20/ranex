# Ranex adoption and Hermes runtime bootstrap — frozen HY3 review packet

## Review control

| Field | Value |
|---|---|
| Review purpose | Fresh independent final review of the completed upstream adoption and Hermes runtime bootstrap |
| Reviewer route | `openrouter/tencent/hy3`, variant `high` |
| Execution mode | Tool-less, read-only, fresh OpenCode session with sharing, snapshots, plugins, and automatic compaction disabled |
| Review date | 2026-07-27, Asia/Manila |
| Decision authority | Human owner; HY3 is advisory only |
| Repository | `anthonykewl20/ranex` |
| Upstream | `NousResearch/hermes-agent` |
| Upstream baseline | `d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012` |
| Published Ranex `main` | `9be6bd9443e447b205ad265d44238436910dfbce` |
| Published Ranex `develop` / review subject | `beee3cdc431e38b6e82ec5628263f743932022e4` |
| Review worktree | `/home/soultransit/devtony/ranex/.claude/worktrees/phase-2-runtime-bootstrap` |

This is a new review. Do not reuse or defer to any historical HY3 verdict. Judge
only this packet and its attached annexes.

## Exact decision question

Is the published Ranex `develop` revision and its installed, isolated Hermes
runtime ready for the owner to begin **bounded Ranex development now**, without
claiming that deferred cleanup, product rebranding, or the target Ranex
architecture is already implemented?

Also answer directly:

1. Was upstream adoption performed safely and honestly enough to serve as the
   development base?
2. Is Hermes itself correctly installed and configured for immediate use with
   the `openai-codex` provider and `gpt-5.6-sol`?
3. Are the test results and `PARTIAL` phase labels represented honestly?
4. Which gaps block coding now, which are required follow-ups, and which are
   merely optional convenience or capability additions?

## Scope

Review these completed slices:

- Phase 1: adoption of upstream Hermes history into standalone Ranex branches.
- Phase 2: isolated Python/Node development runtime bootstrap.
- Phase 3: upstream baseline test execution and classification.
- Post-baseline: separate OpenAI Codex OAuth login and one-call
  `gpt-5.6-sol` Hermes smoke.
- Current operational configuration needed to begin development through the
  CLI or web dashboard.

## Explicit non-goals

Do not grade these as though they were claimed complete:

- deferred Codex/VS Code cleanup under the owner's explicit sequencing waiver;
- Ranex public rebranding or compatibility migration;
- implementation of the target governed-execution architecture;
- public dashboard exposure, messaging gateways, browser automation, external
  web-search providers, or optional third-party integrations;
- a clean primary checkout switch while a separate active editor/session still
  owns changes there.

The correct standard is readiness for **bounded development from the isolated
`develop` worktree**, not completion of the Ranex product.

## Frozen repository evidence

The following observations were captured from the review worktree immediately
before this packet was assembled.

### E-R1 — revision and branch alignment

```text
HEAD                         beee3cdc431e38b6e82ec5628263f743932022e4
origin/develop               beee3cdc431e38b6e82ec5628263f743932022e4
origin/main                  9be6bd9443e447b205ad265d44238436910dfbce
upstream/main                d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012
origin/upstream-sync         d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012
main vs origin/main          0 ahead / 0 behind
develop vs origin/develop    0 ahead / 0 behind
review worktree status       clean before creation of this ignored packet
```

Both ancestry checks exited zero:

```text
upstream/main -> origin/main
origin/main   -> origin/develop
```

### E-R2 — published change shape

`main` layers Ranex documentation, governance, licensing, research, templates,
and a local environment example onto the exact upstream Git history. It does
not merge the unrelated bootstrap root into upstream.

Between the upstream baseline and `develop`, the only non-document tracked
paths added or changed are:

```text
.gitignore
.local/dev-env.sh.example
LICENSE-RANEX.md
NOTICE.md
decisions/local-values.env.example
legal/licensing-manifest.json
README.md
```

All other Ranex-layer changes are Markdown, HTML, or SVG records. No Python,
TypeScript, JavaScript, package-lock, `uv.lock`, production runtime, or test
source differs from the upstream baseline in this phase.

### E-R3 — commit separation

```text
9be6bd9443e447b205ad265d44238436910dfbce
  docs: adopt Ranex guide and governance

beee3cdc431e38b6e82ec5628263f743932022e4
  docs: record gpt-5.6-sol runtime smoke
```

The runtime evidence commit changes only:

```text
docs/fork/IMPLEMENTATION_STATUS.md
docs/fork/UPSTREAM_BASELINE.md
```

### E-R4 — licensing and publication

The attached licensing manifest records the inherited upstream files and Ranex
additions. Prior local publication checks reported:

- public origin was verified empty before adoption;
- `main`, `develop`, and `upstream-sync` were pushed;
- local `main` tracks `origin/main`;
- the annotated local upstream-baseline tag resolves to the upstream SHA;
- upstream is an ancestor of `main`, and `main` is an ancestor of `develop`;
- the primary checkout was deliberately not switched because an active
  Codex/VS Code session owns uncommitted documentation there.

Treat the last item as a declared, owner-approved sequencing deviation, not as
evidence that cleanup passed.

## Frozen runtime evidence

### E-H1 — isolated installation

```text
Hermes Agent        0.19.0 (2026.7.20)
Python              3.11.15
Install method      editable Git checkout
Install directory   /home/soultransit/devtony/ranex/.claude/worktrees/phase-2-runtime-bootstrap
Application home    /home/soultransit/.local/share/ranex
Development venv    /home/soultransit/.local/share/ranex/venvs/dev
```

The host's Python 3.14 is outside upstream's supported range, so the setup uses
an external uv-managed Python 3.11 environment. It does not replace the system
Python and does not place the venv inside the Git checkout.

The tracked `.local/dev-env.sh.example` exports:

```text
HERMES_HOME=$HOME/.local/share/ranex
RANEX_HERMES_VENV=$HERMES_HOME/venvs/dev
HERMES_PYTHON=$RANEX_HERMES_VENV/bin/python
PATH=$RANEX_HERMES_VENV/bin:$HOME/.local/bin:$PATH
```

The host-specific `.local/dev-env.sh` is ignored and contains the resolved
equivalent. Therefore the current CLI launch contract is:

```bash
source .local/dev-env.sh
hermes
```

Without sourcing that file or explicitly setting `HERMES_HOME`, a direct
invocation would select the user's separate default `~/.hermes` profile.

### E-H2 — persistent model configuration

The entire isolated `config.yaml`, mode `0600`, is:

```yaml
model:
  provider: openai-codex
  default: gpt-5.6-sol
```

`hermes config check` exits zero. It reports that the minimal file has config
schema version `0` while the running defaults are version `33`; runtime defaults
are deep-merged, so this is an available migration rather than a parse or model
selection failure.

### E-H3 — authentication boundary

The isolated `auth.json`:

- has mode `0600`;
- selects `openai-codex` as the active provider;
- contains one separate OAuth credential labeled `ranex`;
- records device-code origin;
- contains refresh material and no last authentication error.

No token or credential value is included in this packet. The credential was
created independently for Hermes and was not copied from or written into the
Codex/VS Code authentication store.

`hermes status` reports:

```text
Project:  /home/soultransit/devtony/ranex/.claude/worktrees/phase-2-runtime-bootstrap
Python:   3.11.15
Model:    gpt-5.6-sol
Provider: OpenAI Codex
Auth:     OpenAI Codex logged in
Backend:  local
```

### E-H4 — live smoke

After configuration and login, Hermes was invoked with an explicit provider,
model, safe toolset, and exact-response prompt:

```bash
HERMES_HOME=/home/soultransit/.local/share/ranex \
hermes \
  --provider openai-codex \
  --model gpt-5.6-sol \
  --toolsets safe \
  --oneshot 'Reply exactly: RANEX_HERMES_OK'
```

Recorded result:

```text
Authentication       openai-codex logged in
Provider             openai-codex
Model                gpt-5.6-sol
API calls            1
Output               RANEX_HERMES_OK
Input tokens         17,088
Output tokens        11
Usage-report error   null
```

No inference request was sent with `gpt-5.4`; the obsolete fixture-derived
value was replaced before the first live call.

### E-H5 — operational surface status

- `hermes dashboard` is installed and defaults to loopback
  `127.0.0.1:9119`.
- Its backend and Node/npm dependencies are installed.
- The generated web distribution does not exist yet, so first dashboard launch
  is expected to build it.
- No dashboard process is currently running.
- No user or system Hermes/Ranex dashboard service is installed.
- No Hermes project is registered in the optional project database; CWD-based
  CLI operation still resolves the review worktree correctly.
- No user-installed skills are present in the isolated home; bundled skills
  remain available from the editable source distribution.
- Optional browser automation is unavailable until Playwright Chromium is
  installed.
- Optional web-search tools have no third-party search API key.
- The local terminal, file, delegation, memory, project, session, todo, and
  skills tool families are available.

Judge whether any of these are blockers for bounded local coding, and distinguish
that from a request for an always-on dashboard or every optional tool.

## Frozen baseline verification

### E-T1 — environment and integrity checks

These completed successfully:

```text
uv sync --locked --python 3.11 --extra all --extra dev
uv lock --check
python compileall across agent, CLI, gateway, tools, providers, plugins
hermes --version
hermes --help
hermes-acp --version
hermes config check
npm ci --no-audit --no-fund
npm run check
```

The checked-in Python and npm lockfiles remained unchanged.

### E-T2 — Python baseline

```text
Passed        48,519
Failed        3
Skipped       236
Workers       32
Runner time   562.9 seconds
Wall time     567.12 seconds
```

The three failures were reproduced narrowly with one worker and were classified
against byte-identical upstream source/tests:

1. one Copilot HOME test sees host Docker/containerd mount paths and the
   inherited detector falsely treats the systemd host as a container;
2. two credential-pool tests discover the real user's Claude credential file
   and violate their temporary one-entry assumption.

The two credential tests pass when run with an isolated nonexistent `HOME`.
Per-file subprocess isolation and a narrow rerun rule out parallel or cross-file
contamination. A context-compressor timeout passed on retry.

No production or test-source patch was mixed into baseline capture.

### E-T3 — JavaScript baseline

```text
Vitest          4,826 passed, 0 failed, 7 skipped
Workspace       516 passed, 1 skipped
TypeScript      pass
ESLint          pass with 76 warnings and zero errors
Desktop checks  pass
Lock digest     unchanged
```

Inherited nonblocking warnings include build-time dependency advisories,
deprecated package notices, build-size/CSS/canvas notices, and one TUI
subprocess warning. The relevant suites still passed.

## Known limitations and honesty constraints

1. Raw CI-style logs are not attached; the detailed baseline record and counts
   are attached. HY3 must state the attestation limit instead of pretending to
   have rerun 50,000+ tests.
2. HY3 has no tools in this run and cannot inspect credentials, the network, or
   mutable host state. It must not claim otherwise.
3. The review packet creation makes one ignored local file; it is outside the
   frozen Git subject.
4. `PARTIAL` is intentionally retained for Phase 0A, Phase 1, and Phase 3. Do
   not silently upgrade those labels merely because bounded development may be
   safe.
5. A passing runtime-bootstrap verdict is not an architecture implementation
   verdict.

The declared phase state that must be audited rather than silently promoted is:

```text
Phase 0A cleanup               PARTIAL
Phase 1 upstream adoption      PARTIAL
Phase 2 isolated environment   PASS
Phase 3 upstream baseline      PARTIAL
```

For this review, `PASS` means that the packet is materially consistent, its
claims are supported at the stated attestation level, and its sequencing is
safe for the bounded decision question. It does not mean every phase is
complete.

## Attached annexes and digests

| Annex | Lines | SHA-256 |
|---|---:|---|
| `.local/dev-env.sh.example` | 8 | `ef41d13baa9c666d71709e40ec2928a0a516ae9af97256af7e5af8d996f83fcf` |
| `legal/licensing-manifest.json` | 358 | `cfd58b130960560d0ebf83caf3cc9beaaba0e7fd9d398c82249f9fc163c86d95` |
| `docs/fork/IMPLEMENTATION_STATUS.md` | 71 | `2d52cd7dd5ad20f940dfc3f6107b37fa8e0cff536eeb9a9365bf06b685cc62e1` |
| `docs/fork/UPSTREAM_BASELINE.md` | 169 | `7c2013321cd4cae3fdb6594061ac16585bf64b90033c582ecb0eb98b491fb908` |
| `docs/fork/FORK_POLICY.md` | 41 | `c13e9b4bda91849ce84f8dfeddfb918e20c67c29f21f899feba4a154f20bfebd` |
| `docs/fork/UPSTREAM_SYNC.md` | 42 | `a5f791c63b2841f1720e56e3fcbbec4952b5b7c79fd134c6bb7c3e3e2d4dda04` |
| `docs/fork/BRANDING_STRATEGY.md` | 34 | `8ae3c4e7dc2dc5f8b85c676189cb3bc8716c19f58244fadc2e333d3cd6ca5162` |

## Required response schema

Return Markdown using exactly these top-level headings.

### 1. FINAL VERDICT

Choose exactly one:

- `READY_FOR_BOUNDED_RANEX_DEVELOPMENT`
- `READY_WITH_REQUIRED_REMEDIATIONS`
- `NOT_READY`

Define the subject precisely in one paragraph. Do not call the target
architecture implemented.

### 2. GATE VERDICTS

Use a table with these exact rows and choose `PASS`, `CONDITIONAL`, or `FAIL`:

- Upstream adoption integrity
- Published branch and ancestry integrity
- Licensing/provenance evidence
- Isolated runtime installation
- Provider/model/auth configuration
- Baseline test honesty
- Immediate CLI development usability
- Immediate web dashboard usability
- Evidence sufficiency

For each row, cite packet evidence IDs or attached annex path/line references.

### 3. BLOCKERS

List only issues that prevent the owner from beginning bounded Ranex coding now.
Write `None` if there are none.

### 4. REQUIRED REMEDIATIONS

List mandatory follow-ups, identify whether each must happen before the first
coding task, before the first merge, or before release, and give a concrete
acceptance check.

### 5. NONBLOCKING GAPS

Explicitly classify config schema migration, optional project registration,
global launcher, background dashboard service, first dashboard build,
Playwright/browser support, web-search keys, optional integrations, and the
deferred primary-checkout cleanup.

### 6. CLAIMS THAT MUST NOT BE MADE

State which stronger completion or approval claims the evidence does not
support.

### 7. DIRECT ANSWER TO THE OWNER

In no more than 150 words, answer:

> Is Hermes properly configured for me to start using it to develop Ranex, and
> what exact launch contract applies today?

### 8. REVIEW LIMITATIONS

State the tool-less and evidence-attestation limits and reiterate that HY3 has
advisory, not gate, authority.

### 9. MACHINE-READABLE VERDICT

End with one fenced `json` block matching this shape:

```json
{
  "review_verdict": "PASS|CHANGES_REQUIRED|INCONCLUSIVE",
  "readiness_verdict": "READY_FOR_BOUNDED_RANEX_DEVELOPMENT|READY_WITH_REQUIRED_REMEDIATIONS|NOT_READY",
  "phase_status": {
    "phase_0a": "PASS|PARTIAL|FAIL|UNKNOWN",
    "phase_1": "PASS|PARTIAL|FAIL|UNKNOWN",
    "phase_2": "PASS|PARTIAL|FAIL|UNKNOWN",
    "phase_3": "PASS|PARTIAL|FAIL|UNKNOWN"
  },
  "blocker_ids": [],
  "required_followups": [],
  "authority_note": "ADVISORY_ONLY_NO_GATE_AUTHORITY"
}
```
