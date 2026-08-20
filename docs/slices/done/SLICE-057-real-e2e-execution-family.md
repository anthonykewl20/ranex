# SLICE-057 — real e2e: execution family (run + confinement + suite freeze)

**Status:** done
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
  real confined spawn, the descendant-containment contract (final
  scope at 5510c7767: shell-constructed descendants die and the
  three layers are pinned to their call sites), and timeout-vs-exit
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
5. **Confinement journey — real build, spawn, containment; golden**
   (deterministic gate 3; sad paths 1, 3, 8 — sad path 3 as reframed
   by the sanctioned amendment at c981074fd, below): where
   `qualified_host` holds — real build/install/qualify, a real
   confined spawn recording evidence that binds
   `confinement_result_digest` and `confinement_profile_digest`
   (openssl-verified with those fields), the rendered confinement
   report matches `expected/confinement-report.out`; descendants of
   the confined worker are UNCONSTRUCTIBLE and containment holds BY
   CONSTRUCTION — an outside poller holds the worker cgroup leaf's
   visible membership at the direct pair through a deliberate
   fork-exec attempt, and all three construction layers are pinned
   against the launcher source that ran (mutation-verified); the REAL
   kill/drain proof — a genuine wall-time hang killed and refused over
   a drained teardown (`E-C18-LIMIT`, exit 2, no evidence) — lives in
   the timeout arm, while a confined `exit 3` propagates exactly
   (RECORDED exit=3, run exits 3). Proven by
   `test_confinement_real.py::test_strict_local_journey_matches_the_golden`,
   `…::test_descendant_processes_are_unconstructible_and_containment_is_by_construction`,
   and `…::test_timeout_refusal_is_distinct_from_the_exit_code`. Where
   the probe is absent the arms skip with the probe's named reason —
   never a silent green — and
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

## Close-out record (2026-08-20)

Closed against the nine done-criteria contracts, every one proven by
the named frozen tests at the final state. Commits this slice:
7bdcae8b2 (frozen red) → 0013bf427, f4b09b264, 128d13552 (the two
early kernel fixes + re-qualification) → d2881a2e0 (run + confinement
goldens) → 36983ae31 (blocked state) → e1e6dc8a7 (the process-creation
allowlist fix + re-pin) → 59479a1e7 (ceremony + freeze golden) → the
docs close-out.

**The three never-executed-code kernel fixes the journey forced**
(each an orchestrator-ruled amendment on #37, each a one-family
allowlist/re-pin through the f4b09b264 mechanics; the security review
gates the whole range 0013bf427…e1e6dc8a7 before push):

1. **Enrollment drain** (0013bf427): the strict-local session's
   controller leaf could not enroll on the host's delegated cgroup
   (cgroup-v2 no-internal-process rule) — `_create_worker_cgroup` now
   mirrors the qualify probe's drain (`_move_all_cgroup_processes`)
   and reverses it at teardown (`_release_controller_leaf`).
2. **Sleep family** (128d13552): `default-deny-v1` omitted
   `clock_nanosleep`, so every sleep-family observed command died
   instantly under EPERM; admitted after the strace census.
3. **Process-creation family** (e1e6dc8a7): the allowlist also omitted
   `clone`/`execve`/`wait4` + the dash id-probes
   (`getuid/getgid/geteuid/getegid/getppid`), so the survivor arm's
   dash died with "Cannot fork" (RECORDED exit=2); the eight census'd
   entries admitted. RECORDED RESIDUAL: the filter is nr-only, so
   `clone` is admitted with ANY flags (nested userns/PID-ns creation
   contained by the inheritance facts: seccomp+NNP+Landlock inherit,
   descendants stay in the PID namespace and the confined cgroup,
   cgroup.kill reaches nested namespaces, pids bounds the count); an
   argument-filtered clone is a filter redesign, ruled out of scope.

