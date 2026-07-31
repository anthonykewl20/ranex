# Walking Skeleton — slice definition

The fourteen pre-coding deliverables required by the owner's 2026-07-31 policy.
**Supersedes** [`2026-07-31-slice-01-plan.md`](2026-07-31-slice-01-plan.md),
which is retained as history.

Objective is **architectural validation**, not feature completeness.

---

## 1. Slice objective

Prove end-to-end that a **deterministic gate can refuse a real change in this
repository on evidence alone** — no model consulted, verdict reproducible,
reason recorded.

## 2. Business outcome

Ranex's entire commercial premise is one sentence: *rules compiled into code
change what an agent produces; rules in a prompt do not.* That has **never been
tested**. Twenty accepted ADRs and 54,823 lines of validator rest on it.

This slice is the first evidence either way. If the mechanism works, every later
capability is an extension of a proven core. If it doesn't, we learn it now,
having spent one slice rather than another year of architecture.

## 3. User / operator workflow

```
An operator (or an agent) has produced a change and believes it is ready.

  $ ranex gate evaluate HEAD

  FAIL  gate=landing  rule=TESTS_EXECUTED
        required claim "tests-executed" has no evidence
        subject sha256:9b177f3e…
        exit 1

They supply the missing evidence, re-run, and get:

  PASS  gate=landing  subject sha256:9b177f3e…
        exit 0

The verdict and its reason are appended to a journal. Nothing was asked of a
model. Running it twice gives byte-identical output.
```

## 4. Scope

- One CLI entry point, one subcommand.
- One gate definition loaded from a **YAML catalog**, as the tracer does today.
- One rule carrying required claim IDs.
- Evidence records for those claims.
- Verdict `PASS`/`FAIL`, naming the failing rule and the missing claim.
- One append-only evaluation record bound to the subject digest.
- Non-zero exit on `FAIL`.
- Tests covering every contract and failure mode below.

## 5. Explicit exclusions

None of this may be added mid-slice. Adding any of it **ends the slice** and
requires re-acceptance.

Loading from `architecture/contracts/` (see §6) · a second gate · a second rule
type · fleet, workers or dispatch · worktree isolation · leases · **queues,
event buses, upcasters** · the readiness resolver · authenticated
human-decision records · capability scoring · record-freshness as a product ·
**plugins · caching · orchestration layers · generalized abstractions** ·
generalization to a second repository · **installation as a required merge
blocker**.

## 6. Applicable architecture sections

| Section | Bearing on this slice |
|---|---|
| §1.1 product thesis | The assumption under test |
| §4.1 central mechanism | The `generate → enforce` link this slice does **not** close |
| §5.3 components with executed evidence | ~70% of this slice already exists here |
| §6.2 compilation flow | `CONFIRMED`; unchanged by this slice |
| §6.3 the missing flow | **Stays missing.** See below |
| §8.1 trust boundaries | Agent↔checker, producer↔approver, enforcement↔inference |
| §8.3 determinism | RFC 8785 + SHA-256 |
| §11.1 `RISK-01` | This slice's target |

**Why §6.3 stays open — `SPIKE-01`, executed.** The generated registry holds
*readiness* gates (`evidence_role` → tier); the kernel needs *action* gates
(`action` → rules). Three load attempts failed; **five fields would have to be
invented**. So this slice loads YAML and **does not claim** to have closed the
pipeline. Claiming otherwise would be the false-closure pattern this project
keeps recording.

## 7. Applicable ADRs

**Governing:** `ADR-0007` (modular DDD layout) · `ADR-0008` (TDD) · `ADR-0014`
(Python) · `ADR-0015` (canonical event schema) · `ADR-0018` (pyrefly strict,
run from `scripts/architecture`) · `ADR-0019` (uv).

**Blocking, unresolved:** `ADR-0012:72` forbids product capability before
`IMPLEMENTATION_START_READY`. `RFC-0010` would authorize it and is not promoted.
**No new ADR is proposed by this slice** — under the frozen-expansion rule, the
one blocking decision already has its record.

## 8. Behavioural contracts

