# ADR-026 — real subject bootstrap

**Status:** accepted
**Date:** 2026-08-16
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-035-real-subject-bootstrap.md`

## Context and Problem Statement

SLICE-044 needs two real, pin-bound provider subjects without granting a worker
the controller's GitHub authority. Ranex is public; Arxic is an operator-owned
subject whose bootstrap must use an existing controller credential profile.
The controller must prove facts, run no credential-bearing worker, and leave no
clone when any security assertion is doubtful.

## Decision Drivers

- Bind repository, commit, issue, license, lockfile, and commands in versioned JSON.
- Use one exact, process-local Git credential helper for both Arxic network calls.
- Never persist, print, or pass authentication to the yielded object store.
- Refuse predictably on host, identity, dependency, process, and cleanup drift.
- Keep real process evidence optional on an unqualified host, never synthetic.

## Prior art

- Searched: GitHub code search for `gh auth git-credential` helper protocol and
  nonpersisting Git credential helper implementations.
- Searched: GitHub code search for checkout credential cleanup, temporary Git
  configuration, and token-safe process logging.
- [GitHub CLI `helper.go` at commit 0eeec0b92edbe70199f9768522f831d3534f41ad](https://github.com/cli/cli/blob/0eeec0b92edbe70199f9768522f831d3534f41ad/pkg/cmd/auth/gitcredential/helper.go)
  implements the `git credential` protocol and deliberately makes `store` and
  `erase` no-ops.
  License: MIT, verified from LICENSE blob at the cited commit.
  Weakness: its successful `get` writes a password to stdout, so this broker
  must never invoke it directly or capture its protocol output.
  Vendored: docs/adr/prior-art/ADR-026/gh-gitcredential-helper.go blob:9b64f74b9986ef0f9d5637666a52213580b76d4d
- [actions/checkout `git-auth-helper.ts` at commit f548e57e544e1ff5a4c46bf1e1b8685f8e4a348a](https://github.com/actions/checkout/blob/f548e57e544e1ff5a4c46bf1e1b8685f8e4a348a/src/git-auth-helper.ts)
  isolates temporary global configuration and removes token configuration during
  cleanup rather than adding it to the checked-out repository.
  License: MIT, verified from LICENSE blob at the cited commit.
  Weakness: it intentionally writes a token-bearing credentials config for CI,
  which is forbidden for this controller-only broker.
  Vendored: docs/adr/prior-art/ADR-026/actions-checkout-git-auth-helper.ts blob:dd7e6fbdb5387908190676a6ec9c4a828a044dea
- Rejected: https://github.com/cli/cli/tree/trunk/pkg/cmd/repo/clone
  because `gh repo clone` is a higher-level clone path and cannot prove the
  required identical explicit helper argv for preflight and clone.
- Rejected: https://github.com/actions/checkout/tree/main/src
  as implementation because its credential config file deliberately persists
  token material for a job, violating the no-copy boundary here.

## Considered Options

1. Process-local `gh auth git-credential` plus fail-closed inspection: chosen.
2. `gh repo clone`: rejected; its helper and persistence cannot be pinned here.
3. Credential-bearing HTTPS URL or Git config: rejected; it copies secret bytes.
4. Public anonymous clone for Arxic: rejected; it does not prove broker access.

## Decision Outcome

Versioned subject JSON describes exact immutable inputs. The broker recognizes
only `github:anthonykewl20/arxic-read`, verifies the existing `gh` keyring
profile, runs the exact view/preflight/clone commands with the same helper,
inspects a no-checkout clone, and yields a credential-free object store only
after every check. Any doubt removes the temporary directory and returns a
stable BLOCKED reason.

### Consequences

- A missing `/usr/bin/gh` blocks Arxic even if an anonymous public clone works.
- The controller does not reconfigure Git or GitHub globally.
- Real public Ranex bootstrap can produce process evidence independently.
- Host skips are explicit evidence limits, not successful provider runs.
- The credential scan is shape-heuristic: as the reviewer noted, it cannot
  detect a novel keyless token form.

### Confirmation

`tests/e2e/test_specification_subject_bootstrap.py` freezes manifest parsing,
negative refusals (including missing helper and helper mismatch), exact helper
identity, credential hygiene, and cleanup. It host-gates both
`test_real_ranex_bootstrap_or_host_skip` and
`test_real_arxic_bootstrap_or_host_skip`; the latter uses the real broker and
records its actual stable BLOCKED outcome after cleanup when the host cannot
satisfy it.

## Improvements on the prior art

1. Unlike GitHub CLI's protocol endpoint, no code captures its credential output.
2. Unlike actions/checkout, no token is written to a temporary configuration file.
3. The same explicit helper argv is asserted for both network operations.
4. Cleanup failure is a refusal, not a best-effort warning.

## Architecture surface

Only `tests/e2e/specification/subjects.py`, its two JSON manifests, and its
e2e tests own this controller-side evidence. No product, harness, or subject
source path changes.

## Scope and threat delta

This reduces accidental authority propagation in subject bootstrap. It does not
make a same-UID controller secret-proof, turn Arxic into a public reproducible
subject, or authorize provider mutation.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| confidentiality | credential helper | no secret in result, config, URL, or log |
| integrity | moved pin or issue | stable BLOCKED refusal |
| cleanup | repeated broker use | no temporary subject survivor |

## Reversibility

Door: two-way

The fixtures and controller-only helper can be replaced through a new pinned
ADR. Credential copies, global helper mutation, and anonymous substitution are
not acceptable rollback paths.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 1 | unknown credential reference | BLOCKED credential-ref-unavailable |
| 2 | no keyring-backed active profile | BLOCKED credential-ref-unavailable |
| 3 | `/usr/bin/gh` absent | BLOCKED helper-unavailable |
| 4 | repo view differs or is private | BLOCKED repository-identity-drift |
| 5 | preflight or clone fails | BLOCKED remote-preflight-failed |
| 6 | helper differs between commands | BLOCKED helper-mismatch |
| 7 | pin, issue, license, or lock differs | stable subject-fact refusal |
| 8 | URL, config, or log contains credential material | BLOCKED credential-copy-detected |
| 9 | unpinned pnpm command | BLOCKED package-manager-unpinned |
| 10 | dependency/process failure | BLOCKED process-failed |
| 11 | cleanup cannot remove a clone | BLOCKED cleanup-failed |

## Test strategy

`tests/e2e/test_specification_subject_bootstrap.py` uses local fixtures and
command fakes for wrong checkout facts, absent license, lock drift, missing
credential reference or helper, helper mismatch, credential-shaped copies, and
cleanup. Those controls run without GitHub access. Host-qualified runs clone
pinned Ranex, execute `uv sync --frozen` and its declared tests; Arxic runs
the real broker and records a stable BLOCKED outcome when the host cannot
satisfy it. Every child uses the same credential-scrubbed environment,
`DEVNULL` stdin, closed file descriptors, and captured output.

## Code review checklist

- Is `/usr/bin/gh auth git-credential` byte-identical in both Git argv lists?
- Are global Git config and all auth environment variables absent from children?
- Does every exception sanitize diagnostics and remove the temporary directory?
- Are clone config, URL, logs, and returned evidence credential-free?
- Are package-manager versions and commands pinned exactly?
- Do all local negative controls run without a real credential?

## More Information

Vendored bytes prove bytes were obtained, not their upstream origin. The
credential reference is an identifier only; it is never resolved to bytes in
test evidence. Arxic issue #109 remains a maintainer test/measurement gap
using actual Express/Playwright processes, not a production-app defect.
