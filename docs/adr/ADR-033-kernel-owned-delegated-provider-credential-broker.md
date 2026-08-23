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
- The delegation provider-attempt stage and CLI events remain the observability surface.
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

In the context of credential-bearing delegated execution, facing an untrusted harness boundary, we choose a kernel-owned `ranex-delegated-provider` v1 broker on `127.0.0.1` with an ephemeral port, to provide accidental secret non-propagation and credential hygiene across the harness process boundary. This is explicitly not isolation against an adversarial same-UID harness.

The raw `OPENROUTER_API_KEY` reaches the kernel only through an inherited FD/pipe owned by the kernel process and remains in kernel/broker memory. It never enters the harness process, argv, bootstrap, file, log, or request body. The kernel reads and closes that ingress FD before creating an in-process broker bound only to `127.0.0.1` on an ephemeral port. It then creates a distinct child pipe carrying capability bootstrap only; its read end is mapped to harness FD 3. FD number 3 is reused across process boundaries, never the same bytes. The bootstrap endpoint is the exact object `{scheme:"http",host:"127.0.0.1",port:<integer 1..65535>}` with no additional properties; the kernel substitutes the OS-assigned port after bind, and the harness accepts only that exact loopback/http/range shape and constructs the URL deterministically. No endpoint environment variable or other out-of-band channel exists. Both pipes use `pipe2(O_CLOEXEC)`; the kernel closes its ingress and the child-pipe source/original and unrelated descriptors using the verified close-all strategy before `setsid`. Bootstrap and every handshake request/response carry the same non-self-referential `protocolFingerprint`: SHA-256 of canonical UTF-8 JSON for exactly `{protocol, schemas}`, with lexicographically sorted object keys, array order preserved, no insignificant whitespace, and no ASCII escaping; `protocolFingerprint`, `vectors`, and the artifact SHA are excluded from that input. A mismatch is `unsupported_version` before upstream.

The child FD 3 carries one bounded canonical JSON bootstrap object of at most 65,536 bytes, never the raw key: protocol/version, task ID, loopback endpoint, random capability, `provider=openrouter`, exact model, sorted unique allowed tool names (at most 32), expiry, and exact limits. The harness reads and validates it at its earliest entrypoint, closes FD 3 immediately after the bounded read and before command/session/model/children creation, then sends an authenticated handshake. Any harness with an absent, malformed, or unsupported FD3 bootstrap, a non-FD3 bootstrap, or no authenticated handshake within five seconds is terminated/refused as `invalid_protocol` or `unsupported_version` before any upstream call; there is no raw-key fallback or legacy CLI path. New invocations require `--delegated-provider-fd 3` and take the model from the bootstrap. The harness cannot override the immutable grant.

The raw-key residency and prohibition statements above hold under non-adversarial broker dataflow (see `protocol.security.sameUidResidual`); they do not claim containment against same-UID process-memory inspection.

The grant is generated once from task/run inputs. Provider is exactly `openrouter`; model is an exact case-sensitive value matching `[A-Za-z0-9._:/-]{1,256}`; tool function names are exact case-sensitive values matching `[A-Za-z0-9_-]{1,64}`, sorted uniquely by UTF-8 byte order. Duplicate incoming tool names are `invalid_request`; an omitted chat provider uses the authenticated session provider, while a present chat provider must equal that session provider; chat model must equal the grant and chat tools must be a subset.

The broker's 64 pending unauthenticated connections can still be occupied by a local process for up to the read deadline, denying legitimate harness admission; this bounded local availability residual is owner-accepted, while the provider slot is never consumed.

The harness performs `POST /v1/handshake`, then `POST /v1/chat/completions` as SSE. Upstream is exactly `https://openrouter.ai/api/v1/chat/completions`, POST with `stream:true`; the broker uses a direct stdlib `HTTPSConnection` to `openrouter.ai:443`, normal certificate and hostname verification, debuglevel 0, no tunnel, proxy, endpoint, transport, TLS, or debug configuration, and constructs `Authorization` internally. The harness cannot supply or forward Authorization or custom headers. Redirects are refused, status must be 200, and media type must be `text/event-stream` (parameters allowed). Bootstrap, handshake request/response, and chat request carry the pinned fingerprint. Each peer MUST compare a received fingerprint against its own pinned expected fingerprint and fail closed as `unsupported_version` on mismatch; presence or echoing alone is non-conforming. The handshake fingerprint pins the subsequent opaque SSE stream; the chat response has no fingerprint field.

