# SLICE-017 — qualify the strict-local host and native launcher

**Status:** open
**Opened:** 2026-08-09
**Priority:** P0 prerequisite — first active work in the approved-specification milestone.
**ADR:** `docs/adr/ADR-006-landlock-confinement-of-the-bound-command.md` —
proposed until planned SLICE-019 closes.
**Tracker:** `https://github.com/anthonykewl20/ranex/issues/10`; issue #10
retains the historical SLICE-017 identity.
**Next:** close this slice, then open planned SLICE-018 for cgroup/output
lifecycle. SLICE-019 alone wires `cmd_run`; SLICE-029 follows it.

## Session-sized result

Produce one byte-reproducible GNU C17 launcher and one fail-closed host
qualification result for ADR-006's strict-local profile. The controller builds,
installs, opens, verifies and executes the same launcher object. Qualification
uses an existing delegated cgroup-v2 root or acquires one through a pinned
controller-side systemd broker, then proves the mandatory Linux primitives with
real child processes.

This slice does **not** run an arbitrary or repository-supplied command, touch
`cmd_run`, create evidence, sign, manage a run's full cgroup lifecycle, or claim
that RISK-06 is closed. Those boundaries keep the work finishable in one session.

## Exact owned paths

Only these six repository paths may change:

- `src/ranex/cli/host_confinement.py`
- `native/ranex-worker-launcher/launcher.c`
- `governance/confinement/native-launcher-build-v1.json`
- `governance/confinement/strict-local-host-v1.json`
- `tests/security/test_slice017_host_qualification.py`
- `tests/integration/test_slice017_native_launcher.py`

`src/ranex/cli/main.py`, evidence/signing code, the pure verdict kernel and the
harness are out of scope. Build, install and qualification outputs exist only at
the exact ignored paths named below and never enter git.

## Frozen build and install contract

Language/target are GNU C17 plus Linux UAPI on `x86_64-linux-gnu`. The committed
build manifest names `/usr/bin/x86_64-linux-gnu-gcc-13`, version `13.3.0`, and
pins by SHA-256 every file opened or executed by the driver, compiler, assembler,
linker and C runtime closure. It also binds source SHA-256, target, exact ordered
argv, allowlisted environment, expected ELF facts and final artifact SHA-256.
An extra/missing/mismatched build input or a network attempt refuses the build.

The ordered compiler flags are frozen in the manifest: C17, `_GNU_SOURCE`, `-O2`,
PIE, strong stack protector, fortify level 3, format-security errors, RELRO/NOW,
non-executable stack, no build-id, no recorded compiler switches, and source plus
macro prefix maps from the absolute repository root to `.`. A pinned tracer observes every file the driver, compiler, assembler, linker and C runtime open or execute; the tracer's own digest is bound in the manifest, and any input the tracer did not observe refuses the build (gate 2). The environment is
built from empty and contains only `PATH=/usr/bin:/bin`, `LC_ALL=C`, `TZ=UTC` and
`SOURCE_DATE_EPOCH=0`.

From repository root, the only build and install commands are:

```text
PYTHONPATH=src uv run --frozen python -m ranex.cli.host_confinement launcher-build --manifest governance/confinement/native-launcher-build-v1.json --source native/ranex-worker-launcher/launcher.c --output .local/ranex/build/strict-local-v1/ranex-worker-launcher
PYTHONPATH=src uv run --frozen python -m ranex.cli.host_confinement launcher-install --manifest governance/confinement/native-launcher-build-v1.json --artifact .local/ranex/build/strict-local-v1/ranex-worker-launcher --destination .local/ranex/libexec/strict-local-v1/ranex-worker-launcher
```

Install is no-follow, exclusive and atomic, sets mode `0555`, fsyncs file and
parent, and refuses replacement. The only admitted artifact path is
`.local/ranex/libexec/strict-local-v1/ranex-worker-launcher`; the only host report
path is `.local/ranex/qualification/strict-local-v1.json`.

## Frozen host-qualification contract

The controller resolves `/proc/self/cgroup`; an environment variable or caller
path can never name the delegation root. A usable existing root is cgroup2,
writable by the controller, exposes `cpu`, `memory` and `pids`, and permits a
probe child plus read-back and removal. If it is absent, the controller invokes
the pinned `/usr/bin/systemd-run` directly, without a shell, as a user service
with `--user --no-ask-password --quiet --collect --wait --pipe --service-type=exec`, exact
`--property=` values for `Delegate=yes` and CPU/memory/task accounting, the exact
repository cwd, qualified Python executable and `host-probe` subcommand. From
`geteuid()` it derives `/run/user/<uid>` and that directory's `bus` socket,
requires a non-symlink directory and socket both owned by that uid, records their
modes without assuming one portable mode, and admits only the derived `XDG_RUNTIME_DIR` and
`DBUS_SESSION_BUS_ADDRESS` to the otherwise-empty broker environment; caller
values never select a bus. It closes non-protocol FDs, records exact
argv/executable digests and never launches worker code. Broker, D-Bus or read-back failure is
`E-C17-CGROUP-DELEGATION`, never a skipped or weaker success.

