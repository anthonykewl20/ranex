# ADR-049 — PR head binding is a projection, not a new signed surface

**Status:** accepted
**Date:** 2026-09-04
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-082-pr-head-binding-v1.md`

## Context and Problem Statement

Ranex is to publish a GitHub check for pull requests, and the check is only
worth requiring in a ruleset if it names the exact code a reader will merge.
Today the signed verdict record (`foundation/verdict_signing.py`) binds its
judgment to `subject_digest` — `sha256(canonical_json({"tree": <tree oid>}))`,
computed by `subject_digest_for` at `cli/main.py:185`. Evidence and verdicts
already refuse to verify against any other subject. What does not exist is the
step from *a pull-request head SHA as delivered by a webhook or named on a
command line* to that subject digest — and the temptation is to add a `head_sha`
field to the signed set so the binding is "in" the record.

## Decision Drivers

- The signed sets are exact by design (`SIGNED_FIELDS`); every field added is
  a field every hand-built fixture must carry, and a domain bump that
  invalidates every prior record. SLICE-081 just paid that cost deliberately;
  paying it again for information the record already implies would be cost
  without a new guarantee.
- A commit SHA and its tree are related by git's own content-addressed object
  store: resolving `<sha>` peeled to its tree locally verifies the commit object's own
  hash. Trusting a GitHub API response for the mapping would import a network
  answer into an otherwise local, self-verifying derivation.
- The kernel does not move (`tests/contract/test_kernel_unchanged.py`), and
  admission stays the only place records are refused.

## Prior art

- GitHub's own check runs are keyed by `head_sha`; a check attached to a commit
  that is not the PR head does not satisfy required status checks. The binding
  must therefore be derived at publish time from the event's head SHA, not from
  a digest recorded at some earlier, possibly different, head.
- `verdict_reader.read_verdict` (CONTEXT_MISMATCH at
  `governed_execution/verdict_reader.py:88-92`) is the established shape for
  "expected context vs record context": the reader is handed the context and
  refuses disagreement. This decision reuses that shape rather than inventing
  a parallel one.

## Considered Options

1. Add `head_sha` to the verdict's `SIGNED_FIELDS` — rejected: commit SHAs are
   names, not content; the same tree arrives under many SHAs (rebase, reword),
   so the field would go stale precisely when the content is unchanged, and a
   domain bump would burn every existing fixture for no added guarantee.
2. Trust the GitHub API's `commit.tree.sha` — rejected: turns a self-verifying
   local derivation into a network answer; a compromised or stale API response
   would then decide what a verdict is about.
3. Derive the binding locally (`git fetch` the head SHA, peel it to its tree
   with `git rev-parse`, then the existing `subject_digest_for` formula) and
   treat the result as a projection over the already-signed verdict — chosen.

## Decision Outcome

`src/ranex/github_app/binding.py` derives `PrHeadBinding{head_sha, tree,
subject_digest}` from a local git object store and nothing else; malformed or
unresolvable SHAs are refused with `E-GITHUB-*` codes.
`src/ranex/github_app/acceptance.py` resolves the outward acceptance of a
binding through `read_verdict` under the committed verdict-signer keyring,
mapping every `ReadState` to a closed outcome; nothing outside `VERIFIED`
publishes green.

### Consequences

- No signed field, domain, or schema changes; SLICE-081's envelope is the
  outward surface unchanged.
- The binding is only as fresh as the local object store: the receiver host
  must `git fetch` the head SHA before deriving, and a SHA that will not
  resolve is refused (`E-GITHUB-UNFETCHABLE-HEAD`), not guessed.
- Two different commits with identical trees yield identical bindings — that
  is correct: the subject is content, and identical content needs one verdict.
- What this does not close: nothing here speaks to GitHub (authentication,
  check-run publication) — SLICE-083; and no anti-replay for webhook
  deliveries — the deferred anti-replay slice.

### Confirmation

- `tests/unit/test_pr_head_binding.py` — the digest formula is byte-identical
  to the subject formula pinned since the presentation contract.
- `tests/integration/test_github_bind_command.py` — real git repos: derive,
  refuse malformed SHA, refuse missing object.
- `tests/contract/test_acceptance_mapping.py` — the `ReadState`→outcome table
  is closed and fail-closed.
