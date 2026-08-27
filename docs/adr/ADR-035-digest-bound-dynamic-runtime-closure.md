# ADR-035 — digest-bound dynamic runtime closure

**Status:** accepted
**Date:** 2026-08-26
**Decision-makers:** repo owner
**Slice:** `docs/slices/done/SLICE-072-digest-bound-dynamic-runtime-closure.md`

## Context and Problem Statement

Strict-local v2 intentionally admits only a self-contained static ELF. Dynamic
programs need an interpreter, transitive libraries, extension modules, and
runtime data. Installed glibc 2.39 still searched `/lib*` and `/usr/lib*` with
`--inhibit-cache` and an empty `--library-path`, so flags over a host root are
not closure. Ranex needs an approved native-runtime filesystem whose bytes and
resolution cannot drift or fall back to the host.

## Decision Drivers

- The invoked loader, entrypoint, native objects, and runtime data are exact bytes.
- Structured ELF parsing and the actual loader independently agree on closure.
- Destination prefixes and loader argv are profile literals; validated relative
  row paths select only children below their kind's fixed prefix.
- Verification and execution share one immutable, host-detached snapshot.
- No cache, `LD_*`, PATH, RPATH/RUNPATH, or host-root fallback exists.
- Ordinary execution and strict-local v1/static-v2 bytes remain unchanged.

## Prior art

- Searched: GitHub code search for glibc loader search, PatchELF dependency traversal, nixpkgs auto-patchelf closure assembly, pyelftools ELF parsing, Flatpak runtime mounts, bubblewrap private roots, and Linux sealed memfds; installed glibc 2.39, binutils 2.42, GCC 13.3.0, and PatchELF 0.18.0 were exercised locally.
- https://github.com/bminor/glibc/blob/ef321e23c20eebc6d6fb4044425c00e6df27b05f/elf/dl-load.c adopts the actual loader's distinct RPATH, RUNPATH, cache, command-line library path, default-directory, FILTER, and AUXILIARY behavior.
  License: LGPL-2.1-or-later.
  Weakness: glibc resolves names but does not approve bytes; its compiled default directories remain live whenever the host root is visible.
  Vendored: `docs/adr/prior-art/ADR-035/glibc-dl-load.c` blob:ce8fdea3024359b0d4f4aea90a49796003aeaa1d
- https://github.com/NixOS/patchelf/blob/99c24238981b7b1084313aca8f5c493bb46f302c/src/patchelf.cc adopts mature PT_INTERP, DT_NEEDED, SONAME, RPATH, RUNPATH, and dynamic-tag inspection semantics.
  License: GPL-3.0-or-later.
  Weakness: rewriting ELF headers breaks ordinary/strict-local byte parity, and this GPL source is evidence rather than copied production code.
  Vendored: `docs/adr/prior-art/ADR-035/patchelf.cc` blob:82b4b46c209128c6a61ccac67f18e8982301972b
- https://github.com/NixOS/nixpkgs/blob/63dacb46bf939521bdc93981b4cbb7ecb58427a0/pkgs/build-support/setup-hooks/auto-patchelf.sh adopts recursive dependency discovery and explicit runtime roots.
  License: MIT.
  Weakness: ignored missing edges and mutation are valid packaging conveniences but invalid governed admission behavior.
  Vendored: `docs/adr/prior-art/ADR-035/nixpkgs-auto-patchelf.sh` blob:783ea45f8eeb16c74ec5d1bb939dd462bd25c935
- https://github.com/eliben/pyelftools/blob/d4ea35fc3c34eb0e4d3f8cfafb31552f5b5c37d6/elftools/elf/elffile.py adopts a maintained structured ELF parser instead of a new byte parser.
  License: public domain.
  Weakness: metadata parsing cannot prove the glibc loader's realized resolution, so a separately confined loader probe is still required.
  Vendored: `docs/adr/prior-art/ADR-035/pyelftools-elffile.py` blob:e75bcf3b9de26814eb90b2f12c9daf7b5392e539
