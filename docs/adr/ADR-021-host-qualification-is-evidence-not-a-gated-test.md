# ADR-021 — host qualification is evidence, not a test the gate runs

**Status:** proposed
**Date:** 2026-08-11
**Decision-makers:** repo owner
**Slice:** planned, opens after SLICE-017 closes. ADR-006 keeps SLICE-018 and
SLICE-019; this decision governs how their host facts reach a verdict.

## Context and Problem Statement

SLICE-017's 47 qualification gates pass on the host and are absent from the run
that gates the repository. The landing gate runs the suite through `cmd_run`,
which materialises an ADR-009 sample and applies `_deny_network`
(`src/ranex/cli/main.py:1411`): `unshare(CLONE_NEWUSER | CLONE_NEWNET)` with no
uid map. The suite therefore runs at an unmapped euid, and `create_user_ns()`
returns `-EPERM` for a creator with no mapping in the parent namespace, so every
nested `unshare(CLONE_NEWUSER)` fails.

The conflict is not a defect on either side. These gates qualify the *physical
host* — `systemd-run --user`, cgroup-v2 delegation, the Landlock ABI, a pinned
compiler — and a hermetic sample exists to abstract the host away. Running a
host qualifier inside a host-abstracting sandbox is a category error, and every
attempt to paper over it has been refused, twice by the repository itself.

## Decision Drivers

- Absence must block. A qualification that never ran cannot read as satisfied.
- Evidence is bound to a subject digest; a fact gathered elsewhere proves
  nothing about this tree unless it says which tree and which host.
- The kernel decides. Whatever carries host facts must be judged by code.
- No control may be weakened to make the suite green.
- A qualified report must not outlive the host state that justified it.

## Prior art

**Searched:** GitHub code for host capability discovery published as consumable
records, and for verifiers that consume attestations bound to an artifact digest
rather than re-deriving the facts.
- **node-feature-discovery separates host discovery from consumption.** <https://github.com/kubernetes-sigs/node-feature-discovery/blob/76e6cc8cc0d54b8bce037098b72611ffdf66ef5a/source/kernel/kernel.go>
  License: Apache-2.0.
  Weakness: `Discover()` logs and continues on every probe failure, so a failed probe becomes an absent feature indistinguishable from a genuinely absent one; Ranex must refuse where NFD degrades.
  Vendored: docs/adr/prior-art/ADR-021/nfd-kernel-source.go blob:0de95ba9163b292ac5984a8cbcc1775cf2570f42
  Vendored: docs/adr/prior-art/ADR-021/LICENSE-NFD-APACHE-2.0.txt blob:d9a10c0d8e868ebf8da0b3dc95bb0be634c34bfe
- **slsa-verifier binds provenance to the artifact hash it describes.** <https://github.com/slsa-framework/slsa-verifier/blob/30d0be3bbab553fc51557377baba2f7572dfc212/verifiers/verifier.go>
  License: Apache-2.0.
  Weakness: it verifies what a trusted builder asserted and never re-derives the facts, so it cannot detect a report that outlived the state that justified it — ADR-006 sad path 21 exactly.
  Vendored: docs/adr/prior-art/ADR-021/slsa-verifier-verifier.go blob:79be0b52f622bd389981efe6cdc3c26aba0b96b5
  Vendored: docs/adr/prior-art/ADR-021/LICENSE-SLSA-VERIFIER-APACHE-2.0.txt blob:261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64
- Rejected: <https://github.com/systemd/systemd> `systemd-analyze` reports host
  capability facts in a mature, well-tested form. Its licence is
  LGPL-2.1-or-later, as its own README states — not the GPL-2.0 the code host's
  metadata reports — so it is readable prior art whose copyleft terms still
  govern derived works, and it stays a reference rather than code adapted into
  this MIT tree. It is rejected on substance: it reports for an operator to
  read, with no notion of binding a report to a subject digest, an approver, or
  a freshness anchor, which is the whole content of this decision.
- Rejected: <https://github.com/sigstore/cosign> attestation verification is the
  closest signed-evidence workflow, and it does verify offline —
  `--insecure-ignore-tlog` exists precisely for artifacts never sent to a log —
  so a transparency log is not the obstacle. It is rejected because ADR-019
  already vendors from it for the signing path, so a second citation adds no new
  evidence, and because it answers "is this signature valid for this artifact"
  and has no concept of the signed facts having gone stale, which is the failure
  this decision exists to catch.

## Considered Options

