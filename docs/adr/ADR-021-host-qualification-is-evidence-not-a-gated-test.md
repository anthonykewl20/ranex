# ADR-021 — host qualification is evidence, not a test the gate runs

**Status:** accepted
**Date:** 2026-08-11
**Decision-makers:** repo owner
**Slice:** SLICE-019, which ADR-006 already gives "`cmd_run` integration,
evidence field binding, signer refusal". It cannot land in SLICE-017: the claim
needs `governance/gates.yaml` and the refusal rule needs the verdict kernel,
neither of which is among that slice's six owned paths, the kernel is named out
of scope there, and its frozen gate 10 requires the kernel byte-exact. It is
not a slice of its own: SLICE-017 currently holds the one-open-slice budget, and
the integration belongs to SLICE-019 after that budget clears. ADR-006 keeps
SLICE-018. **This decision does not close SLICE-017** — see Consequences.

## Context and Problem Statement

SLICE-017's 47 qualification gates pass on the host and are absent from the run
that gates the repository. Under `_deny_network`, qualification first calls
`_validate_profile_and_objects()` (`host_confinement.py:2466`) before any cgroup
or broker work. It opens the launcher through `_open_verified` with
`exact_mode=0o555` and `required_owner=os.geteuid()` (`:2323-2329`).

The exact-mode branch skips `_require_trusted_owner_and_mode`; the measured first
refusal is instead `E-C17-EXEC-OBJECT-DRIFT` at `:331-332`: the unmapped
namespace reports euid 65534 while the launcher retains its host uid.
`_current_cgroup_root()` and broker/delegation logic are never reached. The gate
therefore needs host qualification as separately consumed evidence rather than
pretending this suite run qualified the host.

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
  Weakness: `VerifyImage`/`VerifyArtifact` select a verifier by builder ID and delegate entirely (`verifier.go:16-37, 44-63`); provenance is consumed as the builder asserted it, and nothing in this dispatch re-derives the build facts or checks they still describe a live host — ADR-006 sad path 21 exactly.
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
machine id. **Absence does not block today**: `gates.yaml` requires only
`tests-executed`, so an unqualified host can pass. This decision adds the
qualification claim and kernel rule in SLICE-019; only then will absence refuse.

Options 1 and 2 are refused on evidence, not preference. Option 1 hands the
same `_open_verified` launcher-owner mismatch before `_current_cgroup_root` or
the broker. Option 2 was implemented and reverted: `TESTS_EXECUTED` also fails
by the bound command's exit code, so excluding the files weakened that gate.

### Consequences

- Good: once SLICE-019 adds the required claim, the qualifier runs where its
  facts are true and its absence blocks. That protection does not exist today.
- Good: the report becomes reviewable and re-verifiable independently of the
  suite that produced it, and a stale one is detectable rather than assumed.
- Bad: a second claim is a second thing an operator must run, and a second thing
  that can be forgotten; the gate must therefore refuse loudly on its absence.
- Bad: qualification and its consumer can drift in schema. Signed digest binding
  is a required SLICE-019 envelope dependency, not a control present today.
- Neutral: SLICE-017's 47 gates keep their present shape and keep running on the
  host; this changes who consumes their result, not what they assert.
- Resolved 2026-08-12: SLICE-017 closed on its green QA gate and was archived;
  the open question this bullet posed is answered.

### Confirmation

The independent consensus panel (`consensus-luna` + `consensus-terra`) returned
APPROVE on 2026-08-12 after the prior-art corrections in `69fd9db12f`.
The signed producer/approver envelope bound to the subject digest remained a
required, explicitly deferred SLICE-019 dependency, to be specified by that
slice rather than claimed as a present control. Tests run without model
credentials.

## Improvements on the prior art

1. NFD's `Discover()` degrades on probe failure; the qualifier refuses. A fact
   that could not be read is not a fact that is absent, and neither is a pass.
2. slsa-verifier trusts the builder's assertion of facts it never re-derives.
   Ranex binds host state into the report and re-reads the cheap, decisive parts
   — boot id, machine id, LSM state, userns sysctls — at admission, so a report
   that outlived its host is refused rather than believed.
3. Neither separates the producer from the approver. Qualification needs that
   property, but its signed subject-bound envelope is deferred to SLICE-019.
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

