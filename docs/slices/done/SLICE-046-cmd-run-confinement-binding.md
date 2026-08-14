# SLICE-046 — cmd_run confinement binding

**Status:** open
**Opened:** 2026-08-15
**Priority:** P0 — the qualified strict-local session is not yet the production
`cmd_run` path, so the measured command can still reach signing authority.
**ADRs:** `docs/adr/ADR-006-landlock-confinement-of-the-bound-command.md`
(proposed) and `docs/adr/ADR-023-the-confinement-session-is-invoked-as-a-subprocess.md`
(proposed).

## Session-to-evidence binding

`run --confinement strict-local` is an opt-in CLI surface; ordinary runs retain
the current default. It materialises a closed `ranex-confinement-command-v1`
descriptor, invokes `python -m ranex.cli.host_confinement session` as a child,
then validates the closed `ranex-confinement-result-v1` bytes before it signs.
The result's command exit code is the evidence exit code. Evidence signs the
result SHA-256 and runtime confinement-profile digest. A child refusal, missing,
malformed, incomplete, stale, aliased, timed-out, surviving, or un-torn-down
result is an exit-2 refusal and writes no evidence.

The child-process boundary is mandatory: the controller enrolls its own PID in a
controller cgroup leaf and cannot remove that leaf until it exits. `src/` keeps
its import ban on `host_confinement`.

## Exact owned paths

Product implementation may change only:

- `src/ranex/cli/main.py` (`_execute_hermetically` and the evidence block)
- `src/ranex/foundation/signing.py`: the evidence signed-field set grows 8→10
  with `confinement_result_digest` and `confinement_profile_digest`; unsigned
  digests would be forgeable decoration, and this repository refuses unverified
  fields (ADR-001 precedent: `SIGNED_FIELDS` 5→7 and domain
  `ranex-evidence-v1`→`v2`)
- `governance/gates.yaml` only if a claim/command binding change is unavoidable;
   it is not expected to change
- `tests/security/test_slice046_cmd_run_confinement.py`
- `tests/e2e/test_slice046_evidence_confinement_fields.py` only if implementation
  needs the optional e2e split
- `tests/unit/test_evidence_signing.py:84,94`,
   `tests/unit/test_suite_results.py:275`,
   `tests/security/test_slice003_command_binding.py:123-129`, and
   `tests/contract/test_qualification_admission.py:430`, and
   `tests/security/test_slice008_execute_attest_separation.py:99-110`:
   deliberate contract edits only, retaining their test IDs while changing their
   pinned eight-field expectations to the ten-field set and their evidence-domain
   expectation to v4
- `tests/integration/test_slice017_native_launcher.py`: gate10 main.py production-entrypoint hash pin updated for the authorized binding change
- this slice; ADR-006's status line and MAP §11.5 RISK-06 row only at closure

Explicitly not owned: harness files, `host_confinement` lifecycle semantics,
verdict or journal schema, producer keys, ADR-017 work, or a new broker boundary.

## Frozen cmd_run contract

The implementation must construct descriptor and result paths under its
materialised repository authority and invoke only
`(sys.executable, "-m", "ranex.cli.host_confinement", "session")`. It reads the
child's canonical result bytes after exit zero, validates closed schema and
`teardown == {cgroup_kill: true, populated: 0, cgroup_removed: true}`, and signs
only then. `confinement_result_digest` is SHA-256 of those exact bytes and
`confinement_profile_digest` identifies the runtime profile. The signed exit code
equals `result.command.exit_code`, never a substitute child wait status.

## Deterministic acceptance gates

1. An unqualified strict-local host refuses before evidence, naming the
   qualification refusal. `tests/security/test_slice046_cmd_run_confinement.py`.
2. A nonzero controller, missing result, malformed/incomplete result, alias, or
   teardown mismatch refuses without an evidence file. The same test file.
3. A host-gated real session produces signed digests and result-derived exit code;
   changing the stored result digest invalidates the signature. The same test file.
4. The existing real lifecycle and import boundaries remain green:
   `tests/integration/test_slice018_confinement_session.py`,
   `tests/security/test_slice017_host_qualification.py`, and
   `tests/unit/test_verdict_publication.py`.
5. Documentation, frozen slice tests, and all named import-ban tests are green:
   `tests/contract/test_docs_discipline.py`.

## Sad-path mapping

| Failure | Required result | ADR-023 path |
|---|---|---|
| qualification drift | refuse before spawn; no evidence | 1 |
| controller nonzero | parsed refusal; no evidence | 2 |
| result absent or malformed | E-C18-RESULT; no evidence | 3–4 |
| teardown false/live/unremoved | refuse before signing | 5 |
| evidence/result exit mismatch | refuse | 6 |
| descriptor aliases authority paths | E-C18-PATH-ALIAS | 7 |
| timeout or survivors | kill, reconcile, refuse | 8 |
| no validated result reaches signing | construction and test refusal | 9 |
| import ban regresses | existing frozen tests fail | 10 |
| v3-domain evidence record presented to the v4 verifier | refused at admission — no silent downgrade | ADR-001 |

## Verification commands

```text
PYTHONPATH=src uv run --frozen pytest -q tests/security/test_slice046_cmd_run_confinement.py
uv run --frozen pytest -q tests/integration/test_slice018_confinement_session.py tests/security/test_slice017_host_qualification.py tests/unit/test_verdict_publication.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
```

## One-way door and stop conditions

The strict-local evidence-field/domain change is one-way once accepted records
exist. Old v3 records are refused, not migrated; `governance/evidence.json` is
gitignored and no signed evidence is committed, so there is nothing to migrate.
This follows ADR-001's 5→7/v1→v2 and SLICE-009's 7→8/v2→v3 precedents. Stop rather than import the
controller, add a fallback backend, sign a partial result, downgrade a child
refusal, alter a frozen test outside the five declared deliberate contract
edits, change a non-owned path, accept ADR-006, or close RISK-06 early.

## Not in this slice

- Harness confinement, managed profiles, or a systemd lifecycle broker.
- New verdict, journal, producer-key, or gate schema.
- ADR-017 governed fanout or any harness-lane file.
- ADR-006 acceptance and MAP RISK-06 closure before landed frozen gates prove it.

## Closure

Done criteria met: frozen tests 6 pass + 1 declared host-gated skip; full frozen
 suite 1023 passed / 8 skipped at f63713f43. Independent reviews (blind x2 across
 spec and implementation) completed with all findings fixed; OCR gates PASS per
 commit. ADR-006 accepted and RISK-06 closed this commit; ADR-017 accepted.
Gate9's ADR-006/RISK-06 pins were updated in the same deliberate-edit class.
 Follow-ups recorded: shared result-validator dedup, controller env narrowing,
and claim-type enforcement of confinement digests (follow-up slice).