- Rejected: https://github.com/flatpak/flatpak/commit/3344a7a72ff2e3e728e31c846fff42bda14429dd — its runtime-extension machinery brings socket, device, deployment, and environment policy beyond this exact closure.
- Rejected: https://github.com/containers/bubblewrap/commit/a253257cd298892da43e15201d83f9a02c9b58b5 — its private root informed ADR-034, but directory bind mounts do not freeze descendant bytes against same-inode writes or replacement.

## Considered Options

1. Loader flags over the host root. Rejected: installed glibc found host defaults.
2. Patch PT_INTERP/RPATH. Rejected: executable bytes lose ordinary-mode parity.
3. Read-only bind a validated directory. Rejected: descendant bytes can drift.
4. Seal every approved source file, copy only those immutable bytes into a
   private tmpfs tree, and probe the held loader there before releasing the
   same snapshot. Chosen. Direct memfd mounts were rejected because the
   qualified Linux 7.0 host does not implement the January 2026 memfd-mount RFC.

## Decision Outcome

Add `ranex-strict-local-runtime-v3`, selected by repo-relative `--runtime-input-path` plus `--runtime-closure-root`; `--toolchain-root` remains static-v2-only and is forbidden in v3.
The closure contains the entrypoint at `/ranex/runtime/bin/...`, loader at `/ranex/runtime/loader/ld-linux-x86-64.so.2`, libraries/extensions under `/ranex/runtime/lib`, and data under `/ranex/runtime/data`; no toolchain mount exists.
Closed `closure.json` binds top-level ELF class/endian/machine/OSABI/ABI version, loader path/self-id/version/digest, entrypoint path/digest/PT_INTERP, literal `lib`, maximum 511 files, and canonical path-sorted rows; the separately sealed manifest is descriptor 512.
Each row binds path, octal mode, kind (`loader`, `entrypoint`, `shared-library`, `native-extension`, or `runtime-data`), SHA-256, and either null ELF metadata or exact class/endian/machine/OSABI/ABI/type/PT_INTERP/SONAME/DT_NEEDED; RPATH, RUNPATH, FILTER, AUXILIARY, AUDIT, DEPAUDIT, slash-bearing and `$` dynamic strings are refused.
The manifest is the sole source byte outside `files`: it is separately sealed/digested and mounted noexec; top-level loader/entrypoint facts must equal their corresponding rows, and rows cover every other source byte exactly.
Paths have at most 16 components/255 bytes, components follow the repository grammar, ancestors are directories only, and reserved `closure.json` cannot be a row. Kinds have fixed prefixes: loader under `loader/`, entrypoint under `bin/`, libraries/extensions under `lib/`, and data under `data/`; file/ancestor collisions refuse. The v3 profile pins the one admitted loader SHA-256, self-id, version, and architecture, so loader probing is an independently governed TCB, not closure self-attestation.
The controller copies each captured-commit regular file into a separately sealed memfd, rehashes it after sealing, parses that descriptor with pinned pyelftools 0.32, and passes only the derived path/kind/FD map; links, special files, undeclared bytes, path/SONAME duplicates, and unresolved edges refuse. Native rows use `MFD_ALLOW_SEALING|MFD_EXEC`; data and manifest use `MFD_ALLOW_SEALING|MFD_NOEXEC_SEAL`; declared mode is applied before `F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_FUTURE_WRITE|F_SEAL_EXEC|F_SEAL_SEAL`, then mode/seals are re-read. Qualification refuses kernels/`vm.memfd_noexec` settings that cannot provide those semantics.
The launcher creates a private tmpfs root, copies each sealed descriptor into its manifest-derived literal beneath `/ranex/runtime`, rechecks byte count and digest, and opens a detached mount for each private file. Native rows become read-only; data/manifest rows become read-only-noexec; input/subject become read-only-noexec; output/scratch become writable-noexec. After pivot and old-root detach the tmpfs source directory is inaccessible, so verifier and worker can reach only the same per-file mounted snapshot.
Before any data authority is attached, a sacrificial verifier in a distinct PID/cgroup lifecycle sees only the sealed runtime tree read/execute and a bounded report FD. It runs the profile-pinned held loader with `--inhibit-cache --glibc-hwcaps-mask '' --library-path /ranex/runtime/lib --list` for the entrypoint and every extension root. RPATH/RUNPATH safety comes from descriptor parsing and refusal; glibc's empty `--inhibit-rpath` argument is intentionally not used because it inhibits no object.
Verifier Landlock exposes no input, subject, output, scratch, host paths, other FDs, fork, or writes. The launcher kills the verifier cgroup, waits for population zero, verifies no descendants, and only then may attach worker authorities.
The exact path-sorted root list is controller-supplied. Each root produces one `u32be root-length + root + u32be report-length + report` frame, with a 64-KiB per-root and `roots * 64 KiB` overflow-checked total bound. Missing, duplicate, reordered, replayed, or trailing frames refuse. The controller strips addresses, requires the one kernel `linux-vdso.so.1` pseudo-row and held loader row, compares each root's realized transitive set with the pyelftools set, then sends one bounded GO/REFUSE acknowledgement; GO attaches input/subject/output/scratch and directly invokes the held loader and entrypoint in the immutable snapshot.
Parsed-graph canonical rows are `{path,needed}`; realized rows are `{root,resolved:[{name,path}]}`, with manifest-relative paths and all arrays path/name sorted before SHA-256.
The sealed-file-set digest covers canonical full manifest rows plus expected seal mask and mount attributes. Result-v2 also records per-path post-mount mode/seal/mount readback; it binds manifest, sealed-file-set, parsed-graph, realized-graph, loader, and v3-profile digests, and evidence signs its canonical result digest through the existing owner.
This is native dependency/filesystem closure, not a claim that an approved interpreter cannot interpret input or create anonymous/JIT code; nested execution is allowed only under existing limits and can resolve native file bytes only from sealed executable runtime rows.

