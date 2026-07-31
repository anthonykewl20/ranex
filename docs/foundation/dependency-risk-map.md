# Dependency risk map

**Date:** 2026-07-31 · **HEAD:** `f2c04c167`

What Slice 1 actually depends on, what each dependency can do to it, and where
the real risk sits. Companion to [`hermes-inventory.md`](hermes-inventory.md),
[`hermes-retention-matrix.md`](hermes-retention-matrix.md) and
[`ranex-foundation-boundary.md`](ranex-foundation-boundary.md).

---

## 1. Slice 1's complete dependency path

**FACT**, `grep -rh '^import \|^from ' src/ranex` plus `pyproject.toml`.

```
ranex gate evaluate <ref>
  │
  ├── stdlib     argparse · dataclasses · enum · hashlib · json · pathlib
  │              re · sqlite3 · subprocess · sys · typing · uuid
  ├── PyYAML     >=6.0.2,<7        ← the only third-party runtime dependency
  ├── git        via subprocess — `git rev-parse <ref>^{tree}`
  └── ranex.*    1,050 LOC, first-party
```

That is the entire path. **No Hermes package, no HTTP client, no provider SDK,
no credential source, no network call, no ambient configuration read.**

Test path adds `pytest>=9.0.2,<10`. Validator path (Slice 0, separate) adds
`jsonschema`, `rfc8785`, `pyrefly`, `uv` — all five registered in
`legal/licensing-manifest.json`.

---

## 2. Risk table — what each dependency can do to a verdict

Ordered by consequence, not by likelihood.

| # | Dependency | What it could do to a verdict | Likelihood | Consequence | Mitigation in place |
|---|---|---|---|---|---|
| 1 | **`git` subprocess** | Resolves the subject digest. A different git version, a different `core.abbrev`, or a repository in an odd state changes the tree hash resolution or fails. If it silently returned the wrong tree, every verdict binds to the wrong subject. | Low | **Severe** — breaks `BC-3` exact-subject binding | Explicit `check=False` + non-zero handling raising `ValueError` (`cli/main.py:31-40`). Digest is over the **tree**, not the commit or branch name. |
| 2 | **`sqlite3`** | Holds the append-only journal. A partial write, a locked database, or two concurrent evaluations could corrupt or interleave the record. | Medium | High — breaks the audit trail, not the verdict | Hash-chained journal (`journal.py`). Failure modes "unreadable store", "store write fails mid-append" and "two concurrent evaluations" are named in walking skeleton §9 and covered by `tests/integration/test_journal.py`. |
| 3 | **`PyYAML`** | Parses the gate catalog. A YAML feature (aliases, merge keys, duplicate keys, tags) could make two textually different catalogs load identically, or one catalog load differently across versions. | Medium | High — breaks `BC-7` and catalog integrity | **Partial.** The loader refuses duplicate **YAML mapping keys** (`slice_gate_loader.py:40-56`, a `BaseResolver.DEFAULT_MAPPING_TAG` override) — but duplicate `rule_id` *values* across separate list entries are reported as **accepted** by `docs/architecture/reviews/2026-07-31-slice-01-evidence.md`. Version pinned `>=6.0.2,<7`. An earlier draft of this row overstated the guarantee. |
| 4 | **`hashlib` / canonical JSON** | Produces the subject digest and journal chain. | Very low | **Total** — it is the determinism guarantee | RFC 8785 canonicalisation (`foundation/canonical.py`, 26 LOC). Demonstrated byte-identical across two runs. |
| 5 | **Filesystem paths** | `--repository`, `--gate-catalog`, `--evidence`, `--journal` are operator-supplied paths. A path outside the repository would let the tool govern something it must not. | Medium | High — breaks `SLICE-LANE-007` | ⚠ **NONE IN FORCE.** `cli/confinement.py` exists and its tests pass, but `cli/main.py` **never imports it** — verified: the only non-self reference in `src/` or `tests/` is `tests/security/test_repository_confinement.py:13`. `SLICE-LANE-007` is unenforced at the CLI boundary and a second-repository evaluation has been observed to pass. An earlier draft of this row credited a mitigation that is not wired. See readiness assessment **G6**. |
| 6 | **`subprocess`** | The single escape hatch to the outside world. | Low | High if widened | Used once, for `git rev-parse`, with a fixed argument vector — no shell, no user-supplied command string. |
| 7 | **Python version** | `requires-python = ">=3.11,<3.15"`. Dict ordering, `StrEnum`, and hash behaviour matter to canonicalisation. | Low | Medium | Bounded range declared. **Gap:** not asserted at runtime; see §5. |

