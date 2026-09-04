# ADR-051 — The first listener: a bounded webhook receiver

**Status:** accepted
**Date:** 2026-09-04
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-084-github-webhook-receiver-v1.md`

## Context and Problem Statement

ADR-019's position is that the kernel is a short-lived CLI that exits, and
the repo has honoured it: the only listener anywhere in the tree is the
per-run Unix-socket supervisor (`cli/process_supervisor.py`), torn down with
its run. Receiving GitHub's pull-request events reverses that stance — an
event arrives when GitHub chooses, so something must be listening when it
does — and the reversal must be bounded, or the repo's determinism story
gains an unbounded hole.

## Decision Drivers

- "Minimum" is the stated goal: one endpoint, one event type, one pipeline.
- GitHub's webhook contract (docs.github.com, verified 2026-09-04):
  `X-Hub-Signature-256: sha256=<hex hmac-sha256 of the raw body under the
  webhook secret>`, constant-time comparison required; `X-GitHub-Delivery`
  identifies a delivery; replays of the same delivery are possible.
- Confinement forbids network inside governed execution by construction —
  the receiver is host-side, like `deps fetch`, and can never be an evidence
  producer.
- TLS is a terminator's job: a reverse proxy or a dev tunnel (smee.io) in
  front; the listener itself binds localhost.

## Considered Options

1. Poll the REST API on a schedule instead of listening — rejected for this
   slice: the task is to *receive* events; polling is a documented fallback,
   not the contract.
2. An async framework (FastAPI/Starlette + uvicorn) — rejected: first new
   dependency since the lock's freeze, for exactly one endpoint.
3. stdlib `http.server`, single endpoint, bounded body, one delivery at a
   time, spool of seen delivery ids — chosen.

## Decision Outcome

`src/ranex/github_app/webhook.py` validates deliveries: HMAC-SHA256 over the
raw body with `hmac.compare_digest`; unsigned or tampered deliveries are
401 and unprocessed; `X-GitHub-Delivery` ids are spooled so a replay is a
logged no-op (200, no republish); only allowlisted installations and
repositories are processed. The event grammar is closed: `pull_request` with
action `opened|synchronize|reopened`; everything else is 200, journaled,
unprocessed.

`src/ranex/github_app/receiver.py` binds the pipeline per accepted event:
fetch the head SHA into the local clone → SLICE-082 binding →
`resolve_acceptance` → SLICE-083 publication. One delivery is processed at a
time; the HTTP thread never holds the pipeline. `ranex github listen` runs
it; `--bind` defaults to `127.0.0.1` and the docs say plainly that TLS is
somebody else's job.

The ruleset documentation lands in README (the docs set is closed by
`test_docs_discipline.py`; a new file is a bigger decision than this slice):
App creation (Checks write, Contents read, Pull requests read; subscribe
`pull_request`), and the ruleset — require status check `ranex/acceptance`
with the Ranex App pinned as its source (rulesets' `required_status_checks`
accept `integration_id` for exactly this), targeting the default branch.

### Consequences

- The repo's first long-running process exists and is bounded: one endpoint,
  one event type, one pipeline, localhost by default.
- A delivery that arrives while another is processing waits; there is no
  concurrency contract to break.
- The receiver never evaluates; it publishes what verified verdicts already
  say. A compromised receiver host can suppress or fail checks — visible —
  but cannot forge a green one.
- What this does not close: delivery anti-replay beyond delivery-id dedupe
  (the deferred anti-replay slice owns nonces and anchors); secret rotation;
  multiple installations at scale.

### Confirmation

- `tests/integration/test_github_webhook.py` — the docs' own HMAC test
  vector; signed/unsigned/tampered; action filter; replay dedupe;
  wrong-repo refusal; event → fake-GitHub end to end.
- `tests/security/test_github_receiver_refusals.py` — the sad-path battery.
- `tests/contract/test_readme_github_section.py` — README carries the App
  and ruleset recipe with the pinned context name.
