# ADR-060 — the producer evidence plane: one trust chain, extended at named seams

**Status:** accepted

Issue #96. Architecture anchor for milestone 6; every other issue in that
milestone names the seam it attaches to.

## Problem

Three separate proposals arrived at once — admit a second results format,
instruct delegated workers, and record findings a scanner or a model produced.
Each is reasonable alone. Taken separately, each invites its own admission path,
its own signing surface and its own verdict rule, and the result is three trust
chains wearing one name. The kernel's guarantees are stated per-chain, so a
second chain silently halves them.

The question this ADR settles is not whether to add those capabilities. It is
where a new *kind* of observation may enter, and what it may never do.

## Decision

There is one chain. New capability enters at a named seam and is judged by the
existing kernel.

```
governance/gates.yaml    a claim: claim_id + command argv + optional results artifact/reporter
        |                  SEAM A  policy loader — new reporter kinds, per-claim manifests
        v
ranex run --claim C --producer P -- <argv>
  materialise subject . environment from empty . execute
  parse_results_artifact(reporter) -> the closed suite-summary shape
        |                  SEAM B  foundation normaliser — a new artifact kind reduces to that shape
  sign the 13-field envelope (subject, argv digest, catalog digest, confinement)
        v
ranex gate evaluate <ref>
  trust roots read from the ref . admit() . evaluate() . journal append . anchored signed verdict
        |                  SEAM C  committed_trust_root — every new policy file, in all three readers
        v
github_app: binding -> acceptance -> check run
        |                  SEAM D  publisher text from causes[].detail; conclusion mapping stays closed
        v
tools/dogfood: receipts, negative controls, calibration recall
                           SEAM E  measurement, never authority
```

### The rules that keep it one body

1. **A new artifact kind is a new `results_reporter`, normalised into the
   existing summary.** `Evidence.satisfies()` already judges `missing`
   (absence), `non_passed` against `expected_skips` (declared exceptions) and
   `manifest_digest`. Nothing gets a second verdict path, and `verdict.py` does
   not move.
2. **A new policy file is a trust root or it is a hole.** SLICE-081 closed
   "green evidence plus an edited rulebook". A scan manifest or handbook that
   `run`, `gate evaluate` and `EvidenceEvaluator._policy` do not all pin
   reopens it.
3. **Delegated work enters only as the bound command of `ranex run`.** Its
   output is the artifact; the observation is signed by the observing producer.
   No worker keys, no second signing surface. *Which* model did the work is
   PR-07's production-configuration record (ADR-016), not a field the envelope
   grows here.
4. **A model-backed claim is never in a default `required_claims`.** Putting one
   there knowingly relaxes "removing every model credential must not change a
   verdict", and needs its own ADR saying so.
5. **Guidance is not policy.** Path-scoped rules for workers are read when a
   delegation packet is built, never by `run` or `gate evaluate`. Only the
   kernel enforces.
6. **Closed vocabularies, one meaning of absence.** A missing artifact, an item
   absent from a manifest and an unresolvable finding anchor all reach
   `evaluate()` as absence; rejections leave admission as structured data.

### What the seams are not

Seam E measures and never decides. Seam D renders an admitted record and never
computes one. Neither may introduce an advisory verdict class: the kernel has
`PASS` and `FAIL`, and a gate that cannot block is refused at construction.

## Evidence

Executed 2026-09-09 against the installed kernel and a real throwaway governed
repository — real `git`, real Ed25519 keygen, real `ranex run`, real signed
evidence, real `ranex gate evaluate`. No mocks, no monkeypatched seams.

**An arbitrary program is already a first-class blocking claim.**
`results_required` is derived as `claim.results_artifact is not None`
(`cli/main.py`, `bootstrap/composition.py`), so a claim naming no artifact is
judged on exit code alone. Measured on a real subject: scanner exit 0 →
`PASS gate=landing`; exit 1 → `FAIL — the bound command was observed failing`;
scanner never run → `FAIL — no evidence for required claim`. A new observation
kind therefore needs no kernel change to *block*; it needs one only to say more
than pass/fail.

**Advisory evidence is recorded and cannot decide.** A failing record for a
claim outside `required_claims`, presented beside a satisfied required claim,
produced `PASS` while remaining visible in the evaluation's `considered` list.
Measurement and gate are already distinguishable without a new verdict value —
rule 4 is expressible today.

**"Did less" is caught deterministically.** A suite record whose `missing`
carries one expected ID produced `FAIL — missing test ID(s)`. The frozen
manifest is the counter-metric for any future rule that rewards smaller
changes; no completeness judge is needed, and none may be used.

**Containment is real, and narrower than it reads.** An `argv[0]` resolving
inside the materialised subject is refused: *"a route the observed tree carries
chooses the binary as surely as supplying it does."* But the check inspects
`argv[0]` only. A claim bound to a system interpreter plus an **in-tree script**
(`/usr/bin/python3 neuter.py`) was admitted and returned `PASS` while a
violating file was still present in the tree. This is the F-012 family — a
hostile in-tree component choosing what a claim means — and it is a design
constraint on every scanner added at Seam B: the program must resolve from the
installed kernel, and the claim's argv must carry no in-tree path.

**The envelope binds its own rulebook.** Evidence produced under `gate: landing`
was refused when evaluating `landing-c`: `policy-context-mismatch — record was
produced for gate 'landing', not 'landing-c'`. ADR-048 behaves as documented.

## Limits

The proofs above establish the seams, not the features that will use them. No
SARIF normaliser, handbook, or review packet exists yet. `task delegate`
remains a prototype and not a verdict path (MAP §5.1), and the instructions
handed to a delegated worker are recorded in no artifact today — the outcome,
the ADR-043 log manifest and the signed envelope all lack the field (issue
#111). Seam C is stated as a rule here and enforced only by review until each
consumer adds its own pinning test.

## Prior art

- `alibaba/open-code-review` at `14b84f08a3af7f042d702c721f21f7952d841970`
  (Apache-2.0), read for its SARIF subset with stable per-finding fingerprints,
  its typed run manifest with a closed failure enum, and its delegation packet —
  the shapes that motivated Seams A and B. Nothing copied; no dependency added.
- `DietrichGebert/ponytail` at `356918eba965ee1eac64bd3a7f0dd02108350de5`
  (MIT), read for its measurement/gate separation (`loc.js` records and always
  passes; `correctness.js` gates) and its instrument self-test discipline — the
  shape behind Seam E's refusal to decide.
