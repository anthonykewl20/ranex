# SLICE-072 — digest-bound dynamic runtime closure

**Status:** done
**Opened:** 2026-08-26
**Completed:** 2026-08-28
**Priority:** P0 — complete strict-local dynamic execution
**Issue:** #48
**ADR:** `docs/adr/ADR-035-digest-bound-dynamic-runtime-closure.md`

## Contract

Implement ADR-035 as an additive strict-local v3 branch selected by exactly
`--runtime-input-path` plus `--runtime-closure-root`; static v2 retains its
existing input/toolchain pair. V3 admits a canonical manifest, turns every
captured-commit runtime file into a separately rehashed sealed memfd, and copies
only those immutable bytes to manifest-derived literals beneath
`/ranex/runtime` in an inaccessible private tmpfs. Per-file mounts expose that
one snapshot to verifier and worker. It has no toolchain mount or host fallback.

Pinned pyelftools derives each native root's transitive set. A sacrificial
confined verifier runs the held loader in the same immutable snapshot; the
controller independently normalizes its bounded report and sends one GO only
when both sets match. The launcher then directly invokes the loader/entrypoint.
Result-v2 and existing signed evidence bind the manifest, sealed file set,
parsed graph, realized graph, loader, and profile digests.

The claim is native filesystem/dependency closure. It includes a top-level
interpreter, transitive libraries, native extensions, runtime data, computed
missing-name refusal, and declared nested runtime execution. It does not claim
to constrain interpreted/JIT bytes or malicious interpreter behavior and adds
no package building, mutable caches, caller destinations, publication, fanout,
predecessor artifacts, or new environment/stdin/data-FD authority.

## Owned paths

- ADR-035, its prior-art directory, this slice, README, and `docs/STATE.md`
- `governance/confinement/strict-local-v3.json`
- dynamic-runtime manifest, command-v2, and result-v2 schemas under `governance/schemas/confinement/`
- `src/ranex/cli/main.py`, `src/ranex/cli/host_confinement.py`, and `src/ranex/foundation/dynamic_runtime.py`
- `native/ranex-worker-launcher/launcher.c` and its build manifest
- `pyproject.toml` and `uv.lock` for pinned pyelftools 0.32
- the three frozen SLICE-072 suites and their tracked fixtures/goldens

## Done criteria

1. Integration tests prove dynamic selectors are single, canonical, tracked,
   clean, captured-base, disjoint, strict-local-only, paired with each other,
   and incompatible with `--toolchain-root`; static v2 remains valid.
2. Schema/fixture tests prove exact ABI/loader/entrypoint/path/mode/kind/digest/
   ELF shapes, canonical row order, 511-file-plus-manifest bound, exact source coverage, and
   rejection of links, specials, duplicates, forbidden tags/strings, missing,
   ambiguous, and architecture-incompatible edges.
3. Real sealing tests prove captured bytes are copied to separate memfds,
   post-seal SHA-256 matches, WRITE/GROW/SHRINK/FUTURE_WRITE/EXEC/SEAL and per-kind memfd
   execution flags hold, and source mutation either preserves declared bytes or refuses.
4. Graph tests use real ELF fixtures to prove pyelftools direct/transitive sets
   and normalized held-loader sets match per entrypoint/extension root, with
   exact loader/VDSO handling and missing/host-default/extra/malformed refusal.
5. Security tests prove the launcher copies only sealed-FD bytes to fixed
   runtime paths in private tmpfs, verifies each copy, applies per-kind
   read-only/noexec plus noexec data authorities, pivots and detaches,
   confines/drains a runtime-only verifier before attaching data authorities,
   and releases no worker/output without one timely controller GO.
6. Black-box probes independently prove direct `dlopen`, mmap(PROT_EXEC),
   execve, execveat, and explicit-loader attempts using known-valid ELF pairs
   from input, subject, output, scratch, and runtime-data are denied; manifest
   noexec is proven by mmap(PROT_EXEC); declared runtime-native rows
   and declared nested execution work only under existing limits.
7. Result-v2 producer/consumer tests require canonical manifest/file-set/
   parsed-graph/realized-graph/loader/profile digests and prove signed evidence
   binds the exact result digest; absent, reordered, or substituted data refuses.
8. A qualified-host E2E directly invokes public build/install/qualify/run,
   starts tracked Python, imports a native extension, reads runtime data, writes
   bounded output, independently matches ordinary native-import/runtime-data
   semantics plus all six
   runtime/evidence digests across two independent sealed materializations and
   byte-compares the collected output artifact with its golden.
9. The E2E independently removes/substitutes loader/entrypoint/library/extension/data,
   requests bare host-only and absolute old-root modules,
   and proves every refusal precedes output and leaves no survivor.
10. Focused ordinary, strict-local v1/static-v2, qualification, host-drift,
    v3's exact additive seccomp policy, Landlock, cgroup, output, evidence, broader confinement, and full
    repository suites remain green; pinned v1/v2/schema bytes are unchanged.

## Stable refusal order

Selector/base binding → manifest/tree closure → sealing/post-seal digest →
pyelftools graph → qualification/host drift → private snapshot/readback →
confined realized graph → controller GO → worker enforcement → result/evidence.

## Not owned

No mutation of existing profiles/schemas/branches, interpreted/JIT-code policy,
package resolver/builder, host library/cache/path fallback, caller destination,
new env/stdin/data FD, publication/fanout, harness, provider, or broker work.
This SPEC PRD checkpoint changes no production source.

## Verification

```text
uv run --frozen pytest -q tests/integration/test_slice072_dynamic_runtime_contract.py
uv run --frozen pytest -q tests/security/test_slice072_dynamic_runtime_security.py
uv run --frozen pytest -q tests/e2e/test_dynamic_runtime_closure_real.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen ruff check tests/integration/test_slice072_dynamic_runtime_contract.py tests/security/test_slice072_dynamic_runtime_security.py tests/e2e/test_dynamic_runtime_closure_real.py
```

The SLICE-072 suites were frozen RED in specification commit `0053024fa`.
Implementation acceptance ran the focused integration/security/compatibility
suites and the qualified-host E2E, with the full repository and mutation gates
recorded in the closing issue proof.
