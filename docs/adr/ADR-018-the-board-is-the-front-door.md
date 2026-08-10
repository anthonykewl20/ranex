# ADR-018 — the board is the front door

**Status:** accepted
**Date:** 2026-08-10
**Decision-makers:** repo owner
**Slice:** `n/a — separate UI track; BOARD-01..BOARD-22 are harness work packages, not slices, and do not queue behind SLICE-017. BOARD-02 alone touches the kernel and needs its own slice`

## Context and Problem Statement

The harness TUI is stock opencode. Measured on 2026-08-10, `packages/tui` differs
from the fork base `012c2f57` (`v1.18.11`) by 82 files, 163 insertions and 174
deletions — almost entirely the rebrand. Its default theme was opencode's palette
renamed, still declaring `$schema: https://opencode.ai/theme.json`.

So the operator's screen is a chat transcript: a tool that optimises the throw.
Ranex optimises the scoring, and nothing on that screen says whether work is
acceptable or why not. A verdict reaches the operator only through the Python
CLI. This decides what the harness shows when it opens, and how that surface may
render a verdict without distorting it.

## Decision Drivers

- The operator reads verdicts, not dashboards (`MAP` §17.1). CLI-first stands.
- Verdict content must not vary with whether stdout is a terminal.
- Seven distinct causes of an unsatisfied claim must stay distinguishable.
- The fork must remain mergeable from upstream; divergence is the real cost.
- The non-technical owner needs a surface eventually, not first.
- No enforcement may move into the harness; it collects, the kernel judges.

## Prior art

Searched: GitHub code and repository search for terminal UI frameworks and design
systems, resource-board TUIs, panel layout with focus, and policy or scanner
verdict rendering; release tags resolved to commits, root licences checked first.