| # | Given | Then |
|---|---|---|
| BC-1 | Required claim with satisfying evidence | `PASS` |
| BC-2 | Required claim with **no** evidence | `FAIL`. Never a default, never a skip |
| BC-3 | Evidence bound to a different subject digest | `FAIL`, naming the mismatch |
| BC-4 | Identical inputs, two runs | Byte-identical verdict and record |
| BC-5 | Model access removed entirely | No verdict changes |
| BC-6 | Producer identity equals approver identity | `FAIL` |
| BC-7 | Gate definition with no blocking rule | Refused at load |

## 9. Failure modes

Missing evidence · stale evidence · wrong-subject evidence · malformed catalog ·
duplicate rule IDs · gate with no blocking rule · unreadable store · **store
write fails mid-append** · two concurrent evaluations · absolute path argument ·
**path traversal above the repository root** · remote or second-repository
target.

The last three are the enforcement of "governs only this repository," which is
otherwise only prose.

## 10. Acceptance criteria

1. Every behavioural contract and every failure mode has an **executed, passing**
   test.
2. The command **blocks a real change** in this repository, with output
   recorded. *A check only ever observed passing is not evidence.*
3. Two runs over identical inputs produce byte-identical records.
4. Removing model access changes no verdict.
5. `pyrefly` reports **no new errors** against the 243 baseline, measured from
   `scripts/architecture`.
6. Every recorded measurement carries its command **and working directory**.

## 11. Test plan

`ADR-0008` TDD — failing test first, recorded.

| Layer | Covers |
|---|---|
| Unit | Domain rules: absence blocks, subject mismatch, self-approval, no-blocking-rule |
| Integration | SQLite store: append, read-back, mid-append failure |
| Contract | Catalog loading, malformed input, duplicate rule IDs |
| Replay | Journal determinism — replay yields identical state |
| Confinement | Absolute path, traversal, remote target all refused |
| End-to-end | One real commit, one real refusal, one real pass |

## 12. Observability requirements

Every evaluation appends one record carrying: subject digest · gate id · rule id
· verdict · evidence considered · reason for failure · `subject_lane`.

Never recorded as fact: anything the evaluated party asserts about its own work;
any verdict not derived from observable evidence.

## 13. Rollback strategy

- **Advisory in CI only.** Promotion to a required merge blocker needs a
  separate explicit decision — a required check is gate-like authority.
- Governs only this repository. Grants no authority. Produces **no readiness
  evidence**; every record carries
  `subject_lane: PRE_READINESS_PRODUCT_SLICE`, and quarantine rule
  `QUARANTINE-001` fails any `BRIDGE-READY-*` binding that cites it.
- Rollback is reverting the commits. Nothing else unwinds, because nothing else
  was granted.
- Size bound ≤ 1,000 net lines of product source excluding tests. Exceeding it
  **ends the slice** rather than failing the build.

## 14. Success criteria

The slice succeeds if, with everything executed and recorded:

1. A real change was **refused** by compiled code, and the refusal reason was
   accurate.
2. The same inputs produced the same verdict twice, byte for byte.
3. No model was consulted, and removing model access changed nothing.
4. At least one architectural assumption moved from `PROVISIONAL` toward
   `CONFIRMED` in the map — **or was disproved**, which is an equally valid
   result and must be recorded as such.

**Rule 4 check.** Assumptions validated: exactly one primary — `RISK-01`, the
product thesis — plus its immediate corollaries (absence blocks, exact-subject
binding). It does **not** attempt `RISK-02` (`SPIKE-01` showed that needs an
authored decision first), `RISK-04`, or `RISK-05`. One assumption, not none, not
many unrelated. Correctly sized.

---

## Standing block — the one thing not resolved

This slice is product code. `ADR-0012:72` and the machine contract at `:656-657`
forbid it before `IMPLEMENTATION_START_READY`. `RFC-0010` would authorize it and
is blocked because **no authenticated `HumanDecisionV1` can be minted** — the
machinery now exists (`ADR-0017`, implemented and gated, 11 acceptance cases
passing), but nothing in this repository issues authentication contexts,
challenge digests or nonces.

`RFC-0010` records three routes out. The cheapest that preserves the fail-closed
guarantee is to record the authorization in the form the corpus **can** produce
today and require the issuance mechanism before the *second* slice.

**These fourteen deliverables are complete. Implementation begins when that
block is lifted, and not before** — rule 4 of the original mandate, and
`AGENTS.md` §1.