**Goldens** — run-evidence `d8c363a9`… (held from the prototype
journey, re-verified at every run-family pass, both contexts);
confinement-report `e688a37d`… (captured at artifact d9dd15b8…,
KEPT at the final artifact ea17bcae… — verified equal in-scope: the
normalized report's digests are `<DIGEST>`-tamed, so the golden is
artifact-digest-insensitive); suite-freeze-manifest `c12033d6`…
(the ceremony's own FROZEN line through the normalizer, captured at
the ceremony-sealed state per its construction).

**Delegated-scope note** (the honest host-gating record): the
confinement family's strict-local arms are proven in the DELEGATED
scope (`systemd-run --user --scope -p Delegate=yes`) — 7/7 green,
including the reframed containment arm. The frozen survivor arm was
VACUOUS — its "backgrounded worker" never existed: three independent
layers make a genuine descendant unconstructible in this profile (the
empty MS_NODEV tmpfs on /dev kills dash's async-job children pre-exec;
Landlock admits EXECUTE on exactly the six pinned objects/trees; the
worker is PID 1 of a new PID namespace the kernel reaps at init
exit), so the frozen "no survivor escapes kill/drain" claim was
unfalsifiable as written. Reframed at c981074fd (sanctioned amendment
on #37) into the falsifiable containment-by-construction contract:
the outside poller observes the worker leaf's visible membership held
at the direct pair through a deliberate fork-exec attempt, and all
three layers are pinned against the launcher source that ran —
mutation-verified (populating /dev, widening EXECUTE, or dropping
CLONE_NEWPID each redden; comment-only edits stay green). The REAL
kill/drain proof — a genuine wall-time overrun killed and refused over
a drained teardown — lives in the timeout arm. In a plain session the
five probe-gated arms skip with the live
`ranex-prereq:qualified_host: the delegated cgroup is missing
required controllers: cpu` reason — never a silent green — and the
ceremony froze exactly those five declarations (the correction-round
ceremony exchanged the retired survivor ID for the reframed arm's).

**Ceremony** (59479a1e7): the standing close ceremony re-declared the
119 committed expected-skips verbatim + the 5 new qualified_host
declarations; sealed run **1260 passed / 103 skipped / run_exit=0**
(120.65s). Manifest 1345 → **1363 IDs** (+18: run 5, confinement 7,
freeze 6), expected_skips 119 → **124**. The observed-skip count sits
below the declared count because the closure-matching host now RUNS
tests whose standing declarations date from the pre-re-qualification
drift — declared-but-passed is tolerated by the verdict's non_passed
check (the SLICE-056 ceremony's own shape).

**Full suite at close (plain session):** 1345 passed / 18 skipped /
0 failed (912.10s). Frozen suites over the final re-pin: slice017
launcher + host-qualification 47 passed; slice046 + slice047 +
slice018 + confinement-result + trace-invariance + kernel-unchanged
52 passed / 3 pre-existing skips (delegated; plain 50/5).

**Red → green:** frozen red at 7bdcae8b2 (8 failed / 5 passed /
5 skipped); the run family went green through the prototype-verified
journeys + d2881a2e0; the confinement family through 0013bf427,
128d13552, e1e6dc8a7 (its 7th arm — the survivor — green only at
e1e6dc8a7, later proven VACUOUS by the #37 experiment and reframed
into the containment-by-construction arm at c981074fd); the freeze
family green only past the 59479a1e7 ceremony (its journey arms'
designed pre-ceremony red was the stale-manifest drift the ceremony
resolves). AC2's traced event stream and AC3's sabotage red outputs
are posted on issue #37 by the close lane.

**Correction round (2026-08-20, post-close).** The security review's
vacuity finding on the survivor arm was remediated by experiment →
reframe: the #37 experiment
(/tmp/opencode/slice057-survivor/EVIDENCE.md) proved the frozen arm
vacuous by three independent layers, and the sanctioned amendment
(c981074fd) replaced it with the falsifiable
containment-by-construction contract (verified both contexts:
delegated 7/7 with the arm's own probe telemetry recorded; plain
2 passed / 5 skipped on the unchanged live reason). This round
corrected this file and docs/STATE.md, re-froze the manifest through
the standing ceremony — the sanctioned delta: suite 1363 → 1363 with
exactly one ID exchanged (`test_worker_kill_drain_leaves_no_survivor`
out, `test_descendant_processes_are_unconstructible_and_containment_
is_by_construction` in), expected_skips 124 → 124 with the same pair
exchanged (the reframed arm stays probe-gated under the identical
qualified_host reason) — and re-verified the full suite and the
confinement golden's byte-equality at the final artifact.

**Final-gate round (2026-08-20, post-correction).** The codex final
gate's three P1 remediations and P2 record corrections landed:
P1-2/P1-3 at 5510c7767 (the descendant arm rescoped to its proven
claim — `test_shell_constructed_descendants_die_and_the_layers_are_
pinned`, the three layers pinned to their CALL SITES by the
string-aware per-function scanner, mutation-sanity red on call
removal with definitions intact; the poller's `_stop` shadow renamed
`_stop_event`, process stderr clean in both contexts); P1-1 at
b82c081c8 (the standing ceremony: the rescoped arm's ID exchanged in
both maps, and all five confinement declarations reclassified
`ranex-prereq:qualified_host:` → `ranex-context:host-capability:` per
this file's recorded host-gating strategy — the live limitation
varies by host and the arms legitimately run on qualified hosts, so
prereq-tier would hard-fail both directions off this host; sealed run
1260/103/run_exit=0, lint green, the entrypoint cross-check
informational thereafter). P2s: this file's and STATE's
writable-EXECUTE residual timeline corrected (live since the execveat
admission at 321cb524d, pre-e1e6dc8a7 — openat+execveat; e1e6dc8a7's
execve widened the surface further), README's next-slice line and
retired kill/drain-survivor wording corrected. Final state: full
suite 1345 passed / 18 skipped / 0 failed (794.45s); delegated
confinement module 7/7 (20.31s); all three goldens byte-verified at
the final state.

## Follow-ups register (carried at close)

1. **Argument-filtered `clone` — open, security-review-owned.** The
   recorded residual of the e1e6dc8a7 amendment: `default-deny-v1`
   admits clone nr-only (any flags). Masking the entry to the census'd
   flags (CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD) is a BPF
   filter redesign, ruled out of scope; the review gating the range
   owns the decision.
2. **Writable-tree full-mask EXECUTE — LIVE residual, recorded (the
   security review's MINOR-4).** The launcher's Landlock grants for
   the output and scratch trees carry the full filesystem mask
   including EXECUTE — pre-existing since the profile's first pin,
   and LIVE since the execveat admission, BEFORE e1e6dc8a7: openat
   and execveat were both admitted from the first pinned filter, so
   a confined worker could already exec a binary it wrote itself
   into a writable tree by fd (openat + execveat AT_EMPTY_PATH).
   e1e6dc8a7's execve admission widened the surface further — plain
   pathname exec of a self-written binary — both facts recorded here.
   Contained: the executed code sheds nothing (seccomp + no_new_privs
   + Landlock + PID-ns + cgroup all inherit), so it stays inside the
   same confinement — in-sandbox execution only, no escape. Recorded
   beside residual 1 (same review owns both); masking EXECUTE off the
   writable trees is a profile change for a future slice.
3. **Availability notes — fail-closed, recorded (the security
   review's MINOR-1/MINOR-5).** (a) A launcher/controller crash
   between enrollment and teardown wedges the controller leaf until
   operator cleanup — the next session refuses `E-C18-HOST-DRIFT`
   rather than running degraded (fail closed, not silent). (b)
   Concurrent confinement sessions in one delegated scope interfere
   (the qualification binds one delegation identity); serialized
   sessions are the standing practice. Both are availability limits,
   not escapes.
4. **Mirror-pin contract test for `_journal_first_broken_row` —
   open** (carried from the SLICE-056 close; unchanged).
5. **SLICE-055 follow-ups** — stay queued in its done slice file.
