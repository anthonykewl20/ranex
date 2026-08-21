# ADR-033 — kernel-owned delegated-provider credential broker

**Status:** proposed
**Date:** 2026-08-22
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-069-kernel-credential-broker.md` (opens after this ADR)

## Context and Problem Statement

Issue #43 records that delegated launch places an OpenRouter credential in the child boundary and permits `--auto`; issue #106 freezes the coordinated harness half. The harness must call a provider without receiving the raw key, while uncredentialed execution remains available. The boundary must be versioned, bounded, locally addressable, and testable without a provider call.

## Decision Drivers

- Raw provider material is kernel-only; the harness gets only a capability.
- Fixed endpoint and explicit policy prevent provider, model, redirect, and tool escape.
- Bounds must be exact, fail closed, and have stable machine-readable errors.
- The `provider_attempt` outcome and CLI events remain the observability surface.
- Compatibility must reject old credentialed harnesses without breaking keyless mode.

## Prior art

- Searched: GitHub code search and tagged source inspection for kubelet credential plugins, Envoy ext_authz, Docker credential helpers, AWS process credentials, and loopback HTTP brokers; tags were dereferenced with `git ls-remote` before fetching.
- Searched: Kubernetes `v1.31.0` and Envoy `v1.31.0` source paths, plus issue #43/#106's fixed protocol and error tables; no source was treated as authoritative for Ranex policy.
- Kubernetes credential-provider plugin v1.31.0: https://github.com/kubernetes/kubernetes/blob/e73bd2e33f000c5a2886771e712d6c90796a4873/pkg/credentialprovider/plugin/config.go
  Provenance: `v1.31.0` is an annotated tag object `e73bd2e33f000c5a2886771e712d6c90796a4873`, resolving to source commit `9edcffcde5595e8a5b1a35f88c421764e575afce`.
  Adopts versioned plugin configuration and explicit image/policy matching before invoking an external provider.
  License: Apache-2.0.
  Weakness: the mature implementation returns credentials to kubelet consumers and inherits process environment; it is a policy/caching pattern, not a secret-isolating broker.
  Vendored: docs/adr/prior-art/ADR-033/kubernetes-plugin-config.go blob:841d5b22123f0c4a5b08a1ed2d6ea4987fcedfa5
- Envoy ext_authz common interface v1.31.0: https://github.com/envoyproxy/envoy/blob/7b8baff1758f0a584dcc3cb657b5032000bcb3d7/source/extensions/filters/common/ext_authz/ext_authz.h
  Adopts a narrow authorization service boundary with explicit check result and response handling.
  License: Apache-2.0.
  Weakness: ext_authz is an authorization filter, not a secret broker; its service transport and failure-mode configuration can permit fail-open behavior, which this decision refuses.
  Vendored: docs/adr/prior-art/ADR-033/envoy-ext-authz.h blob:c639e8c3d49879767fd5bd5391467ad6b8a21f25
- Rejected: https://github.com/docker/docker-credential-helpers — its Get protocol returns the credential to the caller by design, so adopting it would reproduce the raw-secret exposure this ADR removes; its store abstraction also does not bind requests to a short-lived capability session.
- Rejected: https://github.com/aws/aws-sdk-go-v2 — process credentials are emitted as JSON on stdout and the command inherits environment/stdin, so the consumer can receive raw secrets and the endpoint/policy is not fixed to one broker session.

## Considered Options

1. Keep the key in the harness environment. Rejected: fails issue #43's isolation objective.
2. Use Docker or AWS process-credential protocols. Rejected: both return raw credentials to the consumer.
3. Use a remote or configurable proxy. Rejected: adds endpoint/redirect and persistence surfaces.
4. Kernel-owned loopback broker with a capability session. Chosen: preserves uncredentialed mode and bounds the credentialed path.

## Decision Outcome

In the context of credential-bearing delegated execution, facing an untrusted harness boundary, we choose a kernel-owned `ranex-delegated-provider` v1 broker on `127.0.0.1` with an ephemeral port, to keep the raw OpenRouter key out of the harness, accepting same-UID capability theft as a residual rather than claiming perfect privilege isolation.

The kernel reads the key from inherited file descriptor 3, a pipe available only at spawn, starts the broker, and passes only a 32-random-byte capability. The capability is prohibited from argv, environment, files, and logs. The harness performs `POST /v1/handshake`, then `POST /v1/chat/completions` as SSE. Upstream is exactly `https://openrouter.ai/api/v1/chat/completions`; proxies are ignored and redirects are refused.

