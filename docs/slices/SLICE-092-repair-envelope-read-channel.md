# SLICE-092 — Repair envelope at the read channel (C1+C6)

**Status:** open
**Origin:** oracle-science report §3.1/§3.6/§8 SLICE-A; captain DIRECT 004.

## Contract

A FAIL verdict today names the claim and nothing else: the closed suite
summary carries counts and non-passed IDs, so an honest agent must re-run
failing tests or ingest raw junitxml to learn *what* asserted and *where*.
This slice ships the repair envelope — a bounded, advisory read-channel
packet carrying failing test IDs, assertion text, file:line, the repro
argv, and the C2 ladder's next-rung pointers (L0 compile → L1 targeted
IDs → L2 full suite). It tells the agent WHAT failed and WHERE; it never
proposes a fix. Kernel untouched: `verdict.py`/`KERNEL_DIGEST` do not
move, `evaluate()` purity unchanged, no new runtime dependency.

- `src/ranex/governed_execution/repair_envelope.py` — the pure renderer
  (`ranex-repair-envelope-v1`, closed key sets at every decode boundary,
  deterministic bytes, bounded: 16 failure entries, 200-char assertions).
- `foundation/suite_results.py` gains `failure_locations()` — junit
  assertion/file:line extraction beside the existing parser, one
  derivation, same refusals (UTF-8, no DTD, duplicate IDs).
- `ranex run` retains the junit artifact one seam longer (captured inside
  the materialisation, before teardown) and writes it to the gitignored
  verdict channel as `<subject>.junit.xml` — runtime state, never
  evidence, never signed.
- `ranex gate evaluate` composes the envelope at the ADR-019/020
  projection boundary when it publishes a verdict: causes verbatim from
  the projected record, repro argv from the freshest admitted suite
  record, failure detail from the retained junit. Published beside the
  verdict as `<subject>.envelope.json`, unsigned, bound to the verdict by
  `verdict_record_digest`. Envelope bytes are NEVER evidence.
- `task delegate` captures the junit at the same seam
  (`_run_suite_with_results`); the ADR-043 retained-log manifest gains an
  additive `envelope` field (stream record: file/bytes/sha256 of
  `repair-envelope.json`, redacted with the same literals as the streams).
- `ranex task stop-hook [--mode stop|pretooluse]` — the C6 harness
  attachment. Stop: runs the governed cycle observer-side (in-process
  `main()`: `run` then `gate evaluate`), reads the published verdict +
  envelope from the read channel, and answers the harness with
  `{"decision": "block"|"approve", "reason": <packet>,
  "envelope": <structured>}` — the agent ingests only verdict + envelope,
  never suite output, and the loop is fully autonomous across a 3-miss
  budget (captain DIRECT 008): a durable per-subject miss counter in the
  read-channel dir (runtime state, never evidence; reset on PASS) stops
  deterministically at `--budget` misses — no human review step, no LLM
  LGTM, no pane wait anywhere in the flow. The envelope is
  machine-consumable structured bytes; the text rendering is derived from
  the same structure and is never the only form. PreToolUse: blocks the
  agent from running the frozen suite argv itself. Without a signing
  credential it never fabricates: it reads whatever verdict is already
  published and says so, because `delegation.py:93` keeps the key out of
  every delegated environment and `main.py:798` refuses unsigned writes.
  Freeze discipline (captain DIRECT 008 FINAL): freeze artifacts are
  minted by promote ships like this one, never by the graded run — the
  loop itself writes no manifest and no freeze, and changing what
  "correct" means needs a new human-approved ADR/spec, not an edit here.

## Non-goals

No localization, no patch generation, no C2 ladder orchestrator (pointers
only), no C3/C4, no BASE freeze file, no new signing domain (the envelope
is unsigned advisory bytes; the signed verdict beside it is the authority).

## Validation

Red-first unit/contract tests (`test_repair_envelope.py`,
`test_repair_envelope_flow.py`, delegate/run/projection/stop-hook rows in
the existing suites). Real-data receipts under
`tools/dogfood/audits/2026-09-25-p0-envelope/`: pinned six@1.17.0 subject
with a real failing test; envelope carries its ID, assertion and
file:line from the real junit; 3× byte-identical envelope digests;
negative controls — envelope bytes offered as evidence refused, unsigned
governed cycle refused, delegated environment + credential refused;
measured bytes-ingested delta quoted from this host, never copied from
the report. Suite manifest refrozen on the committed tree.