The report schema is closed and canonical. It binds kernel release/architecture,
Landlock ABI, seccomp-filter/NNP, user/mount/PID/IPC/network namespace probes,
`openat2`, `cgroup.kill`, cgroup mount/root/controllers, the create-enable-move-
read-remove probe transcript, Bubblewrap plus launcher open-object provenance,
profile/build/artifact digests, exact broker facts and one stable refusal code.
Unknown architecture, unsupported ABI, mutable helper, unreadable fact or
cleanup failure produces no qualified report.

## Native launcher probe

The controller opens the installed launcher with no-follow flags, verifies
owner/mode/mount/capability facts and the manifest digest, and executes that
same FD with `execveat(AT_EMPTY_PATH)` or refuses. The launcher accepts only the
versioned qualification protocol in this slice. It starts behind a pipe gate,
validates its fixed protocol FDs, closes every other FD, invalidates inherited keyrings, reconstructs
the environment from the protocol allowlist, sets NNP, and runs built-in child
probes. It cannot accept arbitrary `argv` or execute a subject command.

The real probe demonstrates that an inherited secret environment value, an
unexpected FD and a session keyring are absent; the gate prevents a child byte
from running before release; NNP and each advertised kernel primitive are
observed rather than inferred. Path swapping after open cannot change the object
executed. Probe output is length-bounded canonical JSON on its dedicated FD.

## Deterministic acceptance gates

1. Two clean builds under different absolute directories have identical bytes
   and equal the manifest artifact SHA-256.
2. Deleting, replacing or adding one traced build-closure input refuses; compiler
   version text without byte identity is insufficient.
3. Install refuses symlinks, existing destinations, wrong modes and a staging
   artifact whose bytes or ELF facts differ.
4. A pathname swap after controller open still executes the verified FD; making
   the launcher/helper chain writable or file-capable refuses.
5. Existing delegation and broker-acquired delegation both create, read back and
   remove a real cgroup probe; no delegation yields a stable refusal.
6. Removing one required controller, namespace, Landlock, seccomp, `openat2`,
   `cgroup.kill` or Bubblewrap fact makes qualification non-successful.
7. A real gated launcher process proves it cannot run early and cannot observe
   the injected secret, unexpected FD or keyring.
8. Malformed protocol, oversized output, extra field, wrong architecture and
   cleanup failure refuse with stable codes and no partial qualified report.
9. Source inspection, mocked subprocesses and a host-feature skip may support
   diagnosis but cannot satisfy any gate above.
10. `src/ranex/cli/main.py`, the kernel and `cmd_run` behavior remain byte-exact;
    ADR-006 and RISK-06 remain open for SLICE-018/019.

## Verification commands

Run from repository root on a recorded Linux host; mandatory-feature absence is
a test of refusal and never a PASS for the positive qualification journey:

```text
uv sync --frozen
uv run --frozen pytest -q tests/security/test_slice017_host_qualification.py
uv run --frozen pytest -q tests/integration/test_slice017_native_launcher.py
uv run --frozen pytest -q tests/contract/test_kernel_unchanged.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen pytest -q
```

Record the two build roots, complete input closure and hashes, artifact/report
hashes, exact broker argv, host facts, negative-control exits and cleanup result.

## Controls most likely to become decoration

1. Pinning only `gcc` while unpinned `cc1`, assembler, linker or CRT bytes decide.
2. Comparing two builds in one path, leaving absolute-path nondeterminism hidden.
3. Reporting cgroup controllers without creating and removing a real child.
4. Treating unavailable user D-Bus/delegation as a green skip.
5. Hashing a launcher pathname and reopening it for execution.
6. A launcher “FD cleanup” test that never injects an inheritable secret FD.
7. Letting qualification execute the eventual untrusted command early.
8. A build-closure manifest that lists inputs from documentation rather than from an actual pinned tracer observing the compiler.

## Not in this slice

- Cgroup ownership for a run, limits/events, `cgroup.kill`/drain, bounded output
  collection and the full namespace/Landlock/seccomp command profile (SLICE-018).
- `cmd_run` integration, evidence field binding, signer refusal and installed-CLI
  attack closure (SLICE-019).
- ADR-017 contracts, harness admission, provider/model runs or parallel agents.