The broker intentionally treats model SSE response structure as opaque and relays the upstream event bytes; it does not constrain `chatResponse.choices` or reinterpret model-specific fields. In `vectorSemantics`, handshake and version vectors use `response` for the literal wire body; chat vectors use `expected` for broker state observations and never for an SSE body. `remainingRequests` is broker session state returned by handshake/state accounting and is never carried in relayed SSE. Safety comes from the fixed upstream, policy checks, and byte/time limits (16 MiB response and 120-second timeout), not response-shape validation.

The wire transport must use the standard-library HTTP stack with standard TLS certificate and hostname verification; no custom TLS or SSE replacement is permitted. A separately owner-approved pinned, mature, license-compatible client may be substituted only after evidence, but this specification slice adds no dependency.

TTL is 300 seconds, maximum eight requests, concurrency one, request 4 MiB, response 16 MiB, and timeout 120 seconds. The harness never retries. Neither prompt nor output is persisted.

Schemas, vectors, and the complete stable error vocabulary are canonical in `governance/schemas/delegated-provider/ranex-delegated-provider-v1.json`; harness consumes pinned vectors and digests. The fixture records the pin location; the canonical digest is `tests/contract/test_delegated_provider_protocol.py`'s `EXPECTED_SHA256` and is not embedded self-referentially in the fixture.

The `schemas` block is structural validation only. Authoritative provider/model/tool enforcement and error ordering live in `validation` plus `policy` and MUST run before upstream. Validation is deterministic and fail-before-upstream: an unknown or unauthenticated session maps to `unauthorized`; a structurally valid active session presented with a different valid capability maps to `session_mismatch`; both retain constant-time capability comparison and disclose no session existence or capability details beyond these stable errors. A replayed request ID maps to `replay`; provider, model, and tool policy mismatches map to `provider_not_allowed`, `model_not_allowed`, and `tool_not_allowed`; structural failures in protocol shape, messages, stream, or request ID map to `invalid_request`. Size, protocol/version, expiry, concurrency/request limits, and terminal response/upstream/broker failures retain their named stable errors.

### Consequences

