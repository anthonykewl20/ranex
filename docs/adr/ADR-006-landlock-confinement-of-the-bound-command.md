# ADR-006 — isolate the bound command from the authority that signs it

**Status:** accepted
**Accepted:** 2026-08-15 — SLICE-046 (issue #21) bound cmd_run to the qualified session; full suite green at f63713f43.
**Date:** 2026-08-02
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-017-confinement-of-the-bound-command.md` (open),
then planned SLICE-018 (issue #21) and SLICE-019 (issue #22); this sequence replaces withdrawn
SLICE-005. **Disposition (owner, 2026-08-09):** ADR-006 remains `proposed` and
RISK-06 open until SLICE-019 binds the qualified profile to `cmd_run`.

## Context and Problem Statement

`cmd_run` resolves `argv[0]` on the pinned toolchain and constructs an empty-base
environment (`src/ranex/cli/main.py:443-466,1841-1850`), but then invokes the
command as Ranex's uid. A hostile child can read `/proc/<ranex-pid>/environ`,
follow `RANEX_SIGNING_KEY`, and forge any record without invoking `run`. The same
uid can alter user configuration used by Ranex and can outlive a process group.

The present `subprocess.run(..., preexec_fn=...)` shape is not a security
boundary: Python documents fork-to-exec child hooks as unsafe with threads, and
`setsid`/`killpg` misses descendants that form another session. The subject is
currently measured and then writable. ADR-002's signer and ADR-005's observation
therefore share authority with the party they measure.

## Decision Drivers

- A worker must never receive a signing key, key path, inherited key FD or secret
  environment entry; managed/high-assurance workers must also have a distinct uid.
- The measured subject and toolchain must be visible read-only; writes go only to
  named output and scratch mounts.
- Filesystem, network, IPC, process-tree and resource controls must fail closed.
- Setup and teardown must be observable and bound into evidence, not inferred.
- The local path must be unprivileged and pin every helper that affects a verdict.
- A compatibility failure is a refusal, never a weaker backend or policy.

## Prior art

**Searched:** GitHub code for `bubblewrap` mount policy, `seccomp` re-exec,
strict `landlock_restrict_self`, cgroup-v2 `cgroup.kill`/`populated` teardown,
separate attestation signers, and OCI gVisor launch paths.
- **containerd manages cgroup-v2 creation, limits, kill and deletion.** <https://github.com/containerd/cgroups/blob/076b5e0e60bd073ead691caf95a90ac0f2fbec5d/cgroup2/manager.go>
  License: Apache-2.0.
  Weakness: `Kill` falls back to PID iteration, and `isCgroupEmpty` treats read errors or a missing `populated` key as empty; Ranex must reject both.
  Vendored: docs/adr/prior-art/ADR-006/containerd-cgroup2-manager.go blob:38d7556598795fe37f5f13d9416a134124b33cf8
- **containerd tests its cgroup-v2 manager.** <https://github.com/containerd/cgroups/blob/076b5e0e60bd073ead691caf95a90ac0f2fbec5d/cgroup2/manager_test.go>
  License: Apache-2.0.
  Weakness: these tests do not assert Ranex's gated enrollment, no-fallback kill, event readback or signing refusal.
  Vendored: docs/adr/prior-art/ADR-006/containerd-cgroup2-manager-test.go blob:5ee6971c3b73c851e656f8bce19030fef119c807
- **Linux demonstrates Landlock syscall-error sequencing.** <https://github.com/torvalds/linux/blob/8cd9520d35a6c38db6567e97dd93b1f11f185dc6/samples/landlock/sandboxer.c>
  License: BSD-3-Clause.
  Weakness: it strictly checks syscalls but best-effort downgrades unsupported ABI features; Ranex rejects that downgrade.
  Vendored: docs/adr/prior-art/ADR-006/linux-landlock-sandboxer.c blob:66e56ae275c6b350cc0dedb4ef05aca5e1d4d8e3
- **landrun assembles a practical strict Landlock sandbox.** <https://github.com/Zouuup/landrun/blob/62823c05e58ec22c1f91b4c8468318c1f97f2d32/internal/sandbox/sandbox.go>
  License: MIT.
  Weakness: an external CLI alone neither pins the launch chain nor separates the signer or owns cgroup teardown.
  Vendored: docs/adr/prior-art/ADR-006/landrun-sandbox.go blob:2487567c1953ac17f0144c7ed6902d6cc2459be3
- **go-landlock handles ABI and all-thread restriction.** <https://github.com/landlock-lsm/go-landlock/blob/e573f52a61e3072813de11359239d2ccae9705d2/landlock/restrict.go>
  License: MIT.
  Weakness: best-effort downgrade can reduce the configuration to no restriction while returning success.
  Vendored: docs/adr/prior-art/ADR-006/go-landlock-restrict.go blob:34755a18d12ba505bacd1cd8b58fceb629d9c5bf
- **py-landlock defaults to strict feature checks.** <https://github.com/SebastienWae/py-landlock/blob/932af28940493fd6189d96a4b00c539a006c96c2/py_landlock/landlock.py>
  License: MIT.
  Weakness: it restricts the calling thread and remains unsuitable for Python `preexec_fn`.
  Vendored: docs/adr/prior-art/ADR-006/py-landlock-landlock.py blob:0a3e98c2cfab07eacdf9cfd4a10a5142a6516f76
- **License/NOTICE payload provenance (not implementation evidence):**
  Vendored: docs/adr/prior-art/ADR-006/LICENSE-CONTAINERD-APACHE-2.0.txt blob:261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64
  Vendored: docs/adr/prior-art/ADR-006/LICENSE-LINUX-BSD-3-Clause.txt blob:34c7f057c8d5441314c339ba574a9c6224ce0f80
  Vendored: docs/adr/prior-art/ADR-006/LICENSE-LANDRUN-MIT.txt blob:7efcb24904d270788935e4c6c7e36b95f871667c
  Vendored: docs/adr/prior-art/ADR-006/LICENSE-GO-LANDLOCK-MIT.txt blob:aaa7810eb0d5112bd55d69d28f58fd54dad51148
  Vendored: docs/adr/prior-art/ADR-006/LICENSE-PY-LANDLOCK-MIT.txt blob:14fac913ccf80234b1848540089a3bbcb6e5283d
- **Rejected:** <https://github.com/openai/codex> informed discussion, but the
  prior focused excerpts were not complete source files; they are removed and
  are not adopted evidence. <https://github.com/containers/bubblewrap> C source
  is LGPL and is invoked as a pinned binary, not copied.
- **Rejected:** <https://github.com/python/cpython> process helpers and
  <https://github.com/slsa-framework/slsa-github-generator> signing workflows do
  not supply whole-tree teardown or runtime signer separation;
  <https://github.com/google/gvisor> launch compatibility stays UNVERIFIED.

## Considered Options

1. Landlock from Python `preexec_fn`: rejected; unsafe hook, same uid and no
   namespace, process-tree, resource or complete network boundary.
2. Bubblewrap alone: rejected; a mount boundary does not bound syscalls,
   resources, inherited authority or teardown.
3. OCI-spec gVisor: retained only as an independently qualified optional profile;
   never `runsc do`, never a fallback.
4. A layered native worker launch plus separate signing authority: chosen. It is
   the only option that answers both isolation and lifecycle.

## Decision Outcome

Choose a **layered worker/authority boundary**. A verified native helper launches
a pinned Bubblewrap policy as the primary local boundary, re-execs inside it, and
applies `PR_SET_NO_NEW_PRIVS`, strict audited Landlock, then a versioned,
architecture-specific default-deny seccomp policy before `execve`. Any unavailable
layer, unknown architecture or unqualified syscall profile refuses the run.

The strict local profile runs authority-free under the caller uid and is admitted
only after local qualification. Managed/high-assurance profiles add a worker host
uid distinct from the controller and signer; neither profile may weaken a layer.
Any launcher requiring privilege belongs to a separately qualified managed profile.

The descriptor mounts subject and toolchain read-only and exposes separate,
explicit output and scratch as the only writable paths. Mount, user, PID, IPC and
network namespaces, fresh `/proc` and minimal `/dev` are mandatory. Managed and
high-assurance profiles use a separately provisioned worker uid or `DynamicUser`;
controller and signer uids, key, path, FDs and environment never enter the worker.

### Consequences

- Good: isolated namespaces close Landlock's metadata and UDP gaps and backstop
  its pathname Unix-socket scope (ABI 9); inner seccomp and Landlock limit damage
  from a launcher defect.
- Good: the measured tree cannot rewrite its own input; outputs are separately
  collected and digested by the controller.
- Good: a cgroup owns every descendant even after `setsid` or a double fork.
- Bad: local support now depends on verified Bubblewrap, user namespaces,
  cgroup-v2 delegation, seccomp and the audited Landlock ABI.
- Bad: commands expecting source-tree writes, host networking, host `/proc` or
  broad devices must be changed or refused, not silently widened.
- User-namespace uid remapping is not a distinct host uid. Local signatures stay
  provisional until the attack suite passes; a strict local profile also needs
  delegated cgroup-v2, while managed admission requires distinct host uids.

### Confirmation

SLICE-017 freezes and qualifies the build/host/launcher without running an
untrusted bound command. SLICE-018 proves namespace, cgroup and bounded-output
lifecycle through real processes without touching `cmd_run`. SLICE-019 first
reproduces today's key/env theft, mutation and survivor controls, then binds the
service to `cmd_run` and proves every layer plus the honest evidence path.

Evidence records backend/profile, open-object digests plus `statx`, mount, owner,
mode and capability provenance, Landlock/seccomp-policy digests, uid/namespaces,
cgroup topology,
limits/quotas, `cpu.stat`, `memory.events`, `pids.events`, teardown and bounded
output-collection readbacks. A missing or mismatched field refuses signing.

## Improvements on the prior art

1. Local launch opens helper/bwrap and its interpreter/library/toolchain chain with
   `O_NOFOLLOW` beneath controller-owned immutable storage, verifies `statx`/mount
   provenance, expected owner/mode and no setuid/setgid/file capabilities, hashes
   each open object, then executes/binds that same FD; otherwise refuse.
2. The inner stage closes unknown FDs and invalidates inherited keyrings, then
   applies NNP → strict full-mask Landlock → versioned arch-specific default-deny
   seccomp → exec. The allowlist permits only qualified toolchain calls/local IPC;
   it excludes keyctl/add_key/request_key, namespace/mount, ptrace/process_vm,
   bpf/perf, userfaultfd, io_uring, module/kexec/reboot and unapproved networking.
3. Subject/toolchain are read-only; separate output/scratch use sized tmpfs or a
   qualified quota backend with byte and inode limits read back before gate release.
4. First create a controller leaf and move the controller from the delegated domain
   root; then enable/read back root `cgroup.subtree_control`, create the domain
   worker sibling, set/read limits, enroll the stopped worker, and release its gate.
   `cpu.max` sets rate; the controller enforces cumulative `cpu.stat usage_usec`.
5. Every exit uses `cgroup.kill`; `memory.events` oom/oom_kill/max,
   `pids.events` max or any read error is fatal. Only after `populated 0` may held
   dirfds drive bounded `openat2` output traversal and cgroup removal.
6. The signer receives only independently computed digests plus complete evidence;
   the managed worker uid cannot address controller or key material.
7. Optional gVisor requires a qualified OCI spec/rootfs; it stays unavailable and
   never falls back to `runsc do` or local execution.

## Architecture surface

A small native launcher owns descriptor validation, FD closure, start gating,
bwrap exec and the inner security sequence. Python owns cgroup creation/readback,
wait/timeout, verified teardown, output collection and evidence construction; it
does not use `preexec_fn`.

The controller resolves (`src/ranex/cli/main.py:443-466`) and constructs the
environment (`src/ranex/cli/main.py:1841-1850`) before authority-free launch.
A profile manifest pins helper/bwrap digests and mount, syscall, network, cgroup
and uid requirements. Strict local launch requires delegated cgroup-v2 or refuses;
managed launch assigns a worker uid distinct from controller and signer. The
signer accepts only a complete qualified result.

## Scope and threat delta

In scope: worker access to files, FDs, environment, network, IPC, processes,
CPU, memory, PIDs and signing authority; complete descendant cleanup; evidence
of enforcement. A worker may fully control its declared output and scratch.

Landlock ABI 6 scopes signals and abstract Unix sockets; ABI 9
(`LANDLOCK_ACCESS_FS_RESOLVE_UNIX`, present on the cited kernel) restricts
pathname Unix sockets. Landlock network rights remain TCP-only, so UDP and other
protocols are closed by the isolated network namespace, and Landlock metadata
gaps are closed by hiding host paths — namespaces stay as defence-in-depth even
where Landlock now covers a path. Kernel compromise, host-admin compromise and
side channels remain out of scope.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Confidentiality | worker seeks signing key | absent by uid, namespace, FD and environment checks |
| Integrity | worker changes subject/toolchain | read-only mount; controller digest unchanged |
| Reliability | descendant changes session | cgroup kill; `populated 0` before success |
| Resource safety | fork/memory/CPU/storage attack | read-back limits, events, usage and quotas bound whole tree |
| Auditability | helper or policy changes | digest/profile mismatch refuses signing |

## Reversibility

Door: one-way

Profiles and evidence schema can evolve, and gVisor can be qualified separately.
Removing a mandatory layer or sharing signer authority again would make later
evidence mean less while retaining the same PASS vocabulary, so downgrade is not
a compatible rollback.

## Sad paths

| # | Input | Required behaviour |
|---|---|---|
| 1 | helper/bwrap chain is mutable/swapped, provenance/owner/mode wrong, setid or file-capable | refuse local launch; execute only verified open objects |
| 2 | user, mount, PID, IPC or network namespace unavailable | refuse; no fallback |
| 3 | subject or toolchain cannot be mounted read-only | refuse; never mount writable |
| 4 | output/scratch aliases subject, toolchain or authority paths | refuse descriptor |
| 5 | worker uid equals controller uid in managed/high-assurance | refuse |
| 6 | key path, key FD, secret env or unexpected inherited FD is present | close/refuse before exec |
| 7 | controller is not moved to its leaf before subtree enable, worker is threaded, or controller/limit/enrollment readback fails | refuse before gate release |
| 8 | worker races before cgroup enrollment | start gate stays closed; kill and refuse |
| 9 | NNP/Landlock fails, keyring survives, or seccomp arch/profile is unknown | inner helper never execs command |
| 10 | command reads controller env, key, home or repository | absent/denied |
| 11 | command writes subject/toolchain or host paths | read-only/absent; refuse result on mutation |
| 12 | command uses pathname Unix socket, UDP, SysV IPC or host `/proc` | isolated namespace/view denies reachability |
| 13 | command forks, double-forks or calls `setsid` | descendants remain in cgroup/PID namespace |
| 14 | command exceeds cumulative CPU, memory/PID events, output/scratch bytes/inodes or wall time | kill whole cgroup; refuse signing |
| 15 | signal/exception occurs before collection | `finally` kills and verifies `populated 0`; never collect live output |
| 16 | `cgroup.events` never reaches `populated 0` or removal fails | refuse signing and report teardown failure |
| 17 | output races, links, magic paths, devices, hardlinks or exceeds count/depth/byte/inode bounds | reject held-dirfd collection |
| 18 | evidence omits or mismatches an enforcement readback/digest | signer refuses |
| 19 | local profile has not passed attack qualification | result remains provisional/unadmitted |
| 20 | gVisor profile lacks verified OCI spec/rootfs/`runsc` pin | unavailable; never use `runsc do` or local fallback |
| 21 | qualified report predates current host state (LSM/AppArmor/SELinux policy, unprivileged-userns sysctl, or cgroup-v2 delegation changed since qualification) | refuse launch; re-qualification required before admission |

## Test strategy

Existing tests remain the cited executable baseline:
`tests/security/test_slice004_hermetic_observation.py` reproduces hostile
same-uid behavior; `tests/security/test_executable_path_confinement.py` and
`tests/security/test_repository_confinement.py` protect the existing path and
repository rules; `tests/e2e/test_run_produces_evidence.py` proves the honest
recording path.

SLICE-017 owns reproducible native-build, same-FD probe and host-delegation tests.
SLICE-018 owns real namespace/syscall/cgroup/output lifecycle attacks, including
`cgroup.kill` and `populated 0` before dirfd-held
`openat2(RESOLVE_BENEATH|NO_SYMLINKS|NO_MAGICLINKS)` collection. SLICE-019 owns
the installed-CLI theft, mutation, survivor and field-binding campaign. Each
future slice names exact tests only when it opens.

Red-then-green: attacks must succeed against today's unconfined `cmd_run` before
the launcher exists. Mutation checks delete or bypass each layer in turn and
require its covering test to fail. gVisor has a separate suite and cannot inherit
local qualification.

## Code review checklist

- Does any error or unsupported feature reach the command or select a weaker path?
- Does local launch bind `statx`/mount provenance, owner/mode and absent setid/file capabilities for every same-FD helper/bwrap dependency?
- Are subject/toolchain read-only and output/scratch the only writable mounts?
- Can the worker learn the signer uid, key path, key FD or secret environment?
- Is the controller moved to its leaf before root subtree enable/readback, then the domain worker sibling created, limited, enrolled and released in that order?
- Are cumulative CPU and memory/PID/storage events monitored and bound into evidence?
- Does every exit path kill, drain and remove the whole cgroup before signing?
- Is the inner order NNP, strict Landlock, default-deny seccomp, exec, with keyring/FD authority absent and unknown profiles refused?
- Does output collection start only after `populated 0` and use held dirfds, safe `openat2`, file-type/nlink and size/count/depth bounds?
- Does evidence bind every enforcement fact used to admit the result?
- Do attacks turn red when their responsible layer is removed?

## More Information

This supersedes ADR-005's process-group assumption and closes its deferred
same-uid/key-theft and survivorship paths only after SLICE-019 lands. Until then
ADR-006 stays proposed and RISK-06 stays open; SLICE-017 qualification alone is
not a production confinement claim.

Kernel selftests (GPL) and CPython process helpers informed negative cases. SLSA
is only a digest-handoff/separate-signing-stage analogy, not runtime isolation,
and was not copied. Linux's pinned cgroup-v2 documentation defines the domain
no-internal-process rule and recursive `cgroup.kill`/`populated` semantics:
<https://github.com/torvalds/linux/blob/8cd9520d35a6c38db6567e97dd93b1f11f185dc6/Documentation/admin-guide/cgroup-v2.rst>;
the GPL documentation is discussion-only. gVisor remains UNVERIFIED.