A qualification claim names the report; a reader validates its closed schema; the kernel refuses
on absence or stale host state. Signed producer/approver and subject binding is a
SLICE-019 dependency whose envelope is not specified by this ADR. No network or
model. The report's facts split in two; only durable properties anchor freshness:
kernel
release, Landlock ABI, LSM state, userns sysctls, machine and boot id,
parent-namespace uid/gid — are re-readable later, while capability
demonstrations prove delegation *could* be obtained, never which cgroup. The
launcher re-acquires and holds delegation by descriptor for the worker's whole
lifetime, enrolling it in the subtree demonstrated.

## Scope and threat delta

In scope: absent qualification and a stale report describing host state other
than the host about to run work. Forged, borrowed, digest-mismatched and
self-approved reports are deferred to SLICE-019's required signed
producer/approver envelope bound to the subject digest, not specified here. Also
out of scope: ADR-006 confinement, kernel compromise and host-admin compromise.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Integrity | host fact differs at consumption | stale-state mismatch refuses after SLICE-019 |
| Freshness | host rebooted or LSM policy changed | bound host state mismatch refuses |
| Auditability | which host facts were qualified | report records the facts |
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
| 3 | report's boot id differs from the running host | refuse; re-qualification required |
| 4 | machine id differs from the recorded one | refuse; this is a different host |
| 5 | LSM state or AppArmor/SELinux policy identity changed | refuse; ADR-006 sad path 21 |
| 6 | unprivileged-userns sysctls changed since qualification | refuse; the profile no longer holds |
| 7 | the durable half of delegation identity — parent-namespace uid/gid — changed | refuse; a different principal was qualified |
| 7b | brokered report's recorded cgroup path is gone, because `--collect` removed the transient unit | never an anchor and never a refusal on that ground; re-acquire and re-demonstrate instead |
| 7c | delegation cannot be re-acquired at launch though the report says it was obtained | refuse the launch; the report attests a past capability, not a present one |
| 7d | the demonstrated delegation is not the subtree the worker is enrolled into | refuse; a demonstration bound to no worker proves nothing about that worker |
| 7e | the held delegation descriptor stops being valid during the worker's lifetime | kill the whole cgroup and refuse the result; never re-resolve the path to recover |
| 9 | report is well-formed but schema version is unknown | refuse; never partially interpret |
| 11 | two reports present, one stale | refuse ambiguity; do not prefer the newer |
| 13 | report readable but a required host fact is absent | refuse; absence blocks |
| 15 | host state changes between gate PASS and the confined launch | launcher re-reads the anchors and refuses; admission alone never authorises a launch |
| 16 | launcher cannot read an anchor at launch time | refuse the launch; an unreadable anchor is not an unchanged one |

## Test strategy

Rows 3–7 require a disposable-VM harness with privileged host-state mutation:
reboot/boot-id, machine-id, LSM policy, sysctl and namespace-principal changes.
Existing namespace/mount masking is a simulated view, not those transitions;
without that VM these rows are manual evidence, not automated PASS claims. Rows
1 and 11 are kernel tests beside `tests/contract/test_kernel_unchanged.py`; row 1
is the single absent-report observable (the duplicate operator-forgot row was
removed). Rows 9 and 13 exercise malformed or incomplete local reports.

`tests/e2e/test_gating_real_suite.py` gains the journey: qualify, approve,
gate PASS; then change one bound host fact and observe FAIL naming the claim.
`tests/security/test_slice017_host_qualification.py` keeps its 47 gates
unchanged and keeps running on the host — this decision changes who consumes
their result, not what they assert. Red-then-green: the qualification claim must
refuse before the reader exists.

## Code review checklist

- Does an absent report FAIL, rather than skip or default?
- Are subject binding and producer/approver separation explicit SLICE-019
  envelope dependencies rather than controls claimed by this ADR?
- Is stale host state a refusal, proven by masking state rather than deleting a
  key from the report?
- Does any read error, unknown schema or partial file select a weaker path?
- Does the process that confines re-read the freshness anchors immediately
  before launch, rather than trusting the gate's earlier PASS?
- Does the kernel still reach the same verdict with no credentials present?

## More Information

ADR-006 owns the confinement these facts describe and keeps SLICE-018 and
SLICE-019. ADR-009 owns the materialised sample whose hermeticity created the
conflict. ADR-011 owns "a skip is absence", which is why exclusion was refused
rather than adopted. Historical attempts are in commits `ee3470de8`, `94d3a8039`
and `0cf81f0de`; `docs/STATE.md` still needs its stale refusal account corrected.
