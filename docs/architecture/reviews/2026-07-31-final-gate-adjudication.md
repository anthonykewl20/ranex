# FINAL GATE — adjudication by execution

Adjudicator: final gate agent. Method: run it, break it, restore it. Nothing below
is accepted on the strength of a document.

Repository: disposable copy at
`/tmp/claude-1000/.../scratchpad/final-gate`
HEAD: `f2c04c1674282052e26648b756481da337b45458`
(`ci: move enforcement onto the branch that actually matters`)
Working tree: dirty — `src/`, `tests/`, `governance/`, `pyproject.toml` and the
walking-skeleton docs are **untracked**; the validator and generator are
**modified but uncommitted**. The claimed work is therefore not committed. All
findings below are against the working tree.

Uncommitted `.github/workflows/` changes ignored per instruction.

Interpreter: CPython 3.14 in `.venv`, `uv 0.11.26`.

---

## 1. The five CLI verdicts

### 1.1 Invocation — the documented command is wrong in three places

`pyproject.toml` declares `[project.scripts] ranex = "ranex.cli.main:main"` but
also `[tool.uv] package = false`, so the console script is never installed:

```
$ uv run ranex gate evaluate HEAD --approver reviewer
error: Failed to spawn: `ranex`
  Caused by: No such file or directory (os error 2)
```

`AGENTS.md:119` and `MASTER_ARCHITECTURE_SPECIFICATION.md:284` give the working
form (`PYTHONPATH=src uv run python -m ranex.cli.main ...`). Three review
documents — `2026-07-31-walking-skeleton-definition.md:32`,
`2026-07-31-slice-01-plan.md:34`,
`2026-07-31-delivery-model-restructure-assessment.md:460` — all promise
`ranex gate evaluate <ref>`, which does not exist. **Cosmetic, but it is a claim
that fails on first execution.** Everything below uses the working form.

Subject under test, computed independently:

```
$ git rev-parse 'HEAD^{tree}'   -> 0beb9bb4e29ac9fb1840169bb4164f578890500d
canonical_sha256({"tree": ...}) -> sha256:9edd77be5492...93fe9e
```

which matches the digest recorded in the committed `governance/evidence.json`.
The evidence is genuinely bound to this tree; it was not fabricated for the demo.

### 1.2 The five required scenarios — all five behave as claimed

Verbatim output.

**A. No evidence at all** (`--evidence` points at a nonexistent file) → **FAIL**

```
FAIL  gate=landing  rule=TESTS_EXECUTED
      no evidence for required claim: contracts-validated, tests-executed
      subject=sha256:9edd77be549282954b4a40a25d549c5923f4505f672a2bc4365f9f396793fe9e
exit=1
```

**B. Evidence present with `exit_code: 1`** → **FAIL**

```
FAIL  gate=landing  rule=TESTS_EXECUTED
      no evidence for required claim: tests-executed
      subject=sha256:9edd77be549282954b4a40a25d549c5923f4505f672a2bc4365f9f396793fe9e
exit=1
```

**C. Wrong `subject_digest`** (`sha256:000...0`) → **FAIL**, and it names the
*reason* correctly rather than collapsing into "missing":

```
FAIL  gate=landing  rule=TESTS_EXECUTED
      evidence bound to a different subject digest: tests-executed
      subject=sha256:9edd77be549282954b4a40a25d549c5923f4505f672a2bc4365f9f396793fe9e
exit=1
```

**D. Producer == approver** (`--approver worker`) → **FAIL**, and it fails on
self-approval *first*, before evidence sufficiency, so a self-approver cannot
read the output as "nearly passing":

```
FAIL  gate=landing  rule=TESTS_EXECUTED
      self-approval refused: worker produced evidence and approved it
      subject=sha256:9edd77be549282954b4a40a25d549c5923f4505f672a2bc4365f9f396793fe9e
exit=1
```

**E. All good** (`--approver reviewer`) → **PASS**