The broker intentionally treats model SSE response structure as opaque and relays the upstream event bytes; it does not constrain `chatResponse.choices` or reinterpret model-specific fields. In `vectorSemantics`, handshake and version vectors use `response` for the literal wire body; chat vectors use `expected` for broker state observations and never for an SSE body. `remainingRequests` is broker session state returned by handshake/state accounting and is never carried in relayed SSE. Safety comes from the fixed upstream, policy checks, and byte/time limits (16 MiB response and 120-second timeout), not response-shape validation.

The wire transport uses Python standard-library `http.client` with standard TLS certificate and hostname verification; no custom HTTP or TLS replacement is permitted. HTTP admission is separately bounded before authentication or provider-slot reservation: maximum aggregate header bytes 16,384, maximum 100 header fields, maximum request-line bytes 8,192, maximum 64 pending unauthenticated connections, and a five-second unauthenticated header/body read deadline. A bounded non-blocking accept loop refuses further accepts while 64 unauthenticated connections are pending. Admission rejects with 413 any declared `Content-Length` above `maxRequestBytes`, avoiding allocation or reading of oversized unauthenticated requests. Requests with bodies require one unambiguous `Content-Length`; `Transfer-Encoding`/chunked, `Content-Length` plus `Transfer-Encoding`, duplicate `Content-Length`, and conflicting `Content-Length` values are refused. JSON parsing rejects duplicate keys. A bounded parser and socket deadlines enforce these values rather than relying on undocumented `http.server` knobs, and partial unauthenticated clients cannot consume the single provider concurrency slot. The in-repo bounded SSE frame validator is the required policy-specific component and implements exactly the frozen grammar; “no custom replacement” does not prohibit that validator. A separately owner-approved pinned, mature, license-compatible client may be substituted only after evidence, but this specification slice adds no dependency.

TTL is 300 seconds, maximum eight **provider attempts**, concurrency one, request 4 MiB, response 16 MiB, bootstrap 65,536 bytes, and total timeout 120 seconds. After local validation succeeds, the broker atomically reserves/decrements one slot immediately before upstream network I/O. Accounting is determined by reservation state, not outcome name: every pre-reservation failure consumes zero and emits none; every post-reservation terminal, including `server_shutdown` and `internal`, consumes exactly one and emits exactly one delegation provider-attempt stage. There are no retries. Neither prompt nor output is persisted. The kernel broker owns a minimal durable reservation ledger with exactly two secret-free, hash-chained rows per reserved attempt: `reserved` before any upstream I/O and one terminal row after it, containing the outcome code but never prompts, outputs, headers, or credentials. The ledger does not detect rollback or truncation; SLICE-056 characterizes that residual.

Each ledger row carries secret-free `taskId`, `session`, `requestId` when applicable, `provider`, `model`, and `attemptCorrelationId`, the SHA-256 of canonical compact sorted-key JSON `{taskId, session, requestId}`. The single ADR-031 `provider_attempt` stage event carries `attemptCorrelationId` as its non-null `subject_digest`; ledger rows and the stage event join on `attemptCorrelationId`; no new trace-schema field is introduced. At broker start, any reserved row without a terminal row is reconciled by appending an `internal` terminal row marked `reconciled_after_restart` before accepting a new reservation; the same rule applies to reserved rows older than `timeoutSeconds + 60` seconds.

Schemas, vectors, and the complete stable error vocabulary are canonical in `governance/schemas/delegated-provider/ranex-delegated-provider-v1.json`; harness consumes pinned vectors and digests. The fixture records the pin location; the canonical digest is `tests/contract/test_delegated_provider_protocol.py`'s `EXPECTED_SHA256` and is not embedded self-referentially in the fixture. Both issue #43 and issue #106 pin the artifact SHA and `protocolFingerprint`, and their cross-repo compatibility gate recomputes both.

