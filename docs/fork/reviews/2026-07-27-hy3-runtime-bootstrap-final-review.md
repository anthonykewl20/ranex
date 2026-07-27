# HY3 final review of Ranex adoption and Hermes runtime bootstrap

| Field | Value |
|---|---|
| Review ID | `REV-RANEX-RUNTIME-HY3-001` |
| Completed | 2026-07-27 21:50 Asia/Manila |
| Subject revision | `beee3cdc431e38b6e82ec5628263f743932022e4` |
| Model route | `openrouter/tencent/hy3` |
| Variant | `high` |
| OpenCode | `1.18.7` |
| Session | `ses_05c2a1005ffeMBOo7aB1q0PzF3` |
| Execution | Fresh `--pure` session using a custom tool-less primary agent |
| Sharing / snapshots | Disabled |
| Packet SHA-256 | `d3f53432aa889f7873708b14c7d0aef48e01a2820bf8e65d74ab01f2026dab56` |
| Repository mutations by HY3 | None |
| Review authority | Advisory only; human owner retains gate authority |
| Token accounting | 34,064 input; 1,386 output; 4,995 reasoning; 42,269 total |
| Reported route cost | `$0.007925808` |

The exact frozen packet is preserved at
[`artifacts/2026-07-27-hy3-runtime-bootstrap-review-packet.md`](artifacts/2026-07-27-hy3-runtime-bootstrap-review-packet.md).
Its annexes were attached separately so HY3 received the complete file text
rather than summaries alone.

The custom reviewer agent exposed no tools: Bash, read, edit, write, glob,
grep, web, task, question, and skill tools all resolved to `false`. HY3
therefore could not mutate or inspect the repository, credentials, or host. One
earlier local invocation was rejected by OpenCode's file-argument parser before
any model request; the successful fresh session above used the corrected
argument order.

## Verdict at a glance

- Review verdict: `PASS`
- Readiness verdict: `READY_WITH_REQUIRED_REMEDIATIONS`
- Immediate blockers: none
- Phase 0A: `PARTIAL`
- Phase 1: `PARTIAL`
- Phase 2: `PASS`
- Phase 3: `PARTIAL`

HY3 found Hermes correctly configured for immediate bounded development through
the documented isolated-home launch contract. It did not promote deferred
cleanup or inherited test failures to `PASS`, and it did not claim that the
target Ranex architecture or rebranding is implemented.

## Post-review configuration hygiene

After preserving the frozen verdict, Hermes' own config migrator updated the
isolated `config.yaml` from schema version `0` to `33`. No optional API key was
added. The file remains mode `0600`, `hermes config check` reports version
`33 ✓`, and the resolved model configuration remains:

```json
{"provider": "openai-codex", "default": "gpt-5.6-sol"}
```

A subsequent live Hermes smoke supplied neither a provider nor model override;
the persistent defaults resolved successfully and returned exactly
`RANEX_HERMES_CONFIG_OK`. This closes the schema-hygiene item without changing
the reviewed Git subject or the unedited HY3 response below.

The dashboard's first production build was also completed after review. A
transient isolated launch served the expected dashboard document with HTTP
`200` at `http://127.0.0.1:9119`; the process was then stopped cleanly. After
the owner explicitly requested reboot persistence, a loopback-only systemd user
service was installed, enabled, restart-tested, and verified at the same URL.
User lingering is enabled, so it does not require an open terminal after login
or reboot. The unedited response below correctly retains the service's
not-yet-installed state at review time.

The three inherited Python failures were assigned stable `BL-001` through
`BL-003` identities in [`../BASELINE_DEFECTS.md`](../BASELINE_DEFECTS.md), with
comparison and closure rules. This completes HY3's tracking action while
retaining the failures and Phase 3 as `PARTIAL`. Deferred Phase 0A cleanup
remains open by owner direction.

## Unedited HY3 response

### 1. FINAL VERDICT

`READY_WITH_REQUIRED_REMEDIATIONS`

The published Ranex `develop` revision (`beee3cdc…`) and its isolated Hermes 0.19.0 runtime at the phase-2 worktree are materially consistent and safe for the owner to begin bounded, local Ranex development now under the documented launch contract, provided the listed required follow-ups are honored. This verdict does **not** represent the target Ranex governed-execution architecture, public rebranding, or deferred Codex/VS Code cleanup as implemented; those remain explicitly open per the non-goals. The four direct questions are answered by the gate verdicts below: upstream adoption is honest (PASS), the runtime is correctly configured for `openai-codex`/`gpt-5.6-sol` (PASS), the test counts and `PARTIAL` labels are honestly retained (PASS), and gaps are classified in sections 3–5.

### 2. GATE VERDICTS

