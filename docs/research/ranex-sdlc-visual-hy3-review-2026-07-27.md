# HY3 independent review of the Ranex SDLC visual system

| Field | Value |
|---|---|
| Review ID | `REV-SDLC-VISUAL-HY3-001` |
| Date | 2026-07-27 |
| Execution completed | 2026-07-27T20:36:35+08:00 |
| Evidence status | Cross-family advisory review; no transition authority |
| OpenCode | `1.18.7` |
| Agent | `plan` (read-only) |
| Provider | OpenRouter |
| Model | `tencent/hy3` |
| Variant | `high` |
| Session | `ses_05c6f1468ffepsTM7Vd8qz7Oqp` |
| Repository mutations by HY3 | None |

## Frozen review inputs

| Input | SHA-256 |
|---|---|
| `docs/research/real-world-sdlc-operating-model-research-2026-07-27.md` | `5067067ebccf66c8fae981c3cb0eddd6decb74953891f70790f97e8538421ea7` |
| `docs/architecture/CORE_SDLC_OPERATING_MODEL.md` | `b2171f6724146224a0eac15cb530b0aff565d9d95e37b41049768ddcfa6d324a` |
| `docs/architecture/SDLC_CONTROL_CATALOG.md` | `6935f9c3bc4e058db940627d2e5e82c7029cca2a18008b9c08295a71f5158e60` |
| `docs/architecture/AI_AGENT_DEVELOPMENT_LIFECYCLE.md` | `b18abdb9389316a9dbaf0a7c28ba441e2def2306d740d5e96202265ea66b4962` |
| `docs/architecture/SOURCE_OF_TRUTH.md` | `807c6bce6d194459f277e69286a861333884aaad65237bd21888f73e07ca37d2` |

HY3 received the files without the other reviewers' conclusions and was asked
to challenge lifecycle namespaces, state transitions, rejection and recovery,
risk, authority, evidence, AI subprocess boundaries, fork lifecycles,
maintenance/retirement, self-development, maturity language, Mermaid
renderability, accessibility, and plain-language simplification.

## Executive verdict

HY3 found the visual broadly faithful but only conditionally usable. It rejected
the phrase “complete operating-model view” until direct contradictions and
human-facing maturity warnings were fixed.

## P0 findings

1. **Missing canonical rollback re-entry.** The normative state machine requires
   `ROLLED_BACK -> TRIAGE`; the draft visual routed rollback to recovery and
   incident handling but omitted the canonical new-attempt path.
2. **Missing non-misleading HTML guard.** The human-facing page must prominently
   state that the policy is `ACCEPTED`, implementation remains `R_AND_D`, and
   adoption gates have not yet passed.

## P1 findings

- Use exact enum labels such as `IN_PROGRESS`, `RELEASE_READY`,
  `OUTCOME_REVIEW`, and `ROLLED_BACK`.
- Add `OUTCOME_REVIEW -> DEFINITION` and generic active-state blocking and
  pre-release cancellation semantics.
- Visually separate incident, maintenance, retirement, and other linked
  lifecycle namespaces from `WorkItemStatus`.
- Include the missing immutable release/update lifecycle from
  `SDLC-FORK-003`.
- Add a text-and-line-style legend so color is not the sole carrier of meaning.
- Align intake and triage role vocabulary with the normative policy.
- Explain that `MERGED` is an event, `L0-L12` are execution activities rather
  than work states, and the HTML is non-normative.

## Reconciliation

All P0 and P1 findings were accepted and applied:

| Finding | Resolution |
|---|---|
| Rollback re-entry | Added exact `ROLLED_BACK -> TRIAGE` transitions to Mermaid, ASCII, semantic HTML, and fork explanation |
| Maturity guard | Added a prominent status banner plus an adoption-gate table |
| Enum labels | Canonical underscores are primary; plain text is secondary |
| Missing feedback | Added outcome-to-definition and generic blocked/cancelled routing rules |
| Namespace blur | Linked lifecycles use namespaced labels, dashed purple treatment, captions, and semantic caveats |
| Missing update flow | Added `CHECKED -> ... -> COMPLETED` and rollback/recovery |
| Accessibility | Added a visible legend, semantic state equivalent, ASCII fallback, keyboard controls, print and reduced-motion behavior |
| Role drift | Standardized to intake owner and product/duty owner |
| Event/subprocess warnings | Added explicit `MERGED` and `L0-L12` warnings |

## Limitations

- HY3 advice is not authority, deterministic proof, accessibility
  certification, or evidence that Ranex implements the process.
- The large Mermaid graph is a complete reference view, not the first teaching
  view. The reviewed static guide led with the thirteen-state normal path and
  documented the three exceptional statuses separately.
- The review is advisory and cannot grant a lifecycle transition or establish
  accessibility certification.

