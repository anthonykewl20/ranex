# SLICE-057 — real e2e: execution family (run + confinement + suite freeze)

**Status:** open
**ADR:** docs/adr/ADR-032-real-e2e-suite-framework.md
**Issue:** #37 (tracker #33, milestone 4 — the ADR-032 frame's second
family customer; SLICE-055 prerequisite accepted 2026-08-19)

## Scope — issue #37's exact ownership, nothing else

- `tests/e2e/test_run_real.py` — the run family: real journeys over
  `ranex run` producing real signed evidence on a real clone of this
  repository, the post-run sabotage controls, and the traced-run
  observability artifact (Worker A, committed red).
- `tests/e2e/test_confinement_real.py` — the confinement family: the
  launcher build-drift/reproducibility contract (SLICE-017 gate 1's
  shapes), and — where the host qualifies — real build/install/qualify,
  real confined spawn, kill/drain survivor detection, and timeout-vs-exit
  distinct reporting (Worker A, committed red).
- `tests/e2e/test_suite_freeze_real.py` — the freeze family: the real
  hermetic `suite freeze` round-trip on the committed tree, the
  dirty-tree refusal, and the manifest hand-edit load refusal
  (Worker A, committed red).
- `tests/e2e/expected/run-evidence.out`, `tests/e2e/expected/suite-freeze-manifest.out`,
  `tests/e2e/expected/confinement-report.out` — the three goldens, the
  implementation lane's artifacts, captured from real runs of the frozen
  journeys (transcripts piped through `_prereqs.normalize_transcript`
  exactly as the tests do) and committed green. Hand-written goldens
  cannot pass: the sabotage control and the normalizer-application
  contracts refuse them.

No new ADR, no frame change, no kernel semantics change, no new pytest
markers, no dependency. The execution family rides ADR-032: the probe it
needs is `pinned_resolver` (the freeze journey) and `qualified_host` (the
strict-local arms), the normalizer is the frame's one function, and the
comparison is the frame's comparator with the family label.

## Determination — no new ADR at open time

