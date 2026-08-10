# Third-party source vendored for ADR-001

These files are copies of upstream implementations, kept so that what ADR-001
claims to have read is on disk and checkable. They are evidence, not
dependencies: nothing imports, executes or lints them.

Each was fetched at the pinned revision named below, and its git blob hash was
then compared against the hash GitHub reports for that path at that revision —
so these copies agree with upstream, not merely with each other.

- `in-toto-verifylib.py` — Apache-2.0 — in-toto `in_toto/verifylib.py` at tag v2.3.0, blob `64f11fb8cb25f556732ead52cda300fde31aaf62`, from <https://github.com/in-toto/in-toto/blob/v2.3.0/in_toto/verifylib.py> — Copyright New York University and the in-toto contributors.
- `dsse-background.md` — Apache-2.0 — DSSE `background.md` at tag v1.0.2, blob `8a9cc46d7b7eaebd58f6e44296f419f429056285`, from <https://github.com/secure-systems-lab/dsse/blob/v1.0.2/background.md> — Copyright the DSSE contributors.
- `in-toto-golang-verifylib.go` — Apache-2.0 — in-toto-golang `in_toto/verifylib.go` at tag v0.11.0, blob `de9dfa7e647b9022c406c807363a2ae0df0ec47b`, from <https://github.com/in-toto/in-toto-golang/blob/v0.11.0/in_toto/verifylib.go> — Copyright New York University and the in-toto contributors.

All three licences are permissive and compatible with this repository's MIT
licence, and each requires the copyright notice to travel with the copy — which
is what this file is for.