**No row in this table is a Hermes dependency.** That is the map's principal
finding, and it is why the Slice 1 verdict in
[`slice-1-readiness-assessment.md`](slice-1-readiness-assessment.md) can be
positive.

---

## 3. Inherited-obligation risk — the real inheritance

Hermes reaches this repository through **contracts, not imports**. These cannot
break a Slice 1 verdict; they can block a release or mislead a future reader.

| Obligation set | Size | Enforcement state | Risk to Slice 1 |
|---|---:|---|---|
| `HERMES-PROMOTION-*` | **65** of 98 catalog entries | `catalog_status: DEFINITION_ONLY` | **None now.** Blocks at `RELEASE` / `PRODUCTION_READY`, stages this project has not reached. |
| `HERMES-OWNER-DECISION-*` | **20** | Unresolved; absence outcome `BLOCK` | **None to the slice.** These are what keep `IMPLEMENTATION_START_READY` undeclared. |
| `HERMES-RESEARCH-ONLY-*` | **13** | Advisory | None. |
| `ADR-0010` test projection | 2,444 paths | `ACCEPTED`, expires **2026-10-31** | **None.** `ADR-0021` narrowed it; zero of 2,444 paths exist in the tree. |

**FACT**, from the catalog's own counters:
`promoted_provision_count: 65`, `owner_decision_count: 20`,
`research_only_count: 13`, `entries: 98`, `catalog_status: DEFINITION_ONLY`,
`catalog_version: 1.4.0`.

---

## 4. Hermes monetization and commercial surface — owner-requested sweep

**Question:** what Hermes monetization survives in the architecture records, and
what must be removed?

**Answer: nothing needs removing. It was decided out, contracted, and is
trivially satisfied — but nothing has executed the check yet.**

### 4.1 The decision

`DEC-RANEX-026` (`ADR-0006:234-241`, `ACCEPTED`, governing ADR `ADR-0011`):

> `Hermes/Nous is provenance, compatibility, and reference only: no live
> inference, parent-agent model loop, Portal/model route, credential/entitlement,
> billing, credits, subscription, managed tool pool, purchase, promotion, or
> fallback`

Rejected alternatives are recorded and are the ones that matter: *"hide
commercial UI"* and *"retain dormant commercial runtime"*. The decision is
removal, not concealment.

`DEC-RANEX-027` closes the adjacent route: a release-pinned catalog "cannot
activate or mutate a route; model/provider/adapter fallback, provider subagents,
and auxiliary model calls are disabled."

### 4.2 The fitness function

`FF-DECOMM-001` (`ADR-0011:475`):

> Static, package, runtime, credential, network, and SBOM evidence proves no
> Hermes/Nous inference, Portal, credential/entitlement, monetization,
> managed-tool, purchase, or fallback route.

### 4.3 The contracted obligations

**21 of 98 catalog entries** carry de-commercialization content — 18
`HERMES-PROMOTION-*`, 2 `HERMES-OWNER-DECISION-*`, 1 `HERMES-RESEARCH-ONLY-*`.
**18 carry `failure_outcome: BLOCK`.** **FACT**, measured by parsing
`hermes-research-promotions.json`.

Rows: `HERMES-PROMOTION-011, -037, -038, -039, -041, -042, -043, -044, -045,
-047, -048, -049, -050, -051, -053, -054, -055, -057` ·
`HERMES-OWNER-DECISION-014, -015` · `HERMES-RESEARCH-ONLY-008`.

