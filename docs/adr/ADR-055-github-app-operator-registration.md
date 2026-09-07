# ADR-055 — Operator registration of the Ranex GitHub App

**Status:** accepted
**Date:** 2026-09-07
**Issue:** #88

## Context and Problem Statement

SLICE-082..084 shipped bind, publish and receive. Issue #88's production
assessment is still NO-GO: there is no live App identity, no HTTPS
delivery, and no App-pinned `ranex/acceptance` ruleset on the pilot
repositories. The documented recipe is a browser walk through GitHub's
settings pages; nothing in the CLI can complete GitHub's own App
Manifest handshake, store the resulting PEM outside the repository, or
create the ruleset that makes the check merge-blocking. Local fake-API
tests cannot close that gap, and guessing live success is forbidden.

## Decision Drivers

- GitHub's App Manifest flow is the documented way to create an App from
  a frozen permission/event set and recover `id`, `pem` and
  `webhook_secret` from `POST /app-manifests/{code}/conversions`.
- ADR-050 already owns network speech (`urllib`, no new dependency) and
  refuses a key inside the repository; registration must reuse that
  client and the same 0600 exclusive-create write `keygen` uses.
- ADR-051's ruleset recipe pins `ranex/acceptance` with
  `integration_id`. Creating that ruleset is a user-admin API call, not
  an App JWT call: the App is the *source* of the check, not the author
  of the rule.
- The App still publishes; it never evaluates. Registration does not
  change `evaluate()`, `KERNEL_DIGEST`, or the signed surface.

## Prior art

- GitHub App Manifest flow (docs.github.com, verified 2026-09-07):
  `POST https://github.com/settings/apps/new` with form field `manifest`;
  redirect carries `code` (and optional `state`); convert at
  `POST /app-manifests/{code}/conversions` within one hour; response
  includes `id`, `pem`, `webhook_secret`.
- Repository rulesets
  (`POST /repos/{owner}/{repo}/rulesets`, API `2026-03-10`):
  `required_status_checks[].integration_id` pins the App as the only
  acceptable source of `ranex/acceptance`.
- This repository: ADR-050 (client, key-outside-repo), ADR-051
  (permissions/events/ruleset recipe), `cmd_keygen` (0600 `O_EXCL` write).

## Considered Options

1. Keep the browser-only settings-page recipe — rejected: issue #88
   cannot close while credentials and the App id are unobtainable from
   the product.
2. Add an App-creation SDK / PyGithub — rejected: first new dependency
   for one handshake GitHub already documents as a form POST plus one
   REST conversion.
3. Frozen manifest, localhost redirect capture, conversion, 0600
   credential store, operator-token ruleset — chosen.

## Decision Outcome

`src/ranex/github_app/registration.py` owns the frozen manifest
(permissions `checks:write`, `contents:read`, `pull_requests:read`;
event `pull_request`; webhook URL must be `https://`), the localhost
redirect catcher with an unguessable `state`, and exclusive-create
writes of `app.pem` / `webhook-secret` / `identity.json` under an
operator directory that `committable_into` refuses. Conversion is
anonymous (`POST /app-manifests/{code}/conversions`); `pem` and
`webhook_secret` never reach stdout. `ranex github status` authenticates
as the App (JWT) and reports installations plus, when `--repo` is
given, whether a ruleset pins `ranex/acceptance` to this App.
`ranex github ruleset` creates that ruleset with the operator token
(`RANEX_GITHUB_OPERATOR_TOKEN`, else `GITHUB_TOKEN`).

Live installation, HTTPS delivery, App-pinned merge refusal, deployment
recovery and production load remain evidence that a run of these
commands against GitHub must retain. They are not inferred from tests
against the fake API. Automatic evaluation, merge-candidate checks and
distributed shard aggregation stay out of scope: the App still
publishes only what `gate evaluate` already produced.

## Consequences

- Three parser-listed verbs join the GitHub group: `register`,
  `status`, `ruleset`. Trace stages grow in place under schema evt 4.
- Credential files are operator state, never repository state.
- A live production sign-off still requires the HTTPS terminator and a
  retained GitHub delivery; this slice makes that journey operable.