## Final reconciliation review

| Field | Value |
|---|---|
| Review ID | `REV-SDLC-VISUAL-HY3-002` |
| Completed | 2026-07-27T20:51:02+08:00 |
| Session | `ses_05c610f0affebS3RKsEa56NgGd` |
| Model | `tencent/hy3`, variant `high`, read-only `plan` agent |
| Verdict | **PASS — no blockers** |
| Repository mutations by HY3 | None |

### Corrected inputs

| Input | SHA-256 |
|---|---|
| Research with Mermaid and ASCII | `307c8b0ca0470d568b81443cd95efb9fa183dba5c9d85a1e271b0e9ac3bd7936` |
| Static HTML visual guide | `5b9375343cf29696ca35e50f31230dc69251e2035c46d1ae22df62b8db1cff8f` |
| Rendered full-spec SVG | `3ecd69d27f1e4c1801a33c05b113307a51a630f88a38104c619fe49b5df3ac64` |
| Core policy | `7b978862b41b48397920f7b7851bfb335fcb248a5abca728325d546e766e926b` |
| Control catalog | `e8c7e696893356ba323afb26fbed9b97fdc474748ecf4726b957263caaeccce4` |

HY3 confirmed:

- `ROLLED_BACK -> TRIAGE` in Mermaid, ASCII, HTML, and the rendered artifact;
- the visible `ACCEPTED`/`R_AND_D` warning and all adoption-gate statuses;
- canonical enum labels and full feedback routing;
- distinct linked-lifecycle namespaces;
- the `SDLC-FORK-003` release/update lifecycle;
- text and line-style meaning in addition to color;
- normative intake/triage role alignment;
- `MERGED`, `L0-L12`, non-normative, and no-auto-advance caveats; and
- consistency with the core state machine and control catalog.

Nonblocking future improvements are deeper screen-reader navigation inside an
inline SVG and a physical print-legibility check. The HTML already supplies
alt text, a semantic state equivalent, an ASCII fallback, keyboard controls,
reduced-motion handling, and print styling.

## Post-review correction

A later whole-map reconciliation made the teaching count explicit: the normal
path has thirteen states, while `BLOCKED`, `CANCELLED`, and `ROLLED_BACK` make
sixteen canonical `WorkItemStatus` values in total. The current HTML now gives
all sixteen their own semantic cards. This clarification postdates
`REV-SDLC-VISUAL-HY3-002`; it is therefore not retroactively claimed as an
input to that historical verdict and is rechecked in the final architecture
review.

## Current exact-subject supersession

The hashes in the two historical review tables above remain immutable evidence
of what HY3 actually reviewed; they are not hashes for the current files. After
the full-map and agent-fleet reconciliation, the current visual evidence set is:

| Current input | SHA-256 |
|---|---|
| `docs/research/real-world-sdlc-operating-model-research-2026-07-27.md` | `aaee137e4a62c4ed965a2be8cbb28a63b428f9b8f6813560cfa2437464d4d572` |
| `docs/architecture/CORE_SDLC_OPERATING_MODEL.md` | `893b9fea76c15e6dce06ed5642ac3519ecc323d2cca203429b0b6fe95cd69980` |
| `docs/research/ranex-sdlc-visual-guide.html` | `56b9b074181b179f142d3ab0348180cf083433161b40b4cb5961eb511f931ffb` |
| `docs/research/ranex-sdlc-full-spec.svg` | `c85d0e0fb7ed92de7a37907c798081d6b66dff3b276e6d80a24465ba4aba7ce5` |

These current hashes supersede the old hashes only for identifying the present
subject. They do not rewrite either historical verdict. The final whole-map
review binds the current subject through its own source manifest; if any file
above changes afterward, that review is stale until a new manifest and review
are recorded.

## Capability scoring and improvement review

This section supersedes the stale “current exact-subject” hashes above for the
scoring and improvement subsystem only. It does not rewrite the two historical
visual-review verdicts.

### Independent challenge

| Field | Value |
|---|---|
| Review ID | `REV-SDLC-SCORING-HY3-001` |
| Completed | 2026-07-27T22:51:17+08:00 |
| OpenCode | `1.18.7` |
| Agent | Custom tool-less, read-only primary reviewer |
| Provider/model | OpenRouter / `tencent/hy3` |
| Variant | `high` |
| Session | `ses_05bf880e5ffezIoD1pLXliy6ED` |
| Repository mutations by HY3 | None |
| Initial verdict | `CHANGES_REQUIRED`; zero P0/P1 blockers, five P2 precision findings |

HY3 received the full normative policy, control catalog, and two YAML record
shapes. To keep the human guide and research review exact-subject, it received
only their scoring sections. It was not given the other reviewers’ conclusions.

