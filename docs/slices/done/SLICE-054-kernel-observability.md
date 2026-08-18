# SLICE-054 — kernel observability framework

**Status:** done
**Opened:** 2026-08-18
**Priority:** P0 — milestone 4's alignment rule (every new kernel path ships a
default-off toggleable trace, proven verdict-neutral) requires this substrate
before any other milestone-4 slice may land.
**ADR:** `docs/adr/ADR-031-kernel-observability-framework.md`
**Issue:** anthonykewl20/ranex#34 (tracker #33, PHASE 2 production; Phase-1
disposable prototype findings already posted there; branch
`prototype/slice054-phase1` retained, never merged).

## Contract

Two independent env-gated targets — `RANEX_TRACE` and `RANEX_TRACE_EVENT` —
carry the same frozen-schema JSONL stream, default off, env read exactly once
at import, targets admitted lazily at first emission, `version` as the first
write on each admitted target. Target grammar is issue #34's enumeration (a
strict trace2 subset): unset/empty/`0`/`false` off; `1`/`true` stderr; a single
digit 2–9 an already-open fd; an absolute path append; an existing absolute
directory one file per process named by the last SID component; relative
paths, `af_unix:` forms, and unknown values refused (case b: shape descriptor,
never bytes). `RANEX_TRACE_PARENT_SID` chains SIDs
(`<yyyymmdd>T<hhmmss>.<frac>Z-<host>-<process>`); a malformed parent mints a
fresh root SID and a note/refusal event records `malformed_parent_sid:<shape>`.
Redaction is a positive allowlist: undeclared fields dropped and named only
when the name fits the identifier grammar; out-of-form values represented by
shape+digest, never bytes. File/dir targets are byte-capped with
refusal-not-rotation; writes are single-call best-effort; a trace problem never
crashes the governed run. `RANEX_TRACE*` is stripped from every observed and
governed command environment (including the host-qualification ambient copy)
and `RANEX_TRACE_PARENT_SID` is passed to exactly one child — the
confinement-session controller — and only when tracing is enabled.

## Slice-time decisions (frozen by tests/contract/test_trace_schema.py)

Resolved under ADR-031's delegation ("value vocabularies frozen by the schema
contract test at slice freeze; their numeric values are slice work"). Any
deviation turns the schema test red. Schema evolution remains a new decision
(`evt` bump), never a patch.

1. `time` = epoch float `time.time()`, UTC, millisecond-truncated
   (`int(now*1000)/1000.0`, e.g. `1786990891.271`). ADR-031's text governs
   over issue #34's review-comment "RFC 3339" reading.
2. Public API surface, module `ranex.observability`: constants
   `TRACING_ENABLED: bool`, `SESSION_ID: str`; functions
   `stage_begin(stage: str)`, `stage_end(stage: str, code: str | None)`,
   `emit_raw(mapping)`. In `ranex.observability.schema`: `SCHEMA_NUMBER = 1`,
   `MAX_LINE_LENGTH = 16384`, `TRACE_BYTE_CAP = 1_048_576`,
   `IDENTIFIER_NAME_CAP = 256`,
   `FIELDS = ("event","sid","time","level","module","stage","subject_digest","duration_us","hierarchy","child_id","code")`,
   `VERSION_ONLY_FIELDS = ("evt","exe")`. In `ranex.observability.emitter`:
   `parse_target(value)`. In `ranex.observability.sid`: `derive_session_id(...)`.
   In `ranex.observability.redaction`: `screen_event(...)`. Exact internal
   signatures beyond those names are the implementer's.
3. Registries: `EVENT_NAMES = {"version","stage","refusal","note"}`;
   `LEVELS = {"debug","info","warn","error"}`;
   `MODULES = {"cli","observability"}`;
   `STAGES` = `cli.<group>.start` / `cli.<group>.end` for the 12 CLI dispatch
   groups enumerated from `src/ranex/cli/main.py`'s argparse subcommands
   (run, gate.evaluate, journal.verify, suite.freeze, deps.fetch, deps.approve,
   keygen, task.dispatch, task.judge, task.merge, task.delegate, task.fanout)
   plus `observability.emission` and `observability.note` — 26 identifiers
   total. `subject_digest`, `hierarchy`, `child_id` stay null at the CLI
   boundary in this slice.
4. `code` grammar: closed ten-kind registry, `schema.CODE_KINDS` — `exit`,
   `undeclared_field`, `out_of_form`, `malformed_parent_sid`,
   `cap_exceeded`, `target_admission_failed`, `oversized_event`,
   `emission_refused`, `emission_not_a_mapping`, `refusal_code_overflow` —
   with per-kind structural argument forms: `exit:<int>`;
   `undeclared_field:<identifier-or-shape>` (identifier grammar, or
   `len=N,sha256_8=<8hex>` for hostile names); `out_of_form:<field>:<shape>`
   with `<field>` one of the frozen eleven `FIELDS`;
   `malformed_parent_sid:<shape>`; `oversized_event:len=<N>`; the five bare
   kinds (`cap_exceeded`, `target_admission_failed`, `emission_refused`,
   `emission_not_a_mapping`, `refusal_code_overflow`) admit no argument at
   all. The slice-time decision was the looser `kind[:arg]` with arg matching
   `[A-Za-z0-9_.=+,:-]{1,200}`; final-gate finding N1 tightened it to this
   frozen form (commits bd1458df0/32b8540c6) so a grammar-shaped secret
   riding a legitimate kind is out of form exactly like an unknown kind.
