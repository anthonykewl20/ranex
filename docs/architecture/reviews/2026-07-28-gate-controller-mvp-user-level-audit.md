# Gate-controller MVP user-level audit

| Field | Value |
|---|---|
| Review ID | `REV-GATE-MVP-USER-001` |
| Date | 2026-07-28 |
| Subject | Uncommitted gate-controller MVP in `.claude/worktrees/gate-controller-mvp` |
| Committed base | `0533e1eaf50ace0eb84435a5c3de05e939fd4daa` |
| Auditor | Fresh read-only validation worker |
| Decision authority | Human owner |
| Verdict as an R&D tracer | `PASS_WITH_BLOCKERS` |
| Verdict as live workflow authority | `REJECT` |

This record separates mechanical test success from authority fitness. The
prototype is useful for learning and fail-closed-path development. It is not a
deployed Ranex gate, must not authorize live transitions, and must not be
described as the hard gate required by the accepted architecture.

## 1. Reproduced automated evidence

The test wrapper initially failed in the worktree because no local virtual
environment existed. Reusing the phase-2 runtime interpreter also failed:
all seven selected files stopped at collection with
`ModuleNotFoundError: No module named 'ranex'` because that interpreter's
editable install targets the phase-2 worktree.

The auditor then created an isolated temporary environment, installed the
gate-controller worktree as editable, and executed:

```bash
HERMES_PYTHON=/tmp/ranex-gate-audit.SQu8PQ/venv/bin/python \
scripts/run_tests.sh \
  tests/unit/ranex/test_gate_controller.py \
  tests/unit/ranex/test_hash_chain_ledger.py \
  tests/unit/ranex/test_evidence_artifact_verifier.py \
  tests/contract/ranex/test_gate_json_schemas.py \
  tests/contract/ranex/test_mvp_gate_policy.py \
  tests/integration/ranex/test_sqlite_gate_authority.py \
  tests/e2e/ranex/test_gate_cli.py -q
```

Observed result:

```text
7 files
46 tests passed
0 failed
runner wall time 0.8 s
```

The captured suite log had SHA-256
`297be2d744e3bca0ae5163c2c84ad48f240defbe48965a9e0c7d10ff2f46a6f40c3bb9e`.
`ruff check` passed. `ty check src/ranex` exited 0 with one warning about
explicitly importing `yaml.resolver` at `policy_loader.py:57`.

The out-of-box environment failures remain real developer-experience defects.
The isolated install proves the selected code can pass its own suite; it does
not erase those failures.

## 2. Protections that worked

| User-level case | Observed result |
|---|---|
| No evidence | Exit 3, `UNKNOWN`, `MISSING_BLOCKING_EVIDENCE`; state and version unchanged |
| Wrong candidate commit | Exit 3, `WRONG_SUBJECT_EVIDENCE`; state unchanged |
| Caller adds `authorized: true` | Exit 2; schema rejects the extra field |
| Artifact digest mismatch | Exit 2; state unchanged |
| Two concurrent identical transitions | One exit 0 and one exit 2; final version exactly 1 |
| Relay replay | First pass published four events; replay published zero |
| Ledger record edited without recomputing chain | Verification exit 4 at broken sequence 1 |
| Relay receives invalid chain | Exit 4; append refused |
| Local authority database and ledger permissions | Mode `0600` |

These are useful tracer properties. They do not close the proof, identity, or
authority gaps below.

## 3. Blocking user-level bypasses

### 3.1 Caller-forged execution evidence was accepted

The auditor created a 76-byte artifact containing:

```text
This is arbitrary caller-controlled text; no recorded command was executed.
```

Its SHA-256 was
`1c2ef7616494817e2809a31a53771d804dda8d6bf79f6fa4de32c16347fe8d`.
Seven caller-authored records claimed `PASS`, named invented producer
identities, and asserted this command:

```text
definitely-not-a-real-command --proof
```

The request exited 0, returned `authorized: true`, and advanced the work item
from `IN_PROGRESS` to `VERIFICATION`. The forged bundle's SHA-256 was
`eca3ed85007452eee8f021051e695a9fdcdfd91b6c389ff96aa8a31e90dcf003`.

The current implementation proves that bytes match a caller-supplied digest.
It does not prove that a command ran, the reported exit code is authentic, the
producer has the asserted identity/role, or the observation belongs to an
isolated execution.

### 3.2 One real artifact proved unrelated claims

The same genuine 46-test log was reused for all seven claims, including:

- a diff exists;
- static checks executed;
- exit codes were captured;
- negative cases executed;
- findings were classified; and
- technical review was independent.

