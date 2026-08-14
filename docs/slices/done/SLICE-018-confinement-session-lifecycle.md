# SLICE-018 — confinement session lifecycle

**Status:** done
**Closed:** 2026-08-14
**Opened:** 2026-08-13
**Priority:** P0 — the qualified launcher has no service that owns a real
worker's cgroup, namespace, syscall, teardown, or bounded-output lifecycle.
**ADR:** `docs/adr/ADR-006-landlock-confinement-of-the-bound-command.md`
(proposed). SLICE-017's qualified artifact is the closed prerequisite. This
middle slice neither accepts ADR-006 nor closes RISK-06; only the already closed
SLICE-019 retained that exclusive disposition right.

## Session-sized result

The qualified SLICE-017 artifact and a closed command descriptor produce one
unsigned `ConfinementResult` through real processes, without exposing the
service through `cmd_run`. Python creates a controller leaf and sibling worker
cgroup, reads back limits and enrollment before releasing the launcher's start
gate, monitors cumulative resources, always kills and drains the whole cgroup,
and only then collects bounded output through held directory descriptors. The
native launcher creates mandatory user, mount, PID, IPC, network and cgroup
namespaces, read-only subject/toolchain mounts, isolated output/scratch mounts,
fresh `/proc` and minimal `/dev`, then applies no-new-privileges, strict
Landlock and the pinned x86-64 default-deny seccomp policy before `execve`.
Missing support or an incomplete readback refuses; there is no weaker backend.

The result is canonical JSON data, not evidence: it binds profile and policy
digests, namespace identities, cgroup topology/limits/events/usage, command
status, teardown (`cgroup.kill`, `populated 0`, removal), and collected output
digests. It contains no signature, signing identity, evidence envelope or
`cmd_run` binding.

## Exact owned paths

Product implementation may change only:

- `src/ranex/cli/host_confinement.py`
- `src/ranex/foundation/atomic_writer.py` only as the existing owner delegated
  to by the directory-walker dedupe below; its atomic-publication behavior may
  not change
- `native/ranex-worker-launcher/launcher.c`
- `governance/confinement/native-launcher-build-v1.json`
- `governance/confinement/strict-local-host-v1.json`
- `governance/confinement/strict-local-v1.json` (new closed runtime profile)
- `governance/suite_manifest.json`
- `tests/security/test_slice018_cgroup_output_lifecycle.py`
- `tests/integration/test_slice018_confinement_session.py`
- this slice, `docs/STATE.md`, and `README.md` only when closing

`host_confinement._open_created_directory` must become a delegation to
`foundation.atomic_writer._open_created_directory`, removing the duplicated
walker identified as P3 in SLICE-020 review. This is an in-scope drive-in
because lifecycle setup creates output directories; it may not alter the shared
walker's contract or widen filesystem access.

Explicitly not owned: `src/ranex/cli/main.py`, evidence/approval/verdict signing,
producer keys, gate admission, journal schema, harness files, ADR-006 status, or
the RISK-06 row.

## Frozen confinement-session contract

### Closed descriptor and runtime profile

`python -m ranex.cli.host_confinement session` accepts only explicit
`--profile`, `--host-profile`, `--artifact`, `--manifest`, `--qualification`,
`--descriptor`, and `--result` paths rooted beneath the repository. The
descriptor is canonical JSON with exact top-level fields `schema`, `argv`,
`environment`, `subject`, `toolchain`, `output`, `scratch`, and `limits`.
`schema` is `ranex-confinement-command-v1`; `argv` is a non-empty list of
non-empty strings; `environment` is a closed string-to-string mapping; the four
paths are distinct repository-relative paths with output/scratch unable to
alias or descend from subject/toolchain. Limits are positive integer
`cpu_usage_usec`, `memory_bytes`, `pids`, `wall_time_ms`, `output_bytes`,
`output_inodes`, and `output_depth`. Unknown/missing fields, links in authority
paths, path aliasing, stale qualification or pin drift refuse before launch.

`strict-local-v1.json` is a closed, versioned runtime profile. It pins the
SLICE-017 host profile/build/launcher, Bubblewrap, minimum Landlock ABI, the
architecture-specific seccomp policy, namespace/mount grammar, cgroup-v2
controllers and exact limit/readback names, start-gate protocol, and safe
output traversal (`openat2` with `RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS|RESOLVE_NO_MAGICLINKS`).
Every mandatory layer is required; profiles have no fallback or optional
security-layer field.

### Gate, execution, teardown, and collection

The controller holds the delegated cgroup root by descriptor, moves itself to a
controller leaf before enabling and reading back `cpu`, `memory`, and `pids`,
creates the sibling worker domain, writes and exactly reads all limits, launches
the stopped worker, enrolls and reads back its PID, and only then releases FD 3.
The launcher must not execute the command before release. It enters real,
observably distinct user/mount/PID/IPC/network/cgroup namespaces and applies
NNP → strict full-mask Landlock → pinned default-deny seccomp → exec. Subject
and toolchain are read-only; output and scratch are the only writable mounts.

Every normal, timeout, signal, protocol, readback, quota and exception exit
writes `1` to held `cgroup.kill`, rejects any read error, waits for exact
`populated 0`, and removes the worker cgroup before output collection or result
publication. CPU usage and memory/PID events are cumulative whole-cgroup facts;
an OOM, `memory.events max`, `pids.events max`, CPU excess, wall timeout, or
storage excess refuses the result.

