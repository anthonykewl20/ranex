# Ranex

Deterministic governance for AI agents that build software. `AGENTS.md`
carries conduct; this file carries orientation.

## Read first, every session
1. `docs/STATE.md` — where we stopped, what is next.
2. The active slice named there, in `docs/slices/` (if any).
3. `docs/MAP.md` — only when the question is *why*.

## Process

Pick an issue → change code with tests → docs touch → one closing issue
comment → fast-forward push. (`AGENTS.md` defines each step.)

- Write new tests red; make them green; keep the full suite green on the
  final commit.
- ADRs are optional: `docs/adr/ADR-NNN-short-name.md`, free-form, ≤300
  lines, one `**Status:**` line (proposed|accepted|rejected|deprecated|
  superseded by ADR-NNN). Do not edit historical ADRs or
  `docs/adr/prior-art/` (closed set).
- Lanes: one mutation writer per repo at a time; every delegated agent
  gets its own worktree. `../ranex-harness` is a separate lane, never a
  kernel release claim.
- Delegating to an outside model: OpenRouter MCP
  (`mcp__openrouter__send-message`), concrete model slug, inline every
  fact, set `timeout_ms`; score against tests, never the model's report.
  The opencode CLI free tier stalls after ~2 calls.

## Commands

```
uv run --frozen pytest -q          # full suite — green before push
uv run --frozen ranex --help       # CLI surface
```

Always `--frozen`: plain `uv run` re-locks and rewrites `uv.lock`, a
trust root. Deliberate re-locks/builds pass
`--exclude-newer 2026-08-04T00:00:00Z` — bare `uv lock` silently strips
the epoch (contract-tested). `uv sync --frozen` builds ranex editable
and the `ranex` console script; governed subcommands anchor to their
checkout (ADR-009).

## Docs discipline — enforced by tests/contract/test_docs_discipline.py

The only documents that may exist:

| Path | Purpose |
|---|---|
| `CLAUDE.md`, `AGENTS.md` | orientation + conduct |
| `README.md` | public overview and status |
| `docs/MAP.md` | the map |
| `docs/STATE.md` | where we stopped (≤50 lines, rewritten) |
| `docs/adr/ADR-NNN-*.md` | optional design notes (append-only) |
| `docs/adr/prior-art/ADR-NNN/` | historical vendored sources (closed) |
| `docs/slices/SLICE-NNN-*.md` | the one open slice (at most one open) |
| `docs/slices/done/` | finished slices (archived) |
| `.claude/skills/<name>/SKILL.md` | `idea-refine` only (closed set) |
| `.claude/skills/LICENSE-agent-skills.txt` | upstream MIT notice |
| `tools/dogfood/*.md` | the dogfood loop's interface docs (closed set: README, FINDINGS, AUTOFIX, site/INTEGRATION) |

Do not create any other document. Future-session knowledge → STATE.md;
current work → the slice file; change reasoning → the commit message;
everything else → chat.

## Invariants — breaking one is a bug
`evaluate()` is pure; no model decides a verdict. Absence blocks.
Evidence is digest-bound to its subject. No self-approval. A gate that
cannot block is refused at construction. The journal is append-only and
hash-chained. Removing every model credential must not change a verdict.

## Repo shape
`src/ranex/{foundation, governed_execution, provisioning, policy, cli,
bootstrap}`; `native/` launcher; `governance/` catalogs + suite manifest
(`evidence.json`/`journal.sqlite3` gitignored); `tests/{contract, e2e,
integration, security, unit}`; `docs/`; `.claude/skills/`.
