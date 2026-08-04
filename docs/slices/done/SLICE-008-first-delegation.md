# SLICE-008 — first delegation

**Status:** done
**Opened:** 2026-08-04
**Closed:** 2026-08-05 — suite 624 green (2 loud skips: credential-gated e2e,
bind-mount), diff-cover 100% on the change, mutmut complete (5589 mutants,
3460 killed; delegation/fanout survivors are the documented subprocess-test
blindness, their proof lives in the excluded live security tests). Criterion 7
ran against `openrouter/cohere/north-mini-code:free`; criterion 11 rebranded
the fork's operator surface (`bin/ranex`, wordmark, help), LICENSE untouched.
**ADR:** `docs/adr/ADR-010-first-delegation.md` — accepted 2026-08-04, including
the fan-out decision taken before it was frozen.
**Closes:** ADR-010's confirmation, ADR-008's open "trusted dispatcher path",
and `MAP §17.5`'s foreman-dispatches proof. Delegated evidence closes the
delegated path of `RISK-06`; the risk itself stays open for `ranex run`.

## The defect

There is no front door. A person cannot hand Ranex a task and get a judged
result: today a human is the wire between `task dispatch`, the harness, the
emission file, and `task judge`. The gear-mesh e2e that proved the parts turn
used a model that does no work and **hand-wrote its own evidence**, so nothing
yet demonstrates the kernel judging work an agent actually produced.

Worse, the obvious build is unsafe. `main.py:1368` reads the signing key into
kernel memory before the bound command spawns, and `RISK-06` reproduces that
command taking it from `/proc/<pid>/environ`. Under delegation the executed
suite is code an AI wrote minutes earlier, so a planted `conftest.py` could
sign anything while every invariant still looked intact.

## Design

Per ADR-010, with execution and attestation in different process lifetimes.

1. **Delegate.** `ranex task delegate` dispatches a worktree (existing
   `task dispatch`), then spawns the harness headless from an environment built
   from empty: pinned `PATH`, scratch `HOME` outside the worktree, the two
   bridge variables, exactly one model-credential variable, an auto-approve
   flag, and a wall-clock bound. It **refuses to start when the signing-key
   variable is present**.
2. **Cross-check.** The kernel parses the emission and matches worktree and
   commit against its own dispatch record. Absence and mismatch both block.
3. **Measure.** The kernel runs the frozen suite against the emitted commit,
   materialised per ADR-009, sealed and offline, holding no key.
4. **Attest.** A separate later invocation signs the result. No untrusted code
   is running at that time.
5. **Judge.** `task judge` journals a CANDIDATE with its missing claims. Never
   a PASS; the stamp stays a human's, out of band.
6. **Fan out.** A bounded pool runs many delegations at once, one worktree
   each. The journal's `BEGIN IMMEDIATE` serialises appends; the store is
   already concurrent-writer safe.
7. **Rebrand.** The harness presents as `ranex` / Ranex, not opencode.

## Done criteria

Each criterion is met only when a test proves it. New coverage belongs in
`tests/unit/test_delegation.py`,
`tests/security/test_slice008_execute_attest_separation.py`, and
`tests/e2e/test_first_delegation.py`.

1. **The execute phase refuses to hold a key.** With the signing-key variable
   present in its environment, `delegate` refuses before spawning anything.
   (ADR-010 s.p. 1)
2. **No key is reachable from the execute process tree.** Proven through
   `/proc` against the live process, not by reading the source. The delegated
   command cannot reach the key by environ, by file path, or by parent.
3. **A planted hook cannot obtain a signature.** A `conftest.py` committed into
   the delegated worktree runs, may fail the suite, and demonstrably produces
   no signed record. (s.p. 9)
4. **The emission is cross-checked.** A forged worktree or commit blocks before
   materialisation; a missing emission blocks as absence. (s.p. 3, 4)
5. **An empty delegation is refused.** `commit == base` is not a subject and is
   refused rather than judged. (s.p. 5, 8)
6. **The run terminates on its own.** Process exit bounds the normal case; the
   wall-clock bound terminates a stall, records the timeout, and journals no
   candidate. (s.p. 2, 6)
7. **A real model produces a real verdict.** One delegated run against a real
   provider ends in a journalled CANDIDATE naming its missing claims, with no
   PASS anywhere, and the diff is reviewable. Skips loudly by name when the
   operator's credential is absent.
8. **N concurrent delegations yield N independent verdicts**, and the journal
   still verifies afterwards — the check that catches a forked chain.
   (s.p. 15)
9. **The pool is bounded.** Fan-out beyond the bound queues rather than
   starving the machine, and no honest work is failed by breadth alone.
   (s.p. 17)
10. **One dispatch, one judgement.** A second `delegate` for a live task id
    refuses, and two concurrent tasks cannot share a worktree path.
    (s.p. 11, 16)
11. **The harness is Ranex.** The operator-facing command is `ranex`, the
    product names itself Ranex in what it prints, and opencode's MIT
    attribution is retained in the tree. Scope is operator-visible surfaces,
    not a wholesale internal identifier rewrite.
12. Every refusal added by this slice is reached by a test, `diff-cover` stays
    100% on the change, and the full suite stays green.

## The controls most likely to become decoration

First: **criterion 2 proving the wrong thing.** Reading the source to confirm
the key is absent proves only that someone intended it. The test must inspect
the live process tree — the environ of the spawned child *and* of its parent —
because `os.environ.pop()` does not alter `/proc/self/environ`, measured here
on 2026-08-04. A test that asserts over a dict it constructed proves nothing.

Second: **a delegation that passes because nothing ran.** Criterion 7 must
assert the suite collected and the diff is non-empty, not merely that no false
PASS appeared. The gear-mesh e2e already made this mistake once with a model
that does no work.

Third: **fan-out proven with one task.** Criterion 8 must run enough
concurrent delegations to actually interleave journal appends. Two sequential
runs dressed as a pool would pass a weaker test and prove nothing about the
chain.

Fourth: **the rebrand measured by grep.** Counting `opencode` strings is not
the criterion; what the operator sees is. The test drives the command a person
would type and reads what it prints.

## What this slice does not close

- **Egress confinement.** The model credential sits in the harness environment
  with the network open; the loop can post it anywhere. Use a scoped,
  spend-limited key. Stated, not mitigated. (s.p. 13)
- **`RISK-06` generally.** This closes the delegated path. `ranex run` as
  invoked today still reads the key before spawning.
- **Merge.** Nothing lands. Concurrent tasks may edit the same file; that
  collision is merge's problem, and merge is a later slice with the merge-time
  digest re-check ADR-010 names. (s.p. 18)
- **Verifiable separation.** SLSA's signatures carry an identity that makes a
  violated separation *detectable*. Ranex's do not yet. A later slice earns it.
- **Gate quality.** A loop writing plausible code that satisfies a weak gate is
  not caught, and cannot be. That burden is the operator's (`PR-06`). (s.p. 14)
