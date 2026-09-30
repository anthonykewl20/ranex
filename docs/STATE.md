# State

**Updated:** 2026-10-01
**Active slice:** docs/slices/SLICE-103-audit-findings-and-remediation.md

**#105 shipped (2026-10-01, branch `captain/105-ocr-static-subject`):**
the static OCR binary is now a governed v3 subject. Static-entrypoint
closure admission (pt_interp null, byte-verified), launcher emits
`statically linked` without exec, sealed inert fds 0-2 for static
workers (Go checkfds), strace-measured worker-only seccomp delta.
Field receipts `tools/dogfood/audits/2026-09-30-ocr-subject-v2/`:
arms 0/1/2/3/5 VERIFIED incl. the credential-invariance invariant
(identical verdict digests key-unset vs key-set, 1 distinct of 6);
arm 4 GAP by owner decision (live PR #12 on ranex-app-live-probe
retained as evidence). Commits: a47306731 docs, 7ff642348 feat,
c1982e0a6 manifest refreeze.

**Suite manifest:** FROZEN tests=2450 expected_skips=157 via the
standing ceremony; `load_manifest` accepted; second freeze on the
unchanged tree byte-stable (deterministic gate 4 proven mechanically —
the journey fixture itself errors on the M5 landmine in direct runs).

**Suite status (documented drift classes, from SLICE-103):** sealed
freeze run 11 failed / 2262 passed / 151 skipped / 26 errors; direct
runs carry the local `third_party/firstmate` docs-cap landmine and the
reproducible-build artifact drift on top. Root causes and the M1-M5 /
C1 / H1 queue live in SLICE-103.

**Remaining queue (SLICE-103):** C1 policy-context fail-open first,
H1 observation-log anchor, M1/M2 promotion gate, M5 freeze/run
self-conflict + red-suite truth, #112/SLICE-036 completion,
centralized logging, dead-code purge + manifest ID fix.

**Housekeeping:** worktrees consolidated 2026-09-30 (rescue branches
pushed, nothing lost); local `third_party/firstmate/` tree breaks
`test_docs_discipline` on this host only.

**Next:** SLICE-103 remediation queue, C1 first.