Collection begins only after drain, walks from held output dirfds with the
pinned `openat2` resolution flags, and accepts only bounded regular files and
directories. Symlinks, magic links, devices, sockets, FIFOs, hardlinks, depth,
count, byte or inode excess, replacement races, and read errors refuse. The
result is written only after complete collection and is canonical, unsigned,
closed-schema `ranex-confinement-result-v1`; a refusal leaves no result or
partial temporary.

## Deterministic acceptance gates

1. A real command runs only after cgroup enrollment/readback and reports
   distinct mandatory namespaces plus active NNP, Landlock and seccomp.
   `tests/integration/test_slice018_confinement_session.py`.
2. Subject/toolchain are read-only, output/scratch are the only writable paths,
   and host `/proc`, network and IPC are unreachable.
   `tests/integration/test_slice018_confinement_session.py`.
3. A worker that forks, double-forks and calls `setsid` remains in the worker
   cgroup and PID namespace; normal and timeout exits use `cgroup.kill`, drain
   to `populated 0`, and remove the cgroup.
   `tests/security/test_slice018_cgroup_output_lifecycle.py`.
4. Gate-release-before-enrollment, forged enrollment/limit readback, threaded
   worker cgroups, stale held delegation and missing controllers refuse before
   command execution. `tests/security/test_slice018_cgroup_output_lifecycle.py`.
5. CPU, memory, PID, wall-time, output-byte and output-inode excess each kills
   the whole cgroup and yields no result.
   `tests/security/test_slice018_cgroup_output_lifecycle.py`.
6. Collection starts only after observed `populated 0`; symlink, magic-path,
   device/FIFO/socket, hardlink, replacement-race, count/depth/byte/inode and
   traversal attacks refuse without partial output.
   `tests/security/test_slice018_cgroup_output_lifecycle.py`.
7. Missing namespace, NNP, strict Landlock ABI/mask, known seccomp architecture
   or policy pin refuses without a fallback execution.
   `tests/integration/test_slice018_confinement_session.py`.
8. Result schema binds every profile/policy, namespace, cgroup limit/event/usage,
   teardown and output digest readback and is canonical and unsigned.
   `tests/integration/test_slice018_confinement_session.py`.
9. The lifecycle surface exposes neither `cmd_run` nor a signing/evidence input
   or output, and `src/ranex/cli/main.py`, ADR-006 and RISK-06 remain unchanged.
   `tests/security/test_slice018_cgroup_output_lifecycle.py`.
10. `host_confinement._open_created_directory` delegates to the foundation
    atomic writer's single directory walker without changing its behavior.
    `tests/security/test_slice018_cgroup_output_lifecycle.py`.

## Sad-path mapping

| Failure | Required result | Gate |
|---|---|---|
| Controller remains in domain root or worker cgroup is threaded | refuse before subtree enable/gate release | 4 |
| ADR-006 #21 host state drifts after qualification (LSM, userns sysctl or cgroup delegation) | refuse before launch; command marker and result absent | 4 |
| ADR-006 #4 output/scratch aliases subject, toolchain, each other or authority paths | refuse descriptor before launch | 4 |
| Required cgroup controller or delegation disappears | kill if needed; refuse, never re-resolve/fallback | 4 |
| Limit write, enrollment, or readback is missing/forged | gate stays closed; kill and refuse | 4 |
| Worker races the start gate | command marker absent; whole cgroup killed | 4 |
| Namespace creation leaks or is unavailable | no command exec; refuse | 1, 7 |
| NNP, Landlock mask/ABI, seccomp arch or policy fails | inner launcher never execs command | 7 |
| Subject/toolchain is writable or host path/network/IPC is reachable | attack denied; result refused on mutation | 2 |
| Child double-forks or changes session | descendant remains owned by cgroup/PID namespace | 3 |
| CPU, memory, PID or wall limit is exceeded | `cgroup.kill`; event/usage refusal | 5 |
| Output byte/inode quota is exceeded | kill, drain, and refuse before collection | 5 |
| Exception or signal arrives before collection | finally kill, observe `populated 0`, remove | 3 |
| `cgroup.events` read fails or never says `populated 0` | refuse; never collect live output | 3, 6 |
| Output contains link, magic path, device, FIFO, socket or hardlink | held-dirfd traversal refuses | 6 |
| Output replacement race or bound excess occurs | no partial result; refuse | 6 |
| Result omits or mismatches an enforcement readback | closed-schema refusal; no unsigned success claim | 8 |
| Descriptor asks for `cmd_run`, evidence or signing | closed descriptor/CLI refusal | 9 |

## Verification commands

```text
uv run --frozen pytest -q tests/security/test_slice018_cgroup_output_lifecycle.py tests/integration/test_slice018_confinement_session.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen pytest -q
uv run --frozen mutmut run
```

## One-way door and stop conditions

The descriptor/result/profile schemas and launcher session protocol become
one-way once a real result is emitted. The implementer must stop rather than
add a fallback backend, release before exact cgroup readback, collect before
verified drain, weaken safe traversal, treat a read error as empty/success,
change `cmd_run`, introduce signing/evidence, accept ADR-006, close RISK-06, or
modify a path outside the owned list. A host unable to provide delegated
cgroup-v2, all namespaces, strict Landlock, the pinned seccomp architecture and
safe `openat2` must produce a stable refusal, not a skipped contract.

## Not in this slice

- Any `cmd_run` binding or production execution path.
- Evidence, approval or verdict signing, signer identity, or key access.
- ADR-006 acceptance/closure or RISK-06 closure.
- Installed-CLI theft/mutation/survivor binding, which was SLICE-019's exclusive
  disposition surface and is not reopened here.
- Managed distinct-uid or gVisor profiles, kernel/host-admin compromise, and
  side channels.