The handshake/chat provider/model/tools schemas are structurally permissive on purpose so authoritative validation plus policy returns stable `provider_not_allowed`, `model_not_allowed`, and `tool_not_allowed`; bootstrap and grant carry stricter immutable shapes. JSON Schema enforces tool-name syntax, uniqueness, and `maxItems=32`, while sorted UTF-8 byte order is canonicalization enforced by kernel grant construction and handshake validation. Authoritative provider/model/tool enforcement and error ordering live in `validation` plus `policy` and MUST run before upstream. Validation is deterministic and fail-before-upstream: an unknown or unauthenticated session maps to `unauthorized`; a structurally valid active session presented with a different valid capability maps to `session_mismatch`; both retain constant-time capability comparison and disclose no session existence or capability details beyond these stable errors. A replayed request ID maps to `replay`; provider, model, and tool policy mismatches map to `provider_not_allowed`, `model_not_allowed`, and `tool_not_allowed`; structural failures in protocol shape, messages, stream, or request ID map to `invalid_request`. Size, protocol/version, expiry, concurrency/request limits, and terminal response/upstream/broker failures retain their named stable errors. The chat provider policy is explicit: absent means the authenticated session provider, present means it must match that provider.

SSE parsing is incremental and WHATWG-compatible with strict UTF-8: one BOM is permitted; CRLF, LF, and CR delimit lines; comments are ignored semantically; data fields join with LF; blank lines dispatch; unknown, event, id, and retry fields are permitted and relayed. Each complete valid event's original bytes are preserved exactly, without JSON rewriting. Raw lines are capped at 64 KiB, event data at 1 MiB, and cumulative upstream bytes at 16 MiB before decode/parse/write, including delimiters, comments, BOM, DONE, and offending bytes. `[DONE]` qualifies only when a dispatched event's assembled data is exactly `[DONE]`; the unchanged terminal event is relayed before success. EOF before DONE, invalid UTF-8, malformed framing, or any limit violation is `upstream_protocol`. Pre-stream broker failures use bounded generic JSON envelopes and deterministic `preStreamHttpStatus` mappings without upstream-body leakage. Every post-reservation terminal detected before downstream 200 headers commit maps to a synthetic response: `upstream_dns=502`, `upstream_connect=502`, `upstream_tls=502`, `response_too_large=502`, `upstream_timeout=504`, `upstream_http=502`, `redirect_refused=502`, `upstream_protocol=502`, `server_shutdown=503`, and `internal=500`. `client_cancelled` has no downstream status because downstream is already gone; its reservation is consumed and terminal outcome is recorded. The ordered preDownstreamNormalization states are: DNS failure → `upstream_dns`; TCP connect failure → `upstream_connect`; TLS failure → `upstream_tls`; upstream disconnect or transport error before COMPLETE valid response headers → `upstream_http`; a complete upstream response (classification at status line and headers, before any body) with a 3xx redirect status → `redirect_refused` (redirects are refused, never followed); any other non-200 status → `upstream_http`; a 200 response with missing, malformed, or non-text/event-stream Content-Type (media-type parameters permitted per RFC 9110) → `upstream_protocol`; all classified before downstream commitment (downstream receives the mapped 502 pre-stream status, never the upstream body). After valid 200 text/event-stream response headers are received and the downstream 200 is committed, EOF before the SSE DONE sentinel or any other upstream protocol violation → `upstream_protocol` with post-200 close-downstream semantics (no synthetic status); `client_cancelled` has no downstream status because downstream is already gone and its reservation is consumed. Only after downstream 200 is committed does failure close downstream without synthetic SSE or status. ADR-031 tracing is a non-durable observability event only; the separate reservation ledger is the authoritative durable accountability record. Timeouts use monotonic deadlines: connect/TLS 10s, first byte 30s, inter-read idle 30s, total `min(120s, remaining TTL)`.

### Consequences

