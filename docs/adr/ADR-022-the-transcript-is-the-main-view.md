# ADR-022 — the transcript is the main view, the board is an opened extension

**Status:** proposed
**Date:** 2026-08-11
**Decision-makers:** repo owner
**Slice:** `n/a — separate UI track; CHAT-01..CHAT-20 are harness work packages, not slices. No package touches the kernel, so none needs a slice`

## Context and Problem Statement

ADR-018 chose the board as the front door and demoted the transcript to a pane.
Ten days later the board is built and **renders nothing**: its every field reads
`no channel reaches the kernel; the bridge emits and nothing returns`
(`packages/tui/src/feature-plugins/board/actions.ts:109` in the harness). ADR-019
is unbuilt and BOARD-01 is open, so the front door is a surface with no data
behind it while the only working screen sits behind a keypress.

That working screen is stock opencode. `routes/session/` diverges from fork base
`012c2f57` by **13 insertions across 7 files**, all rebrand — a 2710-line
component with one plugin slot. The operator therefore meets either an empty
governance table or another vendor's chat.

This decides which surface opens, and how the transcript may be redesigned
without ending the fork's ability to merge upstream.

## Decision Drivers

- A front door that cannot render its own subject is worse than no front door.
- The transcript is the surface an operator uses continuously; the board is
  consulted at decision points.
- Divergence from upstream is the fork's real recurring cost (ADR-018).
- ADR-018's non-front-door decisions are sound and must survive intact.
- The board must remain reachable and unchanged, not deleted.
- No enforcement may move into the harness; it collects, the kernel judges.

## Prior art

Searched: GitHub issue search (`gh search issues`) across `anthropics/claude-code`,
`anomalyco/opencode`, `google-gemini/gemini-cli`, `charmbracelet/crush` and
`Kilo-Org/kilocode` for transcript rendering, tool output, reasoning display,
streaming, scroll, composer, copy and accessibility; then GitHub code search for
terminal markdown and code-block renderers. Release tags were resolved to
commits and root licences read before any file was copied. Upstream churn was
measured by fetching `upstream/dev`, not recalled.

