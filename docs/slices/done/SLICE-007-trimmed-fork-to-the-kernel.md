# SLICE-007 — trimmed fork to the kernel

**Status:** done
**Closed:** 2026-08-03 — all five criteria proven; fork at six commits on `ranex-trim` (sibling repo `ranex-harness`); mutmut 3006 mutants, 1685 killed, 1011 survived (task CLI subprocess-excluded like e2e, weak evidence)
**Opened:** 2026-08-03
**ADR:** `docs/adr/ADR-008-fork-opencode-and-bridge-to-the-kernel.md`
**Closes:** ADR-008 runtime confirmation and `§17.5` gear-mesh. SLICE-006 is parked behind this slice.

## Design

1. **Fork at pin.** Fork `opencode` at tag `v1.18.11`, commit
   `012c2f57f976489d88bd4598a056b4bdcdd428ee`.
2. **Trim to keep-set.** Keep `opencode`, `core`, `cli`, `llm`, `plugin`,
   `protocol`, `schema`, `tui`, `server`, `sdk`, `effect-drizzle-sqlite`,
   `effect-sqlite-node`, and top-level `patches/`; cut the rest.
3. **Patch and manifest edits for cuts.** `script`, `codemode`,
   `http-recorder`, `effect-sqlite-node` and `ui` are cut by manifest edits and
   source edits, including `codemode` source edits, and `ui` retains only `tui`
   audio assets.
4. **Locked plugin set.** Keep no config/npm plugin paths. Lock plugin loading to
   a fixed list of built-ins.
5. **Commit-then-materialise bridge.** The harness runs a bridged plugin in
   `opencode` and emits a task/worktree reference plus commit ref.
   The dispatcher records task→worktree before run. On run end, the harness
   commits. The kernel reads the worktree HEAD itself, cross-checks the emitted
   reference against that same record, materialises the committed worktree, and
   evaluates evidence through existing `evaluate()`.
6. **Out-of-band approval remains.** The harness emits evidence only; no gate,
   merge, stamp or approver can be produced by the harness.

## Done criteria

Each criterion is met only when a test proves it. New coverage belongs in
`tests/integration/test_fork_trim_keep_set.py`,
`tests/integration/test_fork_startup_bridge.py`,
`tests/integration/test_kernel_materialise_reference.py`,
`tests/contract/test_plugin_lock.py`, and
`tests/e2e/test_gear_mesh_candidate_verdict.py`.

1. **Keep-set builds at the pin after trim.** Manifest edits for
   `script`/`codemode`/`http-recorder`/`effect-sqlite-node` and `ui`, and kept
   `patches/`, compile at the pinned tree. (`SLICE-007` must fail before each
   trim change and pass only when all edits land.)
2. **Harness does not start unbridged.** If the bridge hook is missing or
   unbound, `opencode` start fails closed.
3. **Kernel materialises committed work.** The kernel reads task→worktree
   itself, fetches the committed subject and verifies it against the emitted
   reference before judgement. Mismatch or missing records blocks.
4. **Plugin list is locked.** No config or npm plugins are accepted and no
   provider-auth plugin outside the locked built-ins loads.
5. **Gear-mesh verdict path is proof.** One task moves from dispatch to
   worker loop, then hooks, then kernel judgement and journal write with
   evidence and verdict `CANDIDATE`; no auto-approval is emitted.

## What this slice does not close

- **Confinement (`ADR-006` / `RISK-06`).** Same-uid key theft and journal
  rollback risk remain open.
- **Approver authentication (`RISK-07`).** Out-of-band approval is still
  unauthenticated.
- **Delegation.** No worker dispatch, supervisor routing, or clean-room
  orchestration is implemented here.
- **Handbooks.** Policy and operations handbooks remain unstarted.
