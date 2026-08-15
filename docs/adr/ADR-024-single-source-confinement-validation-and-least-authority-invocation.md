# ADR-024 — single-source confinement validation and least-authority invocation

**Status:** proposed
**Date:** 2026-08-15
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-047-confinement-hardening.md`

## Context and Problem Statement

SLICE-046 validates a confinement result in `main.py`, while its producer has a
weaker local check in `host_confinement.py`. The controller also inherits the
signer's ambient environment and a timeout does not explicitly kill its process
group. These are authority and validation-drift risks at the binding boundary.

## Decision Drivers

- One closed result contract must be enforced by both emitter and consumer.
- The controller receives only inputs it demonstrably needs.
- A timeout must reap the controller process group before refusal.
- Existing E-C18 result surfaces and strict-local evidence binding stay stable.
- Failures write no evidence and do not silently inherit new authority.

## Prior art

- Searched: GitHub code search for process environment allowlists, `Cmd.Env`,
  process-group timeout cleanup, and canonical result validation.
- [sudo `plugins/sudoers/env.c` at SUDO_1_9_16p2, commit 172cbd968e6fe5f64d3384896a90c0a1aa73238d](https://github.com/sudo-project/sudo/blob/172cbd968e6fe5f64d3384896a90c0a1aa73238d/plugins/sudoers/env.c)
  starts `rebuild_env()` empty and selectively admits variables (885–940);
  `initial_badenv_table` denies loader poisoning (138).
  License: ISC (verified from LICENSE.md blob:0aa321defd7fcfc09ea3a99f4a164a287b82862f).
  Weakness: configuration glob patterns can re-admit hazards; correctness rests
  on administrator patterns rather than a task-derived fixed allowlist.
  Vendored: docs/adr/prior-art/ADR-024/sudo-env.c blob:95558e9edfa457f5b3a8e5665f5d80e3d21f59ce
- [Go `src/os/exec/exec.go` at go1.22.5, commit 8e1fdea8316d840fd07e9d6e026048e53290948b](https://github.com/golang/go/blob/8e1fdea8316d840fd07e9d6e026048e53290948b/src/os/exec/exec.go)
  documents that nil `Cmd.Env` inherits the current environment (161–169) and
  deduplicates duplicate environment keys.
  License: BSD-3-Clause (verified from LICENSE blob:6a66aea5eafe0ca6a688840c47219556c552488e).
  Weakness: nil inheritance is the leak removed here; its string environment is
  not a checkable minimal authority set and cannot choose one for this task.
  Vendored: docs/adr/prior-art/ADR-024/go-exec.go blob:a52b75f69cde0fa2a007268486e3c0268c446e7e
- Cross-reference, not re-vendored: ADR-023 `bubblewrap.c`
  (blob:f8728c7e127838201061318c32ee42fe4533eeae) and `sudo-exec_monitor.c`
  (blob:c5c4a14b6cca0925cc422c0d1f90042a9b51f1e9) cover monitor lifecycle.
- Rejected: https://github.com/systemd/systemd `src/core/execute.c` makes PID 1
  the broker trust boundary, already rejected by ADR-023, with an unbounded
  footprint unrelated to this child invocation.
- Rejected: https://github.com/openbsd/src `usr.bin/doas/parse.c` relies on
  OpenBSD `setusercontext` semantics, which are not composable with this Linux
  controller or its existing qualified session contract.

## Considered Options

1. Shared foundation validator plus fixed controller environment: chosen.
2. Retain duplicated producer and consumer checks: rejected; they already drift.
3. Configurable environment filtering: rejected; it expands authority by policy.
4. `systemd-run` environment isolation: rejected; it adds the broker boundary.

## Decision Outcome

Move the closed result validation to `foundation.confinement_result`; the
producer delegates and maps its error back to `HostConfinementError`. Invoke the
controller with only PATH, source PYTHONPATH, LC_ALL, and TZ; timeout kills and
reaps its process group, then refuses as `E-C46-CONTROLLER`.

null confinement digests record an unconfined run — explicit absence, never
forged presence.

### Consequences

- Result bytes are rejected consistently at emission and consumption.
- `E-C18-RESULT` remains the existing result-validation vocabulary.
- `E-C46-CONTROLLER` names only the new timeout refusal class.
- A missing future environment dependency fails loudly rather than inheriting.
- A killed controller can leave an unreconciled worker cgroup leaf; refusal is
  fail-closed, while active reconciliation is deferred.

### Confirmation

Frozen tests in `tests/unit/test_confinement_result.py` and
`tests/security/test_slice047_confinement_hardening.py` prove the new contract.
`tests/security/test_slice046_cmd_run_confinement.py` remains a green binding
pin; `tests/integration/test_slice018_confinement_session.py` keeps gate8 error
mapping and `tests/integration/test_slice017_native_launcher.py` pins main.py.

## Improvements on the prior art

1. Unlike sudo configuration patterns, the exact environment is task-derived
   and has no ambient keep-list.
2. Unlike nil `Cmd.Env`, the allowlist is inspectable and testable by key set.
3. Unlike monitor-only lifecycle reports, one validator accepts the exact result
   schema before either emission or signing.

## Architecture surface

Add `src/ranex/foundation/confinement_result.py`. `main.py` imports it for
consumption; `host_confinement.py` imports it for emission and preserves its
local exception surface. No `src/` module imports `host_confinement`.

## Scope and threat delta

This hardens the SLICE-046 child binding, not evidence format or claim meaning.
It reduces signer-secret environment exposure and result-validator divergence.
Controller same-uid trust, host compromise, and cgroup reconciliation remain
outside this slice.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Integrity | malformed result | E-C18-RESULT before evidence |
| Least authority | secret ambient variable | absent from controller env |
| Reliability | controller timeout | kill/reap then E-C46-CONTROLLER |

## Reversibility

Door: two-way

No evidence format changes. The allowlist and validator module can be revised
under a later ADR, but fallback ambient inheritance is not an acceptable rollback.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 1 | non-hex producer runtime digest | refuse at emission |
| 2 | producer non-int exit code | refuse at emission |
| 3 | result bytes non-canonical | E-C18-RESULT refusal |
| 4 | teardown incomplete | E-C18-RESULT refusal |
| 5 | `RANEX_SIGNING_KEY` ambient | absent by allowlist construction |
| 6 | controller timeout | kill group, reap, E-C46-CONTROLLER, no evidence |
| 7 | future missing environment need | loud OSError; never inherit silently |
| 8 | kill races controller exit | absorb ProcessLookupError; still refuse |
| 9 | validator drift | impossible: one foundation validator |
| 10 | v2-style result envelope | not touched; closed v1 contract remains |

## Test strategy

`tests/unit/test_confinement_result.py` freezes canonical parsing, exact schema,
digest width/case, bool exit-code, teardown, and strict in-memory emission.
`tests/security/test_slice047_confinement_hardening.py` drives real `cmd_run`
with controller-shaped Popen doubles to inspect the environment and timeout
cleanup. `tests/security/test_slice046_cmd_run_confinement.py` is re-aimed to a
Popen-compatible controller stub. Existing gate8 and import-ban pins remain in
`tests/integration/test_slice018_confinement_session.py`.

## Code review checklist

- Does the foundation module use only stdlib and canonical JSON?
- Do main and producer call the same validator without changing E-C18 surfaces?
- Is the controller environment exactly the four declared keys?
- Does timeout kill the process group, reap it, and refuse without evidence?
- Does `ProcessLookupError` retain the timeout refusal?
- Is claim-type digest enforcement absent from this change?

## More Information

Vendored bytes prove bytes were obtained, not their upstream origin. SLICE-048
will own claim-type confinement-digest enforcement; this decision does not
change verdict, admission, loader, gate, CI, harness, or suite semantics.
