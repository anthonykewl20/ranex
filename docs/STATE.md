# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-13
**Active slice:** none.

## Where we stopped

SLICE-020 is closed and shipped. It delivered judgment identity: structured
five-kind causes on `Evaluation.as_record`; verdict projection composing refused
and unattributable causes; a dedicated `kernel-verdict-signer` under
`ranex-verdict-v1`; a publication validator; one shared rooted atomic writer;
and a total closed-state reader.

The verdict channel is UI/board-track work under ADR-018/022, not the P0 critical
path. That path remains SLICE-018 followed by SLICE-029..044.

## Next

Open SLICE-018 for the cgroup/namespace/bounded-output lifecycle. ADR-006 is
already written with prior art vendored. The slice has no dependency on the
verdict channel and is ready to open.

## Known limits

- The cgroup-observer test still flakes with `OSError(19)` under load; unfixed.
- Real qualification e2e skips on hosts without delegated cgroup `cpu`, as
  declared in the manifest.
- `mutmut` did not complete for this slice because the SLICE-017 copy-repo test
  environment crashed. This is advisory/non-blocking and remains unverified.
