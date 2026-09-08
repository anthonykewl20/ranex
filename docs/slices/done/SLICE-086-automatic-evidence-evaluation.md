# SLICE-086 — Automatic evaluation of signed PR evidence

**Status:** done

Issue: #88. ADR: docs/adr/ADR-058-automatic-evidence-evaluation.md.

Contract: an opt-in receiver evaluates independently produced evidence for the
exact PR head under an operator-pinned policy, verifies the resulting signed
verdict and publishes its check. It never executes contributor code.

Acceptance:
- `--evaluate-evidence` requires the committed verdict signer's external key.
- `--evidence` and `--suite-manifest` use existing repository confinement.
- The gate, keyring and manifest cannot change through a PR or checkout update.
- Missing evidence waits; stale or failing evidence does not authorize a merge.
- Fresh evidence is evaluated automatically without webhook redelivery.
- Unchanged evidence does not append another judgment or repeatedly query GitHub.
- Publication failures and restart recovery retain work and suppress duplicate success.
- Live GitHub-origin deliveries, upstream Six observations, blocked merges and
  repaired-code acceptance are retained separately from local API-double tests.

Scope excludes automatic observation, arbitrary contributor execution,
merge-candidate/merge-group checks and production deployment qualification.
