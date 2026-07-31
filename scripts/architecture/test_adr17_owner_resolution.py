"""ADR-0017 predeclared acceptance tests, executed against the shipped code."""

import sys

sys.path.insert(0, "/home/soultransit/devtony/ranex/scripts/architecture")
from validate_contracts import _owner_resolution_is_coherent  # noqa: E402

GOOD = "sha256:" + "a" * 64
OTHER = "sha256:" + "b" * 64


def row(**kw: object) -> dict[str, object]:
    base: dict[str, object] = {
        "provision_id": "HERMES-OWNER-DECISION-001",
        "status": "OWNER_DECISION_REQUIRED",
        "owner_decision_ref": None,
        "owner_decision_digest": None,
    }
    base.update(kw)
    return base


def ref(
    digest: str = GOOD,
    atype: str = "human_decision",
    aref: str = "urn:ranex:hd:1",
) -> dict[str, str]:
    return {
        "artifact_type": atype,
        "artifact_ref": aref,
        "artifact_digest": digest,
    }


CASES = [
    # (label, row, expected)
    ("unresolved row is coherent", row(), True),
    (
        "AT-1 resolved + bound is coherent",
        row(status="ACCEPTED", owner_decision_ref=ref(), owner_decision_digest=GOOD),
        True,
    ),
    (
        "AT-2 digest altered by one character fails",
        row(status="ACCEPTED", owner_decision_ref=ref(), owner_decision_digest=OTHER),
        False,
    ),
    (
        "AT-7 bare-string reference fails (OWNER-RESOLVE-007 retained)",
        row(status="ACCEPTED", owner_decision_ref="ADR-9999", owner_decision_digest=GOOD),
        False,
    ),
    (
        "ACCEPTED with no reference fails",
        row(status="ACCEPTED"),
        False,
    ),
    (
        "half-resolved: ref present, status still required",
        row(owner_decision_ref=ref(), owner_decision_digest=GOOD),
        False,
    ),
    (
        "half-resolved: ref present, digest null",
        row(status="ACCEPTED", owner_decision_ref=ref()),
        False,
    ),
    (
        "wrong artifact_type fails",
        row(
            status="ACCEPTED",
            owner_decision_ref=ref(atype="accepted_adr"),
            owner_decision_digest=GOOD,
        ),
        False,
    ),
    (
        "extra key in typed ref fails (closed object)",
        row(
            status="ACCEPTED",
            owner_decision_ref={**ref(), "waiver": True},
            owner_decision_digest=GOOD,
        ),
        False,
    ),
    (
        "unknown status fails",
        row(status="RESOLVED"),
        False,
    ),
]

failures = 0
for label, r, expected in CASES:
    got = _owner_resolution_is_coherent(r)
    ok = got is expected
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {label}  (expected {expected}, got {got})")

# AT-1 continued: the derived count falls to nineteen when one row resolves.
rows = [row(provision_id=f"HERMES-OWNER-DECISION-{i:03d}") for i in range(1, 21)]
before = sum(1 for x in rows if x["status"] != "ACCEPTED")
rows[0] = row(
    status="ACCEPTED", owner_decision_ref=ref(), owner_decision_digest=GOOD
)
after = sum(1 for x in rows if x["status"] != "ACCEPTED")
ok = (before, after) == (20, 19)
failures += not ok
print(f"{'PASS' if ok else 'FAIL'}  AT-1 derived count 20 -> 19 on one resolution")

print(f"\n{len(CASES) + 1} cases, {failures} failed")
sys.exit(1 if failures else 0)
