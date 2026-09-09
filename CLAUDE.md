# Ranex

Deterministic governance for AI agents that build software. `AGENTS.md`
carries conduct; this file carries orientation.

## Read first, every session
1. `docs/STATE.md` — where we stopped, what is next.
2. The active slice named there, in `docs/slices/` (if any).
3. `docs/MAP.md` — only when the question is *why*.

## Commands

```
uv run --frozen pytest -q          # full suite — green before push
uv run --frozen ranex --help       # CLI surface
uv sync --frozen                   # ranex editable + the `ranex` console script
```

Always `--frozen`: plain `uv run` re-locks and rewrites `uv.lock`, a trust
root. Deliberate re-locks and builds pass
`--exclude-newer 2026-08-04T00:00:00Z` — a bare `uv lock` silently strips the
epoch from the lock's `[options]`, which `tests/contract/test_packaging.py`
refuses. `governance/deps.yaml` pins the same epoch for `ranex deps fetch`,
which refuses a lock its pinned inputs cannot reproduce. Governed subcommands
anchor to the checkout holding the CLI, never the caller's cwd (ADR-038);
`--external-repository` names another one explicitly (ADR-052).

## Invariants — breaking one is a bug
`evaluate()` is pure; no model decides a verdict. Absence blocks. Evidence is
digest-bound to its subject. No self-approval. A gate that cannot block is
refused at construction. The journal is append-only and hash-chained. Removing
every model credential must not change a verdict.

`src/ranex/governed_execution/domain/verdict.py` is digest-pinned by
`tests/contract/test_kernel_unchanged.py`. Moving it is a deliberate act that
sets `KERNEL_DIGEST` to the new bytes in the same commit.

## Docs discipline — enforced by tests/contract/test_docs_discipline.py

The only documents that may exist:

| Path | Purpose |
|---|---|
| `CLAUDE.md`, `AGENTS.md` | orientation + conduct |
| `README.md` | public overview and status |
| `docs/MAP.md` | the map |
| `docs/OPERATIONS.md` | operator recipes |
| `docs/STATE.md` | where we stopped (≤50 lines, rewritten) |
| `docs/adr/ADR-NNN-*.md` | optional design notes (append-only) |
| `docs/adr/prior-art/ADR-NNN/` | sources an ADR vouches for (closed set) |
| `docs/slices/SLICE-NNN-*.md` | the one open slice |
| `docs/slices/done/` | finished slices (archived) |
| `.claude/skills/idea-refine/SKILL.md` | the one skill (closed set) |
| `.claude/skills/LICENSE-agent-skills.txt` | upstream MIT notice |
| `tools/dogfood/*.md` | closed set: `README`, `FINDINGS`, `AUTOFIX`, `site/INTEGRATION`, `oss_bench/README` |

Do not create any other document. Future-session knowledge → STATE.md; current
work → the slice file; change reasoning → the commit message; everything else
→ chat.

Slices carry `**Status:** open | blocked | done`, and at most one is `open`
(`blocked` does not consume the slot). ADRs are optional; each carries one
`**Status:**` line (proposed | accepted | rejected | deprecated | superseded by
ADR-NNN), stays ≤300 lines, and ships no placeholder. Vendored prior art is
claimed by its ADR (`Vendored: docs/adr/prior-art/… blob:<40-hex>`) and carries
a NOTICE naming licence and origin. Do not edit historical ADRs or
`docs/adr/prior-art/`. README's "Completed slices" must match
`docs/slices/done/` exactly, and README and STATE.md must name the same active
slice.

## Repo shape
`src/ranex/{foundation, governed_execution, policy, cli, execution,
provisioning, observability, specification_generation, github_app, bootstrap}`;
`native/ranex-worker-launcher`; `governance/` catalogs, schemas and suite
manifest (`evidence.json` and `journal.sqlite3` gitignored);
`tests/{contract, e2e, integration, security, unit}`; `docs/`; `tools/dogfood/`
— the training, audit and benchmark loop.
