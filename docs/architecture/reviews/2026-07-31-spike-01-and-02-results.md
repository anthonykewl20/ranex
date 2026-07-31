# SPIKE-01 and SPIKE-02 — results

Bounded evidence-gathering, executed 2026-07-31. Both spikes were predeclared in
[`2026-07-31-delivery-model-restructure-assessment.md`](2026-07-31-delivery-model-restructure-assessment.md)
§10 with success and failure criteria fixed **before** running.

Neither spike authorizes anything. Both were run read-only or inside the tooling
lane. Every claim below is from an executed command whose output is quoted.

---

## SPIKE-01 — Can the kernel load a gate definition from the generated contract tree?

**Settles `RISK-02`.** Predeclared success: one gate loads from the committed
tree with no hand-editing, and a test asserts the loaded definition equals the
document's declared content. Predeclared failure: loading requires editing a
generated file, or the registry cannot express the gate without a schema change.

### Result: **FAILED — decisively, and the failure is more interesting than a pass**

Executed against `architecture/contracts/readiness-tiers.json` and the tracer's
`ranex.policy.domain.gates`:

```
registry gates: 21
registry gate fields: ['bridge_rule_id', 'evidence_role', 'freshness_rule',
                       'gate_id', 'noncompensating', 'required_result', 'tier_id']
GateDefinition needs:  ['action', 'gate_id', 'rules']
MISSING from registry: ['action', 'rules']

attempt 1 — construct straight from the registry row:
  FAIL TypeError: GateDefinition.__init__() got an unexpected keyword argument 'bridge_rule_id'

attempt 2 — map what exists, invent nothing:
  FAIL ValueError: identity must be a lowercase prefix plus UUIDv7

attempt 3 — is a rule derivable from any registry field?
  rule fields present in registry row: NONE
  FAIL ValueError: required_claim_ids must not be empty
```

### The finding

**The two artifacts are different concepts that share the word "gate."**

| | Registry (`readiness-tiers.json`) | Kernel (`GateDefinition`) |
|---|---|---|
| Answers | *Which evidence role satisfies which readiness tier gate?* | *Which rules must pass before this action is permitted?* |
| Keyed by | `tier_id`, `evidence_role`, `bridge_rule_id` | `action`, `rules[]` |
| Has rules | **No** | Yes — with enforcement class, resolution, required claims |

Five things would have to be **invented** to bridge them: `action`,
`rules[].enforcement`, `rules[].resolution`, `rules[].required_claim_ids`, and a
canonical `gate:` identity. Inventing five fields is not loading a contract; it
is authoring a new one and calling it derived.

### Decision produced

- **Option (a) — load the registry directly: REFUTED by execution.** Not a
  matter of effort. The registry does not contain the information.
- **Option (b) — add a generated runtime projection: the only viable path.** A
  new marked block would have to *declare* action-gate rules in a source
  document, and the generator would project them. That is new authored content,
  not a re-shaping of existing content.
- **Option (c) — keep two catalogs: what exists today**, and now understood to
  be two catalogs because they express two different things, not through
  neglect.

**`RISK-02` is not closed. It is re-stated more precisely:** the compiled tree
contains no action-gate rules for a runtime to enforce, so the
document → registry → running-check path cannot be closed by wiring. It requires
someone to decide what the action gates *are* and write them down. That is a
real architectural decision and belongs in an ADR when a slice needs it.

**Consequence for Slice 1:** the slice must either declare its own gate rules in
a source document and add the projection, or load from a YAML catalog as the
tracer already does and **not claim** it closed the pipeline. The second is
smaller and honest. Recommended.

---

## SPIKE-02 — Is `ADR-0018`'s strict-typing obligation satisfiable?

**Settles `RISK-03`.** Predeclared success: owners cleared with a **valid**
neutrality proof — generate one tree with the OLD script and one with the NEW,
and diff *those two*, never a tree against itself. Predeclared failure: any tree
difference, or per-owner effort extrapolating to an unacceptable total.

### Result: **PASSED**

```
# baseline, OLD script
$ uv run --project scripts/architecture python scripts/architecture/generate_contracts.py
gen_old EXIT=0
BASELINE STABLE: generator is idempotent on committed tree
$ git status --short architecture/contracts
(empty — regeneration changed nothing)

# change: two call sites moved to a fail-closed helper

# NEW script
$ uv run --project scripts/architecture python scripts/architecture/generate_contracts.py
gen_new EXIT=0
$ diff -rq /tmp/spike2_baseline /tmp/spike2_new
IDENTICAL — change is behaviour-neutral on the generated tree

$ cd scripts/architecture && uv run --group typecheck pyrefly check
INFO 243 errors        # was 245

$ uv run --project scripts/architecture python scripts/architecture/validate_contracts.py
status: PASS | scope: EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY
```

### The change

`re.search(...)` returns `Optional[Match]`, so `re.search(...).group(1)` is a
latent `AttributeError` that `pyrefly` reports as `missing-attribute`. Two call
sites — `parse_topology_decision` and `parse_tdd_decision` — now go through:

```python
def require_search(pattern: str, text: str, what: str) -> re.Match[str]:
    match = re.search(pattern, text)
    if match is None:
        raise ValueError(f"{what}: no match for {pattern!r}")
    return match
```

Behaviour on the matching path is identical. On the non-matching path it raises
a message naming the pattern instead of `NoneType has no attribute 'group'` — a
strict improvement, and the reason this is a real fix rather than a silencing.

### Decision produced

**Continue incrementally. `ADR-0018` does not need amending.** The obligation is
satisfiable; the earlier bulk attempt failed on method, not on feasibility.

Two things distinguish this run from the reverted one:

1. **The proof was valid.** The previous attempt regenerated with the *same*
   script and compared the tree to itself, which demonstrates idempotence and
   nothing else. Here the OLD-script output was captured first, then the NEW
   script's output was diffed against it.
2. **The fix removed a real defect** rather than annotating a variable into
   silence. The reverted batch moved `bad-assignment` 3 → 18 precisely because
   annotating a variable that is later reassigned changes what type-checks.

**Method for the remaining 243, recorded so it is repeatable:** one owner at a
time; capture the OLD-script tree before touching anything; diff OLD against NEW
after; run the validator; record the count **with its working directory**. Do
not batch. Do not annotate a variable to satisfy the checker without
understanding why the type is wrong.

---

## Effect on the risk register

| Risk | Before | After |
|---|---|---|
| `RISK-02` — compiled tree has no runtime consumer | `UNRESOLVED` | **`UNRESOLVED`, sharpened.** Wiring cannot close it; the registry holds no action-gate rules. Needs an authored decision |
| `RISK-03` — strict typing may be unsatisfiable | `UNRESOLVED` | **Closed as a risk.** Satisfiable incrementally with a valid proof. 243 remain as ordinary debt |
