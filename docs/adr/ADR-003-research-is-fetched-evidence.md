# ADR-003 — research is evidence, and evidence must be fetched

**Status:** accepted
**Date:** 2026-08-02
**Decision-makers:** repo owner
**Slice:** none — this decision governs how every later slice is researched

## Context and Problem Statement

ADR-000 fixed the ADR format, and its research rule was one URL of any kind
inside `## Prior art`. A blog post satisfied it. A link to this repository
satisfied it. A 404 satisfied it. So "research first, invent last" was prose an
agent could comply with in appearance, in a project whose entire thesis is that a
rule an agent can read is a suggestion and a rule compiled into a check is a
constraint. The research rule was the one place that thesis was not applied to
itself.

The checker has since been tightened four times, each round closing a loophole a
review reproduced. ADR-000's template still describes the rule it had before any
of that, so the document defining the format now contradicts the check enforcing
it. This ADR states the rule that actually runs, and supersedes ADR-000's
research section — the rest of ADR-000 stands.

## Decision Drivers

- A citation is a shape an agent can invent. A file with a matching hash is one
  it had to obtain. The check must ask for the thing that cannot be guessed.
- Copying third-party source into an MIT repository is a licensing act, and no
  other test here would ever notice a GPL file arriving.
- Research must be efficient. Two implementations is a floor on rigour, not a
  reading quota; research that sprawls has stopped being useful.
- Whatever is claimed must be stated at exactly its strength. Overclaiming a
  control is the failure this repository exists to make expensive.

## Prior art

- **pip's hash-checking mode** — `Hashes.check_against_chunks` streams the bytes
  it just downloaded, and raises `HashMismatch` unless a declared digest matches;
  `MissingHashes` is a subclass constructed with an empty allow-list so it can
  *never* match, making "no hash was declared" a raise rather than a branch
  somebody forgets. Absence blocks, expressed as a type.
  <https://github.com/pypa/pip/blob/24.2/src/pip/_internal/utils/hashes.py>
  License: MIT — vendorable into this repository without restriction.
  Weakness: the digests come from the requirements file the user maintains, so
  pip proves the bytes match what was *declared*, never that the declaration was
  right. Trust is moved, not removed — which is exactly our residual risk, and
  the reason this ADR must not describe vendoring as proof of provenance.
  Vendored: docs/adr/prior-art/ADR-003/pip-hashes.py blob:535e94fca0cc8b049673ee0d02dba259c68af76c
- **Go's module checksum verification** — `checkModSum` accepts a module whose
  hash is already in `go.sum`, and otherwise consults an append-only transparency
  log before recording it, so a first sighting is corroborated by a party that is
  not the author. That second, independent source is the half pip does not have.
  <https://github.com/golang/go/blob/6885bad7dd86880be6929c02085e5c7a67ff2887/src/cmd/go/internal/modfetch/fetch.go>
  License: BSD-3-Clause — permissive, requires the notice to travel with the copy.
  Weakness: `checkSumDB` returns nil when the log lists no line for the module at
  all, so absence from the log is acceptance; `useSumDB` lets configuration switch
  the whole check off; and when the cached ziphash is malformed `checkMod`
  recomputes it from the cached zip and returns — the local cache answering the
  question about itself. Deliberately not copied: all three.
  Vendored: docs/adr/prior-art/ADR-003/go-modfetch-fetch.go blob:ad4eb8ecd25b483a79264624fa58a5471c14cd61

## Considered Options

1. **Leave ADR-000's research rule as written.** Rejected: the document defining
   the format would keep contradicting the check enforcing it, and the
   contradiction is load-bearing — an agent reads ADR-000 to learn what to write.
2. **Edit ADR-000 in place.** Rejected. ADRs are append-only here, and its
   research exemption is pinned to its exact bytes, so an edit silently lapses
   the exemption and demands a research retrofit of an accepted decision —
   manufacturing the fake compliance the rule exists to prevent.