1. Keep the qualifier inside the gated suite and relax `_deny_network` so nested
   user namespaces work.
2. Exclude the qualifier from the gated suite, by a skip in the files or an
   `--ignore` in the bound command.
3. Qualification runs as its own governed step and emits a signed report; the
   landing gate consumes that report as evidence bound to the subject digest and
   to recorded host state.

## Decision Outcome

Option 3. Qualification becomes a producer of evidence, not a test the gated
suite executes. The report already exists as an artifact
(`.local/ranex/qualification/strict-local-v1.json`) and already binds the host
facts SLICE-017 records, including LSM state, userns sysctls, boot id and
machine id. What is missing is a claim that requires it, and a kernel rule that
refuses when it is absent, unbound, stale or self-approved.

Options 1 and 2 are refused on evidence, not preference. Option 1 hands the
untrusted bound command nested-userns creation, which is the kernel attack
surface `kernel.apparmor_restrict_unprivileged_userns` exists to block; two
independent reviewers were asked to refute that and both upheld it, and both
confirmed `PR_SET_NO_NEW_PRIVS` does not prevent `unshare(CLONE_NEWUSER)`.
Option 2 was implemented and reverted: `TESTS_EXECUTED` also fails by the bound
command's exit code, which is the only path that made a host run catch a
qualification regression, so excluding the files weakened the landing gate.

### Consequences

- Good: the qualifier runs where its facts are true, and the gate still refuses
  without it, because a required claim with no satisfying evidence is FAIL.
- Good: the report becomes reviewable and re-verifiable independently of the
  suite that produced it, and a stale one is detectable rather than assumed.
- Bad: a second claim is a second thing an operator must run, and a second thing
  that can be forgotten; the gate must therefore refuse loudly on its absence.
- Bad: qualification and its consumer can drift in schema. The report's digest
  is bound into the claim so drift is a refusal, not a silent mismatch.
- Neutral: SLICE-017's 47 gates keep their present shape and keep running on the
  host; this changes who consumes their result, not what they assert.

### Confirmation

A gate whose qualification claim is unsatisfied refuses. A report bound to a
different subject digest, a different boot id, or a different LSM/userns host
state refuses. A report approved by whoever produced it refuses. A host whose
anchors change between gate PASS and launch refuses at the launcher, proven by
changing one anchor in that window rather than by deleting a field. Each is a test
in `tests/security/` or `tests/e2e/`, run with every model credential removed.
No outside panel has read this ADR; the OpenRouter MCP is reachable and the
review is pending, and this line stands rather than implying consensus.

## Improvements on the prior art

1. NFD's `Discover()` degrades on probe failure; the qualifier refuses. A fact
   that could not be read is not a fact that is absent, and neither is a pass.
2. slsa-verifier trusts the builder's assertion of facts it never re-derives.
   Ranex binds host state into the report and re-reads the cheap, decisive parts
   — boot id, machine id, LSM state, userns sysctls — at admission, so a report
   that outlived its host is refused rather than believed.
3. Neither separates the producer from the approver. Ranex already refuses
   self-approval, and qualification inherits that: the party that ran the probes
   cannot be the party that admits their result.
4. Both publish for a scheduler or a release pipeline that is free to ignore
   them. Here the consumer is a blocking gate, and a gate that cannot block is
   refused at construction.
5. Admission is not launch, and neither prior art distinguishes them. A gate
   PASS says the host qualified when the verdict was reached; it cannot speak
   for the moment work starts. The process that confines therefore re-reads the
   freshness anchors immediately before it launches anything, and refuses there
   on its own authority. This host reset its userns sysctl on a reboot during
   this slice, so that window is measured rather than imagined.

## Architecture surface

A qualification claim in `governance/gates.yaml` naming the report as its
artifact; a reader validating it against its closed schema and the subject
digest; a kernel rule refusing on absence, mismatch, stale state or
self-approval. No new process, no network, no model. The report's facts split
in two and only one half can anchor freshness: durable properties — kernel
release, Landlock ABI, LSM state, userns sysctls, machine and boot id,
parent-namespace uid/gid — are re-readable later, while capability
demonstrations prove delegation *could* be obtained, never which cgroup. The
launcher therefore re-acquires, holds that delegation by descriptor for the
worker's whole lifetime, and enrols the worker in the subtree it demonstrated.

## Scope and threat delta