```
PASS  gate=landing  subject=sha256:9edd77be549282954b4a40a25d549c5923f4505f672a2bc4365f9f396793fe9e
exit=0
```

Exit codes are `1/1/1/1/0`. Absence blocks; the gate is not decoration.
**Claim 1 as literally stated: UPHELD.**

### 1.3 But the subject binding is bypassable by OMISSION — DEFECT (HIGH)

`main.py:53`:

```python
subject_digest=item.get("subject_digest", subject_digest),
```

Evidence that simply **omits** the field is silently stamped with whatever
subject is currently being evaluated. The domain docstring claims "The subject
check is what makes stale evidence not evidence: the same command run against a
different commit proves nothing about this one." Executed:

```
$ cat /tmp/fg/ev_nosubj.json
[{"claim_id":"tests-executed","producer_id":"worker","command":"echo i-never-ran","exit_code":0},
 {"claim_id":"contracts-validated","producer_id":"worker","command":"echo i-never-ran","exit_code":0}]

$ ... gate evaluate HEAD   --evidence /tmp/fg/ev_nosubj.json --approver reviewer
PASS  gate=landing  subject=sha256:9edd77be...93fe9e            exit=0

$ ... gate evaluate HEAD~1 --evidence /tmp/fg/ev_nosubj.json --approver reviewer
PASS  gate=landing  subject=sha256:c03291ec...951534            exit=0
```

The *same two-line file*, containing a command that was never run, passes the
gate against **any** ref you point it at. Scenario C is defeated not by forging a
digest but by declining to supply one. The domain layer (`verdict.py`) is
correct — it demands an exact match and validates the digest format. The
**adapter throws the check away** before the domain ever sees it. This is the
single most load-bearing property of the design (unforgeable subject binding)
and the CLI edge does not hold it.

Fix is one line: `subject_digest=item["subject_digest"]` — make omission a
`KeyError`, which `cmd_gate_evaluate` already catches and turns into exit 2.

**Verdict on section 1: the five demonstrations are real and reproducible, but
the property they are meant to demonstrate is not enforced at the boundary.**

---

## 2. Repository confinement — NOT ENFORCED. `resolve_within_repository` is dead code.

### 2.1 Static fact: the function is never called by any production code

```
$ rg -n "resolve_within_repository|confinement" -g '!*.md' .
./tests/security/test_repository_confinement.py:13   from ranex.cli.confinement import resolve_within_repository
./tests/security/test_repository_confinement.py:18,24,29,38,48,57  (6 call sites — all tests)
./src/ranex/cli/confinement.py:1,21                  (the definition and its docstring)
```

**Zero call sites in `src/`.** `cli/main.py` does not import it.
`cmd_gate_evaluate` does `Path(args.repository).resolve()`,
`Path(args.evidence)`, `Path(args.gate_catalog)`, `Path(args.journal)` — four raw
paths, none of them confined. The module is a correctly-written function with a
passing six-test suite that guards nothing, because nothing calls it.

### 2.2 Executed proof: the CLI governs a foreign repository and PASSES

Built a second, unrelated git repository:

```
$ mkdir /tmp/fg/otherrepo && git init && echo "ATTACKER CONTROLLED" > payload.txt && git commit
HEAD 2825b584...  tree 667b8e9e...
```

First, pointed at it with this repository's evidence — it **evaluated the
foreign repo** (note the subject digest is the *foreign* tree, `acc8d35f…`, not
`9edd77be…`). It failed only on evidence mismatch, not on confinement:

```
$ ... gate evaluate HEAD --repository /tmp/fg/otherrepo --evidence /tmp/fg/ev_good.json --approver reviewer
FAIL  gate=landing  rule=TESTS_EXECUTED
      evidence bound to a different subject digest: contracts-validated, tests-executed
      subject=sha256:acc8d35ff0cb5d9f3a7e54de64e2ac21da87648084a694b387edee0c5edc0a97
```

That "FAIL" is not confinement. It is coincidence. Supply matching evidence and
the foreign repository passes:

```
$ ... gate evaluate HEAD \
    --repository   /tmp/fg/otherrepo            \  # foreign repo, absolute path
    --evidence     /tmp/fg/ev_foreign.json      \  # evidence from outside the repo
    --gate-catalog /tmp/fg/attacker-gates.yaml  \  # POLICY loaded from outside the repo
    --journal      /tmp/fg/attacker-journal.sqlite3 \  # journal WRITTEN outside the repo
    --approver reviewer
PASS  gate=landing  subject=sha256:acc8d35ff0cb5d9f3a7e54de64e2ac21da87648084a694b387edee0c5edc0a97
exit=0

$ ls -la /tmp/fg/attacker-journal.sqlite3
-rw-r--r-- 1 soultransit soultransit 12288 ... /tmp/fg/attacker-journal.sqlite3
```

Every one of the three refusals `SLICE-LANE-007` names was performed
successfully in a single command: **absolute path**, **second-repository
target**, and a write **outside the root**. The governing *policy itself* was
loaded from an attacker-controlled file outside the repository — the gate does
not merely evaluate the wrong subject, it applies rules it was handed.

### 2.3 The contract this violates, in its own words

`RFC-0010` §`SLICE-LANE-007` (`docs/architecture/rfcs/RFC-0010-...md:411`):

> A slice's **entry point** resolves every path against the governed repository
> root and **rejects** an absolute path, a traversal outside that root, or any
> remote or second-repository target. **This is a behavioural contract with a
> sad-path test, not a statement of intent.**
> `OPERATION_ON_ANY_OTHER_REPOSITORY` is in the lane's forbidden scope.

`2026-07-31-slice-01-plan.md:101`:

> The last three implement `SLICE-LANE-007`; they are the enforcement of
> "governs only this repository," which is otherwise **only prose**.

The entry point is `ranex.cli.main`. It rejects none of the three. The
sad-path tests exist and pass, but they test a library function that the entry
point never invokes — so they certify a boundary that is not installed. The RFC
explicitly anticipated this failure mode ("not a statement of intent") and the
implementation landed as exactly the thing it warned against.

`OPERATION_ON_ANY_OTHER_REPOSITORY` is declared forbidden scope. I performed it,
and got exit code 0.

**RULING: confinement is NOT enforced. Claim REFUTED.** Severity HIGH — this is
not an omission at the margin, it is the named contract of the slice, and the
tests that were offered as its evidence are testing an orphan.

Mitigating note in fairness: `MASTER_ARCHITECTURE_SPECIFICATION.md` §5.3 lists
the Slice 1 components with executed evidence and `cli/confinement.py` is *not*
among them, and §4 marks the CLI `CONFIRMED advisory only`. The master spec does
not overclaim. RFC-0010 and the slice plan do.

---

## 3. ADR-0021's non-inheritance branch — OBSERVATION at runtime, ASSERTION for the thresholds

Baseline first: the validator PASSES at HEAD in 85 s
(`uv run --project scripts/architecture python scripts/architecture/validate_contracts.py`
→ `"status": "PASS"`), and reaches the branch under test:

```
"test_layout_migration": "NOT_APPLICABLE_NO_INHERITED_SUBJECT"
"test_layout_validation": "CANONICAL_TOPOLOGY_PASS"
```

I loaded `validate_contracts.py` as a module and drove the lineage functions
directly. Observed facts at HEAD:

```
source_commit_is_ancestor              false   (git merge-base --is-ancestor 0533e1ea HEAD -> 1, confirmed by hand)
boundary_commit_is_ancestor            true
root_is_boundary_ancestor              true
boundary_root_commit_sha1              4ee007fc...   (git rev-list --max-parents=0)
boundary_committed_test_path_count     0
boundary_ancestry_test_commit_count    0
boundary_baseline_path_intersection_count 0
bootstrap_authorization_digest_matches true
walking_skeleton_definition_digest_matches true
OUTCOME: NOT_APPLICABLE_NO_INHERITED_SUBJECT
```

