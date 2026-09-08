# ADR-058 — Automatic judgment without executing contributor code

**Status:** accepted

Issue #88; opt-in.

## Problem

The GitHub receiver required an operator to evaluate a gate after an observer
produced evidence. A verdict that arrived late could be published automatically,
but fresh evidence itself could not complete the PR acceptance journey.

## Decision

`github listen --evaluate-evidence` invokes the installed kernel's existing
`gate evaluate` command for the exact fetched PR SHA. It does not invoke a
command from the PR, launch tests, or accept an unsigned verdict. The controller
requires an external verdict-signing key matching the committed signer.

The gate catalog, producer keyring and frozen test manifest are pinned in memory
from the operator checkout at startup. Each target commit must contain those
same bytes. A contributor cannot lower the test requirements, replace the
trusted producers, or choose a different command through webhook content.
Policy changes require operator review and an explicit receiver restart.

The evaluation subprocess receives a minimal environment, with no GitHub App
credentials, Git overrides or Python startup configuration. It uses the trusted
kernel location as its working directory. All domain evaluation, evidence
admission, signing, path confinement and journal writes remain canonical.

A durable per-subject receipt binds the evidence fingerprint, gate, approver and
policy. Unchanged inputs do not append repeated judgments. Absent evidence keeps
the existing action-required check; failed evidence keeps the head waiting.
Every 15 seconds the opt-in receiver checks for new evidence. Publication uses
a verdict-specific external ID and a durable completion receipt, so an API
failure or restart can recover without another successful check. The existing
300-second failed-delivery backoff remains in force. Publisher-only mode retains
its existing cadence and behavior.

## Evidence and limits

Integration tests execute a real external Python application's tests, generate
signed evidence and invoke the kernel subprocess. Receiver tests use real Git,
HTTP and signatures with a local GitHub API double; that is not live GitHub.
The retained live Six journey uses actual GitHub-origin webhook GUIDs, real
upstream test results, real checks and merge refusals. Observation is explicitly
performed by the test driver. It does not establish automatic, isolated
execution of arbitrary contributor code.

Live merge enforcement sometimes disagreed with the Checks API while a
deliberately forged same-name Actions check was queued. One later unchanged
retry succeeded, and a second fresh PR merged; a third pass remained blocked
beyond 120 seconds. Propagation alone is not established as the cause. The
driver retains failures and never relaxes the ruleset. Availability under this
foreign-check collision remains UNVERIFIED.

This feature does not implement merge-candidate evaluation, merge groups,
automatic observer scheduling, multi-tenant execution isolation, queue quotas,
credential rotation, or a production service deployment. It is one completed
integration boundary, not production sign-off for the whole product.

## Prior art

GitHub documents webhook acknowledgments within ten seconds and warns against
running untrusted PR code in privileged workflows:
https://docs.github.com/en/webhooks/using-webhooks/handling-webhook-deliveries
https://docs.github.com/en/actions/reference/security/secure-use

The installed smee-client 5.0.0 source (index.js, lines 38–70) was inspected
for body/header forwarding; it is an external development relay, not a Ranex
dependency. Six at Git commit c8e394065cd541a16c040515dc0afb85cf22a7c3
(MIT) supplies the real test subject in the probe repository. Leitir also
verified the six 1.17.0 sdist checksum
ff70335d468e7eb6ec65b95b99d3a2836546063f63acc5171de367e834932a81,
reporting registry/Git drift; that artifact is not claimed Git-identical and
is not imported or installed by Ranex. No target dependency changed.
