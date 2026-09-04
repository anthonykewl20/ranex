# SLICE-083 — GitHub Check Publisher v1

**Status:** open
**Opened:** 2026-09-04
**Priority:** P1 — second of three slices: bind, publish, receive
**ADR:** docs/adr/ADR-050-github-check-publisher-v1.md
**Issue:** #79
**Follows:** SLICE-082 (PR head binding)

## Contract

The Ranex GitHub App publishes one check, `ranex/acceptance`, on the exact
PR head, with a conclusion that is reachable from exactly one place: a
verified, passing verdict record. Everything else is a louder, never greener,
outcome.

Acceptance:

- `client.py`: JWT (RS256, `iat` now−60, `exp` now+600, `iss` = App ID);
  installation token exchanged at `/app/installations/<installation>/access_tokens`
  and cached until `expires_at − 60s`; `create_check_run` sends the
  documented headers (`Authorization`, `Accept: application/vnd.github+json`,
  `X-GitHub-Api-Version`).
- Non-2xx or transport failure refuses `E-GITHUB-API-REFUSED` naming the
  status; there is no silent retry.
- `publisher.py`: `VERIFIED+PASS → success`; `VERIFIED+FAIL → failure`
  (failing rule, missing claims); `E-GITHUB-VERDICT-ABSENT → action_required`;
  rejected → `failure` naming the state. `success` is unreachable from any
  other input, and a test says so from every direction.
- The check name is `ranex/acceptance`, always; `head_sha` is the binding's
  head SHA, always; output carries `subject_digest`, `record_digest`, `tree`.
- Credentials come only from `RANEX_GITHUB_APP_ID`,
  `RANEX_GITHUB_APP_PRIVATE_KEY`, `RANEX_GITHUB_WEBHOOK_SECRET`; private-key
  paths inside the repository are refused; no secret value reaches a log
  line.
- `ranex github check publish --head-sha <sha> --installation <id> --repo
  owner/name [--verdicts-dir ...] [--gate ...]` binds (SLICE-082), resolves,
  publishes; exit 0 published, 1 published-failure conclusion, 2 refusal.
- No new dependency: `uv.lock` unchanged. `KERNEL_DIGEST` untouched.

Out of scope, deliberately: receiving webhook events (SLICE-084); producing
verdicts (the App never evaluates); polling APIs.

## Owned paths

- Add: `src/ranex/github_app/client.py`, `src/ranex/github_app/publisher.py`.
- Modify: `src/ranex/cli/main.py` — `github check publish` subcommand only.
- Tests: `tests/integration/test_github_client.py` (new),
  `tests/security/test_github_publisher_fail_closed.py` (new),
  `tests/contract/test_check_payload.py` (new), `tests/_github_fake.py`
  (shared fake server + seeded clone, the `launcher_host` pattern).
- Governance: `governance/suite_manifest.json` re-freeze.
- Docs close-out: this slice to `docs/slices/done/`, `docs/STATE.md`,
  README completed-slices row.

Not touched: `verdict.py`, `foundation/signing.py`, `uv.lock`,
`pyproject.toml`.

## Order of work

One green commit: client and publisher land together with the fail-closed
tests, because the conclusion mapping is the contract and the transport is
only reviewable against it.

## Done criteria

1. Full suite green on the final commit (fake-server arms only; no test
   speaks to the real API).
2. `tests/contract/test_kernel_unchanged.py` green, `KERNEL_DIGEST`
   unchanged.
3. Manifest re-frozen; `expected_skips` accounted for.
4. Closing issue comment with SHA + evidence; the live one-shot publish
   against the real API is UNVERIFIED until the App exists (SLICE-084 wires
   the real journey).

## Sad paths pinned

1. Missing `RANEX_GITHUB_APP_ID` / key path / webhook secret — structured
   refusal at startup, no default.
2. Key path inside the repository — refused (`E-GITHUB-KEY-INSIDE-REPO`).
3. Malformed / wrong-type key file — refused, no traceback.
4. Expired token at publish time — re-exchanged once, then refused.
5. API 4xx/5xx — `E-GITHUB-API-REFUSED` with status; no silent green.
6. Verdict absent / rejected / for another subject — never `success`
   (pinned from every `ReadState`).
7. Secret value in any log line — redaction suites cover it; a test greps
   the emitted lines for the key and token literals.

Each is a refusal test, not a comment.

## Notes

The JWT is minted, never verified, by this code: GitHub verifies. That is
why the absence of `pyjwt`'s verification armour is not a gap here.