### 3.1 The observation side is real — four attacks refused

**A. Can absence of evidence pass as evidence of non-inheritance?** This was my
main hypothesis. `HEAD`'s commit message itself says commit `0533e1ea` "is
reachable from no other ref" — so a clone or CI checkout lacking `develop` cannot
see it, and if a missing object read as "not an ancestor" the branch would be
satisfied *by failing to look*. Executed:

```
$ git merge-base --is-ancestor 0533e1ea... HEAD   # in a repo without the object
fatal: Not a valid commit name 0533e1ea...
exit=128
```

and `git_commit_is_ancestor` does `require(returncode in {0, 1}, "ADR21_GIT_ANCESTRY_UNRESOLVED")`.
128 is refused, not coerced to `False`. Ran the observation against my foreign
`/tmp/fg/otherrepo`:

```
REFUSED: ContractFailure ADR21_BOUNDARY_TREE_UNRESOLVED:fatal: not a tree object
```

**This hole is genuinely closed.** It is the one that would have mattered most,
and someone thought about it.

**B. Tamper with a source document the contract pins.** Appended one newline to
`2026-07-31-walking-skeleton-definition.md`:

```
walking_skeleton_definition_digest_matches: False
outcome: UNKNOWN_BLOCKING
snapshot validation REFUSED: ADR21_LEGACY_TEST_LINEAGE_UNKNOWN_BLOCKING:UNKNOWN_BLOCKING
```

Fails **closed** to a blocking unknown, not open to the convenient branch. File
restored byte-for-byte (verified).

**C. Invent legacy provenance inside the non-inherited branch.** Added a fake
`migration_proofs` entry:

```
REFUSED: ContractFailure ADR21_INVENTED_LEGACY_PROVENANCE
```

You cannot claim to have migrated an inherited corpus in the branch that says
there is no inherited corpus.

**D. Re-assert the counts in the contract file.** Set
`boundary_committed_test_path_count` to `2444`:

```
REFUSED: ContractFailure ADR21_LINEAGE_PROJECTION
```

because the contract must equal the YAML block embedded in ADR-0021 itself, and
tampering with the ADR is refused too:

```
tampered ADR REFUSED: ContractFailure ADR21_SOURCE_DIGEST
```

Triple pinning confirmed: contract JSON → ADR YAML block digest → ADR file
digest, the last two hard-coded as constants in the validator source
(`ADR21_SOURCE_SHA256 = 1b6ca005…`, matching the file on disk).

### 3.2 But the branch condition is `facts == asserted`, not `facts == 0` — WEAKNESS (MEDIUM)

`resolve_legacy_test_lineage_outcome` compares each observed fact against the
value the **contract asserts**, not against a literal. Executed proof: I fed the
resolver facts describing a fully contaminated boundary (2444 inherited test
paths, 2444 baseline-path collisions):

```
outcome with contaminated facts, unchanged contract:              UNKNOWN_BLOCKING   <- correct
outcome after ASSERTING those same counts in the contract:        NOT_APPLICABLE_NO_INHERITED_SUBJECT
```

So the answer to the question as posed is: **the branch is satisfied by
observation-matching-assertion, and the assertion is editable.** Reality is
consulted, but reality is only ever compared to a number the repository supplies
about itself.

Likewise `inherited_baseline.source_commit_sha1` is schema-constrained only by
`pattern: ^[0-9a-f]{40}$` — any commit. I pointed it at the repository root
commit and the resolver dutifully flipped the other way:

```
--- assert a different inherited source commit ---
source_commit_is_ancestor: True -> outcome: ADR0010_APPLIES
```

Which commit counts as "the inherited baseline" is a declaration, not a
measurement.

### 3.3 Ruling

**Not satisfiable by pure assertion — a lie must be told in six places at once.**
To move the branch you must edit: the contract JSON, the schema's three `const: 0`
constraints, the YAML block inside ADR-0021, the ADR file, and *two hard-coded
SHA-256 constants inside `validate_contracts.py`* — plus regenerate the manifest
digests. Every one of those is a visible, reviewable diff, and no single-file edit
survives.

