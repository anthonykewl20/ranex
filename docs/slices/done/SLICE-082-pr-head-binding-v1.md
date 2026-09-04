# SLICE-082 — PR Head Binding v1

**Status:** done
**Opened:** 2026-09-04
**Closed:** 2026-09-05
**Priority:** P1 — first of three slices: bind, publish, receive
**ADR:** docs/adr/ADR-049-pr-head-binding-v1.md
**Issue:** #78
**Follows:** SLICE-081 (evidence envelope)

## Contract

A pull-request head SHA, resolved through the local git object store, derives
the exact subject a verdict must already name — or the binding is refused.
No new signed surface; the tree digest stays the whole subject.

Acceptance:

- `PrHeadBinding` (head_sha, tree, subject_digest) derives by peeling the
  head SHA to its tree with `git rev-parse` and the existing subject
  formula; the digest is byte-identical to `subject_digest_for`.
- A malformed SHA refuses `E-GITHUB-BAD-SHA`; a SHA the object store cannot
  resolve refuses `E-GITHUB-UNFETCHABLE-HEAD`; a SHA that stops resolving
  mid-derivation refuses `E-GITHUB-HEAD-MOVED`.
- `resolve_acceptance` maps every `ReadState` to a closed outcome:
  `VERIFIED` → publishable record; `ABSENT` → `E-GITHUB-VERDICT-ABSENT`;
  every other state → `E-GITHUB-VERDICT-REJECTED:<state>`. Nothing outside
  `VERIFIED` is publishable.
- The outward keyring is exactly the committed verdict signer
  (`verdict_signer_id` → public key from `governance/producers.yaml`), not
  the whole producer map.
- `ranex github bind --head-sha <sha>` prints the binding; exit 0 on
  derivation, 2 with `ERROR  <code> <detail>` on refusal. No network.
- `evaluate()` does not move. `KERNEL_DIGEST` untouched.

Out of scope, deliberately: speaking to GitHub at all — authentication,
check-run publication are SLICE-083; receiving events is SLICE-084. Webhook
anti-replay is the deferred anti-replay slice and only delivery-id dedupe
belongs there.

## Owned paths

- Add: `src/ranex/github_app/__init__.py`, `src/ranex/github_app/binding.py`,
  `src/ranex/github_app/acceptance.py`.
- Modify: `src/ranex/cli/main.py` — `github bind` subcommand only.
- Tests: `tests/unit/test_pr_head_binding.py` (new),
  `tests/integration/test_github_bind_command.py` (new),
  `tests/contract/test_acceptance_mapping.py` (new).
- Governance: `governance/suite_manifest.json` re-freeze.
- Docs close-out: this slice to `docs/slices/done/`, `docs/STATE.md`,
  README completed-slices row.

Not touched: `verdict.py`, `foundation/signing.py`,
`foundation/verdict_signing.py`, `governed_execution/verdict_reader.py`.

## Order of work

One green commit: the binding module, the acceptance mapping, the CLI
subcommand, and their tests land together, because the mapping is only
reviewable against the refusals that pin it.

## Done criteria

1. Full suite green on the final commit.
2. `tests/contract/test_kernel_unchanged.py` green, `KERNEL_DIGEST`
   unchanged.
3. Manifest re-frozen; `expected_skips` accounted for.
4. Closing issue comment with SHA + evidence.

## Sad paths pinned

1. Malformed SHA (`E-GITHUB-BAD-SHA`): not 40 hex.
2. Unknown object (`E-GITHUB-UNFETCHABLE-HEAD`): never fetched / pruned.
3. Ground moves (`E-GITHUB-HEAD-MOVED`): SHA resolves, then does not.
4. No verdict (`E-GITHUB-VERDICT-ABSENT`): nothing published for the tree.
5. Verdict for another subject (`E-GITHUB-VERDICT-REJECTED:context-mismatch`).
6. Forged signature (`E-GITHUB-VERDICT-REJECTED:bad-signature`).
7. Verdict signed by a non-verdict-signer key
   (`E-GITHUB-VERDICT-REJECTED:unknown-signer`) — a producer key is not
   outward authority.

Each is a refusal test, not a comment.

## Notes

The ADR records why the head SHA is not added to `SIGNED_FIELDS`: names are
not content, and git's object store already notarizes the mapping.