- Good: raw key is absent from harness args, environment, protocol bodies, artifacts, and logs.
- Good: exact bounds and fixed upstream make provider attempts finite and reviewable.
- Bad: same-UID code can steal a live capability; the capability limits spend but does not create privilege isolation.
- Bad: credentialed delegation is unavailable during broker shutdown or any refusal.
- No new journal record is added in v1: `provider_attempt` is the bounded outcome field introduced by SLICE-069; there is no `TaskProviderAttempt` record.
- The kernel broker is the sole authority for `provider_attempt` and the terminal delegation audit outcome. It emits both existing `cli.task.delegate.start` and `cli.task.delegate.end` events through the current emitter, using the literal schema fields `sid`, `code`, and `duration_us` (plus the schema's required null fields); the harness emits neither delegation audit event. An oversized response has canonical broker outcome `response_too_large`; a harness observation of the closed stream may be reported locally as `upstream_protocol` only and cannot become an authoritative provider-attempt outcome.

### Confirmation

The kernel tests must prove the FD/pipe boundary, constant-time capability comparison, exact limits, fixed URL, redirect refusal, SSE parsing, all stable errors, no persistence, no secret-bearing output, and old-harness refusal. The harness tests must prove it sends only the protocol capability and rejects direct credential/endpoint/`--auto` paths.

## Improvements on the prior art

1. Replace kubelet's credential-returning plugin result with a capability-only session; the key stays in the kernel.
2. Retain kubelet-style version and policy matching, but make provider and endpoint closed rather than configuration-selected.
3. Use Envoy's explicit check boundary while refusing its fail-open option and allowing no response mutation or credential return.
4. Add constant-time capability validation, one-use session state, TTL/request/concurrency/byte/time bounds, and redirect refusal.
5. Reuse the `provider_attempt` outcome and delegate event fields instead of adding a journal row or broker log stream.

## Architecture surface

Kernel: `src/ranex/cli/delegation.py`, `src/ranex/cli/credential_broker.py`, and the existing delegate outcome surface. SLICE-069's intended implementation lanes are `tests/unit/test_credential_broker.py` and `tests/security/test_credential_broker.py`; they are not part of this specification-only change. Harness consumption is the coordinated issue #106 surface; no harness code lands here. Contract artifact is the governance JSON named above. No dependency, manifest, or new observability schema changes.

## Scope and threat delta

Moves the raw-key trust boundary from harness process memory to the kernel broker and adds a loopback capability channel. STRIDE moves: spoofing/replay (capability/session checks), tampering (closed schemas and fixed upstream), disclosure (no raw key in harness; same-UID theft remains), denial of service (strict bounds). Non-goal: perfect isolation from code running as the same UID.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Confidentiality | inspect child args/env/body/artifacts | zero raw-key bytes |
| Security | replay, expiry, mismatch, wrong capability | stable refusal, zero upstream effect |
| Reliability | timeout, shutdown, oversized response | bounded completion within 120s, no retry |
| Interoperability | v1 handshake and SSE chat | pinned vectors and schema digest match |
| Auditability | successful and failed provider attempts | existing event fields only; no prompt/output persistence |

## Reversibility

Door: one-way

Disable credentialed delegated mode while preserving uncredentialed execution; never restore raw-key transport. Old credentialed harnesses refuse. Rollback is a feature flag/configuration removal followed by restart; changing v1 wire fields or errors requires a superseding ADR.

## Sad paths

Derived by equivalence partitions, boundary values, and protocol state transitions:

- 1. Missing or malformed handshake → `invalid_protocol` or `handshake_required`; no upstream call.
- 2. Unsupported version → `unsupported_version`; no downgrade.
- 3. Unknown/unauthenticated session → `unauthorized`; an active session under a different valid capability → `session_mismatch`; both use constant-time capability comparison and disclose no session existence or capability details beyond the stable error.
- 4. Reused session/request → `replay`; no duplicate upstream request.
- 5. Expired session → `expired`; no completion.
- 6. Wrong model/provider/tool → `model_not_allowed`, `provider_not_allowed`, or `tool_not_allowed`.
- 7. Request over 4 MiB or response over 16 MiB → size error and bounded cleanup.
- 8. Concurrent request or ninth request → `concurrency_limit` or `request_limit`.
- 9. Upstream timeout, HTTP failure, malformed SSE, or redirect → `upstream_timeout`, `upstream_http`, `upstream_protocol`, or `redirect_refused`; no retry.
- 10. Broker shutdown/internal failure → `server_shutdown` or `internal`; no secret log and no persistence.
- 11. Old credentialed harness or endpoint override → refuse and preserve uncredentialed mode.
- 12. Same-UID capability theft → bounded capability spend is the only mitigation; perfect privilege isolation is explicitly not claimed.

## Test strategy

Kernel paths: `tests/unit/test_delegation.py` covers the existing delegation boundary and no-secret assertions; `tests/integration/test_delegation_command.py` covers the existing loopback command boundary. `tests/contract/test_delegated_provider_protocol.py` freezes this artifact. Broker unit and security paths are opened by SLICE-069; harness paths use `packages/opencode` and are specified by issue #106.

`tests/contract/test_docs_discipline.py` verifies this ADR's sections, prior-art pins, vendored blob hashes, NOTICE, line budgets, sad-path count, and test paths. `tests/contract/test_delegated_provider_protocol.py` freezes the JSON artifact digest, exact vector IDs, constants, errors, validation precedence, transport/accounting, event authorship/fields, vector field semantics, and request/session/model/tool semantics before implementation; chat vectors assert expected broker state rather than SSE bodies. Red-first implementation tests are owned by SLICE-069, not this specification commit.

## Code review checklist

- Verify the raw key enters only the kernel FD/pipe and never the harness boundary.
- Verify capability is exactly 32 random bytes and comparison is constant-time.
- Verify URL, redirect, provider, model, tool, request, response, timeout, TTL, request, and concurrency bounds are closed and exact.
- Verify all issue #43/#106 stable errors are present and no fallback/retry exists.
- Verify no prompt/output persistence, independent broker raw logs, new journal record, or new telemetry schema.
- Verify old credentialed harness refusal and uncredentialed preservation.
- Verify vendored source files match their pinned commit URLs and NOTICE licenses.
- Verify same-UID theft is recorded as residual, not described as solved.

## More Information

Issue #43 is the kernel contract and issue #106 is the harness dependency. ADR-010 records the prior credential-bearing delegation residual; ADR-031 governs the existing event emitter. The protocol/schema/vector artifact is the canonical wire source; this ADR is the ownership decision. No secret location, credential value, exploit command, or private advisory identifier is recorded.
