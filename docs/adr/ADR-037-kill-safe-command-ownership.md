# ADR-037 — kill-safe command ownership

**Status:** accepted
**Date:** 2026-08-28
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-074-kill-safe-command-ownership.md`

## Context and Problem Statement

A real current-main operator journey registered a real producer, approved the
real 26-wheel lock, and ran the committed full landing command. SIGKILL of the
`ranex run` kernel process left uv, pytest, nested Ranex, strace, GCC, and cc1
alive under PID 1. Evidence was absent, but governed execution continued and the
verified `/tmp/ranex-subject-*` tree remained. In-process cleanup cannot run
after SIGKILL. The kernel therefore needs an external lifecycle owner that
survives kernel death, plus a live-kernel fallback after identity handoff.

## Decision Drivers

- Governed execution must not outlive the kernel invisibly.
- Kernel death, terminal loss, guardian crash, and normal exit are distinct.
- Descendants that fork or create a new session must remain owned.
- No evidence is durable until raw wait status, namespace drain, and cleanup complete.
- The exact command return code and existing hermetic environment stay stable.
- Missing lifecycle support refuses before the governed command starts.
- Real Ranex history and the committed landing command are the proof corpus.

## Prior art

- Searched: GitHub code search and installed-source inspection for parent-death signals, PID-namespace init reaping, process-group supervisors, subreapers, lifeline pipes, cgroup kill, and crash-safe resource cleanup.
- https://github.com/containers/bubblewrap/blob/8e51677abd7e3338e4952370bf7d902e37d8cbb6/bubblewrap.c combines `PR_SET_PDEATHSIG`, a PID namespace, and a PID-1 monitor so monitor death kills the namespace rather than only one process.
  License: LGPL-2.0-or-later.
  Weakness: it is an external Linux host dependency and its mount namespace can change runtime behavior unless Ranex deliberately binds the existing root view.
  Vendored: `docs/adr/prior-art/ADR-037/bubblewrap.c` blob:9b78a9ae30dd8f3361f95ae0132d1c32a4ac3329
- https://github.com/bazelbuild/bazel/blob/b352e52393ab2722204c2d06d065c4bdf9a1df6d/src/main/tools/process-wrapper-legacy.cc starts a session, acts as a Linux subreaper, kills the process group, reaps descendants, and preserves the child's exit status.
  License: Apache-2.0.
  Weakness: SIGKILL of the wrapper bypasses its handlers and can still orphan the process group, which is the Ranex failure being fixed.
  Vendored: `docs/adr/prior-art/ADR-037/bazel-process-wrapper-legacy.cc` blob:664f272ddc0c0a2e5189e9b7d2a1492a9cf38564
- https://github.com/sudo-project/sudo/blob/172cbd968e6fe5f64d3384896a90c0a1aa73238d/src/exec_monitor.c keeps structured command status outside the observed command and distinguishes exit, signal, and exec failure.
  License: ISC.
  Weakness: its same-UID status channel is not cryptographically authenticated, and it does not prove PID-namespace drain or scratch cleanup.
  Vendored: `docs/adr/prior-art/ADR-037/sudo-exec_monitor.c` blob:c5c4a14b6cca0925cc422c0d1f90042a9b51f1e9
- Rejected: https://github.com/systemd/systemd/tree/main/src/core A transient user service owns a cgroup strongly, but a client process disappearing does not itself stop that service, and user-manager availability is not the kernel's current host contract.
- Rejected: https://github.com/krallin/tini Tini reaps and forwards signals inside a container, but killing Tini outside a PID namespace does not provide the parent-death plus whole-tree destruction guarantee required here.

## Considered Options

1. Add `finally` cleanup or a SIGTERM handler. Rejected: SIGKILL runs neither.
2. Start only a new process group and call `killpg`. Rejected: the kernel cannot
   call it after death, and a descendant can call `setsid`.
3. Use only `PR_SET_PDEATHSIG` on the command. Rejected: the setting is cleared
   across fork and kills one process, not its descendants.
4. Use systemd as a durable cgroup owner. Rejected for this path: ADR-023/024
   already refuse that new broker boundary, and fresh-clone user managers vary.
5. Use a lifeline guardian, bubblewrap PID namespace, trusted wait relay, and
   explicit kernel fallback, with dual-death recorded rather than hidden. Chosen.

## Decision Outcome

The kernel starts a single-threaded guardian, which launches bubblewrap in a dedicated process group without `--new-session`. Exact flags include
`--bind / /`, `--dev-bind /dev /dev`, `--proc /proc`, `--unshare-pid`, `--die-with-parent`, `--block-fd`, and JSON status.
PID 1 stays blocked before `setsid` while pidfds transfer and ACK; a separate
kernel-owned relay gate requires byte `1`, with EOF/error forbidding command exec.
The relay restores the sealed environment and reports raw exited/signalled/exec
status. Admission waits for status, bwrap, PID-1 pidfd, then exact-root cleanup.
After identity transfer, either survivor sends SIGKILL through the saved PID-1 pidfd and waits it; dedicated-group killing is only supplemental.

| process | session/group | ownership fact |
|---|---|---|
| kernel | operator | holds lifeline/start-gate writers and fallback pidfds |
| guardian | new session, own group | lifeline reader and normal cleanup owner |
| bwrap/PID1/relay | guardian session, dedicated group | blocked until pidfds ACK |
| command | PID namespace; may call `setsid` | cannot escape namespace drain |

### Consequences

- Good: kernel SIGKILL closes the lifeline; a live guardian drains and cleans.
- Good: nested sessions cannot escape the lifecycle boundary.
- Good: guardian death after identity transfer has a live-kernel pidfd fallback.
- Good: evidence publication remains after execution and cleanup.
- Bad: non-confined `run` and `suite freeze` now require working bubblewrap and
  unprivileged or setuid namespace support; absence is a loud refusal.
- Bad: this is lifecycle containment, not new filesystem or network confinement.
- Bad: guardian SIGKILL before identity transfer, and simultaneous kernel+
  guardian SIGKILL, can leave setup processes or scratch; both are UNVERIFIED.
- Bad: strict-local's separate cgroup/controller crash path remains separately
  measured and is not relabelled green by this decision.

### Confirmation

A real CLI test kills the kernel during the committed full landing command and
observes real descendants and exact scratch disappear with no evidence. Separate
tests kill the guardian at every handoff phase and at steady state while the
kernel lives; pre-identity proves no command exec but retains a named residual.
They distinguish explicit exit 143 from SIGTERM and wait on the PID-1 pidfd
while a background writer remains, and prove cleanup precedes result admission.
Dual kernel+guardian SIGKILL is recorded as a residual, never a passing arm. The
canonical suite and another destructive current-main replay are the final gate.

## Improvements on the prior art

1. Combine an EOF lifeline with bubblewrap's PID namespace while refusing to
   treat its racy parent-death signal as the readiness or drain proof.
2. Add sudo-style structured raw wait status and a PID-1 pidfd barrier, avoiding
   bubblewrap's ambiguous 128-plus-signal status.
3. Bind cleanup to the exact materialisation owned by that invocation; never
   scan and delete another concurrent Ranex session's scratch tree.
4. Give the live kernel a guardian-crash fallback and state simultaneous
   uncatchable death as a residual instead of promising impossible cleanup.

## Architecture surface

`main.py` keeps policy; `process_supervisor.py` owns mechanics; `subject.py`
keeps the one cleanup implementation. Descriptor ownership is closed:

| channel | kernel | guardian | bwrap/relay | command |
|---|---|---|---|---|
| lifeline | write | read | closed | closed |
| control/readiness/release | endpoint | endpoint | block-fd | closed |
| relay start gate | write | closed | relay reads | closed |
| bwrap status | closed | read | bwrap writes | closed |
| raw wait status | closed | read | relay writes | closed |
| executable | read | read | relayed read | exec-only read |

## Scope and threat delta

Guardian and bubblewrap receive responsibility for the command and scratch root;
their same-UID host authority is not reduced. No additional key, journal,
evidence, approval, or repository descriptor/environment authority enters the child. Explicit
mounts preserve the needed root/dev view and make `/proc` namespace-correct, so
observable PID and mount facts change. A malicious same-UID command can rename
scratch or attack its owner; that remains outside this non-confinement boundary.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Ownership | kernel receives SIGKILL | zero live namespace descendants |
| Recovery | kill during real landing suite | exact scratch root removed |
| Honesty | lifecycle primitive absent | refusal before command side effect |
| Fidelity | explicit 143 vs SIGTERM | distinct raw structured outcomes |
| Concurrency | two real runs overlap | each guardian removes only its root |

## Reversibility

Door: two-way

The service can be removed and direct spawn restored mechanically, but doing so
reopens issue #53. Replacement must prove the same lifeline, descendant, raw-
status, PID-1-drain, fallback, and exact-root cleanup contract.

## Sad paths

- Bubblewrap is missing, writable, replaced, or cannot pass the exact real feature probe → refuse before subject materialisation.
- Kernel dies before guardian readiness → guardian observes lifeline EOF,
  SIGKILLs the dedicated bwrap group, waits/drains it, and cleans its exact root.
- Kernel dies after identity transfer while uv, pytest, or a compiler runs →
  guardian sends SIGKILL directly through the saved PID-1 pidfd, supplements
  it with dedicated-group SIGKILL, waits the PID-1 pidfd, and publishes no
  evidence.
- Guardian dies before bwrap/PID1 identity transfer → start gate forbids command exec; setup-process/scratch cleanup is UNVERIFIED.
- Guardian dies after identity transfer but before ACK or block release → PID 1
  is held before `setsid`; kernel sends SIGKILL directly through the saved PID-1
  pidfd, supplements it with dedicated-group SIGKILL, waits the PID-1 pidfd,
  then cleans.
- Guardian dies after readiness while kernel lives → kernel sends SIGKILL
  directly through the saved PID-1 pidfd, supplements it with dedicated-group
  SIGKILL, waits the PID-1 pidfd, then cleans.
- Kernel and guardian receive SIGKILL together → UNVERIFIED residual; never report cleanup or containment PASS.
- A descendant forks, double-forks, or calls `setsid` → it remains inside the PID namespace and dies with PID 1.
- Explicit exit 143 and SIGTERM → relay reports distinct exited/signalled records and legacy return codes remain exact.
- Command leader exits while a background writer remains → no result admission until PID-1 pidfd signals namespace-init death.
- Result channel is absent, duplicated, truncated, malformed, or names another child → refuse and publish no evidence.
- Scratch deletion hits read-only descendants → the one existing permission-repair cleanup runs before any result is admitted.
- Scratch deletion still fails → guardian reports cleanup refusal; parent writes no evidence.
- Guardian dies during cleanup → live kernel becomes the only fallback remover; no concurrent deletion occurs.
- Two runs overlap → distinct lifelines, namespaces, result channels, and exact roots cannot kill or delete each other.
- Child attempts to inherit lifeline, control, or raw-status read authority → explicit endpoint allowlists prevent it.
- Relay start gate closes without exact byte `1` → relay refuses without executing the governed command.
- Bubblewrap adds `PWD` or another ambient variable → relay replaces the whole child environment with the sealed pre-bwrap mapping.
- Child renames scratch or attacks same-UID guardian → outside non-confinement threat boundary; residue is not claimed absent.
- Strict-local controller is killed → remains UNVERIFIED by this slice and cannot borrow the non-confined PASS.

## Test strategy

`tests/security/test_slice004_hermetic_observation.py` is extended to freeze the
endpoint/FD table, bwrap preflight and mount argv, exit-143 versus SIGTERM,
four block-fd/start-gate handoff kill points, PID-1 pidfd drain, guardian fallback, and
ordered exact-root cleanup. It drives a current-tree helper that double-forks, calls `setsid`, and
keeps writing after its leader exits.
`tests/e2e/test_run_real.py` repeats the operator run and recovery journey.
`tests/integration/test_deps_commands.py` keeps
the real approved wheel path intact. `tests/contract/test_docs_discipline.py`
and the canonical full suite remain mandatory.

## Code review checklist

- Verify exact bubblewrap flags omit `--new-session`; probe `/dev`, namespace `/proc`, cwd, environment, and executable FD on installed 0.9.0.
- Verify an endpoint table makes kernel the sole lifeline writer, guardian the sole reader, and relay the sole raw-status writer.
- Verify exit 143 differs from SIGTERM and child bytes cannot enter the structured status channel.
- Verify PID-1 pidfd readiness and cleanup both precede result/evidence admission.
- Verify relay gate EOF never execs and pre-identity guardian death remains a residual, not PASS.
- Verify kernel and guardian SIGKILL separately; keep simultaneous death residual.
- Verify no strict-local or same-UID security claim is inferred from this slice.
- Verify frozen tests, gate commands, signing, and trust-root controls are not weakened.

## More Information

Issue #53 carries the PID/PGID reproduction from the real current-main landing
command and the independent absence/materialisation observations. ADR-023 and
ADR-024 remain the strict-local controller boundary; this decision hardens the
non-confined hermetic path found broken and records strict-local as separate.
