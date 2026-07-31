# AGENTS.md — read this before doing anything

You are an AI agent working in the Ranex repository. This file tells you what
you may do, what you may not, and where to look. It is short on purpose.

If you read nothing else, read §1 and §2.

---

## §1 The one thing that stops most work

**No product code may be written, with exactly one live exception.**
`IMPLEMENTATION_START_READY` is not declared. `ADR-0012:72` and its machine
contract at `:656-657` forbid implementing a product capability.

**The exception:** `architecture/records/bootstrap-authorizations/BOOTSTRAP-AUTH-001.md`
authorizes the **first walking skeleton only**, defined at
`docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md`. It expires
on completion and verification of that slice. It does **not** authorize unrelated
product work, and the permanent authorization issuance mechanism is a required
prerequisite before any second slice.

If your task is not that slice, the prohibition applies to you in full.

You may build **tooling**: compilers, generators, validators, schemas, fixtures,
manifests, review harnesses. You may write documents. You may run read-only
analysis.

If your task requires product code, **stop and say so**. Do not start it, do not
prototype it "just to explore," and do not put it in a worktree and call it
research without saying that is what you are doing.

`RFC-0010` would make this lane permanent. It is at `2.2.0`, **rejected twice**
by independent review, and authorizes nothing until promoted to an ADR. The
bootstrap record above is a bounded exception, not that lane.

---

## §2 Where to start, by what you were asked to do

**Do not read the whole corpus.** It exceeds ten million tokens. Read the one
document that matches your task.

| Your task | Read this, and stop |
|---|---|
| Understand the system | [`docs/architecture/MASTER_ARCHITECTURE_SPECIFICATION.md`](docs/architecture/MASTER_ARCHITECTURE_SPECIFICATION.md) — **the map.** Start here by default |
| Find what is decided | `docs/architecture/decisions/` — 20 ADRs, all `ACCEPTED` |
| Find what is proposed | `docs/architecture/rfcs/README.md` — proposals, **no authority** |
| Continue an in-flight session | `docs/HANDOFF.md` |
| Check a specific rule or ID | `docs/architecture/SDLC_CONTROL_CATALOG.md`, `docs/architecture/SOURCE_OF_TRUTH.md` |
| Change the generator or validator | `scripts/architecture/README.md` |

The map (§0 of the MAS) labels every claim `CONFIRMED`, `PROVISIONAL`,
`UNRESOLVED` or `OUT-OF-SCOPE`. **An accepted ADR does not make something
`CONFIRMED`.** Twenty ADRs are accepted; almost nothing is confirmed by running
code. Do not treat a written decision as a working system.

---

## §3 Hard rules

Violating any of these is a defect regardless of outcome.

1. **Never hand-edit generated output.** Everything in `architecture/contracts/`,
   `schemas/` and `docs/architecture/assessments/` is produced by
   `scripts/architecture/generate_contracts.py`. Edit the source document and
   regenerate.
2. **Never relax a check to make code pass.** If code cannot satisfy a rule,
   that is a finding. Report it.
3. **Never run `git push --all` or `git push --mirror`.** The object database
   contains copyrighted PDFs under `refs/codex/**` and `origin` is a **public**
   repository. A normal `git push <remote> <branch>` is safe.
4. **Never claim something is verified unless you executed the command.** Record
   the command **and its working directory** beside every number. A figure in
   this repo has been wrong three times for exactly that omission.
5. **Never state a checkable claim without checking it.** This is the single
   most common recorded failure here. Search before declaring anything absent —
   a negative result is evidence about your search, not about the corpus.
6. **Never let a model verdict act as authority.** A model's output is evidence
   at best. It cannot approve, and it cannot discharge an obligation that
   constrains it.
7. **ADR expansion is FROZEN** (owner decision, 2026-07-31). You may create an
   ADR only if **all four** hold: the current slice depends on it; delaying it
   blocks implementation; it is architecturally significant; and enough evidence
   exists to accept it. If any is false, record the uncertainty in the map with
   its deferral reason and reopen trigger — and move on.
8. **Do not build infrastructure because it might be useful.** No plugin
   systems, orchestration layers, distributed services, queues, event buses,
   caching layers or generalized abstractions until a slice demonstrates a real
   need.
9. **Evidence is the only valid reason to change accepted architecture.** When
   evidence invalidates an ADR, supersede it and cite the evidence. Never
   silently rewrite.

**The loop you are working inside:** map → smallest slice → only the blocking
ADRs → contracts → acceptance criteria → implementation → verification →
evidence → update the map → repeat. Architecture is no longer the bottleneck;
implementation evidence is.

---

## §4 Verify the repository yourself

All read-only. Run them rather than trusting this file.

```sh
# regenerate and validate the contract tree
uv run --project scripts/architecture python scripts/architecture/generate_contracts.py
uv run --project scripts/architecture python scripts/architecture/validate_contracts.py

# records must match reality; exits non-zero on staleness
uv run --project scripts/architecture python scripts/architecture/check_record_freshness.py

# type check — the working directory is LOAD-BEARING, see §3.4
cd scripts/architecture && uv run --group typecheck pyrefly check   # tooling: 243
uv run --with pyrefly==1.1.1 pyrefly check                          # product code: 0

# the slice's own gate, run against this repository
PYTHONPATH=src uv run python -m ranex.cli.main gate evaluate HEAD --approver owner
```

---

## §5 State as of 2026-07-31

Every row below was measured, not recalled.

| | |
|---|---|
| Product code | `src/ranex/` — the first walking skeleton **only**, under `BOOTSTRAP-AUTH-001`. 36 tests pass; 0 strict type errors |
| Accepted ADRs | 21 |
| Open proposals | `RFC-0002`, `-0003`, `-0007`, `-0009`, `-0010` |
| Contract validation | `PASS`, scope `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY` |
| Runtime validation | `NOT_ASSESSED` — nothing runs |
| Readiness | Neither tier declared |
| R&D tracer | 82 tests pass, in `.claude/worktrees/kernel-tracer`, **claims no authority** |
| Known debt | **243** strict type errors; type-check gate has no CI step; three stale figures. See MAS §11.2 |

---

## §6 If you are unsure

Say so and stop. This project treats an unreported assumption as a defect even
when the assumption turns out to be correct. Asking the owner costs a message;
guessing costs the evidence chain.

The owner is **not technical**. Lead with the answer, use plain language, and
keep it short.
