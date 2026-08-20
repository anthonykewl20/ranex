# SLICE-058 — real e2e: provisioning family (deps fetch/approve + keygen)

**Status:** open
**ADR:** docs/adr/ADR-032-real-e2e-suite-framework.md
**Issue:** #38 (tracker #33, milestone 4 — the ADR-032 frame's third
family customer; SLICE-055 prerequisite accepted 2026-08-19)

## Scope — issue #38's exact ownership, nothing else

- `tests/e2e/test_deps_real.py` — the deps family: the real-index journey
  (real clone keeping its committed `governance/deps.yaml`, the real
  pinned resolver, the real wheel sources, a real content-addressed wheel
  store), the approve flow, the sabotage controls, and the local-index
  fixture ADR-032 sad path 12 deferred to exactly this family (Worker A,
  committed red).
- `tests/e2e/test_keygen_real.py` — the keygen family: the real `keygen`
  journey whose keys the kernel signs and accepts AND openssl verifies
  independently both ways, plus the key-material confinement gates
  (Worker A, committed red).
- `tests/e2e/expected/deps-fetch-lock.out`,
  `tests/e2e/expected/keygen-verify.out` — the two goldens, the
  implementation lane's artifacts, captured from real runs of the frozen
  journeys (transcripts piped through `_prereqs.normalize_transcript`
  exactly as the tests do) and committed green. Hand-written goldens
  cannot pass: the sabotage control and the normalizer-application
  contracts refuse them.

No new ADR, no frame change, no kernel semantics change, no new pytest
markers, no dependency. The provisioning family rides ADR-032: the probes
it needs are `pinned_resolver` and `network_available` (the deps file's
arms; the keygen file needs none), the normalizer is the frame's one
function, and the comparison is the frame's comparator with the family
label. The in-process stdlib index server with ephemeral-port binding is
the ADR-032 sad-path-12 deferred fixture — this family owns it, inside
`test_deps_real.py`, never as a conftest service abstraction.

## Determination — no new ADR at open time

