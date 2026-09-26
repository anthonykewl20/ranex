# ADR-064 — the Agnostic Diagnostic Plane: authority split, and the architecture freeze as its first claim

**Status:** proposed

DIRECT 011 (flagship), DIRECT 008 FINAL (machine-closed scoring), DIRECT 013
(per-language diagnostics feed). Source evidence: the arch-maintain scout
report (`third_party/firstmate/data/ranex-arch-maintain-steal/report.md`,
2026-09-25) whose micro-experiment proved the mechanism through the real
kernel before this ADR was drafted — pristine PASS ×3, planted forbidden
edge FAIL ×3, absence FAIL. This ADR is **proposed**: under DIRECT 008
FINAL the operator's approval of this document is the freeze — until then
no repository's graph is frozen, and the machinery shipped beside this ADR
stays proof-backed and unwired.

## Context and Problem Statement

IDE-grade diagnostics — typecheckers, linters, language servers, compilers,
format checkers — already answer, deterministically and per-language, most
of the questions an agent building software is graded on. What they never
answer is the question this kernel exists for: *who decided*, and on which
bytes. An agent that owns its own linter config owns its own verdict; an
LLM asked "is this architecture good?" owns a verdict no one can audit.

The Agnostic Diagnostic Plane (ADP) is the flagship answer: one plane in
which every language's deterministic diagnostics become digest-bound claims
the existing kernel already knows how to judge, with the authority split
decided once, per diagnostic kind, instead of per language or per repo.

## Decision Outcome

In the context of language-specific deterministic diagnostics facing the
kernel's purity and trust-root invariants, we chose **a three-way authority
split (A/B/C), the architecture freeze as the first A-family claim, the BASE
freeze as the per-language calibration backbone, and an operator-origin
rule for every frozen graph**, accepting that this constrains future
diagnostic integrations to the seams that already exist.

### The A/B/C authority split

- **A — deterministic diagnostics as claims.** Typecheck, lint, LSP
  diagnostics, compile, format-check: any tool that is a pure function of
  (subject bytes, pinned policy bytes), runs offline, and can emit SARIF
  2.1.0 (or be wrapped to). It enters as a scan-claim exactly as ADR-060
  and the #97/#110 lineage define: scanner bound as the kernel's own entry
  point, one canonical argv, its own frozen manifest, `evaluate()` deciding
  PASS|FAIL. No model in the loop, ever — removing every model credential
  must not change a verdict.
- **B — feedback-only diagnostics through the repair envelope.**
  Completions, hover, references, rename-preview: diagnostics that *advise*
  an agent mid-repair. They may shape the candidate a delegate proposes,
  never the verdict on it. Their only channel is the C1 repair envelope
  (`ranex-repair-envelope-v1`) — failing IDs, assertion text, file:line,
  repro argv, next rung — which is itself derived from A-family outcomes.
- **C — rejected: judgement-shaped authorities.** LLM-as-judge and
  RAG-as-oracle-knowledge are refused as verdict inputs (the standing
  C-axis). Free-text or rendered outputs (HTML reports, badges, prose
  summaries) are not reducible to the closed summary, so they are not
  evidence, whatever their persuasive value as advisory packets.

The routing test for any future diagnostic (the decidability rule): an
assertion is routable to A iff it is a pure function of (subject bytes,
committed policy bytes) with no model in the loop — the same standard
`evaluate()` already meets.

### First claim family: the architecture freeze

A human-approved document names a package's modules and the import edges
between them; the kernel holds that naming true on every candidate.

- **Freeze schema v1** (`ranex-architecture-freeze-v1`, canonical JSON
  bytes only): `approved_by` (the approving ADR), `package_root`,
  `modules` (name → file or directory prefix), `allowed_edges` (sorted
  unique pairs of declared names). Default-deny: an internal edge not
  listed is a finding. v1 covers direct edges only; transitive-chain rules
  and seam-protection blocks are studied extensions, not shipped.
- **Scanner** (`ranex-arch`, its own installed console script): stdlib
  `ast`, exit 0 however many findings, deciding through its SARIF artifact
  through the #97 fingerprint. Rules: `arch/forbidden-import` (error) and
  `arch/freeze-tampered` (error). A `.py` file under `package_root` in no
  freeze module refuses the scan (exit 2, no artifact, absence blocks) —
  the module-set analog of `missing`; a finding on an out-of-scope path is
  invisible to the frozen universe, so refusal is the only shape that
  blocks. The only remedy is a freeze update, never an acceptance.
- **Digest pin.** The claim's argv carries
  `--expected-freeze-digest sha256:<canonical freeze bytes>`; the catalog
  that names the scanner also pins the freeze. Editing the freeze without
  editing the catalog is a finding, not a silent policy change. The pin
  rides the signed argv, so evidence recorded under a different pin cannot
  satisfy the claim (`command_digest`).
- **Acceptance.** A forbidden edge review has answered for is declared
  `--accepted` at manifest-freeze time, by finding ID. The ID binds
  ruleId + path + region + the subject's own bytes, so an accepted
  exception stays accepted only while the code under it is unchanged, and
  cannot be renamed or moved into validity.

### Per-language calibration policy

