"""Corpus-driven trainer: ranex exercised like an athlete, not quizzed.

The scenario curriculum (dogfood.py) is an exam: 33 fixed behavioural points.
The trainer is the complementary regime: it generates labelled exercises from
a CORPUS of real tasks (VulcanBench suites on disk), runs each through the
real governed cycle (`ranex run` -> signed evidence -> `gate evaluate` ->
`journal verify`), and checks the verdict against a label derived from the
task's own ground truth — no model, no network, no hand-typed expectations:

  gold            apply the task's gold_patch       -> gate MUST PASS
  empty           apply nothing                     -> gate MUST FAIL
  delete-tests    gold + test functions deleted     -> gate MUST FAIL naming
                                                      the missing test IDs
  goalpost-move   gold evidence, then the tree moves under it
                                                  -> gate MUST FAIL calling
                                                      the evidence stale
  partial-gold    only part of gold_patch           -> gate MUST FAIL

Every exercise records the input-space classes it touched (the taxonomy from
AUDIT-2026-09-03), so `coverage` answers "which of ranex's judgement paths
has the corpus actually trained" — and a disagreement between label and
verdict is a FINDING, not noise.

Determinism: passes are canonical JSON, sorted iteration, no clocks; the
pass chain links each pass to the previous pass's digest.
"""