### Consequences

- Good: interpreters, extensions, and data run from one exact host-detached tree.
- Good: verification and execution share one inaccessible private snapshot
  copied from sealed, rehashed descriptors rather than a mutable source directory.
- Good: no ambient toolchain, distribution root, or loader configuration survives.
- Bad: closures are architecture-specific and capped at 511 files plus one manifest descriptor.
- Bad: runtime data may need deterministic archives to stay within that bound.
- Bad: interpreted/JIT semantics and requested-but-absent late module names are not predicted.

### Confirmation

Ungated tests freeze closed schemas, sealed-FD immutability, selector/source
admission, exact graph normalization, v1/v2 bytes, and result-v2 validation.
Qualified-host tests independently invoke the public commands, inspect result
and evidence bytes, and exercise real Python startup, native import, runtime
data, direct `dlopen`, explicit-loader attempts against valid ELF probes,
mount/file tampering,
and each input/output/scratch/subject noexec boundary without trusting worker
or implementation-generated booleans.

## Improvements on the prior art

1. Pair glibc's realized transitive sets with pyelftools-derived sets and an approved manifest.
2. Replace auto-patchelf's mutation/ignored-missing mode with closed unique edges.
3. Preserve executable bytes by direct loader invocation rather than ELF mutation.
4. Replace mutable directory binds with sealed source descriptors, exact
   private-file copies, and one verify-then-GO snapshot.

## Architecture surface

`src/ranex/cli/main.py` owns selectors/materialization; a new foundation owner
uses pinned pyelftools and sealed memfds; `host_confinement.py` owns command-v2,
profile-v3, verifier handshake, and result-v2; the native launcher owns literal
mounts and loader execution. New runtime/result schemas are additive. Existing
v1/v2 profiles, command-v1, result-v1, and launcher branches remain immutable.

## Scope and threat delta

The trusted controller gains ELF parsing and sealed-file creation, not native
payload execution. The confined verifier alone runs the supplied loader before
GO and has only the final snapshot plus its bounded report pipe. Workers gain
read/native-execute access to sealed runtime files. Same-UID controller, kernel,
malicious interpreter semantics, anonymous/JIT code, packaging, and publication
remain outside the claim. V3 has a separate closed syscall policy, qualified
against the exact frozen Python workload; additions over static-v2 are recorded
in the profile and security tests, while cgroup/network limits remain.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Security | source mutates after admission | sealed bytes/result digests unchanged or refuse |
| Closure | missing/host-only/ambiguous native edge | verifier refuses before worker GO |
| Determinism | two materializations of identical input/closure | identical output and six runtime digests |
| Compatibility | ordinary, v1, or static-v2 call | unchanged public behavior and pinned bytes |
| Auditability | admitted dynamic run | result-v2 and signed evidence bind exact closure |