In scope: a stale, forged, borrowed or self-approved qualification report, and a
report describing a host other than the one about to run work. Out of scope:
the confinement the report describes, which is ADR-006's; kernel compromise and
host-admin compromise, which remain out of scope everywhere.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Integrity | report edited after signing | digest mismatch refuses |
| Freshness | host rebooted or LSM policy changed | bound host state mismatch refuses |
| Auditability | who qualified this host, and when | report names producer, approver, host |
| Determinism | credentials removed from the machine | identical verdict |

## Reversibility

Door: two-way

The claim can be dropped and the qualifier returned to the suite without
rewriting the kernel, since the report is an artifact either way. What is not
reversible is weakening `_deny_network` to make the old arrangement work.

## Sad paths

| # | Input | Required behaviour |
|---|---|---|
| 1 | qualification report absent | claim unsatisfied; gate FAIL, never a skip |
| 2 | report present but names a different subject digest | refuse; evidence is not about this tree |
| 3 | report's boot id differs from the running host | refuse; re-qualification required |
| 4 | machine id differs from the recorded one | refuse; this is a different host |
| 5 | LSM state or AppArmor/SELinux policy identity changed | refuse; ADR-006 sad path 21 |
| 6 | unprivileged-userns sysctls changed since qualification | refuse; the profile no longer holds |
| 7 | the durable half of delegation identity — parent-namespace uid/gid — changed | refuse; a different principal was qualified |
| 7b | brokered report's recorded cgroup path is gone, because `--collect` removed the transient unit | never an anchor and never a refusal on that ground; re-acquire and re-demonstrate instead |
| 7c | delegation cannot be re-acquired at launch though the report says it was obtained | refuse the launch; the report attests a past capability, not a present one |
| 7d | the demonstrated delegation is not the subtree the worker is enrolled into | refuse; a demonstration bound to no worker proves nothing about that worker |
| 7e | the held delegation descriptor stops being valid during the worker's lifetime | kill the whole cgroup and refuse the result; never re-resolve the path to recover |
| 8 | report approved by the identity that produced it | refuse; no self-approval |
| 9 | report is well-formed but schema version is unknown | refuse; never partially interpret |
| 10 | report bytes do not match their recorded digest | refuse; no repair, no re-canonicalisation |
| 11 | two reports present, one stale | refuse ambiguity; do not prefer the newer |
| 12 | qualifier exits non-zero yet leaves a report | refuse; a partial report is not a report |
| 13 | report readable but a required host fact is absent | refuse; absence blocks |
| 14 | operator forgets to run qualification entirely | identical to row 1; the gate says which claim |
| 15 | host state changes between gate PASS and the confined launch | launcher re-reads the anchors and refuses; admission alone never authorises a launch |
| 16 | launcher cannot read an anchor at launch time | refuse the launch; an unreadable anchor is not an unchanged one |

## Test strategy

Every row above is a test, and none may be satisfied by a mock. Rows 3–7 need a
real change of host state between qualification and admission, not a deleted
field: deleting a fact-key proves the reader reads a key, while masking the
state proves the check defends the host. Rows 8 and 11 are pure kernel tests and
belong beside `tests/contract/test_kernel_unchanged.py`. Row 1 is the honest
first failure and is asserted before any qualified report exists, so the FAIL is
observed rather than assumed.

`tests/e2e/test_gating_real_suite.py` gains the journey: qualify, approve,
gate PASS; then change one bound host fact and observe FAIL naming the claim.
`tests/security/test_slice017_host_qualification.py` keeps its 47 gates
unchanged and keeps running on the host — this decision changes who consumes
their result, not what they assert. Red-then-green: the qualification claim must
refuse before the reader exists.

## Code review checklist

- Does an absent report FAIL, rather than skip or default?
- Is the report bound to the subject digest, and is that binding asserted?
- Is stale host state a refusal, proven by masking state rather than deleting a
  key from the report?
- Can the producer of a report approve it?
- Does any read error, unknown schema or partial file select a weaker path?
- Does the process that confines re-read the freshness anchors immediately
  before launch, rather than trusting the gate's earlier PASS?
- Does the kernel still reach the same verdict with no credentials present?

## More Information

ADR-006 owns the confinement these facts describe and keeps SLICE-018 and
SLICE-019. ADR-009 owns the materialised sample whose hermeticity created the
conflict. ADR-011 owns "a skip is absence", which is why exclusion was refused
rather than adopted. The measured cause, the two refused routes and the reviewer
verdicts are in `docs/STATE.md` and in commits `ee3470de8`, `94d3a8039` and
`0cf81f0de`.
