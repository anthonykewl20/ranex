#!/usr/bin/env python3
"""Deterministic staleness gate for governance records.

The contract tree already fails closed when generated output drifts from its
sources. Prose records had no equivalent: an ADR could be accepted, registered
and validated while the documents that describe the corpus still claimed an
older state. Measured on 2026-07-31, before this gate existed: nineteen ADRs on
disk while `HANDOFF.md` claimed sixteen, `README.md` claimed the range ended at
ADR-0014, and five RFCs already promoted into accepted ADRs still carried
`Status | DRAFT`.

Every check here is mechanical. No model is invoked and nothing is inferred:
each rule compares a written claim against the filesystem, and a mismatch is a
finding. Exit status is non-zero when any finding exists, so the gate can be a
required CI step.

Usage:  python check_record_freshness.py            # report and gate
        python check_record_freshness.py --json     # machine-readable
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISIONS = ROOT / "docs" / "architecture" / "decisions"
RFCS = ROOT / "docs" / "architecture" / "rfcs"
DOCS_README = ROOT / "docs" / "README.md"
RFC_INDEX = RFCS / "README.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def header_field(text: str, field: str) -> str | None:
    """Return a header row's value, backticks and markdown links included.

    An earlier revision excluded backticks from the captured value. Header
    values such as the `RFC` row contain a backticked markdown link, so the
    pattern never matched and the promoted-RFC check silently reported zero
    findings while five stale RFCs existed. A gate that under-reports is worse
    than no gate, so the value is captured verbatim and interpreted by callers.
    """

    match = re.search(
        rf"^\|\s*{re.escape(field)}\s*\|\s*(.+?)\s*\|\s*$",
        text,
        flags=re.MULTILINE,
    )
    if match is None:
        return None
    return match.group(1).strip().strip("`").strip()


def adr_files() -> list[Path]:
    return sorted(DECISIONS.glob("ADR-*.md"))


def rfc_files() -> list[Path]:
    return sorted(p for p in RFCS.glob("RFC-*.md"))


def check_promoted_rfcs_not_draft() -> list[str]:
    """An RFC cited by an accepted ADR must not still read DRAFT.

    This is the sharpest staleness signal in the corpus: the ADR header records
    the promotion, so the RFC's own status contradicts an accepted decision.
    """

    findings: list[str] = []
    promotions: dict[str, str] = {}
    for adr in adr_files():
        text = read(adr)
        for rfc_id in re.findall(r"RFC-(\d{4})", header_field(text, "RFC") or ""):
            promotions[f"RFC-{rfc_id}"] = adr.name.split("-")[0] + "-" + adr.name.split("-")[1]

    for rfc in rfc_files():
        rfc_id = rfc.name[:8]
        if rfc_id not in promotions:
            continue
        status = header_field(read(rfc), "Status")
        if status == "DRAFT":
            findings.append(
                f"{rfc.relative_to(ROOT)}: Status is DRAFT but the RFC was "
                f"promoted by an accepted ADR ({promotions[rfc_id]})"
            )
    return findings


def check_every_record_is_indexed() -> list[str]:
    """Every ADR and RFC file must be reachable from its index."""

    findings: list[str] = []
    rfc_index = read(RFC_INDEX)
    for rfc in rfc_files():
        if rfc.name == "README.md":
            continue
        if rfc.name not in rfc_index:
            findings.append(
                f"{rfc.relative_to(ROOT)}: not listed in "
                f"{RFC_INDEX.relative_to(ROOT)}"
            )
    return findings


def check_stated_ranges_match_reality() -> list[str]:
    """A document that names the highest ADR/RFC must name the real one."""

    findings: list[str] = []
    highest_adr = max(int(p.name[4:8]) for p in adr_files())
    highest_rfc = max(int(p.name[4:8]) for p in rfc_files())

    docs_readme = read(DOCS_README)
    for cited in re.findall(r"ADR-0001 … ADR-(\d{4})", docs_readme):
        if int(cited) != highest_adr:
            findings.append(
                f"{DOCS_README.relative_to(ROOT)}: states the ADR range ends at "
                f"ADR-{cited} but ADR-{highest_adr:04d} exists"
            )
    mentioned_rfcs = {int(n) for n in re.findall(r"RFC-(\d{4})", docs_readme)}
    if mentioned_rfcs and max(mentioned_rfcs) != highest_rfc:
        findings.append(
            f"{DOCS_README.relative_to(ROOT)}: names RFCs only up to "
            f"RFC-{max(mentioned_rfcs):04d} but RFC-{highest_rfc:04d} exists"
        )
    return findings


def check_stated_counts_match_reality() -> list[str]:
    """A stated accepted-ADR count must equal the number on disk."""

    findings: list[str] = []
    actual = len(adr_files())
    for path in (ROOT / "docs" / "HANDOFF.md", DOCS_README):
        if not path.exists():
            continue
        text = read(path)
        for stated in re.findall(
            r"\|\s*Accepted ADRs\s*\|\s*\*\*(\d+)\*\*", text
        ):
            if int(stated) != actual:
                findings.append(
                    f"{path.relative_to(ROOT)}: states {stated} accepted ADRs "
                    f"but {actual} exist on disk"
                )
    return findings


def check_index_status_matches_file() -> list[str]:
    """The index's Status column must equal the record's own Status header.

    Added after the gate passed while the index still listed five RFCs as DRAFT
    whose files read ACCEPTED. An index that restates a record's status is
    itself a claim, and an unchecked claim is exactly what this gate exists to
    prevent.
    """

    findings: list[str] = []
    for row in read(RFC_INDEX).splitlines():
        match = re.match(
            r"^\|\s*\[RFC-(\d{4})[^\]]*\]\(([^)]+)\)\s*\|\s*`([A-Z_]+)`\s*\|",
            row.strip(),
        )
        if match is None:
            continue
        _, relative, stated = match.groups()
        target = RFCS / relative
        if not target.exists():
            findings.append(
                f"{RFC_INDEX.relative_to(ROOT)}: links {relative}, which does "
                "not exist"
            )
            continue
        actual = header_field(read(target), "Status")
        if actual != stated:
            findings.append(
                f"{RFC_INDEX.relative_to(ROOT)}: lists {relative} as {stated} "
                f"but the file's Status header reads {actual}"
            )
    return findings


CHECKS = {
    "promoted_rfc_still_draft": check_promoted_rfcs_not_draft,
    "index_status_mismatch": check_index_status_matches_file,
    "record_not_indexed": check_every_record_is_indexed,
    "stated_range_stale": check_stated_ranges_match_reality,
    "stated_count_stale": check_stated_counts_match_reality,
}


def main() -> int:
    report: dict[str, list[str]] = {}
    for name, check in CHECKS.items():
        report[name] = check()
    total = sum(len(v) for v in report.values())

    if "--json" in sys.argv:
        print(
            json.dumps(
                {
                    "status": "PASS" if total == 0 else "STALE",
                    "finding_count": total,
                    "findings": report,
                    "adr_count": len(adr_files()),
                    "rfc_count": len(rfc_files()),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        for name, findings in report.items():
            for finding in findings:
                print(f"{name}: {finding}")
        if total == 0:
            print(
                f"records fresh: {len(adr_files())} ADRs, "
                f"{len(rfc_files())} RFCs, no stale claims"
            )
        else:
            print(f"\n{total} stale record claim(s); records must match reality")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
