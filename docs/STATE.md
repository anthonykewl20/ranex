# State

**Updated:** 2026-09-24
**Active slice:** none — live observer is next under ADR-061.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
SLICE-091 / #114: bare-arm purity. The two-arm adapter's bare arm now runs
from a DECLARED allowlist (BARE_ENV_PASSTHROUGH + an asserted venv-on-PATH
entry over BARE_SYSTEM_PATH — never dict(os.environ)); an in-child canary
measures the environment every command actually receives, and any RANEX_*
variable, kernel-naming PYTHONPATH, vendored kernel on PATH, or
constructed-vs-observed deviation fails the run loudly (exit 3, no ground
truth written). --contaminate {pythonpath,ranex-var,vendored-path} is the
caught negative control; prior two-arm numbers are re-labelled UNVERIFIED
(F-041). Five ceremony arms VERIFIED, outputs byte-identical ×3
(tools/dogfood/audits/2026-09-24-bare-purity/): probe clean, each channel
caught 3/3, governed arm byte-identical before/after the change (elapsed
zeroed), real task both arms with journals verified, environment digests
stable per arm. verdict.py untouched.

SLICE-090 / #113 stands as recorded: instrument self-test; every dogfood
driver pre-flights its gauge on a committed good/bad pair; calibration
refuses --skip-selftest and writes no receipt without a passing self-test.
Next: #111 (instruction digest), #112 (minimization ladder), #115, then
milestone 7 (#107, #108, #109), then #102, #105, #106, #119. Live
observer under ADR-061 remains the program's next exit; no ranex prove
exists yet.

Suite status, measured 2026-09-23/24: host glibc moved past the owner's
pinned native build inputs, so the drift family (slice036 selectors,
approved-batch contract, specification-batch qualification) and every
nested-green ceremony test (gating stage_08b/slice009, suite-freeze golden's
run_exit=0) are red on a pristine base checkout too — the owner re-pin main
already records is still needed. Refreezes stay mechanical (IDs only).
host_result_dir's traversal probe is root-clamped (2026-09-24), so its
refusal fires from any checkout depth; the short form hit writable `$HOME`.

Parallel work and overlapping verification are owner-authorized
(2026-09-12): use separate writer worktrees and pinned verification
worktrees. Refreeze on a committed tree; load_manifest must accept the
result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined. Full installed harness
mediation, observer scheduling, merge-group checks and production hosting
are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
