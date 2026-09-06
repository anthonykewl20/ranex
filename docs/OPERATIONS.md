# Operating Ranex

[Public overview and quickstart](../README.md) · [Architecture](MAP.md)

These are the detailed source-checkout, trust-root and host instructions.
Start with the public quickstart for a small real-repository demonstration.

## Running it

```sh
uv run --frozen pytest -q

uv run --frozen ranex gate evaluate HEAD --approver reviewer_alice
# Equivalent module-path form from the source checkout:
PYTHONPATH=src uv run --frozen python -m ranex.cli.main gate evaluate HEAD --approver reviewer_alice
```

Always `--frozen`. Plain `uv run` re-locks and rewrites `uv.lock`, which is a
trust root here: it silently dropped the resolution epoch once, after which
`ranex deps fetch` refused the lock against its own clean derivation. The
gated command needs no flag — its argv stays exactly as the catalog binds it,
and `run` sets `UV_FROZEN` in the environment instead.

### Installing as an operator

```sh
git clone https://github.com/anthonykewl20/ranex && cd ranex
uv sync --frozen
```

`uv sync --frozen` builds and installs ranex editable plus the `ranex`
console script into the checkout venv (CPython; dependency versions come from `uv.lock`). Invoke it as
`.venv/bin/ranex` — it works from outside the checkout, with no `PYTHONPATH` —
or as `uv run --frozen ranex` from inside one. The wheel is the shippable
artifact. By default governed subcommands anchor to the checkout containing
the CLI (ADR-009); the core observation/evaluation commands also accept an
explicit external target (ADR-052), described below. Strict-local host runtime
profiles still require a qualified kernel source checkout.

**On a fresh clone `gate evaluate` fails, and that is correct.** Absence
blocks: no evidence exists yet for `tests-executed`, so the verdict is FAIL
with a nonzero exit, naming the missing claim — the journal and evidence
store are gitignored, and a fresh keygen key is not the committed
`producers.yaml` keyring. Producing evidence needs a signing identity of your
own — the private key must live outside the repository, and `keygen` refuses
to write it anywhere inside:

```sh
export RANEX_SIGNING_KEY=~/.config/ranex/worker.key
uv run --frozen ranex keygen --producer worker
# Equivalent module-path form from the source checkout:
PYTHONPATH=src uv run --frozen python -m ranex.cli.main keygen --producer worker
```

This repository commits the **public** keyring, `governance/producers.yaml` —
it is the trust root, and review of it is the control on it. It holds public
halves only; no private key is anywhere in the tree. `keygen` prints a valid
new keyring with matching producer and active worker entries. In this checkout,
merge those entries into the existing mappings; preserve the other identities
and `verdict_signer`. Both mappings must attribute the same public key:

```yaml
producers:
  worker: ed25519:<the key keygen printed>
principals:
  worker:
    role: worker
    keys:
      - key: ed25519:<the key keygen printed>
        status: active
```

Commit the change. A historical keyring without `principals` can continue to
register just the producer entry. Adding a principal catalog to such a keyring
requires attributing every existing producer and verdict signer too.

Next, provision dependencies. The bound command is `uv run pytest -q`, and the
observation is built from committed blobs only — so `.venv` is not in it and the
suite has nothing to import until its wheels are provisioned deliberately. The
resolver is pinned by path **and** digest in `governance/deps.yaml`, at a
root-owned location. Before proceeding, an operator must install the exact resolver
and interpreter named in `governance/deps.yaml` and verify the resolver SHA-256.
Installing an arbitrary current `uv` binary will not satisfy those pins. On an
already provisioned host:

```sh
uv run --frozen ranex deps fetch
uv run --frozen ranex deps approve --approver reviewer_alice
# Equivalent module-path forms from the source checkout:
PYTHONPATH=src uv run --frozen python -m ranex.cli.main deps fetch
PYTHONPATH=src uv run --frozen python -m ranex.cli.main deps approve --approver reviewer_alice
```

`deps fetch` is the only networked step: it re-derives the lock from the manifest
alone under those pinned inputs, refuses any byte of difference, and admits only
SHA-256-addressed wheels to the store. `deps approve` prints the package delta
and records that a human accepted exactly it. **Skipping either makes the next
command refuse, by name** — a lock nothing regenerated may be entirely authored.
Approval reduces hidden change; it cannot make third-party code truthful, and
`tests/security/test_slice006_approved_wheel_can_lie.py` demonstrates an
approved, hash-correct wheel forcing a passing verdict. Then:

```sh
uv run --frozen ranex run \
    --claim tests-executed --producer worker -- uv run pytest -q
# Equivalent module-path form from the source checkout:
PYTHONPATH=src uv run --frozen python -m ranex.cli.main run --claim tests-executed --producer worker -- uv run pytest -q
```

`gate evaluate` then judges that run for real. The observation is a fresh
single-commit repository carrying the verified tree (`ADR-009`, accepted), so
the handful of this repository's own tests that ask git about themselves are
told the truth, and the gate compares signed structured outcomes against the
frozen manifest diff rather than the exit code alone (SLICE-009). On a qualified
host, matching passing evidence satisfies this claim; deleting a frozen test's
file makes the gate reject the incomplete suite.

Once the tree moves past the digest the evidence was bound to, `tests-executed`
stops counting too. A record that fails verification is reported as *refused*,
with a reason — never as "no evidence", because an attack and an unfinished task
are not the same event.

### Governing an external repository

`--external-repository PATH` selects an existing Git checkout root for `keygen`,
`suite freeze`, `run`, `gate evaluate`, `journal verify`, `deps fetch` and
`deps approve`. The installed kernel stays separate; an application's own
`src/` is preserved. Do not combine this flag with a non-default `--repository`.
All governance file arguments remain relative to, and confined within, the
selected root. Private keys must be outside that repository and its worktrees.

From the Ranex checkout, after committing the external repository's reviewed
catalog, public keyring and frozen manifest, the core loop is:

```sh
uv run --frozen ranex run --external-repository /path/to/repo \
  --claim tests-executed --producer worker -- /usr/bin/python3 -m pytest -q
uv run --frozen ranex gate evaluate HEAD --external-repository /path/to/repo \
  --approver reviewer_alice
uv run --frozen ranex journal verify --external-repository /path/to/repo
```

Use the exact command bound in the target's catalog, including any results
artifact flag. `suite freeze` accepts the same target selector and retains its
existing `--artifact`, `--output` and expected-skip rules. `keygen` accepts the
selector before writing the operator's externally stored signing key. Signed
verdict publication uses the target's committed verdict signer and the same
`RANEX_VERDICT_SIGNING_KEY`/`RANEX_VERDICT_DIR` configuration as the local loop.

External targeting changes repository selection, not the acceptance policy or
the execution trust boundary. It does not make candidate-controlled tests an
independent oracle. Default hermetic runs need their runtime dependencies
outside the target; inherited `PYTHONPATH` and arbitrary environment variables
are not a provisioning mechanism. Strict-local runs retain their qualified
host/runtime requirements. Live App setup and check scheduling are separate.

Full-repository production acceptance is not established by the small external
pilots. The [production audit](../tools/dogfood/FINDINGS.md)
records full baseline and governed attempts, runtime/provisioning differences,
JUnit collection-skip refusal and the live App requirements still unverified.
Do not use those baseline test counts as signed Ranex acceptance results.

For Vitest JUnit, the claim must explicitly set `results_reporter: vitest-junit`
and bind the exact tokens `--reporter=junit` and `--outputFile=PATH`, where
`PATH` equals `results_artifact`. Duplicate/overriding reporter or output options
and a `--` separator in that bound argv are refused. This spelling was verified
with installed Vitest 4.1.11; it avoids assuming pytest flags work with another
runner. Freeze its manifest using `suite freeze --results-reporter vitest-junit`.
Vitest IDs preserve `classname::name`; pytest's existing ID mapping stays the
default. A manifest frozen with the wrong convention cannot satisfy the gate.
Both reporters use the same JUnit safety, duplicate-ID, missing-ID and outcome
checks. This supports one results artifact per claim; distributed collection
and shard aggregation are not implied.

## The GitHub acceptance loop (Ranex GitHub App)

Ranex can answer pull requests the way GitHub natively understands: a check
named `ranex/acceptance`, published by the Ranex GitHub App, required by a
repository ruleset. The App is a publisher, never a judge — it reads the
signed verdict a `gate evaluate` run already produced for the PR head's
exact git tree and turns it into a check. No verdict, no green.

