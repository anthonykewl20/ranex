# SLICE-070 — stable strict-local I/O namespace

**Status:** open
**Opened:** 2026-08-26
**Priority:** P0 — generic kernel prerequisite for SLICE-036
**Issue:** #47
**Parent tracker:** #11
**ADR:** `docs/adr/ADR-034-stable-strict-local-io-namespace.md`

## Contract

Additive strict-local v2 initially supports genuinely self-contained governed
executables. It gives them four runtime-owned stable I/O aliases for exact
objects held by the confinement descriptor:
`/ranex/input` read-only and cwd, `/ranex/toolchain` read-only,
`/ranex/output` writable under existing output bounds, and `/ranex/scratch`
writable under existing scratch bounds. The observed subject remains separately
read-only and recursively `MOUNT_ATTR_NOEXEC` at `/ranex/subject`; it is not
executable authority. V2 Landlock grants subject read-file/read-directory but
never execute, while the v1 policy remains byte-for-byte unchanged. The descriptor
retains source fields only. Destinations are launcher literals, never caller paths.

The launcher creates a private tmpfs root and fixed targets, clones each source
from its held directory FD with `open_tree`, recursively applies read-only with
`mount_setattr` to input/toolchain, attaches held mount FD to held target FD with
`move_mount`, pivots, and detaches the old root. Failure of any syscall, flag,
identity recheck, or target check refuses; path-preserving bind mount is not a
fallback. The worker cannot call mount APIs after seccomp.

Output-producing commands name artifacts explicitly beneath
`/ranex/output/...`. The existing bounded held-dirfd collector remains the
evidence owner and records relative path, byte count, inode count, and SHA-256.
Environment remains exactly `{LC_ALL,TZ}`; stdin and inherited data FDs stay
closed. No PATH, repository-geometry, caller-destination, or predecessor-input
channel is added. SLICE-036 C only orders after A/B and does not consume their
artifact bytes, so its smallest contract is the same four-name ABI.

Ordinary execution and strict-local v1 remain unchanged. Dynamic executables,
interpreters, shared-library search, extension modules, and runtime data are
unsupported in the initial v2 contract and refuse; #48 owns a future governed
runtime closure. There is no hidden host-root fallback. Operators invoke the existing public
launcher-build/install/qualify/session path under a delegated host unit, and
the existing qualification/host-drift checks remain authoritative.

## Owned paths

- `docs/adr/ADR-034-stable-strict-local-io-namespace.md`
- `docs/adr/prior-art/ADR-034/`
- `docs/slices/SLICE-070-stable-strict-local-io-namespace.md`
- `docs/slices/SLICE-036-approved-batch-qualification.md`
- `governance/confinement/strict-local-v2.json`
- `tests/contract/test_docs_discipline.py`
- `tests/integration/test_slice070_strict_local_io_contract.py`
- `tests/security/test_slice070_strict_local_io_security.py`
- `tests/e2e/fixtures/slice070-input.txt`
- `tests/e2e/fixtures/slice070-worker.c`
- `tests/e2e/fixtures/slice036-worker.c`
- `tests/e2e/fixtures/slice036-worker-build-v1.json`
- SLICE-036 schemas, fixtures, protected vectors, goldens, and frozen tests
- `tests/e2e/test_strict_local_io_real.py`
- `README.md` and `docs/STATE.md`

## Done criteria

1. The v2 parser admits only the exact profile schema and the public
   `strict-local` selector uses v2 without changing ordinary execution or v1.
2. Launcher tests prove held-source clone, recursive read-only application,
   held-target attach, private-root pivot/detach, and no legacy fallback.
3. Descriptor tests refuse unknown destinations, aliases, writable/authority
   overlap, absolute/remote/traversing/symlink-escaping refs before launch.
4. Security tests prove the worker cannot mount, write input/toolchain, execute
   an executable from the observed subject, inherit
   stdin/data FDs, expand env beyond `LC_ALL,TZ`, or escape output bounds.
5. On a qualified host, one mature delegated systemd unit invokes the existing
   public launcher-build, launcher-install, qualify, and session commands in
   order so qualification and execution share a real delegation identity.
6. A compiled self-contained static fixture reads a committed input through
   `/ranex/input`, observes input write refusal, produces
   `/ranex/output/result.txt`, and matches ordinary execution's result bytes.
7. The real journey independently verifies the tracked input, child exit,
   output file bytes, canonical collected path/size/SHA-256 rows, profile
   digests, and drained-teardown result. Undelegated use fails closed.
8. Existing strict-local v1, ordinary runs, output collection, qualification,
   host-drift, Landlock, seccomp, cgroup, and evidence tests remain green.

## Stable refusal order

Descriptor schema/path closure → source alias/overlap → qualification/host
drift → source/target held-object identity → private-root/mount setup → worker
enforcement → output bounds/collection. Any setup failure precedes worker exec;
any output refusal publishes no admissible result.

## Not owned

No SLICE-036 batch implementation, dependency
mechanism, signing/keyring authority, new environment/FD/stdin channel,
predecessor artifact namespace, harness, broker, provider, or publication work.
This SPEC PRD changes no `src/ranex` or native production source.

## Verification

```text
uv run --frozen pytest --collect-only -q
uv run --frozen pytest -q tests/integration/test_slice070_strict_local_io_contract.py
uv run --frozen pytest -q tests/security/test_slice070_strict_local_io_security.py
uv run --frozen pytest -q tests/e2e/test_strict_local_io_real.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen ruff check tests/contract/test_docs_discipline.py tests/integration/test_slice070_strict_local_io_contract.py tests/security/test_slice070_strict_local_io_security.py tests/e2e/test_strict_local_io_real.py
```

At SPEC PRD, profile/descriptor/security closure is green and implementation
tests are honestly RED only at the absent v2 parser, selector, mount assembly,
and real journey. Implementation starts only after independent review, owner
approval, OCR, fast-forward publication, and `status:ready` on #47.