5. `exe` = `importlib.metadata.version("ranex")`, falling back to walking
   parents for `pyproject.toml` `[project] version`, last resort `"unknown"`
   (today `"0.0.0"` — static pyproject, `[tool.uv] package = false`).
6. Version-event discipline: the internal first-write `version` event is built
   from literals and bypasses screening; any `version` emission through the
   screened surface is validated with variant discipline (non-null stage
   fields on a version event are out-of-form; `evt`/`exe` on non-version
   events refused as undeclared fields).
7. Controller seam: tracing off — the confinement-session controller
   environment is byte-identical to today's
   `{PATH, PYTHONPATH, LC_ALL, TZ}`; tracing on — the delta over that base is
   exactly the enabled trace target variable(s) plus
   `RANEX_TRACE_PARENT_SID` (ADR-031: "extending … by exactly the trace
   variables"), so the controller can emit chained events into the same tree.
   `RANEX_TRACE_PARENT_SID` reaches no other child surface.

## Exact owned paths

Product implementation may change only (issue #34's Exact ownership):

- `src/ranex/observability/__init__.py`, `emitter.py`, `schema.py`,
  `redaction.py`, `sid.py` (new)
- `src/ranex/cli/main.py` (stage emissions at CLI boundaries, ambient strip,
  PARENT_SID seam)
- `src/ranex/cli/host_confinement.py` (the session child's own stage boundary)
- the four frozen test files below, plus the two sanctioned amendments in the
  next section.

No emission inside `src/ranex/governed_execution/verdict.py` or the journal
append path; `evaluate()` stays pure and silent.

## Done criteria (each provable by a named frozen test)

1. Schema freeze: exact `FIELDS` order, `VERSION_ONLY_FIELDS`, constants,
   registries, `code` grammar, time truncation, version-variant discipline,
   `exe` = "0.0.0" — `tests/contract/test_trace_schema.py`.
2. Target grammar, admission (governed-root/symlink/hardlink refusal,
   open-once, held-descriptor writes), SID chain and malformed-parent
   handling, allowlist redaction, cap refusal-not-rotation, write-failure
   single-warning disable, off-state `_nop` + one env read per variable,
   both-target routing, version-first, canonical serialization —
   `tests/unit/test_observability.py`.
3. Verdict neutrality off vs on × {stderr, fd, file, dir} over the real
   run → gate evaluate → journal verify spine; governed-root target refusal
   end-to-end; ambient strip for observed and host-qualification environments;
   worker-descriptor `RANEX_TRACE*` pre-spawn refusal (launcher descriptor env
   stays `{LC_ALL, TZ}`); SID tree stitching CLI → confinement-session
   controller with the frozen controller-environment shape —
   `tests/contract/test_trace_invariance.py`.
4. Secret-scrubbing attack suite (PEM key material, bearer tokens,
   credential-URL env vars; ambient, embedded in `RANEX_TRACE` values, rogue
   `emit_raw` payloads) — zero planted bytes in any captured trace file or
   stderr — `tests/security/test_trace_secret_scrubbing.py`.
5. Default full-suite run with no trace env set: zero trace output, unchanged
   results — 1229 passed / 38 skipped / 0 failed at the close-out SHA
   b3c3ca86e — full `uv run --frozen pytest -q`.

## Sanctioned frozen-test amendments (mandated by ADR-031 and STATE)

1. `tests/integration/test_slice017_native_launcher.py`: `MAIN_PY_SHA256` is
   amended in the same commit that adds stage emissions to `main.py` — the
   digest exists to pin the launcher-relevant bytes of `main.py`, not to block
   this ADR's boundary change.
2. `tests/security/test_slice047_confinement_hardening.py::
   test_controller_gets_only_the_declared_environment` is extended with a
   tracing-on case asserting the controller environment gains exactly the
   trace variables — the enabled `RANEX_TRACE`/`RANEX_TRACE_EVENT` target(s)
   plus `RANEX_TRACE_PARENT_SID`, per ADR-031's "by exactly the trace
   variables" — over the frozen four-variable base. The launcher descriptor
   env stays frozen at `{LC_ALL, TZ}`; no other frozen assertion in that file
   moves.

## Residuals / disclosure

- fd targets (digit form) set O_NONBLOCK and non-inheritable on the
  operator-supplied descriptor and never restore the flags — the operator's
  open-file description for that fd persists O_NONBLOCK after the CLI exits
  (default-off, operator opt-in; deliberate per ADR-031 sad-path-3/CLOEXEC
  design; claude-gate follow-up).

## Not owned

- Harness-lane effect admission (milestone 3), verdict/gate-catalog/journal
  semantics, any behavior change hidden in "logging" work.
- Off-state overhead measurement (recorded at slice close, per ADR-031).
- The C launcher itself: it never receives a trace variable and emits nothing.

## Stop conditions

Stop rather than weaken a frozen test, emit from a non-boundary path, pass a
trace variable to any child other than the confinement-session controller,
rotate instead of refuse past the cap, echo refused bytes in a diagnostic, or
add a dependency. A schema change is a new decision (`evt` bump), not a patch.

## Verification commands

```text
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen pytest -q tests/unit/test_observability.py tests/contract/test_trace_schema.py tests/contract/test_trace_invariance.py tests/security/test_trace_secret_scrubbing.py
uv run --frozen pytest -q
```