But every one of those is also **inside this repository**, checked by this
repository, against constants this repository holds. There is no external anchor.
`runtime_enactment_status: NOT_ASSESSED` and `status: ACCEPTED_PAPER_DECISION` are
carried honestly in the contract, so it does not overclaim.

**Claim 3: UPHELD with a stated limit.** The non-inheritance branch is
observation-driven and fails closed when it cannot observe. It is not
assertion-proof against an author with commit access; it is assertion-*expensive*.
That is the correct thing to say about it, and stronger than I expected going in.

---

## 4. Every deletion in the validator and the generator, ruled

`git diff --stat`:

```
scripts/architecture/generate_contracts.py |  388 +++++++++-
scripts/architecture/pyproject.toml        |   15 +-
scripts/architecture/validate_contracts.py | 1091 +++++++++++++++++++++++++++-
3 files changed, 1463 insertions(+), 31 deletions(-)
```

29 deleted lines, forming 9 logical deletions. Every one read; every one ruled.

| # | Deletion | Ruling |
|---|---|---|
| D1 | `ARCHITECTURE_PRACTICE_PROFILE_SHA256` `4eedd6e1…` → `91ef34b1…` (both files) | **Neutral** — re-pin, not removal |
| D2 | `re.search(...).group(1)` → `require_search(...)` ×2 (generator) | **STRENGTHENS** |
| D3 | generator: `or row["owner_decision_ref"] is not None` | **Mixed** — see 4.2 |
| D4 | generator: unconditional `runtime_status = "BLOCKED_OWNER_DECISION_REQUIRED"` | **Mixed** — see 4.3 |
| D5 | generator schema: `"status": {"const": "OWNER_DECISION_REQUIRED"}` | **WEAKENS** — see 4.2 |
| D6 | generator schema: `"owner_decision_ref": {"type": "null"}` | **WEAKENS** — see 4.2 |
| D7 | generator: `unresolved_owner_decision_count` pinned → derived by counting | **STRENGTHENS** |
| D8 | validator: `and row["owner_decision_ref"] is None` / `status != "OWNER_DECISION_REQUIRED"` / `or row.get("owner_decision_ref") is not None` / `!= "BLOCKED_OWNER_DECISION_REQUIRED"` | **Mixed** — see 4.2 |
| D9 | validator: the 11-line `if not tests_root.is_dir(): return {…"NOT_ASSESSED"…}` early return | **STRENGTHENS — the single best change in the diff** |

### 4.1 D9 — a fail-open path deleted. Verified by execution.

The old code: no `tests/` directory → return `validation_status: NOT_ASSESSED`,
all counts `None`, **no failure**. Delete your test tree and the test-layout
contract simply stops applying. The new code opens with
`require_production_test_root(tests_root.is_dir())`.

I renamed `tests/` away and called the function:

```
--- H: DELETED fail-open early return (tests/ missing -> NOT_ASSESSED) ---
  REFUSED: ContractFailure PRODUCTION_TEST_ROOT_MISSING:tests
  restored tests/: True
```

Unambiguous strengthening. Directory restored.

D7 is the same instinct: `unresolved_owner_decision_count` was *pinned* to
`owner_decision_count`, which was only ever right because no row could resolve.
It is now counted from row state. Derived beats pinned. The change comments say
exactly that, and the comment is true.

D2 is small and correct: `re.search(...).group(1)` crashes with
`AttributeError: NoneType` if an ADR heading is ever renamed;
`require_search` raises a message naming the pattern. Same behaviour on the
matching path.

### 4.2 D3/D5/D6/D8 — the ADR-0017 widening. Net WEAKENING, and here is the exact reason.

