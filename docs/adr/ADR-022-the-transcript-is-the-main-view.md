# ADR-022 — the transcript is the main view, rendered through slots in the session route

**Status:** proposed
**Date:** 2026-08-11
**Decision-makers:** repo owner
**Slice:** `n/a — separate UI track; CHAT-01..CHAT-20 are harness work packages, not slices. No package touches the kernel, so none needs a slice`

## Context and Problem Statement

ADR-018 chose the board as the front door and demoted the transcript to a pane.
The product judgement behind that has not held: the transcript is the surface an
operator works in continuously, and the board is consulted at decision points.
A front door is the continuous surface, not the periodic one.

Corroborating, not causing, that judgement: the board currently renders no data
at all, because ADR-019's read channel is unbuilt
(`packages/tui/src/feature-plugins/board/actions.ts:109` in the harness spells
the reason on screen). The decision below would stand if that channel landed
tomorrow, and this ADR must not rest on its absence.

The screen the operator actually meets is another vendor's. `routes/session/` is
13 insertions from fork base `012c2f57` across 7 files, all rebrand, inside one
2710-line component. This decides which surface opens, and how it may be
redesigned without ending the fork's ability to merge upstream.

## Decision Drivers

- The front door should be the surface used continuously, not periodically.
- A rationale that expires when a dependency lands cannot justify a permanent
  architectural change.
- **UI is owned, not merged.** Upstream UI changes are not carried forward, so
  ADR-018's merge argument does not apply here — nor its additive-plugin rule,
  which that argument was the sole justification for.
- `routes/session` owns live behaviour — permissions, questions, subagents,
  retries — not merely a view. Duplicating an owner duplicates its bugs.
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
in ten days, and all of `packages/tui` by +146/−26 across 15. That is the
measurement this ADR rests on, and it argues for a small seam rather than
against one.

