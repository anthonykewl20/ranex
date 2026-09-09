# Ranex — agent conduct

Standing owner rules, every agent, every harness. `CLAUDE.md` carries
orientation; this file carries conduct. Loop: pick an issue, make it green,
leave one comment, push.

## Lanes — check before you write
One mutation writer per repository at a time. Before your first write, commit,
push, or full-suite run:

- `git status -sb` — commits ahead of `origin` mean another session owns this
  lane and has not finished;
- `pgrep -af pytest` — a running suite means one is mid-verification.

If either shows another writer, stay read-only until it clears. Never start a
second full suite on this host while one is running: concurrent suites have
exhausted its memory and been OOM-killed.

Delegated agents work in their own `git worktree`, never the main checkout.
`../ranex-*` siblings are separate lanes and never a kernel release claim.
`ranex run` refuses a dirty tree, so leave the working tree clean.

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
