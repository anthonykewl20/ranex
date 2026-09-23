# SLICE-088 — Path-scoped kernel handbook injection

**Status:** done
**Issue:** #100
**ADR:** docs/adr/ADR-062-path-scoped-kernel-handbook-injection.md

## Contract

`governance/handbook.json` in the dispatched base tree is the project layer;
`${XDG_CONFIG_HOME:-$HOME/.config}/ranex/handbook.json` is the system layer —
two layers, one operator, no others. Entries are
`{path_glob, text, merge_system}` in declaration order, first match per
layer; a system entry may carry `sniff_marker` (first-non-blank-line prefix)
and nothing else may sniff. Resolution is pure over (entries, paths, peeks):
project beats system, `merge_system` keeps the system chapter first, a path
with no match is a recorded `unmatched` row, and one digest
(`sha256:` over canonical chapters+rows) changes on any chapter byte.

`task delegate` resolves the handbook against every file of the dispatch base
tree, appends chapters plus the full per-path table to the worker's brief,
and lands `{digest, chapters, matched, unmatched}` as the additive `handbook`
field of the ADR-043 retained-log manifest. No handbook anywhere → the
packet and manifest are byte-identical to pre-#100. Malformed handbooks
refuse the run. `run`, `gate evaluate`, the journal, signing and verdict.py
never read a handbook; verdict.py stays digest-pinned.

## Boundaries

Guidance only — no chapter can widen, narrow or replace a gate, claim,
verdict or journal rule, and nothing on an enforcement path imports the
engine (compiled by tests/contract/test_handbook_surface.py). The sniff reads
one bounded line per sniff-globbed path; `--log-retention off` retains no
manifest, hence no digest record. #102's delegated review command and #112's
minimization ladder compose this later; include/exclude filters and further
layers stay refused (§17.6).

## Validation

Red-first: tests/unit/test_handbook_resolution.py (58 cases),
tests/integration/test_handbook_delegate_cli.py (real git target, real
harness, real `cmd_task_delegate`), tests/contract/test_handbook_surface.py,
tests/e2e/test_handbook_injection_real.py (real subprocess journey, ADR-032
golden `expected/handbook-delegate-brief.out` with sabotage control). Field
proof per #95: tools/dogfood/handbook_proof.py runs the issue's five
real-data arms as control pairs — resolving every path of six@1.17.0
(ebd9b3af90247b8858d415a05e96e9ee61e48d07) and of Ranex, project-over-system
with both matches recorded, the sniffer under the project layer, the
manifest digest (equal to the engine's over the same inputs) with the
one-byte change refused, a governed run/gate-evaluate byte-identical with
and without a system handbook, and unmatched recorded. All six controls
VERIFIED over three repeats;
tools/dogfood/audits/2026-09-24-handbook-injection/.
