# SLICE-056 — real e2e: verdict family (gate evaluate + journal verify)

**Status:** done
**ADR:** docs/adr/ADR-032-real-e2e-suite-framework.md
**Issue:** #36 (tracker #33, milestone 4 — the ADR-032 frame's first
family customer; SLICE-055 prerequisite accepted)

## Scope — issue #36's exact ownership, nothing else

- `tests/e2e/test_gate_evaluate_real.py` — the gate-evaluate family
  journey and its frozen contracts (Worker A, committed red).
- `tests/e2e/test_journal_verify_real.py` — the journal-verify family
  journey and its frozen contracts (Worker A, committed red).
- `tests/e2e/expected/gate-evaluate-pass.out`,
  `tests/e2e/expected/gate-evaluate-fail.out`,
  `tests/e2e/expected/journal-verify-clean.out`,
  `tests/e2e/expected/journal-verify-tampered.out` — the four goldens,
  the implementation lane's artifacts, captured from real runs of the
  frozen journeys (stdout piped through
  `tests/e2e/_prereqs.py::normalize_transcript` exactly as the tests do)
  and committed green. Hand-written goldens cannot pass: the sabotage
  control and the normalizer-application contracts refuse them.

No new ADR, no frame change, no kernel semantics change, no new pytest
markers, no dependency. The verdict family rides ADR-032: the probes it
needs are none (git+python are the lane's hard tool requirements, and
openssl is this family's hard independent-re-check requirement — issue
#36 names it), the normalizer is the frame's one function, and the
comparison is the frame's comparator with the family label.

## Determination — no new ADR at open time

Issue #36's header says "ADR to be written at open time"; its workflow
checklist instead demands "ADR deltas accepted (family-specific sad
paths folded in)". ADR-032 already carries this family's frame — the
per-family golden files, the sabotage red control, the centralized
normalizer, the declared-skip grammar — and names SLICE-056 as its first
family customer, so no new ADR is written and this slice links ADR-032
(docs-discipline's open-slice rule). One ADR delta remains open for the
implementation/close lane, exactly as the checklist item says: the
rollback/truncation blind spot must be characterized in the ADR record
(issue #36's frozen input→output: "recorded honestly in the ADR, not
hidden"). The characterized behavior the frozen tests assert (verified
against the installed kernel at freeze time): deleting the last journal
row out-of-band leaves a chain that `journal verify` reports
`PASS chain=verified` over — the surviving rows are vacuously intact, so
a vanished record is invisible to the verifier. That limit is frozen as
the documented outcome in
`test_journal_verify_real.py::test_tampered_row_detection_names_the_row_and_rolls_back_honestly`
(issue #36 sad path 4: "the test asserts the documented outcome whatever
it is"); folding the characterization into the ADR is Worker B's
close-out obligation, and closing the blind spot itself is a
slice-governed change, never a quiet rebase.

## Frozen decisions carried as done-criteria contracts

Every criterion is provable by a named test in the two frozen files;
from the freeze commit on they are read-only to the implementer
(spec-prd step 6).

1. **Fail golden — absence blocks** (issue #36 deterministic gate 2,
   sad path 2): the pristine clone of this repository at HEAD — real
   `governance/gates.yaml`, real `governance/suite_manifest.json`, real
   committed keyring, no evidence at all — must FAIL `gate evaluate`
   (exit 1) with the honest-absence sentence, and the normalized
   transcript must match `expected/gate-evaluate-fail.out` byte-exactly.
   Proven by
   `test_gate_evaluate_real.py::test_fail_transcript_matches_the_golden`,
   whose stdlib-sqlite3 re-check also proves the durable journal row
   agrees with the transcript (gate, verdict, approver, missing claims).
2. **Pass golden — a real green gate on real signed evidence** (issue
   #36 deterministic gate 1): the journey's `keygen`-generated producer
   registered in the committed keyring, a committed family gate
   (`verdict-family`) whose claim binds `git status --porcelain`, the
   committed `governance/deps.yaml` removed so the subject keeps the
   kernel's documented self-contained behaviour, a real `run` of the
   bound command recording real signed evidence, and a green
   `gate evaluate` (exit 0) whose normalized transcript matches
   `expected/gate-evaluate-pass.out`. Proven by
   `test_gate_evaluate_real.py::test_pass_transcript_matches_the_golden`,
   which also freezes the evidence's honesty guards: openssl (a
   non-kernel tool) verifies the Ed25519 signature the kernel admitted;
   `run` without `RANEX_SIGNING_KEY` refuses (exit 2) and writes nothing
   (sad path 5); once the subject moves past the recorded evidence the
   evaluation FAILs with the stable reason "evidence bound to a
   different subject digest" (sad path 1).
3. **Journal clean golden** (issue #36 deterministic gate 3, first
   half): two real evaluations write a real two-row hash chain;
   `journal verify` prints the clean PASS transcript matching
   `expected/journal-verify-clean.out`; the stdlib sqlite3 module
   independently re-reads the rows and checks chain continuity as pure
   data. Proven by
   `test_journal_verify_real.py::test_clean_transcript_matches_the_golden`.
4. **Journal tampered golden + row naming** (issue #36 deterministic
   gate 3, second half; sad path 3): a single byte of row 1's record
   flipped out-of-band (inside a digest hex run, so the row stays
   parseable — the chain, not a parser, must catch it) flips `journal
   verify` to FAIL matching `expected/journal-verify-tampered.out`, and
   the FAIL transcript must NAME the row (`row`/`seq` plus its ordinal).
   Today's CLI prints only `chain=invalid` with no row identity — that
   is the frozen behavioral red; the implementation lane lands the
   naming (a presentation change: `Journal.verify`'s detection semantics
   are not trust-rule changes). Proven by
   `test_journal_verify_real.py::test_tampered_row_detection_names_the_row_and_rolls_back_honestly`,
   which also proves the edit really was one byte and freezes the
   truncation blind spot as the documented outcome (criterion above).
5. **Sabotage negative control** (issue #36 deterministic gate 5, AC2;
   ADR-032's mutate-the-golden red control): for every one of the four
   goldens, mutating a meaningful byte of the expected file must make
   the comparison diff dirty, with the failure naming the family and
   carrying exactly the first differing hunk untruncated. Proven by
   `test_gate_evaluate_real.py::test_sabotage_control_mutated_golden_diffs_dirty`
   and
   `test_journal_verify_real.py::test_sabotage_control_mutated_golden_diffs_dirty`.
   The sabotage run itself (a real mutated golden producing the red
   output) is posted on issue #36 by the implementation lane as AC2's
   proof.
6. **Normalizer application — no hand-sanitized goldens**: each golden
   must carry the normalizer's own token where the journey emits live
   volatile material (`<DIGEST>` for the real subject digests,
   `<ABS-PATH>` for the real journal path), must be a fixpoint of
   `normalize_transcript`, and a golden holding the live volatile bytes
   provably cannot match the normalized actual (demonstrated by
   substituting one live value back in and proving the comparison
   fails). Proven by both files'
   `test_goldens_carry_real_volatile_material`.
7. **Independent-tool re-check in every journey test** (issue #36 AC3):
   stdlib sqlite3 reads the journal rows the CLI reported on; openssl
   verifies a signature the kernel accepted. Folded into the
   golden-matching tests named above — no assertion-only tests exist in
   the two files, so every test is red at the freeze commit.
8. **Manifest registration at close** (issue #36 AC4): both files' test
   IDs enter `governance/suite_manifest.json` through the existing
   `ranex suite freeze` ceremony at slice close, no hand edits. The
   family declares no expected skips (determination below), so the
   freeze ceremony should register eight passing IDs and zero new
   declarations.

## Declared-skip determination — none

The verdict family runs on any host with git, python, and openssl (all
three hard requirements, failed loudly when absent — never skipped
green). No `ranex-prereq:` probe applies and no `ranex-context:`
declaration is expected. If the hermetic `suite freeze` environment at
close cannot host the journeys (unverified at freeze time — the sealed
env's behavior is an honest UNKNOWN), the sanctioned remedy is a
context-guard skip declared through the freeze ceremony (the
`nested_hermetic_self_gate` precedent in
tests/e2e/test_gating_real_suite.py), recorded then as a sanctioned
amendment — not improvised now.

## Sanctioned amendments — none

The frame exists for this family; nothing in the frozen contracts
needed an ADR-032 amendment or an issue #36 change request at freeze
time. The two implementation-lane obligations recorded above (the
row-naming presentation change, the truncation-blind-spot ADR delta)
are the issue's own demands, not amendments.

## Close-out record (2026-08-20)

- **Hermetic-freeze verification — hermetic-green.** The standing
  `ranex suite freeze` ceremony at implementation commit b4e835c00
  (clean tree, the 119 committed declarations re-declared verbatim)
  ran the full suite inside the sealed environment: **1227 passed,
  118 skipped, run_exit=0** (103.17s). Against the 41bb4fef6 ceremony
  baseline (1219 passed / 118 skipped) that is exactly +8 passed with
  the skip set unchanged — every family arm ran inside the sealed env
  and passed. No env-dependent journey; the pre-registered
  context-guard remedy was not needed and nothing was declared.
- **Ceremony** (commit dabc91f68): suite 1337 → 1345 (+8, −0 — this
  slice's two files' eight test IDs); expected_skips 119 → 119
  byte-identical. New manifest
  sha256:539315038c919050537203f6508ac76c418c43d0a0db3d7d0c24ee88300
  97139.
- **Full suite at close:** 1305 passed, 40 skipped, 0 failed
  (724.72s).
- **Red → green:** frozen red at 8931e1223 (8 failed / 0 passed);
  green through 8bdccb60d (journal-verify row naming, the issue's
  sanctioned src surface), 2e6947e36 (the four goldens captured from
  the real journeys), b4e835c00 (the truncation-fixture construction
  fix, ruling on issue #36 comment 5346068327, Option 1). The AC2
  sabotage-control red output is posted on issue #36 by the
  implementation lane.

## Follow-ups register (carried at close)

1. **ADR-032 fold-in of the truncation blind spot — RESOLVED at
   8a5ed3837.** The Determination section above assigned the
   close-out lane the obligation to fold the characterized
   rollback/truncation blind spot into ADR-032's record; the close
   lane's writable surface excluded `docs/adr/**`, so the edit
   landed as the follow-up commit 8a5ed3837 (docs(ADR-032): fold
   in the SLICE-056 truncation blind-spot characterization —
   disclosed kernel limit). ADR-032 now records the limit —
   `journal verify` proves integrity over the rows present and
   nothing more, so a journal whose last row was deleted out-of-band
   still reports `PASS chain=verified` — pinned by the frozen
   truncation layer of
   `test_journal_verify_real.py::test_tampered_row_detection_names_the_row_and_rolls_back_honestly`,
   with the closing rule that changing the semantics needs an ADR
   of its own. The characterization itself stays frozen and
   asserted as the documented outcome in that test; closing the
   blind spot itself remains a slice-governed change, never a
   quiet rebase.
2. **Mirror-pin contract test for `_journal_first_broken_row` —
   open; the next test-author follow-up (the final-gate review's
   P3).** The row-naming presentation helper landed at 8bdccb60d
   mirrors `Journal.verify`'s detection walk (same row order,
   genesis root, and recomputation) by construction, but no
   contract test yet pins that mirror: a future change to
   `Journal.verify`'s detection semantics that leaves the naming
   walk un-updated would name the wrong row silently. The next
   test-author lane adds a mirror-pin contract test so such drift
   fails loudly.
