# SLICE-074 — kill-safe command ownership

**Status:** open
**Opened:** 2026-08-28
**Priority:** P0 — stop invisible governed work after kernel death
**Issue:** #53
**ADR:** `docs/adr/ADR-037-kill-safe-command-ownership.md`

## Contract

Implement ADR-037 for non-confined `run` and `suite freeze`. A real governed
command must not outlive a SIGKILLed kernel. Admission requires structured raw
status, outer-process completion, PID-namespace drain, and exact-root cleanup.
Unsupported lifecycle primitives refuse before the command starts.

## Owned paths

- ADR-037, its prior-art directory, this slice, README, and `docs/STATE.md`
- `src/ranex/cli/main.py`
- `src/ranex/cli/process_supervisor.py`
- `src/ranex/cli/subject.py`
- `src/ranex/cli/toolchain.py` only if the verified preflight owner requires it
- lifecycle security, integration, and real-run e2e tests

## Done criteria

1. A frozen real CLI regression kills the kernel during the committed landing
   command and proves its uv, pytest, nested Ranex, strace, compiler, and
   background descendants plus exact scratch root disappear without evidence.
2. Frozen handoff tests prove the command cannot exec before PID-1 identity and
   exact-byte start-gate release; pre-identity guardian death stays a named
   residual rather than a cleanup PASS.
3. Post-identity kernel and guardian crash paths send SIGKILL directly through
   the saved PID-1 pidfd, wait that pidfd, and treat dedicated-group killing as
   supplemental.
4. Explicit exit 143 remains distinct from SIGTERM, and malformed, absent,
   truncated, duplicate, or child-controlled status refuses without evidence.
5. Result admission follows raw wait status, outer-process completion,
   PID-namespace drain, and the existing exact-root cleanup in that order.
6. Installed bubblewrap is feature-probed with the accepted literal mount argv;
   absence, replacement, or unusable namespaces refuse before command effects.
7. Overlapping real runs retain separate lifelines, pidfds, channels, process
   groups, and roots; one owner cannot kill or delete the other run.
8. Focused security/e2e tests, documentation contract, canonical suite, and a
   destructive real current-main replay pass without weakening existing gates.

## Stable refusal order

Lifecycle preflight → guardian identity handoff → relay start gate → command →
raw status → outer completion → PID-1 drain → exact-root cleanup → admission.

## Not owned

No strict-local controller-crash claim, delegation or harness-lane change,
production action, same-UID malicious scratch-rename defense, or claim that
simultaneous kernel+guardian SIGKILL and pre-identity guardian SIGKILL are safe.

## Verification

```text
uv run --frozen pytest -q tests/security/test_slice004_hermetic_observation.py
uv run --frozen pytest -q tests/e2e/test_run_real.py
uv run --frozen pytest -q tests/integration/test_deps_commands.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen pytest -q
```

The failure was first reproduced with the real committed landing command in a
disposable current-main clone. Regression tests are frozen RED before runtime
implementation and must clean any deliberately orphaned process tree in their
own teardown.
