# ADR-043 — retained, redacted execution logs

**Status:** accepted
**Date:** 2026-08-31
**Decision-makers:** repo owner
**Issue:** #58 (retain redacted delegation and fanout execution logs; production consequence recorded in the #55 audit)

## Context and Problem Statement

Real `task delegate` and `task fanout` executions passed, but their scratch
directories and harness stdout were deleted, and durable outcomes retained
only summary fields (#55 audit, issuecomment-5460862632). A passing or
failing delegated task cannot be independently understood from durable
artifacts — no transcript survives to diagnose or audit it.

The problem: what must `task delegate` and `task fanout` persist beside each
outcome, at what size and redaction discipline, so a human can inspect a real
run's transcript afterward without the outcome ever leaking a secret or
hiding the reason a run failed.

## Decision Drivers

- A durable outcome must let a human inspect what actually happened, not
  only whether it passed.
- Credentials and other sensitive values must never reach disk in the clear.
- Truncation must never erase the terminal failure reason.
- Retention/cleanup must be operator-configurable, never silently automatic.
- Stay inside the existing outcome-file architecture; no new store.

## Prior art

Searched: GitHub code search for subprocess-timeout partial-output handling
in Python, and for log-secret-scrubbing prior art (structured-log redaction
vs. free-form process-output redaction), before designing a bespoke
retention/redaction path.

- https://github.com/python/cpython/blob/v3.14.0/Lib/subprocess.py —
  grounds: `Popen.communicate`'s timeout handling returns already-read
  partial output.
  License: PSF-2.0 (BSD-style Python Software Foundation License Version 2).
  Weakness: partial output from `communicate` on timeout is raw bytes even
  when the `Popen` was constructed with `text=True`, and only `run()`'s
  docstring calls this out — a caller reading `TimeoutExpired.stdout`
  naively as text can crash on decode.
  Vendored: docs/adr/prior-art/ADR-043/cpython-3.14.0-subprocess.py blob:54c2eb515b60dafec986af59fc74fda796b1ee47

- https://github.com/python/cpython/blob/v3.14.0/Lib/hashlib.py —
  grounds: the stdlib's own `sha256` construction, used to digest each
  retained stream so an outcome can bind to it.
  License: PSF-2.0 (BSD-style Python Software Foundation License Version 2).
  Weakness: unopinionated about which bytes to hash; the choice to hash the
  retained bytes exactly as written to disk (post-redaction, post-truncation)
  is ours and is pinned by tests, not by this module.
  Vendored: docs/adr/prior-art/ADR-043/cpython-3.14.0-hashlib.py blob:0e9bd98aa1fc31b5dccef0d34780b86ae05f6ab3

- Rejected: https://github.com/mozilla/bleach — a mature HTML allowlist
  sanitizer, since retired upstream. Wrong domain: it parses markup tags and
  attributes, not free-form, unstructured child-process stdout/stderr, so
  its allowlist model has nothing to allow or deny here.
- Rejected: https://github.com/pinojs/pino — a structured JSON logger whose
  redaction targets known object key paths. It cannot scrub a keyless
  free-form byte stream where a secret may appear anywhere in the text, which
  is exactly the shape of harness stdout/stderr this ADR must redact.

## Considered Options

1. Keep summary-only outcomes (status quo) — the #55 failure itself.
2. Extend `ranex.observability.redaction.screen_event`'s allowlist schema to
   cover log text. Wrong domain: that screens eleven frozen structured
   fields (ADR-031); free-form text has no field set to allowlist.
3. New sibling module, denylist-by-value, retained beside each outcome file
   with fixed stream names and an additive `logs` outcome block. Chosen.
4. Journal-embedded log bytes (extend the hash-chained Journal itself).
   Rejected: unbounded per-entry size in an append-only chain sized for small
   structured rows; deferred, see Reversibility.

## Decision Outcome

Chosen option 3. Logs live beside each outcome: delegate `PATH.json` gets a sibling
`PATH.json.logs/` (or `--log-dir` override); fanout gets `<task_id>.json.logs/` plus
parent `fanout.logs/`. Fixed files are `harness.stdout.log`, `harness.stderr.log`,
`suite.stdout.log`, `suite.stderr.log`, and `manifest.json`.
Redaction runs before truncation in fixed order: ambient sensitive-name env values →
forced `--redact-env` values → PEM blocks → credential-URL passwords, replacing each
with `[REDACTED:...]` markers.
Each stream uses `--log-max-bytes` (default 262144; bounds [4096, 8388608]), preserves
the tail, and prepends a deterministic marker.
Fanout accepts `--log-max-bytes`, `--log-retention`, and repeatable `--redact-env NAME`,
with delegate-identical refusals, and forwards all three to every child delegate.
The outcome gains an additive `logs` block per stream—file, bytes, sha256, original
size, truncated, and redaction kind→count—via `canonical_json_bytes` + `write_atomic`.
`--log-retention keep|replace|off` (default `replace`) governs collision/disablement; see Sad paths.

### Consequences

- Every delegated/fanout run now writes up to five extra files per task;
  disk use grows in proportion to log volume, bounded by `--log-max-bytes`.
- Redaction only catches value-shaped or structurally-shaped secrets; a
  secret that is neither long, named, PEM-shaped, nor a credential URL is
  not redacted — an accepted residual, not a promise of completeness.
- Outcome consumers that `json.loads` the file are unaffected: `logs` is an
  additive key.
- No age-based cleanup exists; unbounded retention across many runs is an
  operator disk-management responsibility, not a kernel behavior.
- `cmd_task_delegate` now refuses (ERROR, exit 3) on log-persistence OSError,
  so a run whose transcript could not be retained is never reported success.

### Confirmation

Evidence intent: the implementation tranche adds unit coverage for the
redaction passes and their fixed order, unit coverage for truncation
(bounds, tail-preservation, UTF-8 boundary alignment, non-UTF-8
`errors="replace"` decoding, `TimeoutExpired` partial-output-as-bytes),
integration coverage for delegate/fanout log-dir layout and the `--log-dir`
override, an end-to-end real-process run proving a real transcript is
retrievable, and a security-focused test that injects a real secret value
and asserts it never appears in any retained file or in the manifest, only
the redaction kind and count. All new tests are added under `tests/unit`,
`tests/integration`, `tests/e2e`, and `tests/security` by the implementation
tranche (T1), frozen red before code lands, proven green after.

## Improvements on the prior art

- subprocess.py documents `communicate`'s timeout behavior only in `run()`'s
  docstring; this decision makes the byte-vs-text ambiguity explicit at the
  retention boundary — a timed-out stream is always retained and digested as
  the bytes CPython actually produced, never assumed to be decodable text.
- hashlib.py provides the primitive but no policy; this decision fixes what
  gets hashed (bytes exactly as retained on disk, after redaction and
  truncation) so the digest is a promise about what a reader will see, not
  about upstream child output that was never persisted.
- Neither cited implementation redacts anything; this decision adds a
  denylist pass ordered so structural and forced redactions cannot be
  undone by a later truncation cutting mid-marker, because redaction always
  runs first.
- Where `screen_event` (ADR-031) allowlists eleven known structured fields,
  this decision explicitly does not extend that model to free-form text —
  a denylist-by-value is the only workable shape when the field set is
  unbounded and unknown in advance.
- Truncation is deterministic and self-describing (a marker recording
  dropped/retained/original counts), unlike a silent `communicate(timeout=)`
  callsite that would just lose the head with no trace.

## Architecture surface

- New: `src/ranex/execution/__init__.py`, `log_redaction.py` (redaction
  passes), `retained_logs.py` (layout, truncation, manifest, outcome `logs`
  block construction).
- Changed: `src/ranex/cli/delegation.py` (log-dir plumbing, refusal on
  OSError), `src/ranex/cli/fanout.py` (`--log-max-bytes`/`--log-retention`/
  `--redact-env` forwarding + parent transcript), `src/ranex/cli/main.py`
  (new flags: `--log-dir`, `--log-max-bytes`, `--log-retention`,
  `--redact-env`).
- No change to `ranex.observability.redaction` (ADR-031's frozen allowlist
  stays untouched) and no change to the hash-chained Journal.

## Scope and threat delta

- In scope: `task delegate` and `task fanout` harness/suite stdout/stderr.
- Out of scope: `task batch qualify` child logs (non-publishable path,
  unchanged); the Journal's own record shape.
- Threat delta: retained logs are a new on-disk artifact that could leak a
  secret if redaction misses it; mitigated by the denylist passes and the
  security test, not eliminated.
- No new network call, credential, or privilege; redaction runs locally
  against bytes the process already produced.

## Quality attributes

| Attribute | Effect |
|---|---|
| Auditability | a real transcript is retrievable per task, not only a verdict |
| Safety | denylist redaction before truncation; secrets never digested or counted by value |
| Honesty | truncation marker states exact dropped/retained/original counts |
| Availability | OSError during persistence refuses the run rather than reporting false success |
| Cost | up to 5 extra files and up to `--log-max-bytes` bytes per stream per task |

## Reversibility

Door: two-way

Removing `--log-dir`/`logs` support restores the pre-#58 summary-only
outcome; the `logs` key is additive, so older readers ignore it and newer
readers tolerate its absence. The rejected option 4 (journal-embedded logs)
remains a two-way upgrade path if structural outcome-digest linking proves
insufficient; no bytes here would need to move, only be re-cited.

## Sad paths

- `--redact-env NAME` whose value is under 16 bytes — refused with `refusing --redact-env NAME: value shorter than the 16-byte redaction floor` (NAME interpolated).
- Ambient sensitive-named env var under the 16-byte floor — silently not
  collected; redacting short values would shred ordinary text.
- `--log-max-bytes` outside [4096, 8388608] — refused: `--log-max-bytes must
  be between 4096 and 8388608 bytes`.
- Stream exceeds the max — head dropped, deterministic
  `[ranex truncated: policy=tail dropped=N retained=N original=N]` marker
  prepended, cut aligned down to a UTF-8 character boundary.
- Child emits non-UTF-8 bytes — decoded with `errors="replace"`, retained
  and digested as the replacement bytes actually on disk.
- Delegated run times out — `TimeoutExpired` partial output is raw bytes
  even in text mode; retained as bytes, never crashed on decode.
- `--log-retention keep` meets an existing log directory — refused with `refusing to overwrite existing log directory DIR: --log-retention is keep` (DIR interpolated); the existing directory is untouched.
- `--log-retention off` — nothing retained; the outcome carries
  `{version: 1, retained: false, reason: "operator-disabled"}`.
- OSError while persisting logs — `cmd_task_delegate` refuses with ERROR and
  exit 3; no success is reported for an unretained transcript.
- A secret value coincidentally appears in a stream — replaced by
  `[REDACTED:env:VARNAME]` (or `pem`/`credential`); the manifest counts the
  kind, never records secret bytes or a secret digest.
- Empty stream — recorded as `bytes: 0` with the sha256 of empty input.
- Fanout child log directory collides under `keep` — the child's delegate
  refusal surfaces through the parent fanout run unchanged.

## Test strategy

`tests/contract/test_docs_discipline.py` governs this ADR itself (budgets,
citations, vendored digests, NOTICE, section order). Product tests to be
added under `tests/unit`, `tests/integration`, `tests/e2e`, and
`tests/security` by the implementation tranche (T1), frozen red before
implementation and proven green after, covering: redaction pass order and
each kind; truncation bounds, tail preservation, and UTF-8 boundary
alignment; delegate/fanout log-dir layout including the `--log-dir`
override; a real end-to-end delegated run with a retrievable transcript; and
a security run that injects a real secret and asserts it never appears
outside its `[REDACTED:*]` marker anywhere in the retained files.
`governance/suite_manifest.json` will freeze the new test IDs once T1 lands.

## Code review checklist

- [ ] Redaction always runs before truncation, never after, for every stream.
- [ ] No code path writes a secret's raw bytes or a digest of a secret's raw
      bytes into a manifest or outcome file.
- [ ] The `--log-max-bytes` bounds and the 16-byte redaction floor are
      enforced before any bytes are written, not only documented.
- [ ] Truncation's UTF-8 boundary alignment cannot itself split a
      `[REDACTED:*]` marker in half.
- [ ] `cmd_task_delegate` refuses (exit 3) on every OSError from log
      persistence, not only on the common ones exercised by tests.
- [ ] Fanout forwards every new delegate flag it already forwards siblings
      of (gate/claim/gate-catalog/suite-manifest), not a partial subset.

## More Information

- Issue #58 is the production blocker this decision closes; the #55 audit
  is where it was first recorded (issuecomment-5460862632).
- `docs/adr/ADR-031-kernel-observability.md` — the frozen structured-event
  allowlist this decision deliberately does not extend.
- Vendored prior art and licensing: `docs/adr/prior-art/ADR-043/NOTICE.md`.
- Both vendored files were fetched over the network via `curl -fsSL` against
  `raw.githubusercontent.com` at tag `v3.14.0`, against an installed
  Python 3.14.6 interpreter; no local-stdlib fallback was needed.