Rejected: [Ink](https://github.com/vadimdemedes/ink) is the mature React-for-CLI
runtime and the closest match to a component-shaped transcript, but the harness
renders through OpenTUI and SolidJS; adopting it means a second runtime in one
process for no governance gain.

Rejected: [cli-table3](https://github.com/cli-table/cli-table3) is what cliui
itself wraps and would give tables directly, but it owns its own border and
colour vocabulary, which would put a second palette beside the generated theme —
the exact failure recorded against glamour above.

## Considered Options

1. **Keep ADR-018 unchanged.** Rejected: it keeps the periodic surface as the
   front door, which is the product error, independent of the read channel.
2. **A new transcript route, upstream's left stock and unreached.** Rejected on
   evidence: `component/prompt/index.tsx:1133` and `app.tsx:999` both navigate to
   `{ type: "session" }`, which `app.tsx:1121` renders with upstream's component.
   "Unreached" would require changing every producer *and* reimplementing
   permissions, questions, subagents, timeline and retries — duplicating a live
   owner, not a view.
3. **Edit `routes/session` directly.** Chosen — UI is owned, so its rendering
   is written where it is used.
4. **Rewrite `routes/session` in place.** Rejected: 2710 lines of permanent merge
   surface, and it deletes the two-way door.

## Decision Outcome

In the context of an operator opening the harness, facing a front door that is
the periodic surface and a transcript that is another vendor's product, we chose
**the transcript as the main view, with its rendering edited directly in
`routes/session`**, to obtain a Ranex-native surface while keeping one owner of
session lifecycle, accepting that ADR-018's rules on touching upstream files and
adding surface as plugins are both superseded for UI.

The board is unchanged and reached deliberately through the command palette
(`/board`), as `feature-plugins/board/index.tsx:74` already records. ADR-018 is
superseded in its front-door clause and **amended** in its checklist rule
"`routes/session` and upstream-owned files are untouched beyond imports". Its
additive-plugin rule, cause-as-structure rule, contrast gate and presentation
contract all stand.

Door: two-way

### Consequences

- Good: the front door is the surface the operator works in, on a basis that
  does not expire when ADR-019 lands.
- Good: one owner of permissions, questions, subagents, retries and revert. No
  second implementation to keep at parity and no deletion trigger to schedule.
- Good: the merge surface is the slot plumbing — tens of lines against the
  +30/−13 measured above — not 2710.
- Good: a component is read where it is used. No slot declaration, no props
  contract, no registration between a renderer and its only caller.
- Bad: it edits files upstream still owns on paper. ADR-018 forbade that, and
  this supersedes the rule for UI, which the fork does not merge.
- Bad: the transcript now hosts the permission interaction, so its threat
  posture is not the board's read-only one.
- Neutral: this does not close BOARD-01 or ADR-019. The board stays empty until
  the read channel lands; it is simply no longer the first thing seen.

### Confirmation

`tests/contract/test_docs_discipline.py` binds this document's form and its
citations. On the harness side, frozen before build:

- `packages/tui/test/transcript-routing.test.tsx` asserts a fresh start resolves
  to the transcript and that no path lands on the retired opencode landing.
- `packages/tui/test/transcript-slots.test.tsx` asserts every named slot renders
  its plugin content and falls back to upstream rendering when unfilled.
- `packages/tui/test/transcript-presentation.test.tsx` asserts styled and
  unstyled renders carry byte-identical text content.
- `tests/contract/test_verdict_presentation.py` stays green, proving this moved
  no verdict rendering into the transcript.

## Improvements on the prior art

1. **Collapsed by default, and the collapsed line carries the outcome.** The
   target collapses to a name, so a reader expands to learn what happened. An
   outcome column means the common case needs no expansion at all.
2. **Identity above content, not beside it.** The target has an open request to
   strip its left gutter because it corrupts copied text; removing the gutter
   removes the option, the setting and the defect class.
3. **One projection per number.** The target's status line disagrees with the
   command reporting the same figure; every count here reads one projection.
4. **The contrast gate already covers diffs.** Two open issues on the target
   concern unreadable diff text; `visual-identity.md` computes WCAG 2.1 for every
   emitted pair and writes nothing on a breach, so that defect fails the build.
5. **`raw` is an output, not a debug flag.** cliui's raw branch becomes the
   supported path for pipes, logs and screen readers.
6. **A slot seam instead of a fork of the owner.** Upstream ships twelve slots
   but none for the transcript body; extending its own idiom is what keeps this
   mergeable and plausibly upstreamable.
7. **No content sniffing.** Both carry filed issues in *both* directions on
   inferring maths from a dollar sign; a fixed grammar has none.

## Architecture surface

Changed: `routes/session` renders Ranex components directly. **No slot and no
plugin is added for UI.** A plugin per piece of UI bought only distance between
a component and its one caller; slots exist for third parties, not for us.
`feature-plugins/transcript/` supplies all three, plus the route default.

Changed: permission and question **rendering** — `index.tsx:1283` shows only
`permissions()[0]` and hides questions while a permission exists, and
`permission.tsx:401` is `fullscreen`. Authority is untouched. Unchanged:
lifecycle ownership, the board, the sidebar slots, the theme, the kernel.

## Scope and threat delta

STRIDE: **spoofing and information disclosure move; elevation does not.** The
transcript renders the permission interaction, and
`routes/session/permission.tsx:168` dispatches `sdk.client.permission.reply`.
Decision authority stays with the kernel, but the surface that displays what is
being approved — tool, path, session and child identity — is now Ranex's, so a
mislabelled request is a spoofing risk, and raw tool payloads are a disclosure
risk. Both are rendering controls, tested below.

Non-goals: localisation, mouse-only affordances, owner-facing translation. Out of
scope: an operator who edits durable state to change what is rendered — the
record is the kernel's to defend.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Maintainability | upstream releases a session-route UI change | not carried; the rendering surface is owned outright |
| Usability | operator reads a tool result without expanding it | outcome present on the collapsed line |
| Functional correctness | styled and unstyled renders compared | text content byte-identical |
| Accessibility | colour or glyph removed | every state still spelled |

## Reversibility

Door: two-way

Removing the slots restores `routes/session` to its upstream shape, and deleting
`feature-plugins/transcript/` removes the rendering. Restoring the route default
returns the board to the front door. The board was never modified. Nothing
durable is written, so there is no migration and no record to unwind. What does
not revert is the 13-insertion rebrand, which predates this decision.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 1 | a slot is unfilled, or the plugin fails to load | upstream rendering shows through, bound via OpenTUI's `fallback` option; `slots.tsx:26`'s empty view returns `null` and drops children, so this is work, not a given |
| 2 | an entry kind arrives that no module handles | render the raw payload labelled `unrendered`, never drop it |
| 3 | two entries registered at the same order | fail at construction, not by silently reordering |
| 4 | the same delta is delivered twice | **not caught at the renderer** — `sync.tsx:405` concatenates on `partID`+`field` and the protocol carries no delta identity; a fix belongs upstream of the TUI |
| 5 | deltas arrive out of order or after reconnect | ordered by the part index the sync layer holds, never by arrival |
| 6 | terminal resized mid-stream | full redraw, never a diff against a stale layout |
| 7 | `NO_COLOR` set or stdout is a pipe | styling drops, content byte-identical |
| 8 | terminal lacks the Unicode range | ASCII glyphs; no state was carried by a glyph, so nothing is lost |
| 9 | permission request cannot be rendered | spelled error state, never an indefinite spinner |
| 10 | a permission reply fails or the request is already resolved | say so and re-read state; never report success unsent |
| 11 | permission and question outstanding together | both visible and separately addressable — today `index.tsx:1283` hides the question and every permission after the first, so this is the change, not the status quo |
| 12 | session not found, or bootstrap fails | spelled failure with the session id; never an empty transcript that reads as idle |
| 13 | provider retry, abort or stream error mid-turn | rendered as its own state, not as a completed answer |
| 14 | reader scrolls up while output streams | autoscroll releases and does not reclaim itself |
| 15 | draft or queued input present at navigation | preserved and shown as queued, never silently dropped |
| 16 | an initial plugin route names an unregistered id | `PluginRouteMissing` renders, as today; the transcript is not a fallback for it |
| 17 | operator believes the transcript shows admissibility | **not caught** — the board is the only verdict surface; review's job |

## Test strategy

Frozen before build, red then green, reviewed against the diff on disk rather
than an implementer's summary.

Repository contract level, in this repo:

- `tests/contract/test_docs_discipline.py` — this ADR's form, citations, sad
  path count and door line.
- `tests/contract/test_verdict_presentation.py` — unchanged and required to stay
  green; the evidence that no verdict rendering moved into the transcript.
- `tests/contract/test_kernel_unchanged.py` — asserted, not assumed.

Harness level. **The contract test above resolves only Python paths inside this
repository, so it cannot validate the files below; the harness suite is their
enforcing gate and this is stated rather than left implied:**
`packages/tui/test/transcript-routing.test.tsx` (sad paths 1, 12, 16),
`transcript-slots.test.tsx` (1, 2, 3), `transcript-stream.test.tsx` (4, 5, 6,
13), `transcript-permission.test.tsx` (9, 10, 11),
`transcript-degraded.test.ts` (7, 8), `transcript-scroll.test.tsx` (14),
`transcript-composer.test.tsx` (15).

Levels: contract for the record and the kernel invariant, component for the
renderers, and **integration for routing** — a default-route change is a runtime
path, so the earlier claim that none is introduced was wrong.

Coverage: no global percentage. Sad paths 1 to 16 each map to a named file
above; 17 is declared uncatchable, because a reader's belief about what a screen
means is not a testable property of the screen.

## Code review checklist

- Read the diff on disk. The implementer's summary is discarded.
- Is every edit to `routes/session` a slot, and is each one named in this ADR?
- Does any collapsed entry hide its outcome, rather than only its detail?
- Is any state carried by colour or a glyph alone anywhere in the new rendering?
- Does any number appear that was read separately from its sibling display?
- Does a message body carry a decorative left margin that would be copied?
- Does the permission surface show tool, path and session identity unambiguously?
- Is the board reachable, unchanged, and honest about having no channel?
- Is anything here that belongs in code, a commit message, or a slice file?

## More Information

Supersedes ADR-018 in its front-door clause, its checklist rule on touching
`routes/session`, and its additive-plugin rule as applied to UI; ADR-018 stays accepted for everything else and must be
amended in place at that clause only — the status set has no partial form. Parent decisions: ADR-008 (the
fork and the bridge), ADR-018. Related: ADR-019 (the verdict read channel,
unbuilt) and ADR-020 (cause is structure), neither of which this changes.

Three independent fresh-context reviewers returned UNSOUND against the previous
revision; the new-route option, the expiring rationale, the `STRIDE: none moved`
claim and two impossible sad paths were found there and are corrected above.

Open question: whether the slots should be proposed upstream rather than carried.

The harness-side design record lives under `specs/tui-redesign/`, specifically
`chat-ux-research.md` and `transcript-design.md`.
