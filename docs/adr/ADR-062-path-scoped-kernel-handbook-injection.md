# ADR-062 — path-scoped kernel handbook injection for delegates

**Status:** accepted
**Date:** 2026-09-24
**Decision-makers:** repo owner
**Issue:** #100 (MAP §5.1 "the catalog exists, the injection does not"; §17.6 knob 3)

## Context and Problem Statement

MAP §17.6 blocks deep customization of the harness — "a gauge the user can
recalibrate is no gauge" — and allows exactly three knobs, the third being
"handbook additions in a designated directory — read as guidance, never as
authority; only the kernel enforces". MAP §5.1 records the kernel handbook
container as decided-but-unbuilt: `governance/` was to be "the library every
agent reads", and nothing reads it. Delegated workers therefore start from a
bare prompt with zero project-specific craft knowledge, and an operator has
no sanctioned place to put any.

The problem: what shape may operator guidance for delegated workers take,
where may it live, and what may consume it, so that it can never widen, narrow
or impersonate kernel authority — while remaining worth writing.

## Decision Drivers

- §17.6: adding a knob requires an ADR, and the default answer is no. This
  decision must earn the yes inside the smallest possible knob.
- Guidance must stay guidance: no handbook byte may alter a gate, claim,
  evidence envelope, verdict or journal row. `run` and `gate evaluate` must
  never read a handbook.