- Good: raw key is absent from harness args, protocol bodies, artifacts, and logs.
- Good: exact bounds and fixed upstream make provider attempts finite and reviewable.
- Bad: the guarantee is accidental secret non-propagation and credential hygiene across the harness process boundary, not isolation against an adversarial same-UID harness. A same-UID adversary can ptrace-attach or read `/proc/<pid>/` where permitted and extract the raw key; O_CLOEXEC, FD discipline, and capability bounds do not address process-memory inspection. Separate UID, yama `ptrace_scope`, and `hidepid` proc mounts are optional deployment preconditions left to the owner, not protocol requirements.
- Bad: credentialed delegation is unavailable during broker shutdown or any refusal.
- ADR-031 tracing remains a non-durable observability event; separately, the kernel broker writes exactly two secret-free hash-chained reservation ledger rows per reserved attempt, before upstream I/O and after terminal outcome. The ledger never stores prompts, outputs, headers, or credentials and does not detect rollback/truncation (SLICE-056).
- Issue #43 owns the additive ADR-031 `schema.py` and schema-test surface. It must add `stage` to the existing `event` vocabulary, use existing `module=cli` and `event=stage` semantics, register the exact stage `cli.task.delegate.provider_attempt` in `STAGES`, register the closed code kind `delegation_provider_attempt` in `CODE_KINDS`, and register its argument set in the per-kind argument registry with exactly twelve finite arguments: `success`, `upstream_dns`, `upstream_connect`, `upstream_tls`, `client_cancelled`, `response_too_large`, `upstream_timeout`, `upstream_http`, `redirect_refused`, `upstream_protocol`, `server_shutdown`, and `internal`. Implementation tests must assert all three registrations, not merely mirror strings or assert absence. The valid record has the existing eleven fields only: non-null `event`, `sid`, `time`, `level`, `module`, `stage`, `subject_digest`, `duration_us`, and `code`; null `hierarchy` and `child_id`. Its `subject_digest` equals the ledger `attemptCorrelationId`, and its code is `delegation_provider_attempt:<argument>`, never an open grammar. The kernel broker emits exactly one such record per post-reservation terminal; the harness emits none. Existing `cli.task.delegate.start`/`end` remain separate lifecycle events. An oversized response has canonical broker outcome `response_too_large`; a harness observation of the closed stream may be local `upstream_protocol` only and cannot become authoritative.

### Confirmation

The kernel tests must prove the FD/pipe boundary, narrowed accidental-secret claim, constant-time capability comparison, exact limits, fixed URL, redirect refusal, SSE parsing, all stable errors, the two-row reservation ledger, no prompt/output persistence, no secret-bearing output, and old-harness refusal. The harness tests must prove it sends only the protocol capability and rejects direct credential/endpoint/`--auto` paths. Issue #43's observability tests must prove the additive `event=stage`, `module=cli`, exact `cli.task.delegate.provider_attempt` stage, closed argument code kind, required/non-null versus inapplicable/null fields, and exactly one event for every post-reservation terminal. The deterministic zero-byte capability/requestId vectors are syntax vectors only; runtime randomness is implementation-tested.

## Improvements on the prior art

1. Replace kubelet's credential-returning plugin result with a capability-only session; the key stays in the kernel.
2. Retain kubelet-style version and policy matching, but make provider and endpoint closed rather than configuration-selected.
3. Use Envoy's explicit check boundary while refusing its fail-open option and allowing no response mutation or credential return.
4. Add constant-time capability validation, one-use session state, TTL/request/concurrency/byte/time bounds, and redirect refusal.
5. Reuse ADR-031's existing stage-event semantics and evolve its schema additively instead of adding a journal row or broker log stream.

## Architecture surface

Kernel: `src/ranex/cli/delegation.py`, `src/ranex/cli/credential_broker.py`, and the existing delegate outcome surface. SLICE-069's intended implementation lanes are `tests/unit/test_credential_broker.py` and `tests/security/test_credential_broker.py`; they are not part of this specification-only change. Harness consumption is the coordinated issue #106 surface; no harness code lands here. Contract artifact is the governance JSON named above. No dependency, package-manifest, or runtime manifest changes; #43 owns the additive ADR-031 observability schema evolution. The suite-freeze manifest and golden are updated separately for the two contract IDs added by this specification change.

## Scope and threat delta

Moves the raw-key trust boundary from harness process memory to the kernel broker and adds a loopback capability channel. STRIDE moves: spoofing/replay (capability/session checks), tampering (closed schemas and fixed upstream), disclosure (accidental secret non-propagation and credential hygiene across the harness process boundary; same-UID process-memory inspection remains), denial of service (strict bounds). Non-goal: isolation against an adversarial same-UID harness. Separate UID, yama `ptrace_scope`, and `hidepid` proc mounts remain optional owner decisions.

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