3. **Require a networked verifier before accepting any citation.** Rejected for
   now: the suite is hermetic and offline by design, and a check that needs the
   network is a check that is skipped on the day the network is down.
4. **Supersede ADR-000's research section with this ADR.** Chosen.

## Decision Outcome

Chosen: option 4. `## Prior art` must carry at least two **distinct** pinned
citations to source files on a code host, each with its own `License:`,
`Weakness:` and `Vendored:` line, each vendored file fetched into this ADR's own
`docs/adr/prior-art/ADR-003/` directory, git-tracked, distinct in content, and
recorded with the blob hash git itself would give it. A `NOTICE.md` beside them
names every copied file with its origin and its licence.

ADR-000 is left byte-for-byte as it was accepted. Its template section is
superseded by this one; a reader who needs the operative rule finds it in
`CLAUDE.md` and in `tests/contract/test_docs_discipline.py`, which is where a
rule that must be obeyed belongs.

### Consequences

- Good: an ADR can no longer be written from memory. The bytes have to exist.
- Good: the licence of everything copied here is recorded before it is copied,
  in a repository whose licence a copyleft file would change.
- Good: naming the weakness of each implementation is now the price of citing
  it, so adopting a design without its caveats costs something.
- Bad: writing an ADR now requires network access at authoring time, and this
  repository's own suite cannot verify what that fetch returned.
- Bad: three existing ADRs are exempt, so the rule's first real subject is this
  document. A rule with one instance has not yet been stress-tested.

### Confirmation

`tests/contract/test_docs_discipline.py` enforces every clause above, and each
clause was mutation-checked: the control was removed, the covering test watched
go red, the control restored. The two loopholes closed most recently — a repeated
URL counting twice, and a branch URL carrying a 40-hex string in its query string
counting as pinned — were each reproduced against the checker before the fix, and
are pinned by self-tests that feed synthetic prior art through the same helper the
real-tree rule uses, so the rule and its test cannot drift apart.

## Improvements on the prior art

- pip verifies what it downloaded against a digest the *user* wrote. We verify a
  vendored file against a digest the ADR records, which is the same posture, and
  this ADR says so plainly instead of calling it provenance.
- We use git's own blob hash rather than a bare sha256, so the recorded value is
  the *same string* GitHub reports for that path at that commit. A reviewer can
  compare by eye, and a future networked verifier needs no new format.
- Go's checksum database is the design we have not adopted: an independent second
  witness. Ours is a single fetch by the same agent that writes the ADR, so an
  agent determined to lie can vendor a file it wrote itself. Recorded as a known
  limit rather than papered over, and it is what a networked verifier would fix.
- Absence blocks, taken from pip's `MissingHashes`: a citation with no vendored
  file is a named problem, not a skipped entry. Every check here reports its
  refusal by name rather than falling through quietly.
- Not copied from Go: configuration that can switch verification off, and
  treating absence from the record as acceptance. Both are how a check becomes
  decoration, which this repository refuses to ship.

## Architecture surface

`tests/contract/test_docs_discipline.py` reads the repository tree and shells out
to git; it imports nothing from `src/ranex/`. Vendored source lives under
`docs/adr/prior-art/ADR-NNN/` and is never imported, executed or linted — it is
evidence, not a dependency. No runtime code is touched by this decision, and the
kernel's verdict does not depend on any of it.

## Scope and threat delta

In scope: what an ADR must contain before it counts as researched. Out of scope:
whether the decision an ADR records is correct — that is review's job, and always
was. The threat this closes is an agent inventing plausible prior art it never
read. The threat it does not close is an agent that fetches nothing and vendors a
file it wrote itself, recording that file's true hash. That requires a second,
independent fetch of the cited URL, which a hermetic suite cannot perform.

## Quality attributes