- Determinism: resolution must be a pure function of its inputs with a
  digest, so a completed run can name exactly the chapters it was given
  (ADR-043's retained-log discipline extended additively).
- Two layers only — one operator (§7.2): project and system, nothing else;
  no custom/global/marketplace layers, no SDK.
- MAP §15.3 adoption rule: mature upstream behaviour is referenced, not
  reinvented blindly; incompatible or code-level copying is refused.
- No new runtime dependency.

## Prior art

Searched: path-scoped review-guidance configuration in mature tools before
designing the schema. One reference, read at its pinned commit this session
over the network; behaviour adopted, **no code copied** (the issue's §15.3
instruction — Apache-2.0 would travel, but the issue directs behaviour-level
adoption and the engine is ~150 lines the repo should own).

- https://github.com/alibaba/open-code-review/blob/14b84f08a3af7f042d702c721f21f7952d841970/.opencodereview/rule.json
  — grounds: the entry shape (`path`, `rule`, `merge_system_rule`), layered
  resolution (custom > project > global > system, first match wins per
  layer), and merge presentation (system guidance first, user guidance
  second).
  Licence: Apache-2.0 (upstream header). Not vendored.
  Weakness (refused): four user layers and `--rule` override flags grow a
  configuration surface §17.6 forbids here; Ranex takes two layers and no
  flag. Its include/exclude file filters are a second knob this decision
  does not take.
- https://github.com/alibaba/open-code-review/blob/14b84f08a3af7f042d702c721f21f7952d841970/internal/config/rules/sniffer.go
  — grounds: a content sniffer must decorate **only the system layer**, so
  user layers always outrank a heuristic — the exact structural rule arm 3
  of the issue freezes.
  Licence: Apache-2.0 (upstream header). Not vendored.
  Weakness (refused): the sniff hard-codes the `.m`/Objective-C case in
  code; Ranex keeps the mechanism but expresses it as data
  (`sniff_marker` on a system entry), so the knob adds no new code path per
  ambiguity.
- https://github.com/benjaminp/six at tag 1.17.0
  (commit ebd9b3af90247b8858d415a05e96e9ee61e48d07) — not a design source:
  the small real repository the issue's first real-data arm names, cloned
  by the proof driver to resolve every path in a foreign tree.
  Licence: MIT. Not vendored; read in a scratch clone only.

## Considered Options

1. Do nothing — guidance stays chat-only. Rejected: MAP §5.1 records the
   injection as decided; #100 is the owner's direction to build it.
2. Free-text briefing the operator pastes into `--prompt` per delegate call.
   Rejected: not a designated directory (§17.6 wording), not path-scoped, not
   digestable, and per-call paste is the "overwhelmed user" the owner
   directive refuses.
3. Full policy compiler: arbitrary layers, include/exclude filters,
   per-harness overrides (the upstream surface). Rejected: every added layer
   or flag is a knob §17.6's default answer denies; two layers already cover
   one operator (§7.2) plus one repository.
4. Handbooks consulted by `run`/`gate evaluate` too (guidance shown in
   verdicts). Rejected: every read on the enforcement path is a chance for
   guidance to become authority; delegate packet construction is the only
   consumer that cannot touch a verdict.
5. Two layers, path-globbed chapters, pure resolution, digest into the
   ADR-043 retained-log manifest, delegate-only consumption. Chosen.

## Decision Outcome

Knob granted: **handbook additions in designated directories, path-scoped,
read as guidance by delegate packet construction only** — §17.6 knob 3 given
its shape. Why the default no does not apply to this shape:

- It cannot recalibrate anything. The engine is unreachable from `run`,
  `gate evaluate`, the journal, signing and the kernel; a contract test
  refuses any importer outside delegate packet construction, and
  `verdict.py` stays digest-pinned, untouched.
- The surface is two files in designated directories, no flags:
  `governance/handbook.json` in the dispatched base tree (project layer)
  and `${XDG_CONFIG_HOME:-$HOME/.config}/ranex/handbook.json` (system
  layer, one operator). Absent files mean absent layers; the delegate
  behaves byte-identically to a pre-handbook run.
- Entries are `{path_glob, text, merge_system}` (upstream's
  `path`/`rule`/`merge_system_rule` renamed). Declaration order matters;
  first match wins within a layer; **project > system** on the same path.
  `merge_system: true` keeps the matched system chapter in front of the
  project chapter (the reference's presentation).
- The glob language is deliberately small: `**`, `**/`, `*`, `?`, `[a-z]`
  classes; case-sensitive POSIX repo-relative matching; brace expansion and
  negation refused loudly (smaller knob than upstream, on purpose).
- A system entry may carry `sniff_marker`: it wins inside the system layer
  only when the path's first non-blank content line starts with that
  marker (the `.m` MATLAB/Objective-C disambiguation, as data). A sniff can
  never decorate a project rule — the structural rule from upstream's
  sniffer, kept exactly.
- Resolution `resolve_handbook(system, project, paths, peeks)` is pure:
  entries and paths in, chapters + one row per path + one digest out. The
  digest is `sha256:` + `canonical_sha256` over the chapters (texts by
  value) and rows, so one byte anywhere in a chapter, glob or merge flag
  changes it. Unmatched paths are rows with status `unmatched`, never
  silently dropped — absence is recorded, in the house grammar.
- Injection: `task delegate` resolves the handbook against every file of
  the dispatch base tree (`git ls-tree`), appends `render_brief` output to
  the worker's prompt (chapters, then the full per-path table), and lands
  `{digest, chapters, matched, unmatched}` as the additive `handbook` field
  in the ADR-043 retained-log manifest. Nothing lands in any evidence
  envelope or verdict; `--log-retention off` retains nothing, as documented
  for ADR-043.

### Consequences

- Good: an operator can give every delegated worker project craft knowledge
  scoped by path, with a durable, digest-bound record of what was given.
- Good: a repository without handbooks pays one `git ls-tree` and no other
  cost; behaviour is byte-identical to before.
- Bad: the brief grows by the chapter texts plus one line per in-scope
  path; on very large trees that is operator-authored bytes the worker must
  read (bounded by what the operator writes; no truncation is applied —
  truncating guidance silently would falsify the digest's promise).
- Bad: `merge_system` binds per project entry, so a project wanting the
  system chapter on some paths only needs two entries; accepted over a
  per-path merge grammar, which would be a larger knob.
- Bad: sniff peeks read one line per sniff-globbed path at dispatch time;
  a pathological system handbook sniffing `**` would read one line per file.
  The knob is the operator's own; documented, not capped in code.

## Improvements on the prior art

- Two layers where upstream keeps four user-configurable ones plus a flag:
  the configuration surface shrinks to what §17.6 allows, and precedence is
  provable by exhaustion in tests.
- The sniff is data (`sniff_marker`) where upstream hard-codes the `.m`
  case: new ambiguities need no code change, and the marker grammar
  (first-non-blank-line prefix) is trivially auditable.
- Unmatched is a recorded row where upstream falls back to a default rule:
  Ranex has no default chapter, so a path with no guidance says so — the
  packet never implies guidance it did not give.
- The resolution digest covers chapters by value and the full row table,
  where upstream hashes rule configuration only: a completed run names not
  just the rules but the exact path→chapter mapping it was built from.
- Malformed handbooks refuse the delegate run (`refusing handbook …`), where
  upstream warns and continues: guidance nobody can parse is absence wearing
  a costume, and absence blocks.

## Architecture surface

- New: `src/ranex/policy/handbook.py` (pure engine: parse, glob, resolve,
  render, digest).
- Changed: `src/ranex/cli/delegation.py` (layer loading, base-tree scope,
  bounded content peeks, prompt extension, manifest record);
  `src/ranex/execution/retained_logs.py` (additive `handbook` manifest
  field only).
- Explicitly unchanged: `governed_execution/` (verdict.py digest-pinned),
  evidence envelopes and `SIGNED_FIELDS`/`EVIDENCE_DOMAIN`, `run`,
  `gate evaluate`, fanout (children delegate; injection happens per child),
  the dependency graph.

## Scope and threat delta

- In scope: delegate packet construction for `task delegate`; the two
  designated handbook locations; the retained-log manifest field.
- Out of scope: #102's delegated review command; #112's minimization
  ladder (a later slice composes this one); any enforcement read.
- Threat delta: a malicious handbook author is the repository or the
  operator — both already trusted for larger powers (the repo supplies the
  suite command; the operator supplies the harness). The one new vector is
  prompt-shaping: chapters could try to instruct a worker to subvert its
  task. That vector exists for `--prompt` itself today; the digest makes
  the injected bytes auditable after the fact, which is an improvement over
  unaudited prompts. No new network call, credential or privilege.

## Quality attributes

| Attribute | Effect |
|---|---|
| Determinism | identical (handbooks, paths) → identical rows, chapters, digest, brief |
| Auditability | the manifest names digest, chapter ids and counts; one chapter byte changes the digest |
| Honesty | unmatched paths recorded; malformed handbooks refuse; `off` retention retains nothing |
| Safety | no importer on any enforcement path; sniff cannot outrank the project layer |
| Cost | one `ls-tree` always; one bounded `git show` per sniff-globbed path; brief grows by operator bytes |

## Reversibility

Door: two-way. Removing the two loaders and the prompt extension restores
the pre-#100 delegate exactly (the integration test pins that byte-identity);
the manifest field is additive and its absence is the old shape, pinned by
the contract test. Deleting `policy/handbook.py` breaks only its tests.

## Sad paths

- No handbook anywhere → no injection, no manifest field, byte-identical
  behaviour (pinned by tests at both levels).
- Malformed project or system handbook → `ERROR refusing handbook …`, exit
  2, no harness runs.
- Neither `XDG_CONFIG_HOME` nor `HOME` set → refused: the designated
  directory cannot be located, and guessing drops operator guidance
  silently.
- System handbook unreadable (permissions) → refused, naming the path.
- Sniff glob matches a binary/unreadable path → no peek, plain path match
  stands (the sniff is best-effort by construction, upstream's model).
- Project rule and system rule on the same glob → project wins; the row
  still records `system_pattern`, so both matches are on the record.
- `--log-retention off` → no manifest, hence no digest record; the outcome
  carries `{retained: false, reason: operator-disabled}` as ADR-043
  already documents.
- Base tree unreadable at scope listing → refused, naming the git failure.

## Test strategy

Red-first, all frozen in `governance/suite_manifest.json`:
`tests/unit/test_handbook_resolution.py` (grammar, precedence, sniff,
unmatched, digest sensitivity, 58 cases);
`tests/integration/test_handbook_delegate_cli.py` (real git target, real
harness, real `cmd_task_delegate`: injection, arm 2 both sides, arm 3,
arm 4 digest, no-handbook byte-identity, malformed refusal);
`tests/contract/test_handbook_surface.py` (sole-importer rule, no handbook
mention outside the allowed surface, verdict.py digest re-pinned, additive
manifest shape); `tests/e2e/test_handbook_injection_real.py` (real
subprocess journey, ADR-032 golden + sabotage control, the semantic arms,
arm 4's negative). Field proof: `tools/dogfood/handbook_proof.py` runs the
issue's five real-data arms as #95 control pairs over a pinned clone of
`six@1.17.0` and this repository, receipt under
`tools/dogfood/audits/2026-09-24-handbook-injection/`.

## Code review checklist

- [ ] No code path outside delegate packet construction imports the engine.
- [ ] No evidence envelope, verdict, journal or signing surface mentions a
      handbook.
- [ ] The manifest change is the additive field and nothing else.
- [ ] `merge_system` puts the system chapter first, project second.
- [ ] A sniff-marker entry can never supply text for a project-layer win.
- [ ] Unmatched rows exist and reach the rendered brief.
- [ ] One byte of any chapter text changes the resolution digest.

## More Information

Issue #100 carries the binding contract and the five real-data arms; MAP
§5.1 (container row), §7.2 (one operator), §17.6 (knob 3 and the default
no), §15.3 (behaviour-level adoption). ADR-043 owns the retained-log
manifest this decision extends additively. The upstream files were read at
commit 14b84f08a3af7f042d702c721f21f7952d841970 via raw.githubusercontent
this session; nothing was copied, so `docs/adr/prior-art/ADR-062/` does not
exist and no NOTICE is owed.