- [cliui table](https://github.com/poppinss/cliui/blob/319531c0be1946072e7da29ea45f4514939aff06/src/table.ts)
  carries a `raw` render branch that emits pipe-joined cell values with no
  border, padding or colour, and sizes fluid columns by measuring with
  `string-width` rather than `.length`.
  License: MIT.
  Weakness: it is a write-and-forget line printer — `render()` logs and the
  frame is gone. There is no retained scene, no focus and no keybinding, so it
  can supply an output vocabulary and can never back the interactive surface.
  Vendored: docs/adr/prior-art/ADR-022/cliui-table.ts blob:a312cc77c588b5bcf266f97ed3093863cc956615
- [glamour code block](https://github.com/charmbracelet/glamour/blob/05ee9b5f4dcf3e4426c4ba41e1f9d7ea4f34d603/ansi/codeblock.go)
  is the mature terminal markdown code-block renderer: it maps document style
  primitives onto Chroma token entries and degrades to unstyled text when the
  colour profile is ASCII.
  License: MIT.
  Weakness: read at line 86, `theme` is **overwritten** with a globally
  registered style named `charm` whenever a Chroma rule set exists, and the
  formatter defaults to `terminal256` — so the document's own palette does not
  reach the highlighter and colour depth is capped below true colour. That is
  precisely the pair of defects filed against the design target as a theme
  picker that reaches only code blocks, and highlighting that uses basic ANSI.
  Registering into a package-global registry from inside a render call is also a
  side effect this design cannot take.
  Vendored: docs/adr/prior-art/ADR-022/glamour-codeblock.go blob:90976e5696513a4cd62d6a000ce77ceea19443b3

Upstream churn, measured 2026-08-11: fork base `012c2f57` (`v1.18.11`,
2026-08-01) to `upstream/dev` moved `routes/session/` by +30/−13 across 3 files
in ten days, and all of `packages/tui` by +146/−26 across 15.

Rejected: [Ink](https://github.com/vadimdemedes/ink) is the mature React-for-CLI
runtime and the closest match to a component-shaped transcript, but the harness
renders through OpenTUI and SolidJS; adopting it means a second runtime in one
process for no governance gain.

Rejected: [cli-table3](https://github.com/cli-table/cli-table3) is what cliui
itself wraps and would give tables directly, but it owns its own border and
colour vocabulary, which would put a second palette beside the generated theme —
the exact failure recorded against glamour above.

## Considered Options

1. **Keep ADR-018 unchanged**, wait for ADR-019 to fill the board. Rejected: it
   leaves an empty screen as the front door for an unbounded period.
2. **Transcript as the main view, board reached deliberately; the Ranex
   transcript is a new route and upstream's is left stock.** Chosen.
3. **Carve plugin slots into `routes/session` and render through them.**
   Rejected: it edits the one file upstream churns, for a seam that constrains
   the design to upstream's component shape.
4. **Rewrite `routes/session` in place.** Rejected: 2710 lines of permanent
   merge surface, and it deletes the two-way door ADR-018 bought.
5. **Merge board and transcript into one screen.** Rejected: two reads of one
   state is how the target's own status line came to contradict itself.

## Decision Outcome

In the context of an operator opening the harness, facing a board with no read
channel and a transcript that is another vendor's product, we chose **the
transcript as the main view, built as a new route under `feature-plugins/` with
upstream's `routes/session/` left stock and unreached**, to give the operator a
working and Ranex-native first screen, accepting that a second transcript
implementation exists until upstream's is deleted.

The board is unchanged and becomes an extension opened by keybinding — the same
status as the sidebar. ADR-018 is superseded **only** in its front-door clause;
its additive-only rule, its cause-as-structure rule, the contrast gate and the
verdict presentation contract all stand.

Door: two-way

### Consequences

- Good: the first screen renders real work rather than `no channel`.
- Good: upstream's session route is untouched, so `packages/tui` mergeability is
  preserved exactly as ADR-018 required — the rule is honoured by not needing it.
- Good: the transcript redesign is unconstrained by upstream's component shape.
- Good: the board keeps every property it was built with; nothing is rewritten.
- Bad: two transcript implementations coexist until upstream's is deleted, and
  the dead one can rot unnoticed.
- Bad: behaviour currently inside `routes/session` — permission prompts, the
  question flow, subagents, timeline and fork dialogs — must be reached from the
  new route or it regresses.
- Neutral: this does not close BOARD-01 or ADR-019. The board stays empty until
  the read channel lands; it is simply no longer the first thing seen.

### Confirmation

`tests/contract/test_docs_discipline.py` binds this document's form and its
citations. On the harness side, frozen before build:

- A routing test asserts a fresh start resolves to the transcript route, and
  that no fallback path lands on the retired opencode landing.
- A registry test asserts every entry kind is reachable and that entry order
  derives from each entry's own field, not array position.
- A presentation test asserts styled and unstyled renders of one transcript have
  byte-identical text content and differ only in styling attributes.
- `tests/contract/test_verdict_presentation.py` continues to hold the verdict
  channel unchanged, proving this decision moved no verdict rendering.

## Improvements on the prior art

1. **Collapsed by default, and the collapsed line carries the outcome.** The
   target collapses to a name; a reader then expands to learn what happened. The
   outcome column means the common case needs no expansion at all.
2. **Identity above content, not beside it.** Issue 75221 asks for an option to
   strip the left gutter. Removing the gutter entirely removes the option, the
   setting, and the class of defect.
3. **One projection per number.** The target's status line disagrees with the
   command reporting the same figure. Here every appearance of a count reads one
   projection, which is ADR-018's own recorded hazard answered in advance.
4. **The contrast gate already covers diffs.** Two open issues on the target
   concern unreadable diff text. `visual-identity.md` computes WCAG 2.1 for every
   emitted pair and writes nothing on a breach, so that defect fails the build.
5. **`raw` is an output, not a debug flag.** cliui's raw branch becomes the
   supported path for pipes, logs and screen readers, rather than a fallback
   nobody maintains.
6. **Reasoning labelled by content.** Upstream labels it with a duration, which
   cannot tell a reader whether to open it. The first clause can.
7. **No content sniffing.** The target and upstream both carry filed issues in
   both directions on inferring maths from a dollar sign; a fixed grammar has
   none.

## Architecture surface

Added: a transcript route in `@ranex/tui` under `feature-plugins/transcript/`,
plus an entry registry, reading durable state through the existing SDK and event
path. No second event system, no new port.

Changed: the route default and the home-navigation redirect in
`packages/tui/src/context/route.tsx`.

Unchanged: `routes/session/`, the board and all its panes, the sidebar slots,
the theme generator, and the kernel. No adapter is touched; this is presentation
only.

## Scope and threat delta

STRIDE: **none moved.** The transcript issues no verdict, holds no key, writes
no journal entry and reaches no approval path — identical to the board's
posture under ADR-018. A permission request is rendered by the harness and
decided by the existing permission path, which this does not modify.

Non-goals: localisation, mouse-only affordances, and any owner-facing
translation. Out of scope: an operator who edits durable state to change what
the transcript shows — the record is the kernel's to defend, not the renderer's.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Maintainability | upstream releases a session-route change | zero conflicts in Ranex-owned files |
| Usability | operator reads a tool result without expanding it | outcome present on the collapsed line |
| Functional correctness | styled and unstyled renders compared | text content byte-identical |
| Accessibility | colour or glyph removed | every state still spelled |

## Reversibility

Door: two-way

The transcript is additive — a route, a registry, and two lines of routing
default. Deleting `feature-plugins/transcript/` and restoring those two lines
returns the harness to ADR-018's behaviour, because upstream's session route was
never modified and the board was never changed. Nothing durable is written, so
there is no migration and no record to unwind.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 1 | transcript route fails to register | fall back to upstream's session route and say so; never a blank screen |
| 2 | an entry kind arrives that no module handles | render the raw payload labelled `unrendered`, never drop it |
| 3 | two entries registered at the same order | fail at construction, not by silently reordering |
| 4 | a stream chunk is delivered twice | append is idempotent on chunk id; no duplicated tail |
| 5 | terminal resized mid-stream | full redraw, never a diff against a stale layout |
| 6 | `NO_COLOR` set or stdout is a pipe | styling drops, content byte-identical |
| 7 | terminal lacks the Unicode range | ASCII glyphs; no state was carried by a glyph, so nothing is lost |
| 8 | permission request cannot be rendered | spelled error state, never an indefinite spinner |
| 9 | reader scrolls up while output streams | autoscroll releases and does not reclaim itself |
| 10 | draft or queued input present at navigation | preserved and shown as queued, never silently dropped |
| 11 | a keybind is displayed but not dispatchable | fail the keymap test; a shown binding must dispatch |
| 12 | markdown is malformed or fences are nested | render as literal text; never crash and never guess |
| 13 | upstream renames a file the transcript imports | compile error in Ranex-owned files, not a silent merge |
| 14 | the board has no read channel | the board says so; the transcript never invents a verdict |
| 15 | operator believes the transcript shows admissibility | **not caught** — the board is the only verdict surface; review's job |

## Test strategy

Frozen before build, red then green, reviewed against the diff on disk rather
than an implementer's summary.

Repository contract level, in this repo:

- `tests/contract/test_docs_discipline.py` — this ADR's form, citations, sad
  path count and door line. The check that fails if the document drifts.
- `tests/contract/test_verdict_presentation.py` — unchanged, and required to
  stay green. It is the evidence that this decision moved no verdict rendering
  into the transcript.
- `tests/contract/test_kernel_unchanged.py` — the kernel is untouched by a
  presentation decision, asserted rather than asserted-by-assumption.

Harness level, in `packages/tui/test/` of the harness repository, named here so
the packages carry them: a routing test for the front door and every fallback
path; a registry test for entry reachability and order-from-field; a styled
versus unstyled snapshot pair asserting equal text content; a keymap test
asserting every displayed binding dispatches; a streaming test asserting
idempotent append and full redraw on resize; a composer test asserting bounded
per-keystroke cost against a long draft.

Levels: contract for the record and the kernel invariant, component for the
renderers, no end-to-end — there is no runtime path this decision introduces.

Coverage: no global percentage. Sad paths 1 to 14 each map to a named test in
the packages above; sad path 15 is declared uncatchable, because a reader's
belief about what a screen means is not a testable property of the screen.

## Code review checklist

- Read the diff on disk. The implementer's summary is discarded.
- Is `routes/session/` genuinely untouched, imports included?
- Does any collapsed entry hide its outcome, rather than only its detail?
- Is any state carried by colour or a glyph alone anywhere in the new route?
- Does any number appear that was read separately from its sibling display?
- Does a message body carry a decorative left margin that would be copied?
- Is the board reachable, unchanged, and honest about having no channel?
- Does any renderer sniff content to decide a grammar?
- Is anything here that belongs in code, a commit message, or a slice file?

## More Information

Supersedes ADR-018 in its front-door clause only; ADR-018 stays accepted for
everything else and must be marked as partially superseded rather than edited.
Parent decisions: ADR-008 (the fork and the bridge), ADR-018 (the additive rule
and the presentation contract). Related: ADR-019 (the verdict read channel,
unbuilt) and ADR-020 (cause is structure), neither of which this changes.

Open question: when upstream's `routes/session/` is deleted, and by which
package. It is deliberately not scheduled here — deleting it early would remove
the fallback that sad path 1 depends on.

The harness-side design record lives in the harness repository under
`specs/tui-redesign/`, specifically `chat-ux-research.md` and
`transcript-design.md`.
