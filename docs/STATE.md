# State

**Updated:** 2026-08-03
**Phase:** kernel — evidence loop
**Active slice:** `docs/slices/SLICE-006-gating-a-real-test-suite.md`

## Where we stopped

SLICE-004 is closed again: the subject is materialised from verified git blobs,
the environment is built from empty, and executable discovery is pinned. That
honesty withdrew dependency-bearing commands because ignored `.venv` and
`node_modules` are not committed.

ADR-006 remains proposed. Its Landlock slice was opened and then deferred; there
is no open Landlock slice now. The measured same-uid signing-key theft remains a
known limit, not a capability silently claimed.

## Active work

SLICE-006 restores real suites under ADR-007. Networked provisioning derives the
lock under fixed resolver inputs, admits only hashed wheels to a content-addressed
store, shows the dependency delta for approval, and assembles a read-only root
for an offline run.

The acceptance test is the repository itself: its committed gate remains `uv
run pytest -q`, and Ranex must produce evidence for that command from the
materialised current commit and then evaluate it PASS.

## Known limits

- Dependencies are trusted computing base. A hash-correct approved wheel can run
  at import time and force the exit code; this slice mitigates visibility only.
- The installed uv is 0.11.26 in user-writable `~/.local/bin`, outside the pinned
  path. The slice must provision and pin the runner as well as its packages.
- ADR-006's same-uid key theft, unauthenticated approver identity, journal
  truncation, 44 unreached refusals and kernel mutation survivors remain open.
- Symlink and submodule subjects, non-Python dependencies, and mutable index
  history remain unsupported.

## After this slice

Open the Landlock slice against ADR-006; then authenticate approvals and close
journal rollback before widening the worker surface.