## Reversibility

Door: two-way

The additive selector/profile/command/result versions can be disabled without
changing ordinary, v1, or static v2. Published manifests remain immutable;
widening paths, tags, file bounds, or claims needs a superseding schema/ADR.

## Sad paths

- Either v3 selector is missing/duplicated/absolute/remote/traversing/symlinked/untracked/dirty/wrong-base/overlapping, or toolchain is supplied → refuse.
- Manifest is noncanonical, unknown-field, unsorted, over 511 rows, duplicate, violates kind prefixes/path/component bounds, collides with an ancestor/reserved path, or disagrees with the exact source tree → refuse.
- Source row is a link/special file or changes during copy; a sealed memfd can still write/grow/shrink or its post-seal digest differs → refuse.
- ELF identity/type/PT_INTERP/loader self-id/version differs from the manifest or architecture → refuse.
- NEEDED contains slash/`$`, SONAME is duplicate, or an edge is missing/ambiguous → refuse.
- RPATH/RUNPATH/FILTER/AUXILIARY/AUDIT/DEPAUDIT or another forbidden loader-affecting tag exists → refuse.
- Pyelftools closure differs from manifest → refuse before native loader execution.
- Private snapshot mount identity/flags, pivot/detach, or sealed-file map differs → refuse.
- Confined loader probe crashes/times out, emits malformed/oversize/extra pseudo rows, resolves outside runtime, or differs from parsed closure → REFUSE, never GO.
- Controller disappears or sends malformed/duplicate/late acknowledgement → verifier/session teardown; no worker/output.
- Runtime data/manifest is executable, or input/subject/output/scratch noexec is absent → refuse before probe.
- Mutation during copy yields either the exact declared sealed digest or refusal;
  source replacement/submount changes cannot alter the post-seal snapshot.
- Computed `dlopen` requests an undeclared name → loader failure inside private root, not host fallback.
- Direct loader names a noexec non-runtime file → kernel mapping denial; a declared runtime native row may execute under existing limits.
- Result-v2 runtime digest/graph/file row is absent, malformed, inconsistent, or rejected by evidence consumer → no admissible evidence.
- Qualification/host binding, existing limits, output bounds, or teardown fails → existing refusal and no admissible result.

## Test strategy

`tests/integration/test_slice072_dynamic_runtime_contract.py` freezes schemas,
manifest validation, sealed memfds, graph derivation/normalization, selectors,
result-v2 consumer, and ordinary/v1/v2 compatibility.
`tests/security/test_slice072_dynamic_runtime_security.py` freezes the profile,
multi-root verifier decisions, lifecycle, and launcher structure. Executable
black-box mount/noexec, explicit-loader, and qualified pre-GO lifecycle cases
live in `tests/e2e/test_dynamic_runtime_closure_real.py`; source-copy invariants
live in the integration suite. The E2E directly drives public
build/install/qualify/run commands and independently hashes outputs, manifests,
file sets, graphs, results, and evidence on a qualified host.
`tests/contract/test_docs_discipline.py` freezes the ADR/slice lifecycle.

## Code review checklist

- Verify every mounted runtime file is copied from a sealed, manifest-derived
  descriptor and its private source path is inaccessible after pivot.
- Verify loader execution occurs only in the private verifier/final snapshot.
- Verify direct/transitive/pseudo-row normalization and all forbidden dynamic tags.
- Verify GO is single-use, bounded, controller-decided, and precedes worker effect.
- Verify result-v2 production and consumption bind all six runtime digests.
- Verify black-box tests observe kernel/process/filesystem state independently.
- Verify ordinary/v1/static-v2 bytes, schemas, and public behavior stay unchanged.

## More Information

Issue #48 records Option B approval on 2026-08-26. Installed evidence used
glibc 2.39 and binutils 2.42. Linux `mmap(2)` documents `EPERM` for PROT_EXEC on
a noexec filesystem; `fcntl(2)` defines immutable memfd seals. ADR-034 supplies
the inherited private-root/I/O boundary and same-UID controller residual.