### What the check says

- `success` — a verdict publication verified against the committed verdict
  signer names this PR head's tree and says PASS.
- `failure` — a verified verdict says FAIL (the failing rule and missing
  claims are in the check's output), or a verdict exists but was rejected
  (bad signature, wrong context, unknown signer — the reader state is named).
- `action_required` — no verdict publication exists for the PR head's tree
  yet. Run the gate; the App publishes on the next event.

The binding is content, not names: the receiver derives the subject digest
from the PR head SHA's git tree (`git fetch` into the operator clone, then
the same tree digest every Ranex subject uses), so a check can only ever be
about the exact bytes a merge would land.

### Creating the App (one time)

1. GitHub → Settings → Developer settings → GitHub Apps → New GitHub App.
   Name it (e.g. `ranex`), set a webhook URL (HTTPS; for local development
   a smee.io tunnel forwards to the receiver's localhost bind), content
   type `application/json`, and generate a webhook secret.
2. Permissions: **Checks: Read & write**, **Contents: Read-only**,
   **Pull requests: Read-only**. Subscribe to events: **Pull request**.
   Generate and download the App private key (PEM); keep it outside the
   repository, like every Ranex key.
3. Install the App on the repository. Note the installation ID (visible in
   the installation's URL) and the App ID (the App settings page).
4. On the operator host, export `RANEX_GITHUB_APP_ID`,
   `RANEX_GITHUB_APP_PRIVATE_KEY` (path to the PEM, outside the repo) and
   `RANEX_GITHUB_WEBHOOK_SECRET`. A GitHub Enterprise host can be named
   with `RANEX_GITHUB_API_ROOT`.
5. Run the receiver beside a clone of the repository:

   ```console
   uv run --frozen ranex github listen --bind 127.0.0.1:8080 \
     --installation <installation-id> --repo owner/name --approver <id>
   ```

   TLS is the terminator's job — a reverse proxy in front, or the smee.io
   tunnel in development; the listener deliberately binds localhost and
   processes one delivery at a time, with at most 16 connections and a
   five-second total request-read deadline. Excess connections are closed;
   a busy delivery pipeline answers 503. Every delivery proves its
   `X-Hub-Signature-256` HMAC before a byte of it is parsed; replays are
   no-ops after durable completion; failures remain retryable after restart.
   The diagnostic journal is `deliveries.jsonl`; atomic completion receipts
   live in `completed/` under the state dir (`.local/ranex/github` by default).
   Preserve both on upgrades. GitHub does not automatically retry failed
   deliveries: request redelivery in GitHub or through its API. A crash after
   remote publication but before local completion can still duplicate a check.
   Credentials, trusted keys and the allowlist are loaded at startup; restart
   the listener after changing them.

Producing verdicts is unchanged: a `gate evaluate` run against the PR head
(wired with `RANEX_VERDICT_SIGNING_KEY` and `RANEX_VERDICT_DIR`) writes the
signed publication the App reads. The one-shot
`ranex github check publish --head-sha <sha> --installation <id> --repo
owner/name` exercises the same path without a webhook, for debugging.

### Requiring the check (ruleset)

Repository Settings → Rules → Rulesets → New ruleset (target: the default
branch), add rule **Require status checks to pass**, and add the check
`ranex/acceptance`. Pin the source App so only the Ranex App's check
satisfies the rule — equivalently, via REST:

```json
POST /repos/<owner>/<repo>/rulesets
{
  "name": "ranex-acceptance",
  "target": "branch",
  "enforcement": "active",
  "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
  "rules": [{
    "type": "required_status_checks",
    "parameters": {
      "strict_required_status_checks_policy": true,
      "required_status_checks": [
        {"context": "ranex/acceptance", "integration_id": <the Ranex App ID>}
      ]
    }
  }]
}
```

The `integration_id` entry is what makes the Ranex App the expected source
of the check: a same-named check from any other App or token does not
satisfy the rule. With the ruleset active, a merge is blocked unless the
Ranex App published `ranex/acceptance` as `success` on the PR head — and
the App only says `success` when a verified, signed verdict for that exact
tree says PASS.

### Limits, stated plainly

The App publishes; it never evaluates. The receiver host and App credentials
are part of the trust boundary: control of them permits publishing a green
GitHub check directly. GitHub authenticates the publishing App; it does not
verify Ranex's verdict signature. An independent reader can verify the signed
Ranex record separately. This corrects ADR-051's historical claim that a
compromised receiver cannot forge a green check; the ADR is retained unchanged.
Webhook delivery replay is handled by delivery-ID dedup; nonces remain deferred.
Journal history verification requires an independently retained head.
The receiver is the repository's first long-running process and is bounded:
one endpoint, one event type, one delivery at a time, localhost by default.


## Current capabilities and limits

**Current source-run kernel.** The public parser in `ranex.cli.main`
currently exposes:

```text
gate evaluate
journal verify
run
suite freeze
deps fetch | approve
keygen
github bind
github check publish
github listen
host launcher-build | launcher-install | host-probe | qualify | launcher-identity | strict-local
task dispatch | judge | merge | delegate | fanout
task batch qualify | verify
specification draft | advance | questions | status | approve
```

Code-backed capabilities:

- deterministic blocking-gate evaluation with exact subject, claim, command,
  exit, optional suite-manifest, contradiction, and producer/approver checks;
- Ed25519 evidence signing and admission against a committed public keyring;
- committed-tree materialisation, dirty-tree refusal, constrained command
  resolution, and evidence recording through `run`;
- a SQLite append API with update/delete triggers, a hash chain, compare-and-swap
  append, and operator verification;
- JUnit-ID manifest freezing with explicit expected-skip declarations;
- pinned dependency derivation, wheel verification/storage, and separate
  dependency-set approval;
- serial task worktree dispatch, candidate judging, and signed-approval merge
  through policy, ancestry, linear-range, evidence, and stale-ref checks;
- prototype external-harness delegation with emission validation, timeout
  process-group kill, independent suite execution, and structured outcome files;
- retained, redacted, digest-bound delegation/fanout logs beside each outcome
  (`<outcome>.logs/`, fanout parent `fanout.logs/`) with bounded
  tail-preserving truncation and an additive canonical `logs` block carrying
  per-stream sha256, truncation markers, and redaction counts (ADR-043);
- prototype bounded free-prompt fanout over that delegation path;
- A/B/C validators, deterministic specification projections, lifecycle,
  approval/revocation/grant, trace, and candidate-verification Python and CLI
  APIs;
- operator-reachable approval signing (`specification approve`) and
  independent read-only rechecking of a completed qualification
  (`task batch verify`), both composing existing kernel functions (#65);
- A/B/C-bound batch qualification in disposable children whose signed output is
  explicitly non-publishable; and
- optional signed verdict-file publication plus an internal verified reader API.

Host-dependent capability:

- `run --confinement strict-local` implements Linux namespace, Landlock,
  seccomp, cgroup, fixed-mount, static-worker, and dynamic-runtime-closure
  paths. It refuses hosts that do not satisfy the qualification contract. It is
  not available on every Linux installation.

**Operating the strict-local host workflow.** The `ranex host` command group
exposes six verbs: `launcher-build`, `launcher-install`, `host-probe`,
`qualify`, `launcher-identity`, and `strict-local`. The launcher lifecycle is
explicit — build, install, qualify (fresh per run), then verify identity
against the manifest pin (`ranex-launcher-v1`). `ranex host strict-local
--version v1|v2|v3 --claim CLAIM --producer PRODUCER -- <command>` runs the
prechecks, prepares and enters the delegated cgroup scope, and runs
strict-local without manual systemd choreography. Each run — success or
refusal — retains a canonical `host-run-report.json`
(`ranex-host-strict-local-run-v1`) plus redacted, bounded logs under the
result dir. The strict-local controller remains same-UID trusted
infrastructure.

**Operating retained delegation logs.** Each `task delegate` run writes
`<outcome>.logs/{harness.stdout.log,harness.stderr.log,suite.stdout.log,suite.stderr.log,manifest.json}`
beside its outcome file; `task fanout` adds a parent transcript under
`<outcome-dir>/fanout.logs/`. Control them with `--log-dir`,
`--log-max-bytes` (default 262144, bounds 4096–8388608), `--log-retention
keep|replace|off` (default `replace`), and repeatable `--redact-env NAME`;
fanout accepts the same flags and forwards them — including each
`--redact-env NAME` — to every child. Verify a log
against its outcome entry with `sha256sum` — the outcome's `logs` block
carries each stream's digest over the retained bytes on disk. A log that
exceeded the bound begins with a `[ranex truncated: …]` marker: the head was
dropped, the tail (including the FINAL failure reason) was preserved.
Secrets matching the redaction grammars appear only as
`[REDACTED:env:NAME]`, `[REDACTED:pem]`, or `[REDACTED:credential]`.
Ranex never deletes logs on its own — retention and cleanup are yours.

**Operating specification approval and batch verification.** The owner
authority lifecycle ends in a signature:
`ranex specification approve --payload approval-payload.json --output approval-envelope.json`
signs the canonical approval payload with the key `RANEX_SIGNING_KEY` names
(mode 0600, outside the repository), writing the envelope exclusively and
printing `APPROVED <output> key_id=<key>`. After a qualification completes,
`ranex task batch verify --spec-packet spec-packet.json --artifact-manifest manifest.json --approval-envelope approval-envelope.json --qualification qualification.json --target /path/to/governed-repo --journal journal.db`
independently rechecks it — A/B/C chain, protected digests, subject
binding, journal continuity, attestation admission — printing the
canonical facts and `PASS ... VERIFIED`, or refusing with `E-BATCH-*` and
exit 1. Verification is read-only and authorizes nothing.

Current limits visible in code:

- the supported operator install is the frozen checkout: `uv sync --frozen`
  builds and installs the `ranex` console script into the checkout venv; a
  wheel installed into an arbitrary venv prints help but refuses governed
  subcommands, because the CLI anchors to the checkout containing it
  (ADR-009);
- this repository contains no installed agent harness, owner-facing intake,
  task board, deployment command, or built-in model provider;
- ordinary `gate evaluate --approver` uses an unauthenticated string; signed
  approver verification exists only in the task-merge approval path;
- `task delegate` records `suite_exit` but returns orchestration success after a
  completed delegation even when that suite exit is nonzero; it does not issue
  a gate verdict;
- free-prompt `task fanout` has no A/B/C or approved child-scope admission;
- dispatch, judge, and merge derive their journal and evidence locations from
  kernel-owned anchors (ADR-041), so the composed dispatch → judge → merge flow
  needs no manual evidence transfer;
- a successful `task merge` into a checked-out branch synchronizes that worktree
  to the candidate (disjoint operator changes preserved) or refuses before the
  ref moves; a sync failure after the ref moves journals an explicit
  non-`PUBLISHED` ABORTED outcome with a repair command (ADR-042), and files
  hidden by skip-worktree/assume-unchanged bits remain undetected by the dirty
  scan;
- delegation/fanout logs are retained, redacted, and digest-bound, but
  redaction is grammar-based (env-grammar literals, forced `--redact-env`
  names, PEM blocks, credential URLs), so a secret outside those grammars can
  survive in a retained log, and nothing deletes logs automatically —
  retention and cleanup are operator-owned;
- batch qualification sets `publication_allowed` to false and both judge and
  merge refuse it before legacy publication writes; `task batch verify`
  rechecks such a qualification read-only but proves the recorded surface,
  not payload semantics, and authorizes nothing;
- `evidence.json` replaces the previous row for the same claim and producer;
  it is not append-only;
- the suite manifest freezes test IDs and allowed skip reasons, not test bodies;
- journal verification detects changed rows and broken links but cannot detect
  replacement by an internally consistent earlier database snapshot;
- the strict-local controller remains same-UID trusted infrastructure and host
  qualification depends on user namespaces and delegated cgroup controllers;
  the `ranex host strict-local` wrapper prepares and enters the delegated
  cgroup scope itself (2026-09-01 acceptance: real v1, v2, and v3 runs all
  passed inside it), closing the 2026-08-29 gap where direct ordinary v1 use
  did not complete successfully;
  and
- there is no installed end-to-end A/B/C-authorized mutation workflow.


## The real-e2e suite entrypoint

One command runs the whole suite — the real-e2e journeys included — with
subprocess coverage wired through every frame-wired child, tees the transcript
and the coverage report into the ignored artifact home, and exits nonzero on
the hard skip-ledger findings: an observed skip no declaration covers, a
`ranex-prereq:` declaration whose observed skip reason drifted from the
declaration, or a probe-backed declaration whose skip did not occur (ADR-032,
application scope recorded on issue #35; the frame lives in
`tests/e2e/_prereqs.py` and `tests/e2e/coverage/sitecustomize.py`):

```sh
set -o pipefail
uv run --frozen python -c "import sys; sys.path.insert(0, 'tests/e2e'); import _prereqs; _prereqs.probe_artifact_home_writable('.local/ranex-e2e')"
mkdir -p .local/ranex-e2e/coverage
rm -f .local/ranex-e2e/coverage/.coverage*
export COVERAGE_PROCESS_START="$PWD/pyproject.toml"
export COVERAGE_FILE="$PWD/.local/ranex-e2e/coverage/.coverage"
PYTHONPATH="src:tests/e2e/coverage" \
  uv run --frozen pytest -q tests/unit tests/integration tests/contract \
    tests/security tests/e2e \
    --junitxml=.local/ranex-e2e/results.xml 2>&1 \
  | tee .local/ranex-e2e/transcript.txt \
&& uv run --frozen python -m coverage combine --keep \
    .local/ranex-e2e/coverage | tee -a .local/ranex-e2e/transcript.txt \
&& uv run --frozen python -m coverage report --include="$PWD/src/ranex/*" \
    | tee .local/ranex-e2e/coverage-report.txt \
&& uv run --frozen python tests/e2e/_prereqs.py cross-check \
    governance/suite_manifest.json .local/ranex-e2e/results.xml \
&& rm -f .local/ranex-e2e/coverage/.coverage*
```

What each piece is and why it is shaped this way:

- **Coverage env vars.** `COVERAGE_PROCESS_START` names this repository's
  `pyproject.toml` (absolute), whose `[tool.coverage]` block freezes
  `source = ["src/ranex"]`, `parallel = true`, and the fail-under threshold.
  `COVERAGE_FILE` pins one absolute shared base under
  `.local/ranex-e2e/coverage/` — gitignored `.local/*` territory — so every
  process's `parallel=true` suffix file (`.coverage.<host>.<pid>.<rand>`)
  lands in that one directory instead of scattering across working trees.
  The hook directory rides **last** on `PYTHONPATH`
  (`src:tests/e2e/coverage`), appended and never replacing: a replaced
  PYTHONPATH is how a subprocess hook silently dies, and LAST is the
  direction that keeps the hook directory from shadowing a real package a
  child imports. What LAST cannot prevent: Python imports the FIRST
  `sitecustomize` on the path, so an earlier PYTHONPATH entry carrying its
  own `sitecustomize` shadows the hook — the residual silence the frame's
  loud wired-child no-data detection exists to catch. The relative
  `source` is deliberate — a clone-judges-clone child resolves it against
  its own working directory and measures its own vendored copy of the
  kernel.
- **Coverage report scope.** The aggregate report includes only the canonical
  checkout's absolute `src/ranex/*` paths. Disposable clones remain measured
  in their own data and focused contracts, but repeated copies cannot inflate
  the aggregate denominator and dilute the release threshold.
- **The pre-run artifact-home probe** (`_prereqs.probe_artifact_home_writable`)
  is the first command of the entrypoint: an artifact home that cannot be
  written fails loudly — a `RuntimeError` naming the home — before the
  suite runs at all, so no junitxml, no transcript, and no coverage report
  is ever half-written into a home that could not hold them. A writable
  home proceeds quietly and is left untouched by the probe.
- **The pre- and post-run sweeps** (`rm -f .coverage*`) are load-bearing
  hygiene, not tidiness: stale suffix files from an interrupted run must
  never enter a later combine, and the retained `--keep` inputs never
  outlive the artifact. Hard-killed (SIGKILL) children remain a documented,
  threshold-accounted coverage blind spot.
- **The combine is `--keep` and idempotent**: repeated `coverage combine
  --keep` over the retained immutable inputs reproduces identical combined
  data (installed coverage deletes inputs without `--keep`, so inputs are
  retained deliberately).
- **The cross-check** (`tests/e2e/_prereqs.py cross-check <manifest>
  <junitxml>`) is the declared-skip ledger in two tiers. Direction (a) is
  hard unconditionally for undeclared skips: an observed skip no
  declaration covers exits nonzero naming the test ID and its reason. Its
  reason comparison is a hard-tier obligation only (the orchestrator's
  R1d ruling on issue #35): a skip declared `ranex-prereq:` whose
  observed reason drifted from the declaration is a
  `skip reason mismatch:` finding naming both strings — the comparison is
  exact, so the declaration and its live skip message must be the same
  bytes, and a prereq-tier declaration whose test's message cannot carry
  the marker is misclassified (reclassify it context-tier through the
  freeze ceremony, never silence the finding). A skip declared
  `ranex-context:` is never byte-compared — its drift is reported in the
  informational list below. Direction (b) is the probe-backed lie
  detector: a declared skip that did not occur fails hard only when its
  declared reason uses the frame grammar (`ranex-prereq:<probe>:`) — the
  finding names the live verdict of that frame probe on the running host,
  and a present verdict means the declaration is stale: prune it at the
  next `suite freeze`. `suite freeze` itself stays outcome-blind; honesty
  is checked here, at entrypoint time.
- **Declaration grammars.** Every `expected_skips` reason in the manifest
  carries exactly one of two grammars (the orchestrator's ruling on
  issue #35): `ranex-prereq:<probe>: <prose>` — the HARD tier, asserting a
  context-independent condition one of the six frozen probes verifies
  live, both directions — or `ranex-context:<context>: <prose>` — the
  INFORMATIONAL tier, naming the context the declaration belongs to
  (hermetic-freeze, host-capability, operator-action). Unmarked prose is
  refused by the frozen lint; rewording happens through the freeze
  ceremony only.
- **Context-mismatch semantics.** A declared skip that did not occur whose
  reason is *not* probe-backed is a context-bound declaration — the
  manifest is deliberately multi-context (it also describes the sealed
  hermetic freeze environment: no operator `uv` on `PATH`, no sibling
  harness fork in the materialised sample, `unshare(CLONE_NEWUSER)`
  denied, cold-start zero-state re-entry refusal), and those conditions
  are not reproducible in the entrypoint's documented environment. The
  cross-check reports them as an informational `context-mismatch` list —
  names plus a count, `exit 0`. The same list carries the context tier's
  **observed-drift** entries (the R1d ruling's machine-greppable
  promise): a declared `ranex-context:` skip that *was* observed skipping
  with a differing live message is reported as ID + declared context +
  observed message — reported, never byte-compared, because those live
  messages come from other slices' frozen test files and many are
  dynamically composed host-state prose. Forbidding either shape would
  make the entrypoint unsatisfiable on any single host; the probe-backed
  tier above is what catches checkable staleness instead.
- **The canonical entrypoint environment.** The documented command assumes
  the qualified operator host and nothing else: the pinned `uv` toolchain
  on `PATH`, the sibling harness fork present at its default path
  (`../ranex-harness` relative to this repository, or named explicitly via
  `RANEX_HARNESS_DIR` — exporting the variable also makes the frame's
  `harness_fork` probe agree explicitly with the fork tests' default-path
  fallback), delegated cgroup-v2 controllers and unprivileged user
  namespaces for the confinement surfaces, and `RANEX_SIGNING_KEY`
  deliberately **not** exported — the `stage_12` operator gate skips on
  exactly that, and its expected skip is declared in the manifest with the
  probe grammar so exporting the key turns the declaration into a
  probe-backed prune at the next freeze. Delegation needs no provider-specific
  environment variable; authentication, when needed, belongs to the selected
  outer host or adapter-side broker. The command block itself is the only environment wiring the
  entrypoint performs: `COVERAGE_PROCESS_START`, `COVERAGE_FILE`, and the
  hook-last `PYTHONPATH` documented above.
- **Duration budget.** Recent complete qualified-host runs took 33–36 minutes;
  hosted CI has different capabilities and skips. Allow 60 minutes for the
  full entrypoint, inspect its named prerequisites and retain actual results.
  A skip is not a passing observation.

The transcript and the coverage report under `.local/ranex-e2e/` are the
milestone's proof artifacts: a real invocation transcript and a real
per-file, per-line coverage report a human can read at a pinned commit.
The entrypoint never logs key material; the transcript carries suite output
and line numbers only.
