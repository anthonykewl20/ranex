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

### A scan claim (SARIF 2.1.0)

A deterministic scanner — ruff, semgrep, govulncheck, bandit — satisfies a claim
by emitting SARIF 2.1.0. The claim sets `results_reporter: sarif-2.1.0`, binds
the exact tokens `--output-format=sarif` and `--output-file=PATH` where `PATH`
equals `results_artifact` (no overrides, no `--`), and names its **own** frozen
manifest with `results_manifest`. JUnit claims keep using the repository's one
suite manifest; a scan freezes a different universe and must not share that file.

Freeze that universe from a real run, on a clean tree:

```sh
uv run --frozen ranex suite freeze --external-repository /path/to/repo \
  --artifact governance/scan.sarif --output governance/scan-manifest.json \
  --results-reporter sarif-2.1.0 \
  --scan-scope src/app.py --scan-rule F401 --blocking-level error \
  -- /usr/bin/ruff check --output-format=sarif \
     --output-file=governance/scan.sarif src
```

`--scan-scope` is required and repeatable: those paths are the IDs that pass and
fail, exactly as test IDs are for a suite. `--scan-rule` is the reviewed rule
universe — a finding outside it still blocks, but nothing outside it may be
accepted. `--blocking-level` defaults to `error`. `--accepted FINDING_ID=REASON`
declares a known finding, and the freeze refuses an ID the run did not actually
observe. Commit the manifest: it decides the verdict, so review is the control
on it, and `run`, `gate evaluate` and the App receiver all read the committed
bytes.

Two limits to know before binding one:

- **The scanner's exit code decides first.** A claim is unsatisfied unless the
  bound command exited 0, so under a scanner that exits nonzero on any finding
  (ruff's default) an `accepted` declaration can never be reached. A claim that
  wants acceptance to mean anything binds a scanner that reports through its
  artifact and exits 0 — for ruff, `--exit-zero`. What blocks is then the frozen
  manifest, which is the point.
- **Coverage is only as witnessed as the producer makes it.** `missing` is
  computed from `runs[].artifacts[]` when a producer emits it; ruff 0.16.2 emits
  neither `artifacts[]` nor `invocations[]`, so a scope path is proved to exist
  in the subject and nothing more. A scanner that exits 0 having scanned nothing
  is caught by its exit code alone. Prefer a producer that witnesses coverage.

Every reported region is checked against the materialised subject while the run
is still standing: a region past the end of a file, or a snippet the file does
not carry there, makes the artifact malformed — refused, and absence blocks.
Nothing is relocated. A SARIF `invocations[]` entry that reports
`executionSuccessful: false` is refused even with zero findings.

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

1. Terminate TLS in front of the listener (reverse proxy, or a smee.io
   tunnel in development). The webhook URL must be `https://`.
2. Create the App from the frozen manifest. Permissions: **Checks: Read & write**,
   **Contents: Read-only**, **Pull requests: Read-only**. Subscribe to events:
   **Pull request**. The PEM and webhook secret are exclusive-created 0600
   outside the repository and never printed:

   ```console
   uv run --frozen ranex github register \
     --credentials-dir /var/lib/ranex/github-app \
     --webhook-url https://receiver.example/webhook
   ```

   Open the printed localhost URL, submit the form, and GitHub redirects
   back with a one-hour `code`. Rerun with `--code` if the catcher is not
   used. Then export `RANEX_GITHUB_APP_ID`, `RANEX_GITHUB_APP_PRIVATE_KEY`
   (the `app.pem` path) and `RANEX_GITHUB_WEBHOOK_SECRET` from that
   directory. A GitHub Enterprise host can be named with
   `RANEX_GITHUB_API_ROOT` / `RANEX_GITHUB_WEB_ROOT`.
3. Install the App on the repository. Note the installation ID (visible in
   the installation's URL). `ranex github status` authenticates as the App
   and lists installations.
4. Pin the check so only this App's `ranex/acceptance` satisfies the
   default-branch ruleset (`RANEX_GITHUB_OPERATOR_TOKEN` or `GITHUB_TOKEN`):

   ```console
   uv run --frozen ranex github ruleset --repo owner/name --branch main
   uv run --frozen ranex github status --repo owner/name
   ```
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
   A proven delivery is spooled to disk before any work starts. The answer
   waits at most eight seconds for the pipeline (GitHub abandons a delivery
   after ten): a delivery that finishes in time answers its real status
   (200 done, 400 malformed id, 409 conflicting replay, 5xx retry); one that
   does not answers 202 and completes from the spool, which the listener
   drains at startup and every five minutes until each entry completes.
   An entry (or a waiting head, below) whose attempt failed is not retried
   until five minutes have passed, restart or not: a `.failed` marker beside
   it carries the last attempt time, so stuck entries cannot hold the
   pipeline against live deliveries; never-attempted entries drain at once.
   Live deliveries outrank those passes: a delivery arriving while a pass
   holds the pipeline waits for it (within the acknowledgement deadline)
   instead of answering 503, and the pass steps aside after the entry in
   flight and resumes once the delivery is through. Two live deliveries
   still never wait for each other: the second answers 503 as before.
   The diagnostic journal is `deliveries.jsonl`; atomic completion receipts
   live in `completed/`, publication attempts in `attempted/` and pending
   deliveries in `spool/`, all under the state dir (`.local/ranex/github` by
   default). Preserve them on upgrades. GitHub does not automatically retry a
   delivery answered 5xx. The listener retains these failures in its spool
   and retries them too; manual GitHub/API redelivery remains available.
   Publication is at-least-once by construction, never exactly-once: a crash
   between the API call and the local receipt is reconciled on retry, which
   asks GitHub for this App's `ranex/acceptance` run stamped with the
   delivery id and republishes nothing if it exists. Two checks remain
   possible only if that reconciliation itself cannot reach GitHub.
   The App private key must be a regular file readable by its owner alone
   (mode 0600 or tighter); a key group- or world-readable is refused as
   `E-GITHUB-KEY-EXPOSED` before it is parsed. Mode bits are what the loader
   can see; parent-directory and ACL exposure remain the operator's audit.
   A head answered `action_required` (no verdict yet) is remembered in
   `awaiting/`; the same periodic pass re-reads the verdict store and, once
   a verdict for that head exists, publishes it (stamped `refresh:<head>`,
   reconciled if the pass is interrupted) and forgets the head. A fresh
   event for the head does the same immediately. A verdict that never
   lands leaves the head waiting; `ranex github check publish` remains the
   one-shot operator path.
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

### Automatic evidence evaluation

Add `--evaluate-evidence` to `github listen` and set
`RANEX_VERDICT_SIGNING_KEY` to the absolute path of the external private key
matching the committed verdict signer. `--evidence` defaults to
`governance/evidence.json`; `--suite-manifest` defaults to
`governance/suite_manifest.json`. The observer must deliver signed evidence
through the existing evidence format and atomic publication path.

The receiver pins the gate catalog, producer keyring and test manifest from the
operator checkout at startup. PRs that change them refuse evaluation; review
policy changes independently before restarting against an approved checkout.
The receiver checks late evidence every 15 seconds, retaining the existing
300-second failure backoff. Missing evidence produces an action-required check;
failing evidence stays blocked and can recover when fresh evidence arrives.
Unchanged inputs reuse the judgment, and completed refreshes avoid repeated API
queries. Failed or interrupted publication reconciles using the verdict's ID.

Reserve `ranex/acceptance` for the App. A live adversarial probe with a
foreign Actions job using that name remained merge-blocked despite an App
success; collision availability is UNVERIFIED. Keep the required check bound
to the App integration; do not remove protection to work around a collision.

This automates judgment and publication. It does not schedule test execution.
Use a separately controlled observer; do not put arbitrary PR execution beside
the receiver or its credentials. See [ADR-058](adr/ADR-058-automatic-evidence-evaluation.md).

### Limits, stated plainly

By default the App publishes existing verdicts. With `--evaluate-evidence` it
also invokes the trusted kernel to judge signed evidence, without executing
contributor code. The receiver host and App credentials
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
github register
github status
github ruleset
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

GitHub audit follow-up: [2026-09-08 App review](../tools/dogfood/FINDINGS.md#github-app-audit--2026-09-08).
Ruleset setup reuses only an active, strict rule for the exact requested branch
without bypass actors. Other same-App rules are preserved and a matching rule
is created. Status ignores disabled and non-branch rules; a reported pin is
not evidence that every branch or actor is protected.
# Frozen executable probe bundles

To reproduce the bounded live journal experiment, run:

```sh
uv run --frozen python tools/dogfood/probe_bundle_proof.py \
  --output /tmp/ranex-probe-experiment
```

Use a new output path. This clones committed Ranex, freezes the public-CLI
journal journey, commits a known-bad product mutation, and runs three baseline
and three mutant observations. Each journey creates a real SQLite journal
through `gate evaluate`, verifies it, alters a recorded digest, and requires
`journal verify` to reject the altered record. `receipt.json` retains each
observation; `commands.json` retains raw commands, exit codes and output. The
experiment deliberately does not issue verdict evidence or claim process
confinement. A baseline mismatch, missing setup or wrong mutant failure blocks
its experiment-success record. No existing checkout is mutated by the control.

The artifact-freeze commands implement the first stage of ADR-061. They do not
run the product, classify a probe as genuinely black-box, sign an approval, or
issue verdict evidence. The operator owns the source A packet and the complete
support-input selection. Include fixtures, parent conftest/config files, launch
recipes and runtime/dependency declarations as additional `--root` arguments.
Only selected committed inputs are frozen; implicit external inputs are not
discovered. A separate qualified observer is still required for live acceptance.

Start with a canonical A `spec-packet-v1` file and a canonical JSON argv file,
for example the exact bytes `["python","acceptance/probe.py"]` (no trailing
newline). Commit the actual executable probes and their support inputs first.
Then, using an external destination whose parent already exists:

```sh
uv run --frozen ranex specification freeze-probes \
  --external-repository /path/to/product \
  --spec-packet /operator/A.json --invocation /operator/argv.json \
  --root acceptance --root pyproject.toml --root uv.lock \
  --output /operator/frozen-order-probes
```

The bundle holds `spec-packet.json`, `manifest.json` (existing B contract),
`probe-contract.json` and `probes/` containing the original relative files.
The descriptor pins the base commit, exact root membership, executable modes
and argv. B binds A and every copied artifact. Existing C approval binds the
reported `a_digest` and `manifest_digest`; freezing itself is not approval.
The output must be new and outside the candidate repository and linked
worktrees. A directory outside the checkout is not isolation against its owner.

Retain the manifest digest in independently controlled policy/approval state.
After committing product changes, check against that retained identity:

```sh
uv run --frozen ranex specification check-probes \
  --external-repository /path/to/product \
  --bundle /operator/frozen-order-probes \
  --manifest-digest "$APPROVED_B_DIGEST"
```

Exit 0 reports `PROBES-UNCHANGED`; exit 2 refuses. Changed probe bodies, helper
additions, deletions, executable-mode changes, bundle substitutions, invocation
changes and known projection placeholders refuse. Product changes outside the
selected roots are permitted. Do not obtain the expected digest from a mutable
candidate-supplied manifest and treat that circular check as independent approval.
