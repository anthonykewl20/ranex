# ADR-034 — stable strict-local I/O namespace

**Status:** proposed
**Date:** 2026-08-26
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-070-stable-strict-local-io-namespace.md`

## Context and Problem Statement

Strict-local v1 preserves host paths and starts in the scratch directory. An
approved command can therefore be valid yet unable to name its committed input
or bounded output without knowing controller geometry. SLICE-036 demonstrates
the defect: its signed child derives an input path from scratch cwd, although
the launcher deliberately supplies neither repository cwd, stdin, PATH, nor a
data FD. A generic I/O ABI is required before that batch contract can resume.

## Decision Drivers

- Commands name stable runtime locations, never controller or checkout paths.
- Descriptor-held filesystem objects remain the authority root.
- Input/toolchain are recursive read-only; subject is recursive read-only and
  no-exec; output/scratch retain existing bounds.
- No fallback, environment, stdin, inherited-data-FD, or predecessor channel.
- The launcher, not the worker, owns all mount syscalls and target creation.

## Prior art

- Searched: GitHub code search, bubblewrap tags/Ubuntu source package, util-linux mount hooks, installed Linux 6.8 headers, and Linux man-pages for fd-based mount assembly.
- https://github.com/containers/bubblewrap/blob/a253257cd298892da43e15201d83f9a02c9b58b5/bubblewrap.c adopts fd-delayed source resolution, private tmpfs root construction, `pivot_root`, and old-root detach.
  License: LGPL-2.0-or-later.
  Weakness: upstream bind-fd still accepts caller-selected target paths and bubblewrap is a standalone policy engine; Ranex needs four fixed I/O targets plus a fixed observed-subject target and its existing evidence path. Ubuntu 0.9.0's backport additionally lacks upstream a253's post-mount dev/inode source identity comparison, so it is evidence of the unsafe shortcut, not the implementation owner.
  Vendored: `docs/adr/prior-art/ADR-034/bubblewrap.c` blob:bc75da470aec092ec9bdd08c240870507acedd47
- https://github.com/util-linux/util-linux/blob/c1c1ab8b8e67e04ee293d4cf5679430a5b174bb8/libmount/src/hook_mount.c adopts the kernel's `open_tree` → `mount_setattr` → `move_mount` order for recursive read-only mounts.
  License: LGPL-2.1-or-later.
  Weakness: libmount resolves a configured target path; it does not create a private root or bind the closed four-name I/O ABI plus observed subject.
  Vendored: `docs/adr/prior-art/ADR-034/util-linux-hook_mount.c` blob:f0cc381963dba1dbdabe9b5887b9877e8035adb9
- Rejected: https://github.com/landlock-lsm/landlock/blob/main/samples/sandboxer.c — Landlock restricts access but neither creates stable names nor makes a tree read-only.
- Rejected: https://github.com/opencontainers/runc/blob/main/libcontainer/rootfs_linux.go — OCI mount configuration admits caller-selected destinations and a far broader runtime authority surface.

## Considered Options

1. Keep scratch-relative paths. Rejected: command behavior depends on hidden geometry.
2. Add PATH, stdin, inherited FDs, or destination fields. Rejected: each is a new unbounded authority channel.
3. Use installed bubblewrap `--bind-fd`. Rejected: the installed backport omits the mature post-mount identity recheck and still accepts target paths.
4. Assemble runtime-owned fd-bound mounts in the launcher. Chosen: the current launcher already holds every source and owns the namespace transition.

## Decision Outcome

Add `ranex-strict-local-runtime-v2`: create a private tmpfs root with literal
`/ranex/{input,toolchain,output,scratch,subject}`, pivot, and detach the old root.
Clone held sources with `open_tree` and exact empty-path/recursive flags; apply
`MOUNT_ATTR_RDONLY` (`0x00000001`) to input/toolchain and
`MOUNT_ATTR_RDONLY|MOUNT_ATTR_NOEXEC` (`0x00000009`; installed Linux 6.8 spells
`MOUNT_ATTR_NOEXEC` as `0x00000008`) to subject; attach with empty-path
`move_mount`. Any unavailable API, identity/target mismatch, or fallback refuses.
Input is read-only cwd, toolchain is read-only executable authority, subject is
read-only/no-exec, and output/scratch retain descriptor and collector bounds.
Descriptors carry sources, never destinations; artifacts use
`/ranex/output/<relative>`. Env remains `LC_ALL,TZ`; stdin/data FDs stay closed.
V2 Landlock gives subject read-file/read-dir but never execute. V1's existing
executable subject/toolchain Landlock policy and worker seccomp remain unchanged.

### Consequences

- Good: genuinely self-contained governed executables receive stable input/output semantics without checkout knowledge.
- Good: fixed destinations cannot be redirected by descriptor or worker input.
- Good: legacy ordinary execution and strict-local v1 bytes remain unchanged.
- Bad: v2 requires Linux new mount API support and a qualified delegated host.
- Bad: dynamic executables, interpreters, shared-library search, extensions, and runtime data are unsupported and refuse in the initial release; #48 owns a separately governed closure. The ABI never exposes the host root.
- SLICE-036 C is ordering-only: it reads no A/B artifacts, so no predecessor namespace is added.

### Confirmation

The ungated tests freeze the v2 parser, fixed target vocabulary, exact syscall
flags, private-root transition, legacy preservation, descriptor-source closure,
and worker mount refusal. Descriptor tests refuse aliases, writable/authority
overlap, and traversal before launch. On a qualified delegated host, one unit
runs the public build/install/qualify/session sequence; a static arbitrary-code
fixture proves committed input read-only, explicit output creation, ordinary
copy parity, canonical output hashes, profile digests, and drained teardown.

## Improvements on the prior art

1. Replace bubblewrap's caller destination with four runtime-owned I/O literals plus the fixed observed-subject literal.
2. Keep source and target FDs held through attach and compare named/held identity.
3. Combine util-linux's new-mount order with a private root and no legacy fallback.
4. Keep existing qualification, host-drift, Landlock, seccomp, cgroup, output collection, and evidence owners rather than creating another sandbox policy engine.

## Architecture surface

The implementation owner is `native/ranex-worker-launcher/launcher.c`; the
closed parser and public selector remain in `src/ranex/cli/host_confinement.py`
and `src/ranex/cli/main.py`. The profile is
`governance/confinement/strict-local-v2.json`. SLICE-070 owns tests only during
this specification freeze; no production source changes in the SPEC PRD.

## Scope and threat delta

The trusted launcher gains mount-FD assembly authority before worker seccomp.
Workers gain read access to exact input/toolchain and bounded write access to
exact output/scratch at stable aliases; they gain no host path, env, stdin, FD,
network, mount, or predecessor authority. Same-UID controller and host
qualification residuals from ADR-024/SLICE-017 remain unchanged.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Security | alias, overlap, traversal, or mount attempt | refuse before worker effect |
| Determinism | same program and committed input | same output bytes and SHA-256 |
| Portability | host lacks a required new mount API | named fail-closed refusal |
| Compatibility | ordinary or strict-local v1 invocation | unchanged semantics/bytes |
| Auditability | output collection | exact profile digests and path/size/hash rows |

## Reversibility

Door: two-way

The additive v2 profile can be disabled while v1 and ordinary
execution remain. Once approved specifications bind `/ranex/*`, removing or
renaming those aliases requires a superseding ADR and re-approval.

## Sad paths

- Input/toolchain/output/scratch source aliases another object → `E-C18-PATH-ALIAS`.
- Writable source is ancestor/descendant of authority source → `E-C18-PATH-ALIAS`.
- Source traversal, symlink escape, absolute path, or remote spelling → refuse before open.
- Descriptor supplies a destination or unknown field → closed-schema refusal.
- Fixed target is absent, substituted, non-directory, or aliased → refuse before attach.
- `open_tree`, `mount_setattr`, `move_mount`, pivot, or detach is unavailable/fails → no fallback; refuse.
- Held source and named source identity differ before or after attach → refuse.
- Input/toolchain recursive read-only application fails → refuse before worker exec.
- Subject recursive read-only/no-exec application fails, or a subject executable
  is requested → refuse before worker effect.
- Worker attempts input/toolchain write → kernel denies; no input mutation.
- Worker invokes mount-family syscall → seccomp refusal.
- Output path is outside `/ranex/output`, traverses, aliases, links, or exceeds a bound → existing collector refusal.
- Dynamic executable or interpreter requested before #48 → explicit unsupported refusal, never host-root fallback.
- Qualification or host binding drifts → existing host-drift refusal.
- Caller requests predecessor artifacts → closed profile/descriptor refusal.

## Test strategy

`tests/integration/test_slice070_strict_local_io_contract.py` freezes the profile,
parser/selector RED seams, descriptor closure, aliases, overlaps, and traversal.
`tests/security/test_slice070_strict_local_io_security.py` freezes syscall order,
fixed targets, private-root detach, and post-setup mount denial.
`tests/e2e/test_strict_local_io_real.py` is ungated RED at launcher v2 and host-gated
for the public delegated journey. Its subject authority is a distinct tracked
sibling worktree; the journey asserts both-direction realpath non-overlap with
every I/O authority and an unchanged clean tracked-tree fingerprint across the
ignored subject-exec refusal calibration. Its top-level executable remains the
held toolchain worker; committed input alone selects a fixed child `execve` of
`/ranex/subject/.local/subject-worker`. Kernel `EACCES`, successful exec, and
other errno map to distinct frozen exits through a shared anonymous errno cell,
and the expected denial has zero
collected output and no side effect. This supplements the public
`E-C18-GATE` refusal for subject-selected top-level argv.
`tests/contract/test_docs_discipline.py`
freezes the `blocked` status token while preserving at-most-one `open` slice.

## Code review checklist

- Verify source and target objects stay held and identity-checked through attach.
- Verify targets are exactly the four I/O literals plus observed subject and never descriptor fields.
- Verify recursive read-only and subject `MOUNT_ATTR_NOEXEC` precede attach and
  worker exec; v2 Landlock never grants subject execute while v1 stays unchanged.
- Verify old root is detached and mount syscalls are absent from worker seccomp.
- Verify output evidence comes from the held bounded collector root.
- Verify no PATH/stdin/data-FD/env/predecessor expansion.
- Verify v1 and ordinary behavior remain unchanged.

## More Information

Official syscall contracts: https://man7.org/linux/man-pages/man2/open_tree.2.html,
https://man7.org/linux/man-pages/man2/mount_setattr.2.html, and
https://man7.org/linux/man-pages/man2/move_mount.2.html. Issue #47 owns
SLICE-070; issue #19/SLICE-036 remains blocked until this prerequisite lands.