- [k9s resource table](https://github.com/derailed/k9s/blob/558caafe7ba067467de46b320cc22ef11fef9c34/internal/view/table.go)
  binds keys as data (`Actions().Bulk`, `AddBindKeysFn`), guards dispatch behind
  `IsTopDialog()`, drills down via `SetEnterFn`, and dumps the filtered table to disk.
  License: Apache-2.0.
  Weakness: its table caches a remote cluster and renders stale rows without
  apology; here a stale row is a wrong verdict, not cosmetic lag.
  Vendored: docs/adr/prior-art/ADR-018/k9s-view-table.go blob:62404edde0b73965d867fedb2bfeb15e9aee3c9d
- [Trivy table report](https://github.com/aquasecurity/trivy/blob/40c73e5d6166dcc0346a1ab4e94499d1572854e4/pkg/report/table/table.go)
  gates styling alone on `IsOutputToTerminal`, leaving rows, borders and content
  identical, and maps severity to colour through one ordered lookup.
  License: Apache-2.0.
  Weakness: the lookup is an array index because severity is totally ordered;
  Ranex causes are unordered, so the index model cannot be copied.
  Vendored: docs/adr/prior-art/ADR-018/trivy-report-table.go blob:f0f81b44dce23d84b19c5d4b700f39836fbb9992
- [Textual ColorSystem](https://github.com/Textualize/textual/blob/1d99508b928a771b51e1a527319c6b87dcff9e05/src/textual/design.py)
  derives a full palette and its shades from about ten semantic colours, with a
  separate degraded path for 16-colour terminals.
  License: MIT.
  Weakness: shading is luminosity arithmetic and checks no contrast; adopting the
  generator unguarded ships an unreadable palette.
  Vendored: docs/adr/prior-art/ADR-018/textual-design.py blob:290de588054d79feb5158dac6f5ccf75729bd869
- [Lip Gloss colour](https://github.com/charmbracelet/lipgloss/blob/5bd778d050f0a5a130e7cf041917927496dbe722/color.go)
  models absence of colour explicitly as `NoColor` and resolves a light/dark pair
  against the detected terminal background via `LightDarkFunc`.
  License: MIT.
  Weakness: detection needs the terminal to answer a background query; many never
  do and no CI does, so a declared default must win over detection.
  Vendored: docs/adr/prior-art/ADR-018/lipgloss-color.go blob:7443dc10bb0bd49174c22ca1c5804b9ad22fb814
- [lazygit layout](https://github.com/jesseduffield/lazygit/blob/aee0e40ec1235476e9328678f0f3e2462576b9ae/pkg/gui/layout.go)
  recomputes dimensions each frame, diffs against `PrevLayout` before writing,
  registers popup and transient views, and activates focus as context.
  License: MIT.
  Weakness: one global `Gui` struct with layout branching in a single function;
  porting that shape would fight SolidJS reactivity.
  Vendored: docs/adr/prior-art/ADR-018/lazygit-layout.go blob:bcdc0edfc9684ad3cc70b995bf850029787dab3b
  Vendored: docs/adr/prior-art/ADR-018/LICENSE-K9S-APACHE-2.0.txt blob:f433b1a53f5b830a205fd2df78e2b34974656c7b
  Vendored: docs/adr/prior-art/ADR-018/LICENSE-TRIVY-APACHE-2.0.txt blob:261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64

Rejected: [conftest](https://github.com/open-policy-agent/conftest) is the closest domain
match for policy verdict rendering, but GitHub resolves its licence as `NOASSERTION`, and an unresolved licence may not be copied into this MIT tree.

Rejected: [Bubble Tea](https://github.com/charmbracelet/bubbletea) and
[Ink](https://github.com/vadimdemedes/ink) are mature TUI runtimes, but the harness
renders through OpenTUI and SolidJS; either means a second runtime and 190 files
rewritten for no governance gain.

## Considered Options

1. **Chat stays the front door**, governance reported at the edges of the
   transcript.
2. **The board is the front door**, transcript demoted to a pane, owner view
   built later as a second mode.
3. **Plain-language owner view first**, operator board after.
4. **Board built by rewriting the session route** rather than added beside it.

## Decision Outcome

Chosen: **option 2** — the board is the front door, and it is **added as a new
route plus feature-plugin slots, never a rewrite of the session route**.

The first half is the product decision: the screen answers *is this work
acceptable, and why not*. The second half is what keeps the fork alive. The TUI
is 163 insertions from stock opencode; a rewrite of `routes/session` would end
that, and every future upstream merge would pay for it. New files merge cleanly.

Option 1 cannot show the cause of a failure. Option 3 designs a translator for
verdicts no board yet produces. Option 4 buys nothing option 2 lacks.

Door: two-way

### Consequences

- Good: the default screen states a verdict and its cause.
- Good: upstream merges stay tractable because the board is additive; deleting
  the route returns the harness to stock behaviour.
- Good: the owner view (`MAP` §15.2 Translator, absent) becomes a later mode over
  the same durable state, not a parallel product.
- Bad: two surfaces render verdicts — the board and the Python CLI — and they can
  disagree. The presentation contract exists to stop that.
- Bad: the board needs structured cause data the kernel does not yet expose.
- Neutral: the other 32 themes keep opencode's structure until someone needs them.

### Confirmation

Frozen red-first tests, reviewed against the diff on disk, not a summary:

- `tests/contract/test_verdict_presentation.py` asserts a verdict-producing
  command yields byte-equal captures under a pipe and a pty, and no `ESC` byte.
- A TUI test asserts the cause renderer is exhaustive over the closed cause set
  and has no default arm.
- A generator test asserts every emitted theme pair meets its contrast floor.
- Independent review, then a mutation gate over touched kernel files.

## Improvements on the prior art

Trivy proves styling can be gated on TTY detection while content stays fixed, but
it still colours by a severity **rank**. Ranex causes are not ordered: `absent` is
not a worse `failed`, and `refused` is an attack while `absent` is work never
done. So the rank is replaced by a closed sum type matched exhaustively, and the
compiler — not a reviewer — refuses a renderer that has not handled a new cause.

Textual derives a palette from semantic colours and never checks the result
against its surface; contrast lives elsewhere in that codebase. Here the check is
a build gate: the generator computes WCAG 2.1 for every pair it intends to emit
and writes nothing if one is under floor. A governance tool whose FAIL is hard to
read has failed at its only job, so this is not a preference.

k9s exports the table an operator is looking at. That idea is kept and tightened:
the board's export is bound to the subject digest it rendered, so an exported
board is evidence of a specific tree rather than a screenshot.

Lip Gloss detects the terminal background; Ranex declares it and lets detection
only refine, because CI never answers the query and CI is where verdicts matter.

## Architecture surface

Added: a board route in `@ranex/tui` plus feature-plugin slots, reading durable
state through the existing SDK and event path. No second event system.

Changed: `Evaluation` gains a structured per-claim cause alongside `reason`.
`reason` stays, unchanged, for humans and for the journal record.

Unchanged: the kernel judges, the harness collects. The board issues no verdict,
holds no key, and writes nothing to the journal.

## Scope and threat delta

STRIDE: Spoofing — the board renders an approver identity it never checks;
approval remains the kernel's. Tampering — an exported board is bound to the
subject digest, so it cannot be passed off as another tree. Repudiation — export
is a projection, never a journal entry. Information disclosure — the board shows
what the operator may already read via the CLI; no new secret reaches the TUI.

Non-goals: the board never evaluates, merges, approves or publishes. Out of
scope: the owner view, and the parked Manager UI of milestone #2.

## Quality attributes

- Determinism: identical durable state renders identical content.
- Legibility: every emitted colour pair meets its contrast floor or is not shipped.
- Mergeability: divergence from upstream confined to files upstream does not own.
- Honesty: a state the board cannot distinguish is shown as undistinguished.
- Latency is explicitly not a quality attribute here; correctness outranks it.

## Reversibility

Door: two-way

The board is additive — a route and its slots. Deleting those files returns the
harness to stock opencode behaviour, and the kernel is unaffected because it
never depended on the board.

The one-way part is `Evaluation` gaining a structured cause. That field is
additive and append-only in the record, so it widens rather than breaks readers.

## Sad paths

- Durable state carries a cause the renderer does not know → render
  `unclassified` and say so; never fall back to the nearest familiar cause.
- The kernel adds a cause the TUI has not handled → the exhaustive match fails
  to compile. This is the intended failure, not an outage.
- A renderer parses `reason` prose to recover a cause → forbidden; the wording
  is not an interface, and reworded prose would mislabel a forgery as absence.
- Terminal does not answer the background query → the declared default wins;
  detection never overrides it.
- `NO_COLOR` set, or stdout is a pipe → styling drops, content byte-identical.
- Terminal supports 16 colours only → degraded palette, same content, and glyphs
  fall back to ASCII rather than rendering as replacement boxes.
- The board renders while evidence is being written → show the subject digest it
  read and mark the row stale; never render a verdict for a tree it did not read.
- Two panes disagree because one refreshed → both resync from durable state;
  the board never merges two reads into one row.
- An export is taken of a board mid-refresh → the export carries the digest of
  the state actually rendered, or it refuses.
- Upstream renames a file the board imports → the board is additive, so the
  break is a compile error in Ranex-owned files, not a silent merge.
- The operator has no evidence at all → every gate reads `absent`, and the board
  says work never done rather than showing an empty, reassuring table.

## Test strategy

Frozen before build, read-only to implementers, red then green.

- `tests/contract/test_verdict_presentation.py`: run a verdict-producing command
  into a pipe and under a pty; assert byte-equality after stripping the pty
  driver's `\r`, and assert zero `ESC` bytes in either capture.
- `tests/contract/test_docs_discipline.py` continues to bind this ADR's citations
  to vendored bytes; no new exemption is added.
- Kernel: a test that the structured cause partition and the `reason` string
  never disagree, over every diagnosis branch, including contradiction.
- TUI: exhaustive-match test over the closed cause set, asserting no default arm
  and that an unknown cause renders as `unclassified`.
- TUI: snapshot the board styled and unstyled; assert the text content of both
  snapshots is equal and only styling attributes differ.
- Theme generator: assert every emitted pair meets its floor, and that the
  generator exits non-zero and writes nothing when a floor is breached.
- Negative: a renderer that regex-matches `reason` fails review by construction —
  covered by the exhaustive-match test, not by inspection.

## Code review checklist

- Read the diff on disk. The implementer's summary is discarded.
- No renderer parses `reason`, and no cause mapping has a default arm.
- No cause is sorted, ranked, or coloured by severity order.
- Content is computed before any TTY check; styling cannot alter a line.
- Board files are new; `routes/session` and upstream-owned files are untouched
  beyond imports.
- Contrast gate runs in CI and can fail the build.
- No key, no journal write, and no approval path reaches the TUI.
- Exported board carries the subject digest of the state it rendered.

## More Information

Parent decisions: ADR-008 (the fork and the bridge), ADR-017 (approved
specification). Related: `MAP` §17.1 (`tui` is the operator surface), §15.2 (the
Translator, absent), and the parked Manager UI, milestone #2 issue #9, which this
does not open.

Fork base `012c2f57` = opencode `v1.18.11`. Divergence measured 2026-08-10.
The harness-side design record, including the reference library, the verdict
presentation contract and the visual identity, lives in the harness repository
under `specs/tui-redesign/`.