Representative obligations, quoted verbatim:

- *"Remove the Nous commercial model provider and all account, credit,
  subscription, payment, entitlement, Portal, and promotional infrastructure;
  retain only provider-neutral cost and budget measurement."*
- *"Runtime packages exclude `x-nous-credits-*`, `billing:manage`,
  `providers.nous`, Portal OAuth scopes, managed tool-pool entitlement, and
  `product=hermes-agent` request tags."*
- *"`/topup` and `/subscription` commands, billing and subscription RPCs,
  checkout, card, and auto-reload schemas, and Portal proxy routes are
  unregistered."*
- *"Payment methods, subscriptions, balances, entitlements, and billing
  authorization data are never copied into Ranex."*
- *"Sessions, canonical databases, exports, and backups contain no payment
  method, subscription, commercial balance, Portal entitlement, or Nous auth
  token."*
- *"The wheel, container, and SBOM exclude dedicated billing UI, purchase
  clients, Nous provider plugins, generated billing bundles, and
  monetization-only dependencies."*
- *"`nous`, `nous-portal`, and `nousresearch` do not resolve as a runtime
  provider or model-catalog owner."*

Enforcement staging, **FACT**: `blocking_stage` = `RELEASE` (11), `MIGRATION`
(3), `EFFECT_DISPATCH` (2), `PRODUCTION_READY` (2), `MODULE_ACTIVATION` (2).
`check_class` = `RELEASE_FITNESS` (9), `RUNTIME_FITNESS` (4),
`MIGRATION_FITNESS` (3), `SUPPLY_CHAIN_FITNESS` (2).

### 4.4 What must actually be removed: nothing

Every artifact these obligations name — the wheel, the container, the SBOM, the
npm bundle, `providers.nous`, `/topup`, billing RPCs, Portal OAuth scopes —
**does not exist in this repository.** There is no Hermes commercial code in the
tree because there is no Hermes code in the tree at all
([inventory §0](hermes-inventory.md)).

The single declared runtime dependency is `PyYAML`.

### 4.5 The honest caveat — satisfied by absence, not by proof

`catalog_status` is **`DEFINITION_ONLY`**. The obligations are *defined and fail
closed by design*; **no job executes them.** They first bite at `RELEASE` and
`PRODUCTION_READY`, and this project has reached neither.

So the correct statement is: *Ranex carries no Hermes monetization surface,
because it carries no Hermes code* — **not** *"`FF-DECOMM-001` has passed."* It
has never run. Asserting otherwise would be the false-closure pattern this
project keeps recording.

**Risk:** low now, and it **falls further with time** — every day the tree stays
Hermes-free, the eventual `FF-DECOMM-001` run gets cheaper. The risk inverts
only if a future slice imports a Hermes provider adapter for convenience, at
which point 18 fail-closed rows activate at release. That is the system working.

### 4.6 False positives, checked

A naive keyword sweep of `docs/architecture/` returns **613 hits for
"promotion"**. **All 608 in-scope hits are the RFC→ADR promotion concept;
matches for commercial promotion: 0.** **FACT**, measured. Likewise "credit"
matches mostly appear inside "credential".

Recorded because this repository has a documented history of miscounting from
substring matches — a file list built on `429` matching inside a SHA-256 hash,
and a rule tally built on `[value]` matching a code fragment. Any future
monetization sweep must classify its matches, not count them.

### 4.7 Ranex's own monetization is a separate, open question

Distinct from removing Hermes's. `LICENSE-RANEX.md` is personal-use, all rights
reserved, so commercial optionality is preserved; `ADR-0011` forecloses the
Hermes inference-margin model specifically. `docs/HANDOFF.md` records it as an
open thread, with FedRAMP's 2026-09-30 machine-readable authorization-package
requirement (NIST OSCAL) as relevant new context. **Out of scope for this audit
and for Slice 1.**

---

## 5. Where this map is weakest

Stated so absence of a row is not read as absence of risk.

