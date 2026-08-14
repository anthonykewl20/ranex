# ADR-023 — invoke the confinement session as a subprocess

**Status:** proposed
**Date:** 2026-08-15
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-046-cmd-run-confinement-binding.md`

## Context and Problem Statement

SLICE-018 has a qualified strict-local session but `cmd_run` still launches the
bound command in the signer process. Importing that session is impossible:
`host_confinement.py:3058` writes `os.getpid()` to its controller
`cgroup.procs`; lines 3441–3446 say that controller cannot leave or remove its
leaf until the process exits. ADR-006:19–21 also rejects fork hooks with
threads, and ADR-006:160–161 separates the signer from the measured worker.

`cmd_run` must bind the session's complete teardown result before signing, while
keeping the existing `src/`-wide ban on importing `host_confinement` unchanged.

## Decision Drivers

- The controller's process-lifetime cgroup ownership must remain real.
- A child result must be closed-schema, path-confined, and fail closed.
- No evidence may be signed before verified teardown and result binding.
- The default unconfined CLI behaviour must remain available until opted in.
- Existing import-boundary tests must continue to prove authority separation.

## Prior art

- Searched: GitHub code search for monitor child status, privileged command
  monitors, and fail-closed bounded record parsing.
- [bubblewrap `bubblewrap.c` at v0.11.0, commit 9ca3b05ec787acfb4b17bed37db5719fa777834f](https://github.com/containers/bubblewrap/blob/9ca3b05ec787acfb4b17bed37db5719fa777834f/bubblewrap.c)
  documents its monitor design (489–496) and reads its eventfd before reporting
  status (547–562).
  License: LGPL-2.0-or-later (SPDX header of the vendored file; invoked-not-copied precedent ADR-006:73–74).
  Weakness: its 8-bit exit status is primary; structured facts are optional and
  cryptographically unbound.
  Vendored: docs/adr/prior-art/ADR-023/bubblewrap.c blob:f8728c7e127838201061318c32ee42fe4533eeae
- [sudo `src/exec_monitor.c` at SUDO_1_9_16p2, commit 172cbd968e6fe5f64d3384896a90c0a1aa73238d](https://github.com/sudo-project/sudo/blob/172cbd968e6fe5f64d3384896a90c0a1aa73238d/src/exec_monitor.c)
  relays structured `command_status {type,val}` outside the boundary, keeps an
  execve failure from being overwritten by child status (205–223), and defines
  the `exec_monitor` role that relays command status and parent signals
  (534–541).
  License: ISC.
  Weakness: its same-uid backchannel is unauthenticated, and raw wait status
  proves exit rather than confinement.
  Vendored: docs/adr/prior-art/ADR-023/sudo-exec_monitor.c blob:c5c4a14b6cca0925cc422c0d1f90042a9b51f1e9
- [age `internal/format/format.go` at v1.2.0, commit bbe6ce5eeb1bb70cfc705d0961c943f0dd637ffd](https://github.com/FiloSottile/age/blob/bbe6ce5eeb1bb70cfc705d0961c943f0dd637ffd/internal/format/format.go)
  begins exactly `// Copyright 2019 The age Authors. All rights reserved.` and
  uses bounded, fail-closed stanza parsing that refuses rather than repairs.
  License: BSD-3-Clause.
  Weakness: syntax is all it proves; trust comes from a MAC elsewhere. Here
  schema validation is necessary; controller contract plus the new signature
  binding supply trust.
  Vendored: docs/adr/prior-art/ADR-023/age-format.go blob:aa77b756ffc4ca4201e42e0694182fe124316423
- Rejected: https://github.com/google/nsjail is an Apache-2.0 monolithic,
  privileged supervisor that replaces the pinned launch chain ADR-006:84–85
  deliberately retains.
- Rejected: https://github.com/google/gvisor uses an OCI/rootfs model and has no
  cgroup-teardown/readback evidence contract; compatibility remains UNVERIFIED
  per ADR-006:78.
- Rejected: https://github.com/systemd/systemd full `systemd-run` session
  ownership cedes lifecycle/result semantics outside this evidence contract;
  ADR-014:44 rejects new broker trust boundaries.
- Rejected: in-process import is impossible: the controller enrolls its own PID
  at `host_confinement.py:3058`, and its 3441–3446 comment says it cannot leave
  or remove that leaf until it exits; see https://github.com/anthonykewl20/ranex.

## Considered Options

1. Subprocess controller: chosen; its process may exit after cgroup ownership.
2. In-process import: impossible under the controller's cgroup lifetime rule.
3. Wrap `cmd_run`'s spawn in bwrap directly: rejected; ADR-006 already rejects
   bubblewrap-alone as not bounding inherited authority or teardown.

## Decision Outcome

In the context of a qualified session that owns its controller process, facing
an in-process lifetime conflict, choose a child `python -m
ranex.cli.host_confinement session` invocation, to bind verified confinement
facts before signing, accepting descriptor/result protocol complexity.