The gate authorized the transition. Claim identifiers currently have no
claim-specific validator or evidence schema. Artifact integrity is therefore
being mistaken for claim validity.

### 3.3 Canonical state could be fabricated at registration

`register --state CLOSED` returned exit 0 and created a version-0,
canonical-looking closed item without evidence, an evaluation, or an audit
transition. A seed/import capability may be legitimate for fixtures or
controlled migration, but it cannot be the normal caller-accessible creation
path for authority-bearing state.

### 3.4 The hash chain is not tamper-resistant

After changing a decision and recomputing the public hash chain,
`verify-ledger` returned exit 0 and `valid: true`. The current chain detects
accidental or unrecomputed edits. It does not protect against an actor that
can rewrite and rehash the ledger.

## 4. Conflicts with the accepted architecture

1. [Ground-zero architecture](../HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md)
   and the [Core SDLC](../CORE_SDLC_OPERATING_MODEL.md) assign
   `WorkItemStatus` transitions to `work_management`. The prototype's
   `governed_execution` store directly owns and updates `work_items`.
2. The canonical `GateOutcome` set contains `PASS`, `FAIL`, `UNKNOWN`,
   `CONFLICT`, `NOT_APPLICABLE`, and `CHECKER_FAULT`. A waiver is a
   `HumanDecision`, not a gate outcome. The prototype adds `WAIVED` and omits
   `CHECKER_FAULT`.
3. Canonical gate namespaces use `SDLC-*`, `AI-G*`, `MAP-*`, and
   `SDLC-ADOPT-*`. The prototype invents generic `GATE-*` identities.
4. Canonical exact-subject binding includes run, activity, workspace, base
   commit, packet digest, workflow version, policy snapshot, module profile,
   and aggregate version. The prototype binds only a reduced subset.
5. The policy catalog says `R_AND_D`, but neither `GateAuthority` nor
   `GateController` enforces that status. The R&D catalog authorized a state
   transition. Catalog owner metadata is parsed and then discarded.
6. `REQUIRED`, `ADVISORY`, and `EXPERIMENTAL` policy semantics are not
   evaluated. Only blocking-rule handling and presence of human-decision rules
   are materially implemented.
7. The prototype's `VERIFICATION -> RELEASE_READY` gate omits the immutable
   artifact, manifest/SBOM, migration, rollback, runbook, communications,
   observation, and release-authority burdens required by the Core SDLC.

## 5. Documentation and provenance defects

- The documented `init` example omits required `--evidence-root`.
- The documented `request` example supplies unsupported `--ledger`,
  `--policy`, and `--evidence-root` options and exits 2.
- `RULES-THERY.md` is a misspelled pasted AI response, not registered
  normative policy, yet the prototype gate catalog derives its five gates
  from it.
- At audit time, the gate worktree's older `SOURCE_OF_TRUTH.md` said the
  now-deleted `RANEX_IMPLEMENTATION_GUIDE.md` remained a capability checklist.
- The entire prototype is staged/unstaged work and is absent from the
  worktree's committed `HEAD`.
- No `ranex-gate` executable, authority service, live authority database, or
  live ledger is installed in the Ranex runtime.

Post-audit closure note (2026-07-28): the active-looking
`SOURCE_OF_TRUTH.md` and branding references in the phase-1, phase-2, and gate
worktrees were amended to state that the guide is retired, deleted, prohibited
as implementation input, and must not be reconstructed. The tracked guide is
physically absent and recorded as a deletion in all five worktrees. Historical
research citations remain provenance only. This closes the
documentation-contamination finding; it does not change the prototype's
live-authority rejection.

## 6. Required closure before live authority

Do not add more gates yet. Close one truthful vertical authority route first:

1. rebase the prototype onto the accepted source of truth and remove
   `RULES-THERY.md` as a policy source;
2. resolve state ownership between `work_management` and
   `governed_execution` through an ADR and typed contract;
3. align outcomes, identifiers, exact-subject fields, rule levels, catalog
   activation, and owner semantics with the canonical contracts;
4. move evidence production behind trusted execution collectors with
   authenticated workload identity and claim-specific validators;
5. separate privileged bootstrap/import from normal work registration;
6. protect the ledger with an append authority and integrity root outside the
   writer's rewrite boundary;
7. encode the demonstrated forgery, claim-reuse, rehash, and registration
   bypasses as mandatory negative tests; and
8. rerun independent user-level acceptance against an installed candidate,
   not only an editable test environment.

Until all eight close with bound evidence, Hermes and every model remain
proposal producers and the human owner remains the only decision authority.
