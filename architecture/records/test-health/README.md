# Canonical test-health records

This tree is the sole source for governed TDD-cycle, TDD-exception,
flaky-test-quarantine, and obsolete-test-deletion instances.

Records, when present, live directly under the class directory named by
ADR-0008:

- `tdd-cycles/<cycle_id>.json`
- `tdd-exceptions/<exception_id>.json`
- `quarantines/<quarantine_id>.json`
- `obsolete-test-deletions/<deletion_id>.json`

The contract compiler rejects symlinks, nested or hidden entries, non-JSON
files, duplicate JSON keys, unsafe IDs, filenames that do not equal the record
ID, and IDs reused across record classes. The initial instance population is
empty; generated registries content-bind any later canonical source bytes.
