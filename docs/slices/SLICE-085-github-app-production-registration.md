# SLICE-085 — GitHub App production registration

**Status:** open
**Opened:** 2026-09-07
**Priority:** P0 — issue #88 production-readiness remaining product gap
**ADR:** docs/adr/ADR-055-github-app-operator-registration.md
**Issue:** #88
**Follows:** SLICE-084 (webhook receiver); ADR-053/054 durability follow-ups

## Contract

The operator can create the Ranex GitHub App from a frozen manifest,
store its credentials outside the repository, inspect the live App
identity, and pin `ranex/acceptance` as a required check from that App.
The App remains a publisher. Live GitHub success is retained evidence,
never inferred from the fake API.

Acceptance:

- Frozen manifest: homepage `url` required; `hook_attributes.url` must
  be `https://`; permissions `checks:write`, `contents:read`,
  `pull_requests:read`; events `["pull_request"]`; `public` false.
- `ranex github register` without `--code` serves (or prints) the
  GitHub App Manifest form with an unguessable `state`. The redirect
  catcher refuses a mismatched state. `--code` converts at
  `POST /app-manifests/{code}/conversions` and exclusive-creates
  `app.pem` (0600), `webhook-secret` (0600) and `identity.json` under
  `--credentials-dir`. The directory must not be committable into the
  governed repository. Overwrite is refused. `pem` / `webhook_secret`
  never appear on stdout.
- `ranex github status` authenticates as the App, prints id/slug and
  installations, and with `--repo` reports whether a ruleset pins
  `ranex/acceptance` to this App's `integration_id`.
- `ranex github ruleset --repo owner/name --branch <ref>` creates the
  documented ruleset via the operator token
  (`RANEX_GITHUB_OPERATOR_TOKEN` or `GITHUB_TOKEN`).
- `evaluate()` does not move. `KERNEL_DIGEST` untouched. No new
  dependency.

Out of scope, deliberately: the App evaluating; merge-queue /
merge-group checks; distributed shard aggregation; TLS termination;
secret rotation; smee.io as a shipped binary. Those stay documented
operator jobs. Live HTTPS delivery and merge refusal are the slice's
UNVERIFIED-until-observed arms.

## Owned paths

- Add: `src/ranex/github_app/registration.py`.
- Modify: `src/ranex/github_app/client.py` — anonymous conversion,
  `GET /app`, `GET /app/installations`, ruleset list/create.
- Modify: `src/ranex/cli/main.py` — `github register|status|ruleset`.
- Modify: `src/ranex/observability/schema.py` and
  `tests/contract/test_trace_schema.py` — dispatch names in place.
- Tests: `tests/integration/test_github_registration.py` (new),
  `tests/security/test_github_registration_refusals.py` (new);
  `tests/_github_fake.py` grows the conversion and ruleset surface.
- Docs: `docs/OPERATIONS.md` recipe, `docs/STATE.md`, README active
  slice; `tests/contract/test_readme_github_section.py` pins the new
  commands.
- Governance: `governance/suite_manifest.json` re-freeze.

Not touched: `verdict.py`, webhook HMAC, publisher conclusion mapping.

## Order of work

One green commit: the handshake, the store, status, the ruleset, and
the tests land together, because a register command that cannot pin
the check is not production-operable.

## Done criteria

1. Full suite green on the final commit (fake-API arms).
2. `tests/contract/test_kernel_unchanged.py` green.
3. Manifest re-frozen; `expected_skips` accounted for.
4. Issue #88 remains open until live App authentication, HTTPS
   delivery, App-pinned merge refusal, deployment recovery and
   production load are observed. Those stay UNVERIFIED, never PASS.

## Sad paths pinned

1. Webhook URL not `https://` — `E-GITHUB-WEBHOOK-NOT-HTTPS`.
2. Credentials directory inside the repository —
   `E-GITHUB-KEY-INSIDE-REPO`.
3. Credentials directory already populated — refuse overwrite.
4. Redirect `state` mismatch — 403, no conversion.
5. Conversion 404/422 — `E-GITHUB-API-REFUSED`, nothing written.
6. Conversion response missing `id`/`pem`/`webhook_secret` — refuse.
7. Group/other-readable stored key — `E-GITHUB-KEY-EXPOSED` on status.
8. Ruleset without operator token — `E-GITHUB-OPERATOR-TOKEN-ABSENT`.
9. Existing ruleset that names `ranex/acceptance` from another
   `integration_id` — refuse, do not silently replace.