The plane is language-agnostic by mandate (DIRECT 013): its production
target set is **TypeScript/JavaScript, Python, PHP, Java, Go and Rust plus
the common web backends**, measured and promoted per language under the
same claim shape — Python is the bootstrap, not the product.

An A-family claim for a new language is not trusted because it passes on
one tree. The BASE freeze (ADR-063, `governance/calibration/base-freeze-v1.json`)
is the calibration backbone: per-language diagnostic promotions cite the
BASE freeze and show paired marginal deltas on named axes through the
promotion gate (`ranex promotion evaluate`), with the scan manifest of the
promoted claim playing the role the suite manifest plays for suite-family
promotions. Each language earns blocking authority only after its own
BASE-cited calibration and the DIRECT 012 stress gate reports READY; a
STRESS-NOT-READY language stays held and its ships land
implementation-only. No L3 kill-rate calibration (rejected on its own
data, ADR-063).

### The freeze-origin rule

The first freeze of any graph is the operator approving this ADR (or a
repository-specific successor spec) — approval *is* the freeze. Thereafter,
freeze and graph updates that implement an approved ADR are autonomous
promote ships: they move the freeze bytes, the catalog's digest pin and the
scan manifest together in one reviewed commit. Delegated scopes exclude
the freeze file and the scan manifest (ADR-017 path+action disjointness);
`tach sync`-style auto-blessing of new edges is a no-self-approval
violation and refused. An agent that believes an approved edge set is
wrong drafts a proposed ADR; it never edits the freeze.

## Prior art

- SARIF 2.1.0, the artifact every A-family claim speaks:
  <https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html>
- import-linter (BSD-2-Clause, studied at
  `31927f1457e3df673912cb5efb0afa6dbc37585f`): contract taxonomy
  (forbidden/protected/layers) — behaviour stolen, engine not adopted:
  <https://github.com/seddonym/import-linter>
- grimp (BSD-2-Clause, studied at
  `676e490929b906aef2d07c00b8b1525f8f488269`): pure query engine with
  line-precise chain queries — future transitive-edge rules may steal its
  query shapes; as a library dependency it is a runtime dep, refused:
  <https://github.com/python-grimp/grimp>
- tach (MIT, studied at `65df67ac51a8d0e8f9e0398ea72c924fea34fd25`):
  interface-enforcement idea stolen for a possible seam-surface pin;
  `tach sync` (auto-rewrite rules) and `tach show --web` (remote render)
  both refused — self-approval and exfiltration:
  <https://github.com/gauge-sh/tach>
- Cross-ecosystem equivalents, one line each: `depguard`/`importas` (Go
  linters), dependency-cruiser (JS, named rule IDs — the closest analogue),
  ArchUnit (Java, arch-tests-as-code). None change the stdlib-AST choice
  for a Python subject with a no-new-runtime-deps wall:
  <https://github.com/sverweij/dependency-cruiser>

No prior-art bytes are vendored by this ADR; the Ousterhout/Feathers
vocabulary chapters the source report mapped are a later, separate ship
and would carry their own `Vendored:` claims if ever vendored.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 1 | candidate adds an unapproved import edge | blocking finding at the statement's file:line; the carrying path fails the gate |
| 2 | candidate weakens the freeze (adds the edge it wants) | digest pin mismatch: `arch/freeze-tampered`, freeze path fails the gate |
| 3 | file appears under package_root in no module | scan refuses (exit 2), no artifact, absence blocks; never acceptable |
| 4 | accepted exception's code changes under it | finding ID changes; the old acceptance no longer matches; FAIL |
| 5 | scanner never ran | no evidence for the required claim; FAIL |
| 6 | scan manifest removed from the governing commit | claim refused at construction (a scan with no frozen scope decides nothing) |
| 7 | freeze file deleted from the subject | scope path missing; FAIL |
| 8 | A-family scanner exits nonzero on findings | claim unsatisfiable regardless of acceptance (the ruff `--exit-zero` lesson, OPERATIONS) |
| 9 | B-family diagnostic offered as a verdict | refused at review: no envelope-derived record may satisfy a claim |
| 10 | this ADR is never approved | nothing freezes; the shipped machinery stays proof-backed and unwired |

## Door

Door: two-way — supersede this ADR to change the split or the schema; the
freeze files, pins and catalog wiring revert with it. The A/B/C split
itself leans one-way in practice: moving a diagnostic from A to C is a
loosening history will record.

## Test strategy

- `tests/unit/test_arch_scanner.py` — schema refusals, module attribution,
  edge shapes (absolute, `from pkg import name`, relative), default-deny,
  finding-ID stability, digest pin, reduction through the real
  `scan_results_from_sarif`.
- `tests/contract/test_arch_claim.py` — the claim surface: console-script
  argv loads, script operands refused, manifest required, digest pin rides
  the signed argv.
- `tools/dogfood/arch_proof.py` — real-kernel receipts under
  `tools/dogfood/audits/2026-09-26-arch-freeze/`: pristine PASS ×3
  byte-identical, planted edge FAIL ×3 naming file:line (fingerprint
  byte-identical to the source report's lab), accepted both directions,
  tamper control, absence.

## More Information

The source report's §6 is the design's provenance; its §5 engine inventory
is summarised above. Per-language diagnostic engines (the IDE scout,
DIRECT 013) enter as future A-family wrappers, each calibrated against the
BASE freeze per this ADR's calibration policy.
