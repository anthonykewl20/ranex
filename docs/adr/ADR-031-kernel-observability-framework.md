# ADR-031 — kernel observability framework

**Status:** accepted
**Date:** 2026-08-17
**Decision-makers:** repo owner
**Slice:** n/a — SLICE-054 opens after the tracker-#33 Phase-1 disposable prototype; no slice is open now

## Context and Problem Statement

Milestone 4 (tracker #33; MAP §0.24/§0.30 record the owner's build order — milestone 4 first, because P0's exit evidence strictly requires this observability substrate before milestones 3 and 2) has no first-class way to watch the kernel work: observing what a governed run actually did means reading source or re-deriving it from the journal after the fact. Issue #34 (https://github.com/anthonykewl20/ranex/issues/34) freezes the input contract this ADR records: a toggleable, default-off trace at CLI boundaries, chained across subprocesses, and proven verdict-neutral. The program's universal alignment rule binds every new or modified kernel path to exactly this pair — default-off runtime-toggleable trace emission, proven verdict-neutral, plus a real-data e2e assertion — so the framework must exist before the rest of the milestone lands.

The kernel never logs: `evaluate()` and the journal append path stay pure and silent; emission happens only at `src/ranex/cli/` boundaries — `main.py` and the `host_confinement` session child — around them. Observability is a pure observer, never a behavior change hiding inside logging work.

## Decision Drivers

- Default off; one import-time env read; off-state cost measured, not assumed.
- Verdict-neutral by proof: verdict, evidence bytes, and `journal verify` identical off vs on.
- No dependency growth: the runtime graph is three packages (SLICE-002, SLICE-006, catalog format), and an observer adds none.
- Governed and observed commands never receive trace env; the boundary strips ambient copies and refuses pre-spawn.
- Frozen event schema; any addition or removal turns a contract test red.
- Refuse loudly and fail closed; never crash the governed run for a trace problem.
- A trace target may never be, alias, or sit under a governed output; admission is refused before the first write.
- Refusal diagnostics never echo malformed or unknown values — those may carry the attack; a well-formed absolute target is named, because issue #34's sad path 2 mandates naming the path.

## Prior art

- Searched: `gh api repos/git/git/contents/trace2?ref=v2.45.2` (tag-pinned directory listing) to locate the target grammar — `trace2/tr2_tgt.c` does not exist at v2.45.2; the grammar lives in `tr2_dst.c` and the JSON event target in `tr2_tgt_event.c`.
- Searched: `gh api search/code` for `_nop` in hynek/structlog plus a full 24.4.0 source-tarball grep; `_nop` lives in `src/structlog/_native.py`, not `_config.py`.
- Searched: `gh search repos "opentelemetry python"` and direct pinned-ref inspection for the rejected candidates below.
- [git trace2 destination grammar, v2.45.2](https://github.com/git/git/blob/v2.45.2/trace2/tr2_dst.c): `tr2_dst_get_trace_fd` parses the target value — unset/empty/`0`/`false` off; `1`/`true` stderr; a single digit an already-open fd; an absolute path appended; a directory one file per process named by the last SID component.
  License: GPL-2.0 — pattern only, no code enters src/; research evidence (ADR-012 git-file precedent).
  Weakness: unwritable-target warnings are gated behind a debug env (quiet disable by default), `af_unix:` socket targets are accepted, and the directory cap is a file count with a sentinel, not a byte cap.
  Vendored: docs/adr/prior-art/ADR-031/git-tr2_dst.c blob:5be892cd5cdefa654cfd538ea562c2656d23182e
- [git trace2 event target, v2.45.2](https://github.com/git/git/blob/v2.45.2/trace2/tr2_tgt_event.c): JSON-lines events carrying `event`, `sid`, `time`; the first event is `version` with `evt` (format number) and `exe` (git version) — the exact field names issue #34 freezes.
  License: GPL-2.0 — pattern only, no code enters src/; research evidence.
  Weakness: the `evt` policy tolerates additive field changes without an increment, and nothing freezes the field set against drift.
  Vendored: docs/adr/prior-art/ADR-031/git-tr2_tgt_event.c blob:59910a1a4f7c0f280fb6839873429d9cc877d3cf
- [git trace2 session id, v2.45.2](https://github.com/git/git/blob/v2.45.2/trace2/tr2_sid.c): SID component `<yyyymmdd>T<hhmmss>.<frac>Z-<host>-<process>`; `GIT_TRACE2_PARENT_SID` chains parent SID plus `/` plus own component and re-exports itself for children.
  License: GPL-2.0 — pattern only, no code enters src/; research evidence.
  Weakness: any non-empty parent string is blindly prefixed — no validation, so a malformed parent corrupts the chain silently.
  Vendored: docs/adr/prior-art/ADR-031/git-tr2_sid.c blob:09c4ef0d17378748ee67a870301f7b086bcf6163
- [pino redaction, v9.4.0](https://github.com/pinojs/pino/blob/v9.4.0/lib/redaction.js): declared-path redaction over `paths` plus `censor` (default `'[Redacted]'`), built on fast-redact.
  License: MIT.
  Weakness: it is a blocklist — anything not declared, including a secret under an undeclared key, passes through verbatim; `strict` is hard-wired false with a TODO.
  Vendored: docs/adr/prior-art/ADR-031/pino-redaction.js blob:c5d7d897e6232756a1d0b397da723a246eff02af
- [structlog native filtering, 24.4.0](https://github.com/hynek/structlog/blob/24.4.0/src/structlog/_native.py): `_nop` (and async `_anop`) is bound as the method for every level below `min_level`, so a disabled level's call is a single `return None`.
  License: MIT OR Apache-2.0.
  Weakness: the cheapness is per-method binding on a configured logger class, and adopting the library rather than the pattern would violate the dependency policy.
  Vendored: docs/adr/prior-art/ADR-031/structlog-native.py blob:a96e6da2f68a616dddcdab2d77c8b26277de84f8
- Rejected: https://github.com/open-telemetry/opentelemetry-python — the SDK alone declares `opentelemetry-api`, `opentelemetry-semantic-conventions`, and `typing-extensions`, and its context-propagation and exporter machinery is far beyond a confined, stdlib-only, verdict-neutral kernel.
- Rejected: https://github.com/systemd/python-systemd — `systemd.journal` sends structured messages to the journald daemon socket through a libsystemd wrapper (LGPL-2.1), a daemon confined workers cannot reach and a dependency the policy forbids.

## Considered Options

1. No trace facility; keep reading source and deriving behavior post hoc. Rejected: the milestone-4 alignment rule makes default-off trace plus a neutrality proof mandatory on every new kernel path, and without a toggle every real-e2e failure is re-derived by hand.
2. Adopt a logging library (structlog, OpenTelemetry, or similar). Rejected: the runtime graph is three packages — cryptography and packaging on their own records, PyYAML as the catalog-format dependency — and MAP's adoption form is copy-improve-own, never depend; an observer must not grow the graph.
3. Always-on verbose CLI output. Rejected: it changes operator-visible behavior, cannot cheaply be proven verdict-neutral, and prints exactly what an allowlist must drop.
4. A stdlib-only, env-gated, allowlisted JSON-lines emitter at CLI boundaries, SID-chained across subprocesses. Chosen.

## Decision Outcome

`RANEX_TRACE` and `RANEX_TRACE_EVENT` are independent targets for the same frozen-schema JSONL stream, mirroring trace2's independent per-target variables: the off-state is neither set; each set-and-valid variable enables its own target; when both are valid every event is written to both targets; an invalid value on one variable disables only that variable's target, one warning each; caps, refusals, and write-failure accounting are per-target. Both default off; env is read exactly once at import; targets are admitted lazily at first emission, before the first write; and the `version` event is the first write on each admitted target.

The adopted grammar is exactly issue #34's enumeration — unset or empty and `0`/`false` → off; `1`/`true` → stderr; a single digit 2–9 → that already-open fd; an absolute path → append; an absolute directory → one file per process named by the last SID component — a strict subset of git trace2's full grammar, verified in the vendored `tr2_dst.c`. Trace2 additionally accepts `af_unix:[type:]path` socket targets, which Ranex refuses outright — a socket is an exfiltration channel out of a confined tree — and this refusal narrows TRACE2's grammar, not the issue's contract, since issue #34's enumeration never included socket forms.

A relative path trace2 itself treats as malformed, and git's malformed-value handling always warns — the debug env gates only could-not-open and too-many-files — so Ranex's loud refusal of relative and unknown values matches git exactly and narrows nothing; where Ranex differs is git's quiet disable on unwritable targets, which Ranex refuses loudly instead. Tracing stays off and the governed run proceeds.

Target admission (file and directory targets, lazily at first emission, before the first write): a target is refused if it is, resolves to via symlink or hardlink, aliases by device and inode (fd targets, via their `/proc/self/fd` resolution), or sits under the governed repository root, the evidence path, the journal path, or any governed output — a target inside the governed tree dirties the subject, because the run's dirty-tree refusal ignores only evidence and journal today, and a target aliasing evidence or journal corrupts governed bytes outright; a target outside every governed root is the only admitted form. A target is opened once at admission — `O_NOFOLLOW`, fstat on the opened descriptor, device and inode checked against governed outputs at that moment — and only the held descriptor is ever written; the per-process directory file's inode is pinned at creation; the path is never re-resolved, so a later symlink swap or rename cannot redirect a write; an fd target whose `/proc/self/fd` entry cannot be read is refused — fail closed.

`RANEX_TRACE_PARENT_SID` chains SIDs in trace2's format `<yyyymmdd>T<hhmmss>.<frac>Z-<host>-<process>`; a malformed parent is never blindly prefixed (git's weakness) — a fresh root SID is minted and an event notes the malformed parent.

Output is JSON-lines over the frozen field set `event, sid, time, level, module, stage, subject_digest, duration_us, hierarchy, child_id, code`, field names taken from git's event target; all eleven fields appear on every event — inapplicable fields are `null`, never absent, because the set is the contract. The `version` event is a discriminated variant: it carries the eleven (with `event` = "version", other stage fields null) plus exactly two version-only members — `evt` (schema number, starting at 1) and `exe` (the ranex package version string) — and the allowlist admits `evt`/`exe` on the version event only; any other event carrying either is refused like any undeclared field. The schema contract test freezes both sets — the eleven and the version-only pair; any addition or removal turns it red.

Pinned semantics: `time` is wall clock (`time.time()`), UTC, millisecond-truncated; `duration_us` is the stage's elapsed microseconds, a monotonic-clock (`time.perf_counter_ns()`) delta; `hierarchy` is a dot-separated chain of registry identifiers, bounded by the max line length; `child_id` is a per-process monotonic integer starting at 1. Serialization is canonical — the fixed field order as frozen, one JSON object per line, LF-terminated, no extra whitespace — and the max line length and the byte cap are constants declared in `schema.py` and frozen by the schema contract test at slice time; this ADR requires they exist as frozen constants, their numeric values are slice work.

The off-state is one import-time env read; the emitter binds to a `_nop`-style no-op once (structlog's disabled-cost pattern), so a disabled emission is a single call returning None. Measured overhead is recorded at slice close as an acceptance criterion.

Redaction is a positive allowlist — pino's declared-path redaction inverted from blocklist to allowlist: an emission attempt carrying any field outside the frozen set is refused, the undeclared field is dropped, and a refusal event names the drop only when the field name matches the schema's bounded identifier grammar (`[a-z_][a-z0-9_]*`-form, capped by the max line length) — an undeclared name can itself carry secret material from a rogue emission site, so any other field name is represented by variable plus shape plus digest, never its bytes. Refusal diagnostics split by case: (a) a well-formed absolute file or directory target — or an fd target — failing admission (unwritable, aliasing, governed-root) is refused naming the full path, operator input the operator must recognize, which issue #34's sad path 2 mandates naming; (b) malformed or unknown values, and field values outside their closed forms, are represented by variable plus length plus short digest only, never bytes, because those may embed attacker or secret material. The shape descriptor is the value's length plus the first 8 hex characters of SHA-256 over the UTF-8 value; disclosed residual: a short digest is a weak offline-confirmation oracle for low-entropy refused values. Field values are closed: `level` from a frozen enum; `stage`, `module`, `code` from registries frozen in `schema.py` at slice time (the field set is frozen by this ADR now, the value vocabularies by the schema contract test at slice freeze); `subject_digest` is hex; `hierarchy` and `child_id` are bounded formats; any value outside its closed form is refused and represented by shape plus digest, never by its bytes. Under hostile input no key byte, credential URL, or evidence byte may appear in any line — attack-tested with planted key material, bearer tokens, and credential-URL env vars — and the split's one disclosed residual is that a secret formatted as a valid absolute path is named in a case-(a) refusal: the issue's own tradeoff, recorded, not hidden.

Verdict neutrality: the same governed command with tracing off vs on, across stderr, fd, file, and directory targets, yields byte-identical verdict, evidence.json bytes, and `journal verify` result — enforced by a future frozen contract test. `evaluate()` and the journal append path emit nothing, ever.

The propagation boundary: `RANEX_TRACE`, `RANEX_TRACE_EVENT`, and `RANEX_TRACE_PARENT_SID` are stripped from every environment handed to a governed or observed command — including ambient-copy environments such as host qualification, which today copies `os.environ` wholesale — and the strip is mandatory slice work recorded here as a requirement, because an observed command that sees a trace var can branch on it and break byte-invariance; materialised observed-command environments are constructed from a fixed dict and admit nothing ambient. `RANEX_TRACE_PARENT_SID` is passed to exactly one child surface today — the confinement-session controller, the Ranex-owned Python child that `src/ranex/cli/main.py` spawns as `python -m ranex.cli.host_confinement session …` and that can import the emitter — and only when tracing is enabled, extending the controller's fixed four-variable environment (`PATH, PYTHONPATH, LC_ALL, TZ`, frozen by the controller-environment assertion in `tests/security/test_slice047_confinement_hardening.py`) by exactly the trace variables, a deliberate amendment to that frozen test at slice time; with tracing off the environment is byte-identical to today's. The C launcher never receives a trace variable — its environment comes from the descriptor and stays exactly `LC_ALL, TZ`, frozen by the launcher protocol test — and it is C code that emits nothing, so the chain does not pass through it; the future bridge is out of scope (harness lane). The SID-chain acceptance test rides CLI → confinement-session controller, never an observed command. A worker descriptor carrying `RANEX_TRACE*` is refused pre-spawn; trace descriptors are opened non-inheritable (CLOEXEC) and children are spawned with close_fds semantics, so no trace fd crosses exec.

The emitter is stdlib-only — `json`, `os`, `sys`, `time`. The runtime graph is three packages — cryptography (SLICE-002) and packaging (SLICE-006) each justified on their own record, plus PyYAML, the catalog-format dependency — which an observer must not grow, per MAP's adoption-form directive.

Ownership: `src/ranex/observability/` with `__init__`, `emitter`, `schema`, `redaction`, `sid` modules, plus stage emissions at `src/ranex/cli/` boundaries — `main.py` and the `host_confinement` session child's own stage boundary — only; no emission inside `src/ranex/governed_execution/verdict.py` or the journal append path.

The byte cap applies to file and directory targets only — stderr and fd are operator-owned streams. The emitter reserves one max-line-length of capacity for the final refusal event: when the next event would exceed cap-minus-reserved, the refusal event consumes the reserve and the target stops; a cap smaller than one max line is a setup-time target refusal; past the cap the answer is refusal, not rotation — resolving the issue's open choice in line with the kernel's fail-closed posture, never silent disk fill. Writes are single-call best-effort: on write failure — including a full or blocking pipe on an fd target — the target is disabled with one warning and the governed run proceeds; the emitter never blocks or retries. Oversized or recursive payloads are refused the same way against the max line length frozen in `schema.py` — never truncated, never unbounded. Operator-facing warnings — one line each — go to stderr unconditionally, independent of any target; refusal events go to the enabled targets only.

### Consequences

- Good: every new kernel path can satisfy the milestone-4 alignment rule — default-off trace, neutrality proof, real-data e2e.
- Good: trace output is itself governed — frozen schema, allowlist, bounded size, bounded propagation, admitted targets only outside governed roots.
- Bad: schema evolution now requires a deliberate contract-test edit, which is the point.
- Bad: the on-path cost is paid at every stage emission; it is measured at slice close, not waved away.
- Bad: refusal-not-rotation means a capped stream stops rather than continuing into a second file; raising the cap is a deliberate operator act.
- Bad: a trace target must live outside every governed root, so an operator pointing a trace into the working tree is refused rather than tolerated.
- Bad: refusal diagnostics split by case — a well-formed absolute target failing admission is named in full, while malformed, unknown, and out-of-form values are reported as shape plus digest, never bytes, so diagnosing a malformed value means re-reading the environment by hand.
- Bad (disclosed residual): a secret formatted as a valid absolute path is named in the refusal — the issue's own tradeoff, recorded, not hidden.
- Bad (disclosed residual): the 8-hex shape digest is a weak offline-confirmation oracle for low-entropy refused values.
- The kernel stays silent; only the CLI boundary around it changes.

### Confirmation

Future SLICE-054 frozen tests, named here in prose only because they do not exist yet: a schema-freeze contract test that turns red on any field addition or removal — freezing both the eleven-field set and the version-event `evt`/`exe` pair — and freezes the max-line-length and byte-cap constants; an off/on byte-invariance contract test across stderr, fd, file, and dir targets covering verdict, evidence bytes, and journal verify, the governed-root target refusal, and the ambient-env strip; a secret-scrubbing attack suite with planted key material, bearer tokens, and credential-URL env vars, grep-verified against the captured stream; a SID-chain tree stitching one CLI → confinement-session-controller run into one tree (the acceptance test rides CLI → controller, never an observed command); and a default full-suite run with no trace env set producing zero trace output and unchanged results.

Existing suites already guard the boundaries this ADR freezes: the confinement-hardening test's controller-environment assertion freezes the confinement-session controller's environment at `PATH, PYTHONPATH, LC_ALL, TZ` — the four-variable base this ADR extends by trace variables only when tracing is enabled, as a deliberate amendment at slice time; the native-launcher test holds the descriptor-provided launcher env at `LC_ALL, TZ`, so the C launcher never sees a trace variable; the run-produces-evidence e2e is the real-run spine the future invariance test extends; and the docs-discipline contract governs this ADR's own shape.

Tracker-#33 Phase 1 runs a disposable prototype first — emitter plus one CLI stage, invariance spot-check, in `/tmp` or a scratch worktree, findings posted to #34 — per ADR-013's prototype discipline. ADR acceptance is not gated on prototype evidence (ADR-016 precedent); the production slice is.

## Improvements on the prior art

- Loudness where git is quiet: git's unwritable targets are disabled quietly, their could-not-open and too-many-files warnings gated behind a debug env; Ranex refuses loudly by default — naming a well-formed absolute target's full path, and for malformed or unknown values the variable plus shape descriptor, never the bytes — and never crashes the governed run.
- Allowlist where pino blocks: an undeclared field is dropped with a refusal event, so a secret under an undeclared key cannot pass through the way a blocklist lets it.
- SID validation where git blindly prefixes any non-empty parent string: a malformed parent mints a fresh root SID and the event records it.
- Refusal where git counts files: git caps a trace directory by file count with a discard sentinel; Ranex caps the trace file by a declared byte cap and refuses past it.
- Narrowing recorded rather than silent: git's `af_unix:` socket targets are refused outright, never adopted — the only narrowing of trace2's grammar, and none of the issue's contract; relative paths are refused exactly as trace2 refuses malformed values — git always warns on those, and so does Ranex.
- Admission where git writes anywhere: a target that is, aliases, or sits under a governed output is refused before the first write — git happily traces into the very tree it is judging.
- A frozen field set with red-on-drift, stricter than git's `evt` increment policy, which tolerates additive changes without an increment.
- `_nop` binding at import time, so the off-state cost is one env read — measured at slice close, not asserted.

## Architecture surface

Future surface, none of which exists yet and all of which SLICE-054 builds: `src/ranex/observability/__init__.py`, `emitter.py`, `schema.py`, `redaction.py`, `sid.py`, with stage emissions only at `src/ranex/cli/` boundaries — `main.py` and the `host_confinement` session child's own stage boundary. `src/ranex/governed_execution/verdict.py` and the journal append path are untouched and emit nothing.

## Scope and threat delta

Pure observer: no verdict semantics, gate-catalog meaning, or journal trust-rule changes, and no behavior change hidden inside logging work — an explicit non-goal of this decision. STRIDE: the information-disclosure surface adds a channel (trace output) that did not exist; the control is the positive allowlist plus the attack suite, the propagation boundary keeps the channel out of confined workers and their descriptors, target admission keeps it off governed outputs, and refusal diagnostics never echo malformed or unknown values — the disclosed path-naming residual aside — so the disclosure channel is closed at both ends.

## Quality attributes

Encoding is deterministic given (clock, SID) — `time`, `duration_us`, and `sid` are the only run-varying fields, everything else fixed by the frozen schema, canonical field order, and LF-terminated one-object-per-line serialization; the neutrality guarantee governs verdict, evidence, and journal bytes, never trace bytes. Off-state cost is bounded to one env read and measured at slice close; line length and the byte cap are frozen constants in `schema.py`; writes are single-call, append-only, best-effort, inheriting git's one-write-per-line atomicity assumption; default off everywhere, including the default suite run.

## Reversibility

Door: two-way

Env-gated and default-off; the module is removable without touching verdicts or the journal. Once shipped, the frozen field set and the `evt` schema number become the compatibility surface — changing either is a new decision, not a patch.

## Sad paths

- 1. `RANEX_TRACE` unset or `0` → no output, no measurable cost beyond one env read.
- 2. Unwritable target path → loud refusal naming the variable and, when the value is a well-formed absolute target, the full path — the issue's sad path 2 mandates naming it; never a crash of the governed run — tracing is disabled and the run proceeds, because refusing the run would make a trace fault verdict-changing.
- 3. fd target closed, invalid, full, or blocking → disabled with a single warning line, run proceeds; the emitter never blocks or retries.
- 4. Directory target with unwritable dir → refusal, no partial files.
- 5. Oversized or recursive event payload → refused against the schema's frozen max line length, never an unbounded line, never truncated.
- 6. Hostile env (key bytes, tokens, credential URLs — including a `RANEX_TRACE` value embedding secret bytes) → the allowlist drops everything undeclared; a refusal event names the variable and a shape descriptor (length plus 8-hex digest), never the raw bytes — malformed and unknown values are case (b) and never carry bytes.
- 7. Worker descriptor carries `RANEX_TRACE*` → descriptor refused pre-spawn.
- 8. Parent SID malformed → fresh root SID minted, event notes the malformed parent.
- 9. Trace file grows past the declared cap → the reserved refusal event consumes the reserve and the target stops: no further writes, never silent disk fill; a cap smaller than one max line is refused at setup.
- 10. Relative-path or unknown target value, including the `af_unix:` forms git accepts → loud refusal naming the variable and a shape descriptor (case b — these values never carry bytes), tracing stays off, run proceeds — refusing `af_unix:` narrows trace2's grammar, not the issue's contract.
- 11. Emission attempts a field outside the frozen set → refused; the refusal event names the dropped field only when the name matches the schema's bounded identifier grammar (`[a-z_][a-z0-9_]*`-form, capped by the max line length) — any other field name is represented by variable plus shape plus digest, never its bytes.
- 12. File or directory target that is, resolves to, aliases (device+inode; fd targets via `/proc/self/fd`), or sits under the governed repository root, evidence path, journal path, or any governed output → refused at emission setup, before the first write, judged on the once-opened descriptor's fstat; an fd target whose `/proc/self/fd` entry cannot be read is refused the same way — fail closed.
- 13. Ambient-copy environment (host qualification) carrying `RANEX_TRACE`, `RANEX_TRACE_EVENT`, or `RANEX_TRACE_PARENT_SID` → stripped before the command sees it — mandatory slice work, because an observed command that sees a trace var can branch on it.
- 14. One trace variable valid, the other invalid → the valid target runs; the invalid variable's target is disabled with one warning, caps and refusals staying per-target.
- 15. A field value outside its closed form (`level`, `stage`, `module`, `code`, `subject_digest`, `hierarchy`, `child_id`) → refused and represented by shape plus digest, never by its bytes.
- 16. Any event other than `version` carrying `evt` or `exe` → refused like an undeclared field, and a refusal event names the drop.

## Test strategy

Existing suites, each verified on disk: `tests/contract/test_docs_discipline.py` governs this ADR's own shape and the vendored-evidence rules; `tests/security/test_slice047_confinement_hardening.py` freezes the confinement-session controller's environment at `PATH, PYTHONPATH, LC_ALL, TZ` — the base the tracing-gated amendment extends while the strip keeps `RANEX_TRACE*` away from every governed and observed command; `tests/integration/test_slice017_native_launcher.py` freezes the descriptor-provided launcher env at `LC_ALL, TZ`; `tests/e2e/test_run_produces_evidence.py` is the real-run spine the future invariance test extends.

The future SLICE-054 tests are described in prose and named nowhere as paths, because they do not exist: schema freeze (red on any field drift, freezing both the eleven-field set and the version-event pair, plus the max-line and cap constants), off/on byte-invariance across the four target kinds over verdict, evidence bytes, and journal verify — extended to the governed-root target refusal and the ambient-env strip — the secret-scrubbing attack suite, the SID-chain tree riding a CLI → confinement-session-controller run, and the zero-output default suite run. They freeze red before implementation; the Phase-1 disposable prototype's invariance spot-check precedes them per ADR-013.

## Code review checklist

- Verify `evaluate()` and the journal append path emit nothing.
- Verify emissions appear only at `src/ranex/cli/` boundaries — `main.py` and the `host_confinement` session child's own stage boundary.
- Verify the target grammar is exactly issue #34's enumeration — the strict subset of `tr2_dst.c` semantics with `af_unix:` refused — including fd and per-process-directory forms.
- Verify the allowlist refuses undeclared fields and emits a refusal event naming the drop; `evt` and `exe` are admitted on `version` events only.
- Verify `RANEX_TRACE*` never reaches a worker descriptor or the launcher env (descriptor env stays `LC_ALL, TZ`).
- Verify no new dependency enters `pyproject.toml`.
- Verify the cap refuses rather than rotates, the reserved final refusal event fits within it, and that refusal lines are bounded.
- Verify a file or directory target that is, aliases, or sits under any governed output is refused before the first write — opened once (`O_NOFOLLOW`, fstat on the opened descriptor), only the held descriptor ever written.
- Verify every environment handed to a governed or observed command — including the host-qualification ambient copy — strips `RANEX_TRACE`, `RANEX_TRACE_EVENT`, and `RANEX_TRACE_PARENT_SID`, and that trace descriptors are non-inheritable (CLOEXEC) with close_fds spawns, so no trace fd crosses exec.
- Verify refusal diagnostics follow the split: a well-formed absolute target failing admission is refused naming the full path; malformed, unknown, and out-of-form values are represented by variable, length, and short digest, never bytes.

## More Information

Issue #34 freezes the binding input contract — target grammar, field set, sad paths, ownership; tracker #33 owns the phase order (PHASE 0 research → PHASE 1 prototype → PHASE 2 production). MAP §0.24 and §0.30 record the owner's build order; MAP's adoption form records copy-improve-own, never depend. Two corrections to the issue's research table are recorded here: `trace2/tr2_tgt.c` does not exist at v2.45.2 — the target grammar lives in `tr2_dst.c` and the JSON event target in `tr2_tgt_event.c`, both vendored; and structlog's `_nop` lives in `src/structlog/_native.py` at 24.4.0, not `_config.py` — `BoundLoggerLazyProxy` is the lazy-configuration path, a different mechanism. The vendored files and `NOTICE.md` are fetched-byte evidence; their hashes do not prove URL provenance without a second, independent fetch.

Reviewed 2026-08-17 by a fresh-context consensus panel and an independent adversarial acceptance panel, following ADR-013's review-record precedent. The consensus panel found four blockers and three majors — grammar-subset framing, governed-output target admission, propagation strip, shape-descriptor refusals, two-target routing, schema pinning, cap reserve — all remediated. The acceptance panel found three blockers and two majors — the path-naming split, the chain seam at the confinement-session controller with its frozen-test amendment, the version-event variant, clock/format pinning, open-once admission — remediated in this revision. The Prior art citations, the vendored files, and `NOTICE.md` are untouched by this revision.