Before, an owner-decision row was *unresolvable by construction*: schema
`const: OWNER_DECISION_REQUIRED`, `owner_decision_ref` `type: null`, and both
generator and validator rejected any non-null reference. Twenty rows, twenty
hard blocks, no path to lift them. After, `status` accepts `ACCEPTED`,
`owner_decision_ref` accepts a `TypedArtifactRefV1`, and the null checks are
replaced by `_owner_resolution_is_coherent(row)`.

On the **unresolved** path this is strictly stronger — it now requires
`ref is None AND digest is None`, where the old code checked only `ref`. Credit
where due.

On the **resolved** path, here is what "resolved" actually means. Executed:

```
--- I: does 'resolved' require the referenced record to EXIST? ---
  _owner_resolution_is_coherent(invented ref, nonexistent file): True
  file exists on disk: False
  owner-decisions dir contents: ['README.md']
```

with

```python
{"artifact_type": "human_decision",
 "artifact_ref":  "architecture/records/owner-decisions/DOES-NOT-EXIST.json",
 "artifact_digest": "sha256:dede…de"}      # owner_decision_digest: the same string
```

The whole test is: is it a dict with exactly three keys, is `artifact_type` the
literal `"human_decision"`, is `artifact_ref` a non-empty string, and does
`artifact_digest == owner_decision_digest`. **It compares one field of the row to
another field of the same row.** Nothing is read from disk. Nothing is hashed.

Set against what `architecture/records/owner-decisions/README.md` says the
mechanism does:

> Each file validates against `schemas/authority/human-decision-v1.schema.json`
> — 22 required fields, including `principal_id`, `authentication_context_id`,
> `presentation_challenge_digest`, `nonce`, `issued_at`, `expires_at`…
> A record must be **authenticated, unrevoked, unexpired, and authorized for the
> exact role, action and scope** of the row it resolves (`OWNER-RESOLVE-003`).

```
$ rg -n "owner-decisions|human-decision-v1" scripts/architecture/validate_contracts.py
(no hits for either)
```

`OWNER-RESOLVE-003` and `OWNER-RESOLVE-006` are **not implemented**. The
docstring of `_owner_resolution_is_coherent` nevertheless cites
"OWNER-RESOLVE-002/-003" and line 2471 cites "-001/-002/-003/-007". Citing an
identifier is not implementing it. A twenty-row hard block became liftable by
typing a JSON object containing a hex string of your choosing.

Mitigation, and it is substantial: the sanctioned route runs through ADR-0013's
marked YAML, whose digest is pinned in four tracked files, so this is a visible
diff and not a quiet edit. **Ruling: WEAKENS.** Defensible as a deliberate
staged step; not defensible as "no check was relaxed."

### 4.3 D4 — the generator and the validator now disagree. Latent, fails closed.

The generator (`generate_contracts.py:7123`):

```python
runtime_status = "NOT_ASSESSED" if resolved else "BLOCKED_OWNER_DECISION_REQUIRED"
```

The validator's *independent* projection (`validate_contracts.py:2224`) was left
unconditional:

```python
runtime_status = "BLOCKED_OWNER_DECISION_REQUIRED"
```

These agree only while no row is `ACCEPTED`. Measured:

```
owner-decision rows: 20
Counter({('OWNER_DECISION_REQUIRED', 'BLOCKED_OWNER_DECISION_REQUIRED'): 20})
```

Zero resolutions. So the entire ADR-0017 mechanism is **shipped but never
exercised**, and the first genuine resolution will make the independent
projection disagree with the registry and fail the validator. That direction is
fail-*closed*, so it is a broken feature rather than an open door — but "defect
resolved" is a strong word for a path that has never been walked and would break
if it were.

### 4.4 The ADR-0017 acceptance test runs against a different repository

`scripts/architecture/test_adr17_owner_resolution.py`, line 5:

```python
sys.path.insert(0, "/home/soultransit/devtony/ranex/scripts/architecture")
from validate_contracts import _owner_resolution_is_coherent
```

Executed from *this* checkout, it prints `11 cases, 0 failed` — and:

```
$ python -c "sys.path.insert(0,'/home/soultransit/devtony/ranex/scripts/architecture'); import validate_contracts as v; print(v.__file__)"
ADR-0017 acceptance test imports: /home/soultransit/devtony/ranex/scripts/architecture/validate_contracts.py
```

It tested the **author's other working copy**, not the code in the repository it
lives in. It is also outside `testpaths = ["tests"]`, so `pytest` never collects
it, and the validator never invokes it. A green "predeclared acceptance test"
that (a) is never run by any gate and (b) when run by hand exercises a different
file on a different path is not evidence of anything about this tree.

### 4.5 Section ruling

Six of nine deletions strengthen or are neutral, and D9 removes a genuine
fail-open. Three deletions (D3/D5/D6, with D8 mirroring them) **weaken**: they
convert an unliftable block into one liftable by unverified self-declaration,
while the prose describes verification that no code performs. The claim
"no topology or lineage check was relaxed" (`2026-07-31-adr-0021-promotion-record.md:152`) is true
as written — it says lineage and topology, and those were not relaxed. The
**owner-decision** check was.

---

## 5. Breaking the new checks — all three caught, tree restored

### 5.1 The requested break: an unregistered schema

Wrote a syntactically valid, well-formed schema that no registry mentions:

```
schemas/common/final-gate-unregistered-v1.schema.json
```

Ran the full validator:

```json
{"checks": {"schema_documents": 159, "schema_registry_entries": 154,
            "undecided_array_element_types": 173},
 "error": "SCHEMA_REGISTRY_UNCLASSIFIED_DISK_PATH:schemas/common/final-gate-unregistered-v1.schema.json",
 "status": "FAIL"}
exit=1
```

**Caught.** Note the check counts drop from the ~200 emitted on a pass to three:
the validator aborts at first failure and names both the rule and the exact
path. It counted 159 documents against 154 registry entries and refused the
difference — it is comparing the disk to the registry, not trusting either.

### 5.2 Two more breaks, both caught

Unregistered test root:

```
$ mkdir tests/final_gate_probe && touch tests/final_gate_probe/test_probe.py
REFUSED: ContractFailure LEGACY_TEST_UNREGISTERED_ROOT:tests/final_gate_probe/test_probe.py
```

Test file placed directly under `tests/`:

```
$ touch tests/test_direct.py
REFUSED: ContractFailure LEGACY_TEST_DIRECT_ADDITION:tests/test_direct.py
```

These are live on the **new** ADR-0021 non-inherited branch
(`validate_noninherited_test_snapshot`), i.e. the branch that took over from the
deleted fail-open. The new branch is not a rubber stamp.

### 5.3 Tree restored, both gates green again

```
$ uv run pytest -q
36 passed in 0.23s

$ uv run --project scripts/architecture python scripts/architecture/validate_contracts.py
status: PASS
schema_documents: 158
test_layout: CANONICAL_TOPOLOGY_PASS NOT_APPLICABLE_NO_INHERITED_SUBJECT
exit=0
```

`git status --short` shows 48 entries: the 47 present on arrival, plus this
report. Nothing else added, nothing removed. Every
probe file removed, every tampered file byte-restored (ADR-0021, the
walking-skeleton definition and `tests/` were each verified by digest or by
`is_dir()` after restore).

---

# VERDICT

Five checks run, all by execution. Scope held; no corpus audit attempted.

| # | Check | Ruling |
|---|---|---|
| 1 | Five CLI verdicts | **UPHELD** — all five reproduce exactly, exit `1/1/1/1/0` |
| 1b | Subject binding at the CLI boundary | **REFUTED — HIGH.** Omit the field and any evidence passes against any ref |
| 2 | Repository confinement | **REFUTED — HIGH.** `resolve_within_repository` has zero callers in `src/` |
| 3 | ADR-0021 non-inheritance by assertion | **UPHELD with a limit** — observation-driven, fails closed, but thresholds are self-asserted |
| 4 | Every deletion | **6 of 9 strengthen or neutral; 3 weaken** — one genuine fail-open removed, one hard block loosened |
| 5 | Unregistered schema | **CAUGHT**, plus two further breaks caught |

