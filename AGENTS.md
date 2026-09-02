# Ranex — agent conduct

Standing owner rules (2026-09-03), every agent, every harness. Loop: pick
an issue, make it green, leave one comment, push.

## GitHub identity
Operate as `anthonykewl20` on GitHub. Before any `gh` operation or
`git push`, the gh active account must be `anthonykewl20`; if it is not,
run `gh auth switch -h github.com -u anthonykewl20` and proceed.

## One issue, one pass
- Work one issue at a time to completion. Add the `in-progress` label
  when you start; remove it when you stop.
- Do not post progress or status comments.
- After 3 failed fix attempts: remove the label, post ONE comment naming
  the blocker and what you tried, move to the next issue.

## Done means — all four, then stop
1. `uv run --frozen pytest -q` green on the final commit. Always
   `--frozen`.
2. Rewrite `docs/STATE.md` (≤50 lines; active-slice line current). Slice
   work: move the slice file to `docs/slices/done/` and add it to
   README "Completed slices" in the same change. Edit README otherwise
   only when public status changed.
3. Post ONE closing issue comment: commit SHA + one line of evidence
   (command and result). Report anything not verified as UNVERIFIED,
   never PASS.
4. Push fast-forward only; verify the remote tip is your commit. Leave
   the working tree clean.

## Code discipline
- Verify every API, flag, version, and runtime behavior against the
  installed artifact or version-matched docs before writing it.
- Do not ship stubs or placeholders as finished work.
- Do not hand-roll what the repo provides (canonical JSON, digests,
  signing, confinement, journal) or what a mature, pinned,
  licence-compatible upstream provides.
- Never fabricate commands, results, SHAs, URLs, or citations.