- 1. Missing, malformed, absent, or unsupported five-second handshake → `invalid_protocol`/`unsupported_version` (or `handshake_required` on the wire); terminate harness and make no upstream call.
- 2. Unsupported version → `unsupported_version`; no downgrade.
- 3. Unknown/unauthenticated session → `unauthorized`; an active session under a different valid capability → `session_mismatch`; both use constant-time capability comparison and disclose no session existence or capability details beyond the stable error.
- 4. Reused session/request → `replay`; no duplicate upstream request.
- 5. Expired session → `expired`; no completion.
- 6. Wrong model/provider/tool → `model_not_allowed`, `provider_not_allowed`, or `tool_not_allowed`.
- 7. Request over 4 MiB, bootstrap over 65,536 bytes, or response over 16 MiB → size error and bounded cleanup.
- 8. Concurrent request or ninth provider attempt → `concurrency_limit` or `request_limit`; neither reserves a slot.
- 9. Any locally valid distinct request reserves before network I/O; DNS failure maps to `upstream_dns`, TCP connect failure to `upstream_connect`, TLS failure to `upstream_tls`, and upstream disconnect or transport error before COMPLETE valid response headers to `upstream_http`; a complete upstream response (classification at status line and headers, before any body) with a 3xx redirect status → `redirect_refused` (redirects are refused, never followed); any other non-200 status → `upstream_http`; a 200 response with missing, malformed, or non-text/event-stream Content-Type (media-type parameters permitted per RFC 9110) → `upstream_protocol`; all classified before downstream commitment (downstream receives the mapped 502 pre-stream status, never the upstream body). After valid 200 `text/event-stream` headers and committed downstream 200, EOF before DONE or another protocol violation maps to `upstream_protocol` with downstream close and no synthetic status. Client cancellation wins ties observed in the same event-loop iteration. Each consumes the slot and maps to exactly one non-overlapping named outcome; no retry. A replay is rejected before reservation and consumes zero.
- 10. Broker shutdown/internal are classified by actual reservation state: pre-reservation consumes zero and emits none; post-reservation consumes exactly one, emits exactly one delegation provider-attempt stage, and writes the two secret-free ledger rows.
- 11. Old credentialed harness or endpoint override → refuse and preserve uncredentialed mode.
- 12. Same-UID capability theft → bounded capability spend is the only mitigation at the harness boundary; a same-UID adversary may ptrace-attach or read `/proc/<pid>/` where permitted and inspect broker memory/raw key. O_CLOEXEC/FD discipline/capability bounds do not address this; full same-UID compromise containment is not claimed.

## Test strategy

Kernel paths: `tests/unit/test_delegation.py` covers the existing delegation boundary and no-secret assertions; `tests/integration/test_delegation_command.py` covers the existing loopback command boundary. `tests/contract/test_delegated_provider_protocol.py` freezes this artifact. Broker unit and security paths are opened by SLICE-069; harness paths use `packages/opencode` and are specified by issue #106.

`tests/contract/test_docs_discipline.py` verifies this ADR's sections, prior-art pins, vendored blob hashes, NOTICE, line budgets, sad-path count, and test paths. `tests/contract/test_delegated_provider_protocol.py` freezes the canonical JSON bytes/digest, exact 25-code set (including the additions `upstream_dns`, `upstream_connect`, `upstream_tls`, and `client_cancelled`), reservation-state accounting, transport replacement semantics, additive event design, exact status mappings, complete bootstrap example, and derived vector coverage before implementation; chat vectors assert expected broker state rather than SSE bodies. Red-first implementation tests are owned by SLICE-069, and issue #43 owns the additive observability schema tests, not this specification commit.

## Code review checklist

- Verify the raw key enters only the kernel FD/pipe and never the harness boundary.
- Verify the kernel reads/closes the inherited raw-key ingress before creating the distinct child bootstrap pipe; FD 3 reuse crosses a process boundary and never reuses raw-key bytes.
- Verify capability is exactly 32 random bytes and comparison is constant-time.
- Verify URL, redirect, provider, model, tool, request, response, timeout, TTL, request, concurrency, immutable grant, bootstrap FD 3, and reservation bounds are closed and exact.
- Verify all issue #43/#106 stable errors are present and no fallback/retry exists.
- Verify no prompt/output persistence or independent broker raw logs; verify exactly two secret-free hash-chained reservation ledger rows per reserved attempt, the additive ADR-031 event schema, and exactly one broker event per reserved outcome.
- Verify old credentialed harness refusal and uncredentialed preservation.
- Verify vendored source files match their pinned commit URLs and NOTICE licenses.
- Verify same-UID theft is recorded as residual, not described as solved.
- Verify no fixed port is normative, the bootstrap example is complete and explicitly non-normative, the handshake replay key is separate from the chat replay key, and `maxBootstrapBytes` is transport/bootstrap policy rather than grant authority.

## More Information

Issue #43 is the kernel contract and issue #106 is the harness dependency. ADR-010 records the prior credential-bearing delegation residual; ADR-031 governs the existing event emitter. The protocol/schema/vector artifact is the canonical wire source; this ADR is the ownership decision. No secret location, credential value, exploit command, or private advisory identifier is recorded.