| Gate | Verdict | Evidence |
|---|---|---|
| Upstream adoption integrity | PASS | E-R1, E-R2, E-R3; `main` layers docs on exact upstream history; `develop` adds only docs; no runtime diff from baseline |
| Published branch and ancestry integrity | PASS | E-R1; ancestry checks exited zero; `main`/`develop` 0 ahead / 0 behind vs origin |
| Licensing/provenance evidence | PASS | `legal/licensing-manifest.json`; upstream `LICENSE` retained; Ranex license scoped to original material; `CURATED_RESEARCH` marked `NOASSERTION` |
| Isolated runtime installation | PASS | E-H1; external Python 3.11 venv; editable install; not inside Git checkout; system Python untouched |
| Provider/model/auth configuration | PASS | E-H2 (`config check` exit 0), E-H3 (separate `ranex` OAuth, device-code, mode 0600), E-H4 (smoke `RANEX_HERMES_OK`) |
| Baseline test honesty | PASS | E-T2/E-T3; 48,519 Py pass / 3 host-sensitive inherited fails; 4,826 JS pass; `PARTIAL` retained honestly |
| Immediate CLI development usability | CONDITIONAL | E-H1/E-H5; works only under documented env contract; CWD CLI resolves worktree; no project registration (nonblocking) |
| Immediate web dashboard usability | CONDITIONAL | E-H5; installed, loopback `127.0.0.1:9119`, but web dist not built; first launch builds; not needed for CLI coding |
| Evidence sufficiency | PASS | Attestation-level declared; internal consistency; annex digests present; no rerun claimed |

### 3. BLOCKERS

None.

### 4. REQUIRED REMEDIATIONS

- **Before first merge** — Track the three inherited Python baseline failures (copilot home preservation; two credential-pool failure-attribution tests) as recorded baseline defects so future Ranex changes compare against honest counts (`UPSTREAM_BASELINE.md` follow-up 1–2). *Acceptance:* the three failure names are documented in the Ranex defect tracker and referenced from the `develop` CI baseline comparison.
- **Before first merge** — Keep Phase 0A cleanup debt and the deferred primary-checkout switch explicitly visible as open items; do not relabel Phase 0A / 1 / 3 as `PASS` (`IMPLEMENTATION_STATUS.md`). *Acceptance:* status doc retains `PARTIAL` and the owner waiver note.
- **Before release** — Complete the deferred Codex/VS Code cleanup and primary-checkout switch under the owner's sequencing, and complete the config schema version migration if a minimal `config.yaml` is shipped (E-H2 version `0` vs `33` is an available, nonblocking migration now). *Acceptance:* primary checkout on `main`/`develop` with no active foreign session; config schema current or explicitly exempt.

### 5. NONBLOCKING GAPS

- **Config schema migration** (version `0` vs `33`): nonblocking; runtime deep-merges defaults, `config check` passes.
- **Optional project registration** in project DB: nonblocking; CWD-based CLI resolves the worktree.
- **Global launcher**: nonblocking; `.local/dev-env.sh` contract works.
- **Background dashboard service**: nonblocking; not needed for bounded CLI coding.
- **First dashboard build**: nonblocking for CLI; required only if the dashboard is used (E-H5).
- **Playwright/browser support**: nonblocking optional.
- **Web-search keys**: nonblocking optional.
- **Optional third-party integrations**: nonblocking.
- **Deferred primary-checkout cleanup (Phase 0A)**: nonblocking for coding under the waiver, but tracked as debt.

### 6. CLAIMS THAT MUST NOT BE MADE

- The target Ranex governed-execution architecture is implemented (it is not).
- Public rebranding / compatibility migration is complete (only the README license-scope notice changed).
- Phase 0A cleanup, Phase 1 adoption, or Phase 3 baseline are `PASS` (they are `PARTIAL`).
- The three baseline test failures are fixed, absent, or non-existent (they are retained as honest baseline defects).
- The web dashboard is ready to use without a first-build step.
- HY3 reran or independently verified the 50,000+ tests, credentials, or network (tool-less, attestation only).
- Hermes imports or mutates Codex/VS Code credentials (it uses a separate `ranex` OAuth).
- The primary checkout switch completed (it is deferred under the owner waiver).

### 7. DIRECT ANSWER TO THE OWNER

Yes. Hermes is correctly installed and configured for immediate use with `openai-codex` and `gpt-5.6-sol`: the isolated config selects that provider/model, `hermes config check` passes, a separate `ranex` OAuth credential is logged in, and a one-call smoke returned `RANEX_HERMES_OK`. The exact launch contract today is: `source .local/dev-env.sh` then `hermes`, or prefix `HERMES_HOME=/home/soultransit/.local/share/ranex`. Without that env Hermes uses the default `~/.hermes` profile, so always source first. CLI coding works now (terminal/file/delegation/memory/skills available). Dashboard, browser, and web-search are optional and not needed to start. Begin bounded work from the isolated `develop` worktree; keep deferred cleanup and `PARTIAL` labels visible as debt.

### 8. REVIEW LIMITATIONS

This review is tool-less: HY3 received only the frozen packet and annex texts and did not inspect credentials, the network, mutable host state, or rerun any tests. It is attestation-level: baseline counts and environment observations are accepted as reported, not independently reproduced — the packet itself declares this limit and HY3 states it here. HY3 has advisory, not gate, authority; the human owner decides. The frozen evidence (E-R*, E-H*, E-T*) is judged for internal consistency only.

### 9. MACHINE-READABLE VERDICT

```json
{
  "review_verdict": "PASS",
  "readiness_verdict": "READY_WITH_REQUIRED_REMEDIATIONS",
  "phase_status": {
    "phase_0a": "PARTIAL",
    "phase_1": "PARTIAL",
    "phase_2": "PASS",
    "phase_3": "PARTIAL"
  },
  "blocker_ids": [],
  "required_followups": [
    "track_three_baseline_failures_before_merge",
    "keep_phase_0a_and_deferred_checkout_debt_visible",
    "complete_deferred_cleanup_and_schema_migration_before_release"
  ],
  "authority_note": "ADVISORY_ONLY_NO_GATE_AUTHORITY"
}
```
