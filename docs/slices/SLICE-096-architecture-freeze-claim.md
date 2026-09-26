# SLICE-096 — The architecture-freeze claim (ADP's first family)

**Status:** open
**Origin:** captain DIRECT 011 FLAGSHIP; arch-maintain report §6/§10
SLICE-A; ADR-065 (proposed).

## Contract

The Agnostic Diagnostic Plane's first concrete claim: a human-approved
module graph, held true on every candidate by the existing scan surface.
Kernel untouched — `verdict.py`/`KERNEL_DIGEST` do not move, no new
reporter kind, no runtime dependency; the claim rides `sarif-2.1.0` as
ruff does (ADR-060, #97/#110 lineage).

- `src/ranex/foundation/arch_scan.py` — the scanner: stdlib `ast`, freeze
  schema `ranex-architecture-freeze-v1` (canonical bytes, `approved_by`,
  `package_root`, `modules` as file-or-prefix paths, sorted unique
  `allowed_edges`), default-deny edges, `arch/forbidden-import` and
  `arch/freeze-tampered` at `error` through the #97 fingerprint. A file
  under `package_root` in no module refuses the scan (exit 2, no artifact,
  absence blocks — the module-set analog of `missing`; the closed scan
  summary cannot block an out-of-scope finding). Installed as its own
  console script `ranex-arch`: a governed run resolves argv[0] once and
  executes the resolved path, so a `-m` module form loses the venv
  site-packages to the symlink target (measured live); the console
  script's shebang keeps the kernel's own bytes the thing that runs.
- **Digest pin** — `--expected-freeze-digest sha256:<canonical freeze
  bytes>` rides the claim's signed argv; the catalog that names the
  scanner pins the freeze, so weakening the freeze without moving the
  catalog is itself a finding that fails the freeze path.
- `docs/adr/ADR-065-adp-agnostic-diagnostic-plane.md` — the ADP ADR,
  **proposed**: A/B/C authority split (A: deterministic diagnostics as
  digest-bound SARIF-family claims; B: completions/hover/refs/rename
  feedback-only through the repair envelope; C: LLM-as-judge and
  RAG-as-oracle rejected), per-language calibration against the BASE
  freeze, and the freeze-origin rule — the operator's approval of the
  ADR/spec IS the freeze; artifact updates thereafter are autonomous
  promote ships that move freeze bytes, pin and manifest together.
- Because the ADR is proposed, no repository's graph is frozen by this
  ship: `governance/gates.yaml` gains no arch claim, and wiring ranex's
  own ten-subpackage graph is the post-approval promote ship the ADR
  names. Per DIRECT 014 the ship is **implementation-only**: production
  waits for `ranex-stress-arch-freeze` READY (DIRECT 012 stress before
  any language is blocking-on).

## Non-goals

Per-language diagnostic engines (DIRECT 013 IDE scout feeds those later),
handbook vocabulary chapters (later ship), ranex's own freeze file and
gates.yaml wiring (operator approval first), any transitive-edge or
seam-protection schema extension, any change to `evaluate()`,
`scan_results.py` or the gate loader, new runtime dependencies.

## Validation

Red-first unit tests (`tests/unit/test_arch_scanner.py`, 30 rows: schema
refusals by name, attribution, edge shapes, default-deny, finding-ID
stability, digest pin, reduction through the real `scan_results_from_sarif`,
entry-point exits) and claim-surface contract tests
(`tests/contract/test_arch_claim.py`, 5 rows: the console-script argv
loads, script operands refused — including a path-like `-m` value — output
tokens exact, manifest required, the pin rides `command_digest`). The
packaging contract now pins both console scripts.

Real-kernel receipts at `tools/dogfood/audits/2026-09-26-arch-freeze/`
(`tools/dogfood/arch_proof.py`): pristine PASS ×3 byte-identical on the
decision core (subject digests differ by construction — fresh Ed25519 keys
per workspace, the lab's independent-replication design); planted
forbidden edge FAIL ×3 naming `pkg/foundation.py:4` and the
foundation→policy edge, fingerprint `674872ef…711f` byte-identical to the
arch-maintain lab's observation; accepted-exception both directions
(declare → PASS, remove → FAIL); freeze-tamper (weakened allow-list under
the untouched pin → `arch/freeze-tampered`, FAIL); absence (no scan →
FAIL). Scanner argv is `ranex-arch check …` — the shipped shape, not the
lab's standalone script.
