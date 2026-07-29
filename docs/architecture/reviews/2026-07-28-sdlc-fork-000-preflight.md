# SDLC-FORK-000 Fork Ancestry and Provenance Preflight

| Field | Value |
|---|---|
| Review ID | `REVIEW-SDLC-FORK-000-20260728` |
| Gate | `SDLC-FORK-000` |
| Version | `1.0.0` |
| Status | `BLOCKED` |
| Predicate result | `FAIL` |
| Observation window | 2026-07-28T09:33:54Z–2026-07-28T09:40:05Z |
| Mode | Deterministic read-only inspection |
| Construction subject | `bootstrap/pre-upstream@4baad4a67843b02d5970f442fb54aed8d6525dda`; dirty worktree |
| Audited upstream baseline | `d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012`, tree `129a441930d11bc6bace9c72e81c960289008898` |
| Evidence | [`sdlc-fork-000-evidence.json`](./artifacts/enterprise-build-readiness/sdlc-fork-000-evidence.json) |
| Mutations | This review and its evidence file only; no Git/ref/worktree/remote mutation |
| Decision authority | Human owner |

## Verdict

`SDLC-FORK-000` is **BLOCKED**. The current construction head has no merge
base with the accepted Hermes baseline, is not descended from it, omits the
upstream `LICENSE`, and is accompanied by a dirty worktree rather than one
immutable exact construction subject. No runtime implementation commit may be
accepted on this construction line.

This is not evidence that an ancestry-safe line is unavailable. The existing
`main`, `phase/1-adopt-upstream`, and `develop` refs all descend from the
accepted upstream commit. The preflight fails because the active construction
subject is not bound to that line and the remaining preservation/provenance
records are incomplete.

## Exact subject and baseline ledger

| Baseline role | Exact observation | Result |
|---|---|---|
| Current construction | `bootstrap/pre-upstream@4baad4a67843b02d5970f442fb54aed8d6525dda`, tree `418fe1aaf4207209906abda88afc05e30c07d72c` | No merge base with accepted baseline |
| Audited/accepted upstream | `d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012`, tree `129a441930d11bc6bace9c72e81c960289008898` | Local commit object and annotated tag verified |
| Incorporated on adoption line | `phase/1-adopt-upstream@9be6bd9443e447b205ad265d44238436910dfbce`; its sole parent is the accepted baseline | Upstream-derived |
| Published construction candidate | `develop@0533e1eaf50ace0eb84435a5c3de05e939fd4daa`, five commits after accepted baseline | Upstream-derived and observed on `origin/develop` |
| Locally fetched latest seen | `upstream/main@8eaaa5021c098544044cae3dd546f0a011104c1a`, nine commits after accepted baseline | Local tracking ref; accepted baseline is ancestor |
| Remote latest seen | `upstream/main@1dfe781edd5e96d09511cf27d800a03e63b09789`, tree reported as `a7cb751b299debd19dcc5473c825da7da002ccea` | Observed remotely, not fetched or incorporated |

Observed, audited, incorporated, locally fetched, and remotely latest-seen
baselines are deliberately different fields. The remote latest-seen commit
does not silently change the accepted or incorporated baseline.

## Gate predicate results

| Required proof | Result | Evidence |
|---|---|---|
| Immutable bootstrap preservation | `FAIL` | HEAD has no tag and no observed `origin/bootstrap/pre-upstream`; the local branch is mutable and the dirty delta is not content-manifested |
| Pinned upstream commit/tree/license/tag | `PARTIAL` | Commit, tree, annotated tag, and MIT license object verified; no named pristine-upstream source manifest was found |
| Authenticated replay/import strategy decision | `MISSING` | Architecture recommends replay, and an adoption commit exists, but no exact authenticated gate-decision reference was supplied |
| Current-head merge-base/ancestry | `FAIL` | Both merge-base and accepted-ancestor checks fail for current HEAD |
| Fetch-only upstream | `PASS` | Fetch URL is `NousResearch/hermes-agent`; push URL is `DISABLED` |
| Distinct baseline ledger | `PARTIAL` | Roles can be observed, but they are not yet bound in one accepted gate record |
| License/notice continuity | `FAIL` for current subject | Accepted and phase-1 `LICENSE` share blob `75410e...`; current HEAD/worktree has no `LICENSE` |
| Complete per-file provenance/classification | `NOT_PROVEN` | 202 manifest paths versus 7,670 phase-1 tree paths; only 51 phase-1 paths are explicitly listed |
| Clean final branch/worktree topology | `FAIL` | Root has 228 dirty entries at the bound status snapshot; every listed auxiliary worktree also reported dirtiness |
| Actual hosting fact | `PASS` as an observation | GitHub reports `fork=false`, no parent/source; this is recorded separately and is not ancestry proof |

The complete structured facts, commands, exit codes, object IDs, digests, and
limitations are in the linked JSON evidence artifact.

## License and notice continuity

The accepted upstream baseline contains the Nous Research MIT `LICENSE` as Git
blob `75410e73319c72cd3e991a501c5455eb78f38375`, SHA-256
`821556e6336796450ab852d375117b48a4887e71d255794fd6318d99982a5ab6`.
The phase-1 adoption head preserves that exact blob and adds `NOTICE.md`.

The current bootstrap head contains its Ranex notice but no upstream
`LICENSE`; the worktree also lacks `LICENSE`. The notice's statement that the
license will be retained during adoption is not license continuity. The
upstream-derived line is the only inspected line that currently preserves the
license object.

## Minimal landing action

The smallest safe recovery is:

1. Preserve
   `bootstrap/pre-upstream@4baad4a67843b02d5970f442fb54aed8d6525dda`
   plus a content-addressed manifest of the intended dirty delta under an
   owner-approved protected safety ref.
2. Apply only the intended Ranex delta in a **new clean worktree** based on the
   already published, upstream-derived
   `develop@0533e1eaf50ace0eb84435a5c3de05e939fd4daa`; do not overlay the
   bootstrap tree and do not merge unrelated histories.
3. Commit the resulting exact subject while preserving upstream `LICENSE` blob
   `75410e73319c72cd3e991a501c5455eb78f38375`. Record the authenticated replay
   decision, pristine-upstream manifest, complete retained/modified/removed/
   original classification, and final clean branch/worktree topology.
4. Bind the resulting clean commit as the construction head and rerun every
   command in the evidence JSON. Only then may this gate become `PASS`.

No ref, branch, commit, worktree, tag, remote, index entry, or existing
document was changed by this inspection.

## Limitations

- The repository is shared and dirty; the status digest is a point-in-time
  snapshot excluding only this review and its evidence file.
- `git ls-remote` observed a newer upstream head than the local tracking ref.
  It was not fetched. Its reported tree came from the GitHub commit API and is
  not a locally verified Git object.
- This gate does not evaluate inherited behavior disposition, compatibility,
  runtime correctness, or later upstream-sync candidates.
- `github_network_fork=false` may legitimately remain false and does not
  prevent a software-derived fork once ancestry and provenance are proven.

