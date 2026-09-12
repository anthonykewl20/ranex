# Ranex — agent conduct

Standing owner rules, every agent, every harness. `CLAUDE.md` carries
orientation; this file carries conduct. Loop: pick an issue, make it green,
leave one comment, push.

## Parallel work — owner policy, 2026-09-12
Parallel implementation and overlapping verification are authorized. The owner
revoked the previous single-writer/read-only and no-overlapping-suite rules.
A running suite or commits ahead of origin do not block independent work.

Use separate Git worktrees and branches for concurrent writers, and pinned
isolated worktrees for verification. Coordinate edits to the same files; do
not overwrite another session's changes. Check status before commits and push
fast-forward only. `ranex run` still requires a clean candidate tree.

The host lane helper admits two concurrent verification runs by default and
checks available memory. Resource exhaustion is an execution failure, never
PASS. Do not stop another session's process without authorization.

## GitHub identity
Operate as `anthonykewl20`. Before any `gh` operation or `git push`, if the
active account is not `anthonykewl20`, run
`gh auth switch -h github.com -u anthonykewl20` and proceed.

## One issue, one pass
- Work one issue at a time to completion. Add the `in-progress` label when you
  start; remove it before ending a session unless the issue closed in it.
- Do not post progress or status comments.
- After 3 failed fix attempts: remove the label, post ONE comment naming the
  blocker and what you tried, then move to the next issue.

## Done means — all four, then stop
1. `uv run --frozen pytest -q` green on the final commit.
2. Rewrite `docs/STATE.md` (≤50 lines, active-slice line current). When a slice
   closes, move its file to `docs/slices/done/` and update README's "Completed
   slices" in the same change. Edit README only for that, or when a shipped
   command, flag, or default changes.
3. Post ONE closing issue comment: commit SHA plus one line of evidence — the
   command and its result. Anything not verified is UNVERIFIED, never PASS.
4. Push fast-forward only, and verify the remote tip is your commit.

## Code discipline
- Write new tests red, make them green, and keep the full suite green on the
  final commit.
- Adding or removing a test changes `governance/suite_manifest.json`: refreeze
  it on the committed tree, and load the result with `load_manifest` **before**
  committing it. The freeze runs the whole suite, so a malformed manifest costs
  an hour to discover and three seconds to catch.
- Verify every API, flag, version and runtime behaviour against the installed
  artifact or version-matched docs before writing it.
- Do not ship stubs or placeholders as finished work.
- Do not hand-roll what the repo already provides (canonical JSON, digests,
  signing, confinement, journal), and do not reinvent what a mature, pinned,
  licence-compatible upstream provides — copy it in with its notice. Never grow
  the runtime dependency graph.
- Delegating to an outside model: name a concrete model, inline every fact it
  needs, set a timeout, and score the result against the tests — never against
  the model's own report.
- Never fabricate commands, results, SHAs, URLs, or citations.