Issue #37's header defers the ADR to open time; ADR-032 already carries
this family's frame — the per-family golden files, the sabotage red
control, the centralized normalizer, the declared-skip grammar, and the
`qualified_host`/`pinned_resolver` probes — and names the family slices
(SLICE-056+) as its customers, so no new ADR is written and this slice
links ADR-032 (docs-discipline's open-slice rule). Every kernel behavior
the frozen tests assert was verified against the installed kernel at
e84b5176a before freezing, in /tmp/opencode prototypes: the run journey
(keygen → registration → run → evaluate PASS, stdlib subject-digest
recompute, openssl Ed25519 verification, both sabotage refusals with
their stable reasons, the traced stderr/file arms with verdict
neutrality), the launcher-build drift refusal (two roots, both
`E-C17-BUILD-INPUT-DRIFT`, no partial artifacts), the real-tree freeze
round-trip (byte-stable against the committed manifest,
`53931503…97139`, run_exit=0, 99s sealed), and the dirty-tree and
manifest-hand-edit refusals. The strict-local arms that need a qualified
host (spawn, kill/drain, wall-time refusal, exit-code propagation) are
frozen from the already-proven shapes frozen by
tests/security/test_slice046_cmd_run_confinement.py (real-session
signing, refusal propagation without evidence),
tests/integration/test_slice017_native_launcher.py (gate 1 both
branches), and tests/security/test_slice018_cgroup_output_lifecycle.py
(E-C18-LIMIT kill-and-refuse); they first execute for real on a
qualified host — an honest UNKNOWN until then, disclosed here rather
than assumed away.

## Host-gating strategy — the frame's probe/skip grammar

This host (and any host whose pinned launcher build closure drifts)
cannot run the strict-local arms. Those arms consume the frame's
`qualified_host` probe through the module-scoped
`prereq_qualified_host` fixture (tests/e2e/conftest.py): the skip
reason is the probe's live machine-greppable
`ranex-prereq:qualified_host: <limitation>` message, and the
assertions run when capable. Per the classification honesty rule (the
R1d ruling's census precedent), the multi-context manifest's standing
classification for exactly these conditions is
`ranex-context:host-capability:` — the live limitation string varies by
host, so an exact-byte `ranex-prereq:qualified_host:` declaration
cannot hold across hosts, and a probe-backed declaration would
hard-fail direction (b) on every qualified host. The close-time freeze
ceremony declares the observed skips accordingly; the freeze family's
journey declares `ranex-prereq:pinned_resolver:` semantics by
consuming the `prereq_pinned_resolver` fixture (a context-independent,
probe-verifiable condition — the model use of the frame).

## Frozen decisions carried as done-criteria contracts

Every criterion is provable by a named test in the three frozen files;
from the freeze commit on they are read-only to the implementer
(spec-prd step 6).

1. **Run golden — evidence produced and subject-digest-bound** (issue
   #37 deterministic gate 1): the real `run` of the family gate's bound
   command on the real clone records signed evidence
   (`governance/evidence.json` present, exit 0, claim/producer bound),
   the record's subject digest equals a pure-stdlib recompute (json +
   hashlib over `git rev-parse HEAD^{tree}` — no kernel import), and
   openssl independently verifies the Ed25519 signature. The normalized
   RECORDED transcript matches `expected/run-evidence.out` byte-exactly.
   Proven by `test_run_real.py::test_run_transcript_matches_the_golden`.
2. **Sabotage control — post-run evidence tamper** (deterministic gate
   2, AC3, sad path 4): evidence removed post-run → `gate evaluate`
   FAILs (exit 1) naming the absent claim; evidence swapped between two
   real subjects → the evaluation FAILs (exit 1) with the stable reason
   `evidence bound to a different subject digest`. Proven by
   `test_run_real.py::test_post_run_sabotage_controls_refuse`.
3. **Traced-run artifact + verdict neutrality** (AC2, sad path 7; the
   SLICE-054 invariance contract reused): one full traced run with
   `RANEX_TRACE_EVENT=1` — the stderr event stream is version-first and
   carries the run group's stage events (`cli.run.start`,
   `cli.run.end` with `exit:0`); a file target outside every governed
   root keeps the run's stderr byte-empty, receives the same stream,
   and leaves stdout and evidence.json bytes identical to the untraced
   baseline. Proven by
   `test_run_real.py::test_traced_run_is_an_artifact_and_verdict_neutral`.
   The close lane posts the captured event stream on #37 as AC2's
   observability artifact.
4. **Confinement build contract — drift or reproducibility** (gates 3,
   5; sad path 2; SLICE-017 gate 1's shapes): two launcher builds in
   two different absolute roots either prove byte-equality and manifest
   artifact-digest agreement (build closure matches) or both refuse
   `E-C17-BUILD-INPUT-DRIFT` with no partial artifact (foreign host —
   the honest contract this host observes). Proven by
   `test_confinement_real.py::test_two_root_launcher_builds_drift_or_reproduce`.
5. **Confinement journey — real build, spawn, kill/drain; golden**
   (deterministic gate 3; sad paths 1, 3, 8): where `qualified_host`
   holds — real build/install/qualify, a real confined spawn recording
   evidence that binds `confinement_result_digest` and
   `confinement_profile_digest` (openssl-verified with those fields),
   the rendered confinement report matches
   `expected/confinement-report.out`; a backgrounded child that
   outlives its parent leaves no survivor (the result validates only
   over a drained teardown — the test is red on a survivor); a
   wall-time hang refuses `E-C18-LIMIT` (exit 2, no evidence) while a
   confined `exit 3` propagates exactly (RECORDED exit=3, run exits 3).
   Proven by
   `test_confinement_real.py::test_strict_local_journey_matches_the_golden`,
   `…::test_worker_kill_drain_leaves_no_survivor`, and
   `…::test_timeout_refusal_is_distinct_from_the_exit_code`. Where the
   probe is absent the arms skip with the probe's named reason — never
   a silent green — and
   `…::test_golden_contract_confinement_report` still holds the golden
   to its existence/fixpoint/token contract on every host.
6. **Freeze round-trip byte-stable** (deterministic gate 4, AC4): the
   standing `suite freeze` ceremony shape run on the real committed
   tree (declarations derived verbatim from the committed manifest,
   `--output` under the ignored `.local/` home) reproduces the
   committed `governance/suite_manifest.json` bytes exactly; drift is
   the named red (the manifest is stale for the tree — the ceremony
   must re-freeze). The normalized FROZEN line matches
   `expected/suite-freeze-manifest.out`. Proven by
   `test_suite_freeze_real.py::test_manifest_round_trip_is_byte_stable`
   and `…::test_frozen_transcript_matches_the_golden`. A sealed
   materialisation environment is the recursion boundary: the journey
   detects it (the frozen `nested_hermetic_self_gate` shape) and the
   arms pass by proving the boundary instead of recursing.
7. **Freeze sad paths** (sad paths 5, 6): a dirty tree refuses the
   freeze with the stable reason (`refusing to freeze against a dirty
   working tree`, no output written); a hand-edited manifest (non-
   canonical bytes, or an expected-skip naming an absent ID) is refused
   at load by `gate evaluate` (exit 2, stable reasons). Proven by
   `test_suite_freeze_real.py::test_dirty_tree_freeze_refuses_with_stable_reason`
   and `…::test_manifest_hand_edit_is_refused_at_load`.
8. **Golden integrity contracts** (AC1; ADR-032's red control): each
   golden carries the normalizer's own token where its journey emits
   live volatile material (`<DIGEST>` for run-evidence and
   confinement-report, `<ABS-PATH>` for suite-freeze-manifest), is a
   normalizer fixpoint, a golden holding live volatile bytes provably
   cannot match, and a mutated golden byte diffs dirty with the family
   named and the first hunk untruncated. Proven by the
   `test_goldens_carry_real_volatile_material` and
   `test_sabotage_control_mutated_golden_diffs_dirty` tests in all
   three files (the confinement file's golden-contract test runs
   ungated so the golden is held to its contract on every host).
9. **Manifest registration at close** (the standing ceremony): the
   three files' test IDs enter `governance/suite_manifest.json` through
   the existing `ranex suite freeze` ceremony at slice close, no hand
   edits; the confinement arms' observed skips are declared at the
   context tier per the host-gating strategy above, and the freeze
   family's journey declaration is probe-backed.

## Sanctioned amendments — none

The frame exists for this family; nothing in the frozen contracts
needed an ADR-032 amendment or an issue #37 change request at freeze
time, and no `src/` change is demanded: every refusal, transcript, and
binding asserted was observed against the installed kernel at e84b5176a
(run family, drift arm, freeze round-trip, both freeze sad paths) or is
frozen from shapes the existing suites already prove on qualified
hosts (the strict-local arms, disclosed above). The close lane's
obligations — capturing the three goldens from the real journeys,
posting AC2's traced event stream and AC3's sabotage red output, and
the registration ceremony — are the issue's own demands, not
amendments.
