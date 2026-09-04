# SLICE-084 — GitHub Webhook Receiver v1

**Status:** done
**Opened:** 2026-09-04
**Closed:** 2026-09-05
**Priority:** P1 — third of three slices: bind, publish, receive
**ADR:** docs/adr/ADR-051-github-webhook-receiver-v1.md
**Issue:** #80
**Follows:** SLICE-083 (check publisher)

## Contract

The Ranex GitHub App receives pull-request events and answers each with the
one thing it is for: a `ranex/acceptance` check on that event's exact head,
derived from verified verdicts. It listens on localhost, validates every
delivery's HMAC signature, ignores replays, and processes one delivery at a
time. It never evaluates anything.

Acceptance:

- `X-Hub-Signature-256` = `sha256=` + lowercase hex HMAC-SHA256 of the raw
  body under `RANEX_GITHUB_WEBHOOK_SECRET`, compared with
  `hmac.compare_digest`; the docs' published test vector is pinned in the
  tests verbatim.
- Unsigned or tampered delivery → 401, nothing processed, nothing logged
  beyond the refusal.
- `X-GitHub-Delivery` replay → 200, logged no-op, no republish.
- Only allowlisted installation/repository pairs process; others → 200,
  journaled, unprocessed.
- Event grammar closed: `pull_request` + `opened|synchronize|reopened`;
  every other event or action → 200, journaled, unprocessed.
- Per accepted event: fetch the head SHA into the local clone, derive the
  SLICE-082 binding, `resolve_acceptance`, publish the SLICE-083 check.
- `ranex github listen --bind 127.0.0.1:<port>` — localhost default; TLS is
  documented as the terminator's job (reverse proxy / smee.io in dev).
- Request body bounded; oversized → 413, connection dropped, no parse.
- README carries the App creation recipe and the ruleset recipe: require
  status check `ranex/acceptance`, Ranex App pinned as source
  (`integration_id`), default branch.
- `evaluate()` does not move. `KERNEL_DIGEST` untouched. No new dependency.

Out of scope, deliberately: delivery nonces / journal-head anchoring (the
deferred anti-replay slice); polling fallback; secret rotation;
receiver-side evaluation.

## Owned paths

- Add: `src/ranex/github_app/webhook.py`, `src/ranex/github_app/receiver.py`.
- Modify: `src/ranex/cli/main.py` — `github listen` subcommand only;
  `tests/_github_fake.py` grows the shared receiver journey.
- Modify: `README.md` — the App + ruleset section (a shipped command changed;
  the docs set stays closed).
- Tests: `tests/integration/test_github_webhook.py` (new),
  `tests/security/test_github_receiver_refusals.py` (new),
  `tests/contract/test_readme_github_section.py` (new).
- Governance: `governance/suite_manifest.json` re-freeze.
- Docs close-out: this slice to `docs/slices/done/`, `docs/STATE.md`,
  README completed-slices row.

Not touched: `verdict.py`, `.github/workflows/ci.yml` (the App is
independent of Actions, and the workflow is contract-frozen).

## Order of work

One green commit: SLICE-083 already shipped the publisher this pipeline
ends in, so the receiver lands whole — HMAC validation, dedupe, allowlist,
event grammar, the bind → resolve → publish pipeline, and the README
recipes together.

## Done criteria

1. Full suite green on the final commit.
2. `tests/contract/test_kernel_unchanged.py` green, `KERNEL_DIGEST`
   unchanged.
3. Manifest re-frozen; `expected_skips` accounted for.
4. Closing issue comment with SHA + evidence; a live PR receiving a real
   `ranex/acceptance` check is UNVERIFIED until the App is installed —
   reported as such, never PASS.

## Sad paths pinned

1. Unsigned delivery → 401, zero processing.
2. Tampered body under a valid-looking signature → 401.
3. Replayed `X-GitHub-Delivery` → no-op.
4. Event for a non-allowlisted installation/repo → journaled ignore.
5. `pull_request` action outside the grammar → journaled ignore.
6. Head SHA the clone cannot fetch → `E-GITHUB-UNFETCHABLE-HEAD`, no check
   published, delivery logged as refused.
7. Oversized body → 413.
8. Verdict absent for the event's tree → `action_required` check naming the
   subject digest (visible, never green).

Each is a refusal or ignore test, not a comment.

## Notes

The ADR records why this listener exists at all and what bounds it. The
real-App journey (install, PR, observed check) is the slice's live proof and
is honest about being UNVERIFIED until the App exists.