- Determinism: every check is a pure function of bytes on disk plus git's own
  answers about what it tracks. No network, no model, no clock.
- Cost: the whole docs suite runs in well under a second, and research is capped
  at two implementations so the rule cannot become a reading quota.
- Diagnosability: every refusal names the file, the citation and what to do next.

## Reversibility

Door: two-way

The rule lives entirely in one test file and a paragraph of `CLAUDE.md`. Relaxing
it later costs one edit and a superseding ADR; the vendored files would then be
deleted along with the citations that claim them. Nothing in `src/` depends on
any of it.

## Sad paths

Derived by walking each clause and asking what an author who wants the badge
without the work would try next. Every row below was either reproduced against
the checker or is stated as uncaught.

| # | Input | Required behaviour |
|---|---|---|
| 1 | `## Prior art` citing specifications only | refuse — a spec says what someone intended, not what worked |
| 2 | code link on a branch, `/blob/main/f.py` | refuse, and name the unpinned link so the author knows which |
| 3 | branch link carrying a 40-hex string in its query or fragment | refuse — only the URL path can name the revision |
| 4 | the same pinned URL cited twice, or at `#L10` and `#L20` | refuse — one source file is one implementation |
| 5 | two citations, one vendored file between them | refuse — one fetch cannot stand in for two |
| 6 | `Vendored:` path escaping the repository via `../../..` | refuse at resolution — evidence outside the tree is not committed |
| 7 | `Vendored:` naming the directory's own `NOTICE.md` | refuse — vendoring the notice proves nothing was obtained |
| 8 | two vendored files that are byte-identical | refuse — two citations cannot rest on one text |
| 9 | vendored file on disk but untracked by git | refuse — a file absent from a fresh clone was reviewed by nobody |
| 10 | `Vendored:` line with a trailing note after the hash | reported as malformed, never as missing — the author mistyped, and must not be accused of skipping the work |
| 11 | citation vendored under a different ADR's directory | refuse — an ADR vouches for its own copies and no one else's |
| 12 | `NOTICE.md` naming a file and nothing else | refuse — a bare filename records neither origin nor licence |
| 13 | vendored bytes that never came from the cited URL | **not caught** — the trust boundary is the fetch, and closing it needs a networked verifier |
| 14 | a grandfathered ADR edited after the fact | exemption lapses by design — it is pinned to the bytes, not the filename |
| 15 | git unavailable, or the tree is not a repository | refuse — a check that skips when its oracle is missing is a hole an author can create |

## Test strategy

`tests/contract/test_docs_discipline.py` holds every check and its self-tests.
The real-tree tests judge the ADRs on disk; the self-tests feed synthetic
`## Prior art` text through the same helpers, so a loophole can be demonstrated
without writing a fake ADR into the repository. Each rule was verified by
mutation, not by a green suite: the control was deleted, the covering test
watched go red, and the control restored.

What is deliberately not tested here: that a vendored file came from its URL. No
offline test can establish it, and asserting it would be the overclaim this ADR
was partly written to remove.

## Code review checklist

- Does every citation name a *source file*, pinned in the URL path, not a
  repository root, a release page or a branch?
- Does each entry state a licence this repository may actually copy under?
- Is the stated weakness one you could only know by reading the code?
- Is each vendored file git-tracked, distinct, and under this ADR's directory?
- Does the `NOTICE.md` give each copy an origin and a licence?
- Does any sentence claim the vendoring proves provenance? Delete it.

## More Information

This ADR supersedes the research rule in ADR-000 only; the rest of ADR-000
stands, and its bytes are unchanged on purpose.

Recorded because the record is the point: commit `35f3b315f` edited ADR-000 in
place while introducing the rule that ADRs are append-only. Nothing was pushed,
so that commit could have been rewritten away. It was not. Erasing a rule
violation from the history is the same move this project exists to catch, and the
working tree restores ADR-000 to its accepted bytes by superseding it here
instead.
