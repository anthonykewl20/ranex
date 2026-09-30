# SLICE-085 — GitHub App production registration

**Status:** done
**Opened:** 2026-09-07
**Closed:** 2026-09-30
**Priority:** P0 — issue #88
**ADR:** docs/adr/ADR-055-github-app-operator-registration.md
**Issue:** #88
**Follows:** SLICE-084 (webhook receiver); ADR-053/054 durability follow-ups

## Contract (shipped)

The operator creates the Ranex GitHub App from a frozen manifest, stores
credentials outside the repository, inspects live App identity, and pins
`ranex/acceptance` as a required check from that App. The App remains a
publisher. `evaluate()` does not move.

Landed on main: `c581b54bc9` (register/status/ruleset), live journey
`a6ca6518ca`, receiver priority `47e1731c65`, automatic evidence
`e0aee93592` (SLICE-086).

## Closeout evidence (2026-09-30)

- **VERIFIED (today):** `ranex github status` with
  `~/.config/ranex/github-app` credentials → App `4863198` /
  `ranex-gate`, installation `159825611` on `anthonykewl20`;
  `--repo anthonykewl20/ranex-app-live-probe` →
  `ranex/acceptance` pinned to this App (ruleset `22468775` active).
- **VERIFIED (retained receipts):** HTTPS webhook via smee, check
  publication, App-pinned merge refusal, forged same-name check defeat
  (`tools/dogfood/audits/2026-09-08-live-app/`); automatic evidence on
  probe PR #6 (`audits/2026-09-09-automatic-evidence/fifth-pass/`);
  recovery replay (`audits/2026-09-08-app-review/live-recovery.json`).
- **UNVERIFIED:** production hosting/soak, credential rotation,
  backup/restore, full host-qualified Leitir/Arxic acceptance, fresh
  GitHub-origin webhook on this closeout day (no listener/smee running).
- **UNIMPLEMENTED (out of slice):** merge-candidate/merge-group checks,
  shard aggregation, policy compiler/catalog, isolated automatic
  observers.

No production sign-off. Missing env without the credentials dir still
reports `E-GITHUB-CREDENTIALS-ABSENT` (measured before export).
