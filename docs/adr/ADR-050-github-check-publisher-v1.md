# ADR-050 — The outward record: a GitHub check published by the Ranex App

**Status:** accepted
**Date:** 2026-09-04
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-083-github-check-publisher-v1.md`

## Context and Problem Statement

MAP §11.1 / RISK-03 parked the question of an *outward record* — "the
cryptographic substrate for an outward record exists; the position does not,
which is settled by a decision about who the verifier is." A pull-request
acceptance check answers it: the external verifier is a GitHub ruleset
requiring the `ranex/acceptance` check, and the publisher is the Ranex GitHub
App — an identity GitHub can attribute, so a ruleset can demand the check
*from that App* and not from any process that can write a status string.

Publishing requires speaking HTTPS to api.github.com as the App: an RS256 JWT
over the App's private key, exchanged for a per-installation token, then
`POST /repos/<owner>/<repo>/check-runs`. The repo has exactly one networked
step today (`provisioning/fetching.py`, wheel downloads under a pinned lock),
and a standing refusal to grow dependencies without cause.

## Decision Drivers

- AGENTS.md: do not hand-roll what a mature, pinned, licence-compatible
  upstream provides — and do not add dependencies without a slice's cause.
- ADR-033 set the HTTP precedent: stdlib `http.client`/`urllib`, no custom
  HTTP or TLS stack, no new dependency for transport.
- Everything cryptographic already in the lock: `cryptography>=50,<51`.
- Fail-closed is the house rule: absence blocks, refusal is louder than
  silence, and nothing green may be published without a verified record.

## Prior art

- GitHub Apps server-to-server flow (docs.github.com, verified 2026-09-04):
  RS256 JWT with `iat`/`exp` (≤10 minutes)/`iss` = App ID; exchange at
  `POST /app/installations/<installation>/access_tokens`; tokens live ≈1 hour.
- `provisioning/fetching.py` — the repo's shape for bounded stdlib network
  I/O: one function, pinned expectations, refusal on the unexpected.
- Check-run conclusions are a closed vocabulary (`success`, `failure`,
  `neutral`, `cancelled`, `skipped`, `timed_out`, `action_required`);
  `action_required` exists precisely for "a human must do something".

## Considered Options

1. Add `pyjwt` (and an HTTP client) to the lock — rejected: the only need is
   *minting* an RS256 JWT whose verification happens on GitHub's side; the
   signature itself is `cryptography`'s PKCS1v15+SHA256, and the framing is
   base64url of two JSON objects per RFC 7515/7519. A trust-root change to
   avoid fifteen reviewed lines is the worse trade.
2. Publish a classic commit status instead of a check run — rejected: check
   runs carry structured output (summary, details) and are the surface
   rulesets attribute to Apps; statuses are the legacy shape.
3. Stdlib transport + `cryptography` JWT minting; one client module with a
   closed surface; tokens and keys never logged — chosen.

## Decision Outcome

`src/ranex/github_app/client.py` owns all network speech: `AppCredentials`
from `RANEX_GITHUB_APP_ID` / `RANEX_GITHUB_APP_PRIVATE_KEY` /
`RANEX_GITHUB_WEBHOOK_SECRET` (paths and values outside the repository), JWT
minting with the documented claims window, installation-token exchange with
cache-until-expiry, and `create_check_run` over `urllib.request` with the
documented headers and media type. Every non-2xx is `E-GITHUB-API-REFUSED`
with the status named; nothing retries silently.

`src/ranex/github_app/publisher.py` owns the conclusion mapping — the only
place `success` is reachable from is `read_verdict == VERIFIED` with
`verdict == PASS`. `VERIFIED+FAIL` → `failure` with the failing rule and
missing claims in the output; `E-GITHUB-VERDICT-ABSENT` → `action_required`;
every rejection state → `failure` naming the state. The check name is always
`ranex/acceptance`; `head_sha` is always the binding's PR head; the output
carries `subject_digest`, `record_digest`, and `tree`.

### Consequences

- The private key material never enters the repository; the redaction suites
  cover token/key leakage into logs.
- A GitHub outage is a refusal (`E-GITHUB-API-REFUSED`), not a missing check:
  the operator sees the difference, and the ruleset keeps blocking.
- What this does not close: event reception (SLICE-084); anti-replay of
  deliveries (deferred); evaluation itself — the App publishes verdicts, it
  never produces them, by design, so a host compromise cannot forge a
  verdict, only fail to publish one.

### Confirmation

- `tests/integration/test_github_client.py` — JWT structure, claims window,
  token exchange and caching, exact check-run body, against a stdlib fake.
- `tests/security/test_github_publisher_fail_closed.py` — no path to
  `success` without `VERIFIED+PASS`; secrets absent from every log line.
- `tests/contract/test_check_payload.py` — payload shape frozen.