## What is true

The deterministic core is real and I could not talk it out of a verdict.
`verdict.py` demands an exact claim, an exact subject and `exit_code == 0`;
absence blocks; self-approval is refused before evidence is even weighed, which
is the right order. The five demonstrations are not staged — the committed
evidence is genuinely bound to `HEAD`'s tree, verified by recomputing the digest
independently. Deleting the `tests/` fail-open (D9) is a real removal of a real
hole. `git_commit_is_ancestor` refusing exit 128 closes the attack I most
expected to land: absence of a git object cannot masquerade as absence of
inheritance. Three deliberate breaks were caught, each naming the rule and the
exact path.

## What is not

**Two claimed enforcement boundaries are not installed at the edge.**

The CLI parses evidence with `item.get("subject_digest", subject_digest)`. A
two-line JSON file with no subject field and a command that never ran passes the
gate against *any* ref. The domain layer is correct; the adapter discards the
check before the domain sees it. One line fixes it.

`resolve_within_repository` is a well-written function with six passing tests
and **no caller in production code**. `ranex.cli.main` performed every one of the
three acts `SLICE-LANE-007` declares forbidden — absolute path, foreign
repository, write outside the root — in a single invocation, loaded its
governing policy from an attacker-controlled file, and exited 0. The RFC
anticipated this precise failure ("a behavioural contract with a sad-path test,
not a statement of intent") and the implementation is the thing it warned
against. Passing tests around an uncalled function are not enforcement; they are
a boundary certified in a file that is never opened.

**One check was relaxed, and the prose around it describes verification that no
code performs.** ADR-0017 turned an unliftable twenty-row block into one liftable
by a self-declared reference. "Resolved" is decided by comparing one field of a
row to another field of the same row — no file read, no hash, no expiry, no
principal. `OWNER-RESOLVE-003` and `-006` are cited in comments and implemented
nowhere; `rg` finds no reference to `owner-decisions` or `human-decision-v1` in
the validator. The mechanism has also never been exercised (0 of 20 rows
resolved) and the generator and validator disagree about `runtime_validation_status`
for a resolved row, so the first real resolution will fail the validator. Its
predeclared acceptance test hard-codes an absolute path and, when run here,
tested a **different checkout** and reported green.

## Ruling

**The gate itself: SOUND. Its perimeter: NOT SEALED.**

Nothing here is fabricated and nothing is fraudulent — the honest thing to
record is that `MASTER_ARCHITECTURE_SPECIFICATION.md` marks the CLI
`CONFIRMED advisory only`, does not list `confinement.py` among components with
executed evidence, and keeps `runtime_enactment_status: NOT_ASSESSED` throughout.
The master spec does not overclaim. RFC-0010, the slice plan, and the
ADR-0017/ADR-0021 promotion notes do.

The gap is uniform and diagnosable: **the domain is disciplined and the edges are
not.** Every defect found sits in an adapter, an entry point, or a coherence
predicate that checks shape instead of substance. That is a fixable class of
problem, and three of the four fixes are small:

1. `main.py:53` → `item["subject_digest"]`. One line.
2. Route `--repository`, `--evidence`, `--gate-catalog`, `--journal` through
   `resolve_within_repository`, and add a test that invokes **the CLI**, not the
   library.
3. Either implement `OWNER-RESOLVE-003`/`-006` against
   `architecture/records/owner-decisions/`, or amend the README so it stops
   describing authentication that does not exist.
4. Make `validate_contracts.py:2224` conditional to match the generator, and
   move `test_adr17_owner_resolution.py` into `tests/` with a relative import.

Until 1 and 2 land, the sentence "the gate refuses a change when required
evidence is missing" is true, and the sentence "and it can only be satisfied by
evidence that was actually produced for this repository and this subject" is not.

**Not a pass. Not a fraud. A skeleton with two unsealed joints, both cheap to
weld.**