| Initial input | Full-source SHA-256 | Submitted scope / SHA-256 |
|---|---|---|
| Research paper | `312d62d59fc69251e691fec8d0d4c60e4fb4b374b729014798717db097739981` | §8 extract / `a49027d4ecf092766b841a8d03ea74958098a6b7054ad6d702f938623f7442d8` |
| Core policy | `99909174388be82efd39f5549944688ad5ec2fb0e3422356785112b68f8551d8` | Full file |
| Control catalog | `f348b8eed1585b4bae3396b6a39b519335cb2ee73ea4c9140fb47c60e332c8e2` | Full file |
| Per-control assessment shape | `a371aa8a9a41524b134b04c2fde03c2f5516c8934e22a2206b8e94773318f57d` | Full file |
| Domain projection shape | `e2d49760529571de951f71edfbe68462fe4025b6cc31fc7a972f5277153bdc5e` | Full file |
| Static guide | `bd7186700d8a2c86f5d5f1c97e2f2ac4a92485692fec2f68cd0a643d1991b303` | Scorecard extract / `c2c406f73469652e03074b35b72870c094f98c922ce01ae10ff3a192fffa6947` |

HY3 passed anti-gaming, measurement, priority totality, and scorecard semantics,
but asked for five nonblocking precision corrections:

| Finding | Reconciliation |
|---|---|
| Define applicable-member and assessment-begun semantics | An applicable member now means applicability `APPLICABLE`; valid N/A remains visible but outside the floor; all-applicable `NOT_ASSESSED`, partial-start `UNKNOWN`, and all-applicable `SCORED` rules are explicit |
| Register the rubric version | Catalog, research, and both templates bind `SDLC-MEA-002` version `3.0.0` |
| Do not allow a material unknown inside `SCORED` | Any unresolved material gap now forces result `UNKNOWN`, no level, and confidence `LOW` |
| Name the seven checks in the human guide | The guide lists sample, duration, representativeness, authenticity, freshness, missingness, and data quality plus independent sign-off |
| Prevent authored coverage percentages | Coverage percentage is output-only, null in authored input, and derived from the bound population totals |

### Corrected reconciliation

| Field | Value |
|---|---|
| Review ID | `REV-SDLC-SCORING-HY3-002` |
| Completed | 2026-07-27T22:56:37+08:00 |
| Session | `ses_05bf880e5ffezIoD1pLXliy6ED` |
| Corrected verdict | **PASS — no P0/P1 blockers, no unresolved P2, no introduced blocker** |
| Repository mutations by HY3 | None |

| Corrected source | Full-source SHA-256 | Reconciliation scope / SHA-256 |
|---|---|---|
| Research paper | `aaee137e4a62c4ed965a2be8cbb28a63b428f9b8f6813560cfa2437464d4d572` | §8 extract / `abe8baaf13159e7abe461f0eda2f396a958ef644ea95f58a7877c922221591db` |
| Core policy | `893b9fea76c15e6dce06ed5642ac3519ecc323d2cca203429b0b6fe95cd69980` | Corrected §15 extract / `3ba1aa99b5520c428f5068f0d10db53ec3115b490e70b06aebfc108be39a74bb` |
| Control catalog | `4be44c12357cac07ce4189d3651a57550f02ccbce1c3cf257682f2a95d07f0c4` | Corrected `SDLC-MEA-002` extract / `a34d44f2bc83e82bd4feb78855d90e19d8a53b753ce4af36f3fe6dc385816c44` |
| Per-control assessment shape | `7abe5249d4bf9d7c406616d13f911087d69220f97ae6a4bc1a365a7e860a5fb3` | Full file |
| Domain projection shape | `8675ceaea9b3dbe9082c71ff1b7de487c09e391fb8d9ab07ca30fb5eab2192c2` | Full file |
| Static guide | `56b9b074181b179f142d3ab0348180cf083433161b40b4cb5961eb511f931ffb` | Scorecard extract / `828e8fb2e4f59cadabd70109c994b52cb069ee5233ec3409876e1de55ff706ee` |
| Rendered full-spec SVG | `c85d0e0fb7ed92de7a37907c798081d6b66dff3b276e6d80a24465ba4aba7ce5` | Not an HY3 scoring input; separately render-validated |

The corrected verdict is advisory evidence that the documented scoring
semantics are internally consistent. It does not prove Ranex has implemented
the process, passed adoption gates, calibrated its measures, completed an
external appraisal, or earned accessibility certification.

The first Mermaid block under the real-world report's full-spec diagram section
was rendered again with Mermaid CLI `11.12.0`; the regenerated SVG was
byte-identical to the retained SVG at the digest above. The semantic HTML
contains one state card for each of the sixteen canonical `WorkItemStatus`
values.