1. **The import surface is a fact about today, not a guarantee.** Nothing in CI
   fails if `src/ranex/` grows an HTTP client or a second dependency. An
   import-surface assertion is the cheapest closure and is **deliberately not
   built** — it would be new functionality, which the brief forbids.

2. **The Python version range is declared, not asserted.** `>=3.11,<3.15` sits in
   `pyproject.toml`; nothing checks it at runtime, and canonicalisation depends
   on hash and ordering behaviour. Low likelihood, but `BC-4` is a
   cross-machine claim and has only been demonstrated on one machine
   (CPython 3.14, this host).

3. **`BC-4` determinism is demonstrated across two runs on one machine**, not
   across machines, Python versions, or PyYAML patch releases. The stronger
   claim requires CI evidence that does not yet exist.

4. **`develop` is a CI dependency, and the recorded reason for it is wrong.**
   Both `drift` and `validate` read git objects for commit `0533e1eaf`
   (`generate_contracts.py:4938,5140`; `validate_contracts.py:13841`). The
   handoff and the workflow comment
   (`.github/workflows/architecture-contracts.yml:75-76`) both say it is
   "reachable from no other ref." **Measured 2026-07-31 — false.** Four refs
   reach it:

   ```console
   $ git for-each-ref --format='%(refname)' | while read r; do
       git merge-base --is-ancestor 0533e1eaf… "$r" 2>/dev/null && echo "$r"; done
   refs/heads/architecture/validated-baseline-20260728
   refs/heads/develop
   refs/heads/feature/deterministic-gate-controller-mvp
   refs/remotes/origin/develop
   ```

   The object survives deletion of `develop` alone. The stated single point of
   failure does not exist; the dependency on the *object* does. The same two
   lines also call `develop` **UNPROTECTED**, which the handoff contradicts.
   Two stale claims in one comment block — treat it as unverified until
   re-measured.

5. **A green `drift` is not evidence that the `ADR-0010` baseline exists.**
   Reproduced independently from a `--depth 1` clone where `0533e1eaf` is
   **absent**:

   ```console
   $ git -C probe cat-file -e '0533e1eaf…^{commit}'    →  ABSENT
   $ cd probe && uv run … generate_contracts.py
   {"assessments": 41, "projections": 10, "registries": 46, "schemas": 157}
   GEN_EXIT=0
   $ git status --porcelain                            →  (empty)   # DRIFT GREEN
   ```

   The generator falls back to reading its own prior committed output —
   `existing_legacy_policy_file_rows()` reads
   `architecture/contracts/legacy-test-layout-policy-v1.json` — instead of the
   git object, so the projection **confirms itself** and the tree is
   byte-identical.

   **CI as a whole does not fail open.** `validate` catches it:

   ```console
   $ uv run … validate_contracts.py ; echo $?
   1
   status = FAIL
   error  = LEGACY_FIXTURE_GIT_COMMAND:…:read-tree 0533e1eaf…:
            fatal: failed to unpack tree object 0533e1eaf…
   ```

   Both are required checks, so the gate holds. The narrower finding stands:
   anyone reading the four leaf checks as independent proofs would over-read
   `drift`. Surfaced by the HY3 audit, reproduced here.

6. **Determinism survives a hostile environment — a positive result.** The
   generator produced a byte-identical tree under `TZ=Pacific/Kiritimati`,
   `LC_ALL=tr_TR.UTF-8` (the Turkish-`I` case-folding trap), a set
   `PYTHONHASHSEED`, a fake `HOME`, `SOURCE_DATE_EPOCH=0` and `umask 077`.
   Executed by the HY3 audit; **not re-run here**, so INFERENCE as to
   reproducibility on this host.

7. **`refs/codex/**` — 15 refs, 11 copyrighted PDF blobs, public `origin`.**
   Not a Slice 1 dependency; the highest-consequence unresolved item in the
   repository. `git push --all` or `--mirror` publishes them. Unresolved by
   owner choice.

6. **Hermes behaviour was never executed.** All Hermes claims in this audit read
   source at `phase/2-runtime-bootstrap`. Behavioural claims are marked
   **INFERENCE** throughout.
