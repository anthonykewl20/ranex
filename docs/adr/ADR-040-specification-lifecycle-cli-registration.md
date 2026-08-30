# ADR-040 — specification lifecycle CLI registration

**Status:** accepted
**Date:** 2026-08-30
**Decision-makers:** repo owner
**Issue:** #60 (completes the public CLI surface opened by #63's installed entry point)

## Context and Problem Statement

`src/ranex/cli/specification.py` (119 lines) implements the specification
lifecycle CLI — draft, advance, questions, status — with a stable refusal
channel (`E-SPEC-030-*` codes on stderr, exit 2, via `_print_refusal` at
lines 56-58) and canonical JSON on stdout with exit 0 on success. It is
registered nowhere: `build_parser()` in `src/ranex/cli/main.py` has no
`specification` group, so operators who reach the installed `ranex` entry
point (issue #63) cannot drive the lifecycle. The module's standalone
parser (prog `ranex-specification`, lines 101-116) serves only direct
consumers such as `tests/integration/test_specification_cli.py`, which
calls `args.func` directly.

## Decision Drivers

- Register the lifecycle on the installed surface without rewriting it.
- Preserve refusal semantics byte-for-byte: stderr codes, exit 2, canonical stdout.
- Follow the existing `journal` two-level group template, not a new shape.
- Keep the frozen trace-stage registry and the CLI surface in lockstep.
- Make registration an `evt` bump, per the schema's own evolution rule.
- Feed `task batch qualify` from lifecycle records with no new glue.

## Prior art

Searched: GitHub code search 'argparse add_subparsers set_defaults
sub-command registration', 'project.scripts console_scripts entry point
registration'; consulted docs.python.org library/argparse (3.14) for
sub-parser semantics before choosing consumer evidence to vendor.

- https://github.com/pypa/pip/blob/25.2/src/pip/_internal/cli/main.py —
  an installed CLI whose `main()` parses args, resolves the command, and
  returns `command.main(cmd_args)` as the process exit code — the same
  integer-returning dispatch contract `main()` at
  `src/ranex/cli/main.py:3851-3872` already uses around `args.func`.
  License: MIT (pip 25.2).
  Weakness: dispatch resolves commands through pip's own `create_command`
  registry rather than plain `add_subparsers` + `set_defaults`, so the
  two-level group/action pattern this decision needs is only implicit,
  and the file itself warns that in-process use is unstable across
  versions; the snapshot is tag 25.2, not whatever pip the runner has.
  Vendored: `docs/adr/prior-art/ADR-040/pip-25.2-cli-main.py` blob:91b5f4cc03200178865bce69abfdbc12c651e3d6

- https://github.com/pypa/pip/blob/25.2/pyproject.toml —
  `[project.scripts]` maps `pip` and `pip3` to
  `pip._internal.cli.main:main`, which is exactly the mechanism that
  makes issue #63's installed `ranex` entry point publicly reachable:
  registration in the surface definition, not a bespoke launcher.
  License: MIT (pip 25.2).
  Weakness: it only declares the name-to-object mapping; the wrapper's
  generation and behaviour live in the installer, so it evidences
  reachability, not argparse structure, and pins pip's own version
  rather than this repository's build configuration.
  Vendored: `docs/adr/prior-art/ADR-040/pip-25.2-pyproject.toml` blob:f2883366f6e1b8a4bce85f65f2258e1fbb032172

- Rejected: https://github.com/pypa/packaging.python.org — the
  entry-points specification page (entry-points.rst at commit
  bc46f2d79bea6b556d8bfd09ce5ffddb78fa022f) is the canonical wrapper-format
  reference, but the site's content is CC-BY-SA 3.0, a ShareAlike licence
  whose obligations sit badly in an MIT repository, and it governs
  installer wrapper generation, not argparse group registration.
- Rejected: https://github.com/python/cpython — vendoring Lib/argparse.py
  at v3.14.0 as a second evidence file was considered and set aside: it
  is the implementation rather than a consumer pattern, roughly 2,800
  lines of evidence for a decision pip's two small files already cover,
  and the release tag can drift from the installed patch version.

## Considered Options

1. Register a two-level `specification` group in `build_parser()`,
   following the `journal` template (main.py:3548-3554), binding the
   existing cmd_* functions via `set_defaults(func=...)`.
2. Reuse specification.py's standalone `build_parser()` under main's root.
3. Register the commands without trace stages or an evt bump.
4. Rename/alias the standalone parser's prog to `ranex` while registering.
5. Ship a new `ranex-specification` console script beside `ranex`.

Option 1 was adopted. Option 2 does not compose — the standalone parser's
double dest nesting (`command` then `specification_command`) defeats
`_dispatch_stage`'s group/action derivation, and two parsers for one
surface invite drift. Option 3 leaves the commands the only CLI surface
invisible to the governed trace: unregistered groups are silently
dropped (main.py:3818-3819). Option 4 is out of scope; Option 5
fragments the entry point #63 just unified.

## Decision Outcome

Adopt option 1, with the schema edit it forces:

- **Registration shape**: top-level `specification` parser → `add_subparsers(dest="action", required=True)` → four action parsers (options exactly as in specification.py:106-114), each `set_defaults(func=...)` binding the EXISTING cmd_* functions, imported aliased (`cmd_specification_draft` etc.).
- **Evt bump**: `CLI_DISPATCH_NAMES` (schema.py:64-78) gains `"specification"`; per the module's own rule (schema.py:6-7) `SCHEMA_NUMBER` 2→3 ("Version 3 adds the specification CLI dispatch stage pair."); the stage pair comes free from main()'s existing wrapper (main.py:3851-3872).
- **Frozen contracts together**: test_trace_schema.py's literal (61-75), count comment 13→14 and schema assert (134) change in the same slice; equality (152-153) and subset (406-443) then hold.
- **Refusals byte-for-byte**: cmd_* bind as-is; `int(args.func(args))` (main.py:3863) carries exit 2 through; the E-SPEC-030 vocabulary is untouched, the integration test unmodified.
- **Downstream already real**: advance() validates the A/B/C chain (application/specification.py:124-152); the terminal approval envelope IS `task batch qualify`'s `--approval-envelope` input (main.py:3359-3410) — no new glue.

### Consequences

- `ranex specification draft|advance|questions|status` appear in the
  installed help tree; operators no longer need the module's standalone
  parser.
- Every trace emitted under schema 3 carries `evt: 3`; consumers pinned
  to 2 see a version event they must refuse or upgrade for.
- The standalone parser (prog `ranex-specification`) stays untouched for
  its existing direct consumers; both surfaces bind the same cmd_*
  functions, so behaviour cannot drift between them.
- Adding any future fifth action under `specification` is a no-op for
  the stage registry (the group, not the action, names the stage pair).
- The frozen trace-schema test is edited in the same slice as the
  registry — never before, never after.

### Confirmation

Verified now, by exploration: specification.py and its refusal channel;
main.py's journal template, `_dispatch_stage` derivation and
drop-if-unregistered, and int() exit-code passthrough; schema.py's
registries and evt rule; test_trace_schema.py's literals and asserts;
the batch-qualify wiring; and that `tests/e2e/expected/` goldens carry
no evt schema-number field (only `qualification_schema=...` strings).
Implementation must still prove: the registered help surface shows the
four actions; `ranex specification draft --input x` exits 0 with
`state: DRAFT` in canonical JSON; invalid input exits 2 with
`E-SPEC-030-INVALID-INPUT` on stderr through the registered path; the
evt bump propagates (`evt: 3`); and a re-grep of `tests/e2e/expected/`
stays empty on the implementation commit.

## Improvements on the prior art

- pip keeps commands in a parallel `create_command` registry that the
  parser must be reconciled with; this decision binds the existing cmd_*
  functions directly through `set_defaults(func=...)`, so there is one
  registration site and no registry to drift out of sync.
- pip's entry point returns whatever `command.main` returns; main()
  already wraps dispatch in `int(...)` plus crash-paired stage_end, so
  the registered lifecycle inherits trace discipline pip does not have.
- Neither vendored file ties registration to an observability schema;
  here joining the frozen dispatch-stage registry is what forces the evt
  bump, making "new CLI surface" and "new trace stages" one deliberate
  edit protected by a contract test rather than a convention.
- The aliased imports (`cmd_specification_draft`, ...) prevent the
  generic names (`cmd_draft`, ...) from colliding with future commands in
  main.py's namespace — a hazard pip avoids only by its registry
  indirection.

## Architecture surface

- `src/ranex/cli/main.py` — `build_parser()` gains the `specification`
  group (four action parsers, aliased imports, `set_defaults`).
- `src/ranex/observability/schema.py` — `CLI_DISPATCH_NAMES` gains
  `"specification"`; `SCHEMA_NUMBER` 2→3 with the version comment.
- `tests/contract/test_trace_schema.py` — group literal + count comment
  + schema-number assert, edited in the same slice.
- `src/ranex/cli/specification.py` — untouched; its standalone parser
  and `__all__` keep serving direct consumers.

## Scope and threat delta

- No change to lifecycle behaviour, refusal codes, canonical output, or
  the domain/application layers beneath the CLI.
- No change to confinement, journaling, or any governed-execution path.
- Threat model unchanged: registration exposes an existing, already
  refusal-disciplined surface; it adds no new authority, no new inputs
  beyond the four already-required options, and no observability
  emission beyond the registry's standard stage pair.
- The evt bump is the entire protocol delta, and it is additive at the
  version-event level.

## Quality attributes

| Attribute | Effect |
|---|---|
| Auditability | new commands land inside the governed trace stage pair, not beside it |
| Compatibility | refusal channel and canonical stdout unchanged byte-for-byte |
| Consistency | one registration shape (journal template) across all groups |
| Simplicity | no new parser framework, no registry indirection, no glue code |
| Reversibility | delete the group, revert the evt bump, both surfaces return |
| Testability | frozen contract test turns red on any asymmetric edit |

## Reversibility

Door: two-way

Removing the `specification` group from `build_parser()` and reverting
the registry + evt bump restores today's state exactly; the standalone
parser is untouched either way. The only cost of reversal is another evt
bump (3→4), which is the schema discipline working as designed, not a
migration. No data, journal, or golden depends on the group existing.

## Sad paths

- The schema literal and the registry are edited asymmetrically (one
  without the other): the equality test's both-directions assert fails
  by design, turning the slice red until they match.
- The evt bump lands without re-checking schema-number-bearing goldens:
  byte-pinned transcripts would mismatch — this session's grep found no
  evt field in `tests/e2e/expected/`, and the implementation must
  re-verify on its own commit.
- Generic import names (`cmd_draft`) collide in main.py's namespace with
  a future command: mitigated by the `cmd_specification_*` aliases.
- Someone later adds a third level (`specification x y`): `_dispatch_stage`
  derives nothing and silently drops the stages unless
  `trace_dispatch_group` is set — the `task.batch.qualify` precedent
  documents the cure; a sad path only if unread.
- main()'s `int(args.func(args))` wrapping were "improved" to re-map exit
  codes: refusal exit 2 must pass through untouched or the E-SPEC-030
  channel silently breaks.
- The standalone parser and the registered surface drift apart in option
  names: mitigated because both bind the same cmd_* functions, so a
  divergent option surfaces as an immediate argparse error, not quiet
  behavioural drift — but help text can still diverge if hand-copied.
- README/docs claim the lifecycle before the registered help actually
  shows it: docs must be generated or checked against the parser surface,
  not against intent.
- `task batch qualify` consumes lifecycle records whose states were
  produced by the OLD unregistered surface: none exist durably today, but
  a future record-format change would orphan them — the evt discipline
  guards exactly this, which is why the bump is not optional.
- The count comment in test_trace_schema.py says 13 while the literal
  holds 14: no assert fails, and the next reader trusts the wrong number;
  kept honest only by review of this ADR's checklist.

## Test strategy

- `tests/contract/test_trace_schema.py` — must stay green after the
  deliberate edit: equality (152-153), parser-derived subset (406-443),
  and the schema-number assert (134) all updated together in the slice.
- `tests/integration/test_specification_cli.py` — must pass UNMODIFIED:
  proof that the standalone surface and its refusal channel are
  untouched.
- `tests/contract/test_docs_discipline.py` — governs this ADR itself
  (budgets, citations, vendored digests, NOTICE).
- Implementation slice adds a registered-path check: help tree shows
  `specification draft advance questions status`; `ranex specification
  draft --input x` exits 0 with `state: DRAFT` in canonical JSON; invalid
  input exits 2 with `E-SPEC-030-INVALID-INPUT` on stderr.
- `git grep -n "schema" tests/e2e/expected/` on the implementation
  commit — must still show only `qualification_schema` strings, proving
  no golden carries an evt field that the bump would desynchronize.

## Code review checklist

- [ ] `build_parser()` registration follows the journal template exactly
      (two-level, `dest="action"`, `required=True`, four action parsers).
- [ ] Imports are aliased (`cmd_specification_draft` etc.); no generic
      names land in main.py's namespace.
- [ ] `specification.py` diff is empty; the standalone parser is
      untouched.
- [ ] `SCHEMA_NUMBER` is 3 with the version-3 comment;
      `CLI_DISPATCH_NAMES` and the test literal both gained
      `"specification"`; the count comment reads 14.
- [ ] Refusal passthrough proven: exit 2 + `E-SPEC-030-INVALID-INPUT` on
      stderr through the registered path.
- [ ] `tests/integration/test_specification_cli.py` diff is empty and
      green.
- [ ] Full suite (`uv run --frozen pytest -q`) green on the exact commit.

## More Information

- Issue #60 — this decision; issue #63 — the installed `ranex` entry
  point it completes.
- `docs/adr/ADR-027-specification-lifecycle.md` — the lifecycle itself.
- `docs/adr/ADR-031-kernel-observability-framework.md` — the frozen trace
  schema and its evt discipline.
- `src/ranex/cli/main.py:3548-3554, 3795-3820, 3851-3872` — journal
  template, stage derivation, dispatch wrapper.
- `docs/adr/prior-art/ADR-040/NOTICE.md` — provenance and licences for
  the vendored evidence.