Issue #38's header defers the ADR to open time; ADR-032 already carries
this family's frame — the per-family golden files, the sabotage red
control, the centralized normalizer, the declared-skip grammar, the
probes, and (sad path 12) the deferred local-server fixture this family
now owns — and names the family slices as its customers, so no new ADR is
written and this slice links ADR-032 (docs-discipline's open-slice rule).
Every kernel behavior the frozen tests assert was verified against the
installed kernel at 271344443 before freezing, in /tmp/opencode
prototypes: the real pinned-inputs fetch (25-package closure, FETCHED
transcript, fresh-store download and full-reuse shapes), approve, the
second/third fetch shapes, the sha256sum store re-hash, the wheel
byte-flip admission refusal with quarantine and the one-wheel repair
fetch, the unapproved-depset run refusal with its delta, the lock-drift
and missing-epoch-block refusals, the env-var injection being ignored
(identical depset), the local-index liar/dead refusals, the keygen
journey (kernel signs and accepts; openssl PKCS#8/SPKI sign-verify both
directions on OpenSSL 3.0.13), and every confinement refusal. No `src/`
change is demanded anywhere.

## Host-gating strategy — the frame's probe/skip grammar

The real-index arms consume `prereq_pinned_resolver` AND
`prereq_network_available` through module-scoped fixtures (issue #38
deterministic gate 5: an offline host gets the named
`ranex-prereq:network_available:` skip, never green); the local-index
sabotage arms consume `prereq_pinned_resolver` only (loopback, no
external network); the keygen file and the ungated golden-contract test
declare no skips. git, python, sha256sum, openssl, and the pinned
interpreter (`/usr/bin/python3.12`, root-owned, per the committed pins)
are hard tool requirements that fail loudly when absent. The close-time
freeze ceremony declares the observed skips with the probe grammar —
context-independent conditions the frame verifies live, both directions.

## Frozen decisions carried as done-criteria contracts

Every criterion is provable by a named test in the two frozen files; from
the freeze commit on they are read-only to the implementer (spec-prd
step 6).

1. **Fetch golden — the committed lock reproduces byte-exactly** (issue
   #38 deterministic gate 1, AC1): a real fetch on the pinned inputs
   (fresh store) prints the FETCHED transcript frozen against
   `expected/deps-fetch-lock.out` — the depset digest is the one volatile
   class (`<DIGEST>`). Proven by
   `test_deps_real.py::test_fetch_transcript_matches_the_golden`, whose
   sha256sum re-check (AC2) independently re-hashes every store entry to
   its own address and ties the entry count to the transcript's package
   count; the ungated
   `…::test_golden_contract_deps_fetch_lock` holds the golden to its
   existence/fixpoint/token contract on every host.
2. **Provisioning bookkeeping is consistent** (deterministic gates 1's
   reuse half): a second fetch reuses every wheel at an identical depset;
   `deps approve` records the human delta; a third fetch drops the
   not-yet-approved line. Proven by
   `…::test_second_fetch_approve_and_third_fetch_are_consistent`.
3. **Declared-network discipline** (AC4, sad path 8): the committed pins
   declare exactly one index and the digest-verified resolver
   (`…::test_declared_network_is_exactly_the_pinned_sources`), and a
   fetch under hostile `UV_*`/`PIP_*` injection derives byte-identically
   (the injection arm inside the journey and
   `…::test_second_fetch_approve_and_third_fetch_are_consistent`).
4. **Wheel-store sabotage control** (deterministic gate 2, AC3, sad path
   4; the approved-wheel-can-lie gate reused): a governed run over an
   approved set works (RECORDED — the control); one flipped wheel byte
   and admission refuses naming the wheel, quarantines the entry, writes
   no new evidence; only `deps fetch` repairs, re-downloading exactly the
   one wheel. Proven by
   `…::test_wheel_byte_flip_refuses_admission_and_only_fetch_repairs`
   and `…::test_unapproved_depset_refuses_before_spawn`. The sabotage red
   output is posted on #38 by the implementation lane.
5. **Lock-refusal sad paths** (sad paths 3, 7): lock drift and the
   missing epoch block (the known `--frozen` hazard) each refuse with the
   stable byte-compare reason and leave no store. Proven by
   `…::test_lock_drift_and_missing_epoch_block_refuse`.
6. **Local-index sad paths** (sad paths 1, 2; the ADR-032 sad-path-12
   fixture): a lying wheel source refuses naming the wheel; a dead source
   refuses cleanly, never partial green. Proven by
   `…::test_lying_wheel_source_refuses_naming_the_wheel` and
   `…::test_unreachable_wheel_source_refuses_never_partial_green`.
7. **Keygen golden — keys verify independently** (deterministic gate 3,
   AC2): the real `keygen` keypair signs and is accepted by the kernel
   (governed run RECORDED, `gate evaluate` PASS) AND openssl — a
   non-kernel tool — verifies both a signature it made with the private
   key over real subject material and the kernel's own evidence
   signature; the two verdict lines freeze against
   `expected/keygen-verify.out`, with the tampered-message refusal as the
   discriminating negative. Proven by
   `test_keygen_real.py::test_keygen_keys_verify_via_openssl_matching_the_golden`.
8. **Key material confinement** (deterministic gate 4, sad paths 5, 6):
   keygen refuses in-repo targets and unwritable parents leaving no
   partial material; the key is 0600 outside the tree with its private
   bytes in no tracked file; a group-readable key is refused at use.
   Proven by
   `…::test_key_material_confinement_holds`.
9. **Golden integrity contracts** (AC1; ADR-032's red control): each
   golden is a normalizer fixpoint free of leaked key material, the
   deps golden carries `<DIGEST>` where its journey emits live volatile
   material and a live-byte-doctored golden provably cannot match, the
   keygen golden is provably not matchable by the failing verification's
   outcome, and a mutated golden byte diffs dirty with the family named
   and the first hunk untruncated. Proven by both files'
   `test_goldens_carry_real_volatile_material` and
   `test_sabotage_control_mutated_golden_diffs_dirty`.
10. **Manifest registration at close** (the standing ceremony): both
    files' test IDs enter `governance/suite_manifest.json` through the
    existing `ranex suite freeze` ceremony at slice close, no hand edits;
    the probe-gated arms' observed skips are declared with the
    `ranex-prereq:` grammar per the host-gating strategy above.

## Sanctioned amendments — none

The frame exists for this family (including the deferred local-server
fixture ADR-032 sad path 12 assigns to it); nothing in the frozen
contracts needed an ADR-032 amendment or an issue #38 change request at
freeze time, and no `src/` change is demanded: every refusal, transcript,
and binding asserted was observed against the installed kernel at
271344443. The implementation lane's obligations — capturing the two
goldens from the real journeys, posting AC3's sabotage red output, and
the registration ceremony — are the issue's own demands, not amendments.