`cmd_run --confinement strict-local` writes a
`ranex-confinement-command-v1` descriptor, reads a
`ranex-confinement-result-v1` result, validates it before signing, and never
imports `host_confinement` from `src/`.

### Consequences

- The evidence signed-field set grows 8→10 (`confinement_result_digest`,
  `confinement_profile_digest`) and the evidence domain string bumps v3→v4,
  following the ADR-001 (5→7 ⇒ v1→v2) and SLICE-009 (7→8 ⇒ v2→v3) precedents;
  old v3 records are refused, not migrated; nothing signed is committed
  (`evidence.json` gitignored). Verdict/journal schemas unchanged.
- Controller refusal, timeout, missing result, or invalid teardown writes no evidence.
- `--confinement strict-local` is opt-in; default runs retain their current path.
- ADR-006 becomes accepted and MAP §11.5 RISK-06 closes only when this slice's
  frozen gates pass on landed code: delegated-unit battery, 0caa1090f hardening,
  and this binding. Then SLICE-029/#12 unblocks.

### Confirmation

`tests/security/test_slice046_cmd_run_confinement.py` freezes child refusal,
missing/incomplete results, signed-field tamper, and result exit binding.
`tests/integration/test_slice018_confinement_session.py` remains the real
controller lifecycle contract. `tests/security/test_slice017_host_qualification.py`
and `tests/unit/test_verdict_publication.py` stay untouched and green.

## Improvements on the prior art

1. Unlike bubblewrap status, sign a digest of the exact result bytes.
2. Unlike sudo's status channel, accept only a repository-confined result after
   schema, teardown, descriptor-path, and exit-code cross-checks.
3. Like age, reject unknown, missing, oversized, or malformed fields; unlike age,
   bind accepted bytes to evidence under an existing Ed25519 signature.

## Architecture surface

`src/ranex/cli/main.py` owns descriptor construction, child invocation, result
validation, and evidence construction. `host_confinement` remains a module-only
child entrypoint. Verdict and journal schemas are unchanged.

## Scope and threat delta

This governs strict-local `cmd_run` binding. STRIDE: tampering and elevation move
because an unsigned or incomplete result cannot select signed exit facts.
Non-goal: harness confinement, managed profiles, and ADR-017 work. Host-admin,
kernel compromise, and a controller implementation defect remain out of scope.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Integrity | result is changed | signature verification fails |
| Reliability | child/result fails | exit 2 and no evidence |
| Auditability | strict-local run records | two signed confinement digests |

## Reversibility

Door: one-way

The opt-in flag can be removed before evidence is relied upon. Once accepted
records exist, changing their field set requires a new evidence domain/version;
silently accepting old incomplete results is not a rollback.

## Sad paths

Decision-table partitions cover controller, result, path, teardown, and signing.

| # | Failure | Required behaviour |
|---|---|---|
| 1 | unqualified or stale host | E-C18-HOST-DRIFT before spawn |
| 2 | controller nonzero | parse refusal JSON, refuse, never sign |
| 3 | exit zero but result missing | refuse, no evidence |
| 4 | malformed or unknown result schema | E-C18-RESULT refusal |
| 5 | teardown is not kill/populated-0/removed | refuse; result follows teardown only |
| 6 | evidence exit differs from result command exit | refuse |
| 7 | descriptor authority paths alias | E-C18-PATH-ALIAS |
| 8 | timeout or survivors | kill and refuse, per ADR-017:183 |
| 9 | signing is reached without validated result | impossible by construction; test asserts |
| 10 | `src/` imports host_confinement | existing frozen import-ban tests fail |
| 11 | v3-domain evidence record presented to the v4 verifier | refused at admission; no silent downgrade |

## Test strategy

Security tests in `tests/security/test_slice046_cmd_run_confinement.py` use the
public strict-local flag and a child-process-shaped controller double for
nonzero, missing, incomplete, and tampered result partitions. A host-gated real
session proves the success path when delegated cgroup prerequisites exist.
`tests/integration/test_slice018_confinement_session.py` proves result emission;
`tests/security/test_slice017_host_qualification.py` and
`tests/unit/test_verdict_publication.py` protect the unchanged boundary. The
red-first slice test fails before the binding exists; no global coverage target.
The same freeze deliberately updates the pinned signing expectations in
`tests/unit/test_evidence_signing.py`, `tests/unit/test_suite_results.py`,
`tests/security/test_slice003_command_binding.py`, and
`tests/contract/test_qualification_admission.py` for the ten fields and v4
domain.

## Code review checklist

- Is `host_confinement` invoked only as a child, never imported by `src/`?
- Is every descriptor/result path confined and free of aliases before use?
- Does every child failure retain its JSON refusal but prevent signing?
- Are exact result bytes and profile digest signed, not merely displayed?
- Does timeout kill/reconcile before a refusal is returned?
- Does the result exit code, rather than a subprocess wait status, enter evidence?

## More Information

The vendored copies prove fetched bytes were obtained, not that they came from
the cited URLs. NOTICE records source headers and licensing. ADR-006 remains
proposed until this slice lands under its frozen gates; this ADR does not edit it.
