"""Delegated review — packet in, SARIF out, no new signing surface (#102).

A claim binds an argv that runs a review worker against a deterministic
**packet** — (subject digest, frozen diff-range SHAs, resolved handbook
chapters) canonicalised to a digest — and writes SARIF. That SARIF is the
claim's `results_artifact` under the #97 reporter family; the observation is
signed by the observing producer exactly as today. No worker key, no second
signing surface (ADR-060 rule 3).

Captain rulings (binding, from the OCR steal §6 rows 2/7/9):

1. **Anchor re-derivation.** Line numbers are derived from the verbatim
   excerpt against the materialised subject, never trusted from the producer.
   An unresolvable excerpt equals absence (ADR-060 rule 6).
2. **Prose-free fingerprints.** ``sha256(path | category | code-excerpt)``
   with occurrence-index disambiguation when the same base fingerprint
   appears more than once. Message prose is never in the fingerprint.
3. **Findings are advisory-only.** The reporter admits the artifact into the
   closed suite-summary shape; model findings must not sit in any default
   ``required_claims``. Removing every model credential therefore changes no
   verdict when the claim is absent both ways.

``verdict.py`` is untouched. No new runtime dependency.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256
from ranex.foundation.scan_results import (
    SARIF_LEVELS,
    SCAN_REPORTERS,
    _driver_levels,
    _findings,
    _reduce_scan_findings,
    _sarif_packet_digest,
    _subject_relative,
    validate_scan_manifest,
)

DELEGATED_REVIEW_REPORTERS = frozenset({"delegated-review-sarif-2.1.0"})

#: Union with the #97 family so loaders and argv checks treat both alike.
REVIEW_SARIF_REPORTERS = SCAN_REPORTERS | DELEGATED_REVIEW_REPORTERS

_PACKET_KEYS = frozenset(
    {"subject_digest", "range", "handbook_digest", "chapters"}
)
_RANGE_KEYS = frozenset({"base", "head"})
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SARIF_VERSION = "2.1.0"


def build_packet(
    *,
    subject_digest: str,
    range_base: str,
    range_head: str,
    handbook_digest: str,
    chapters: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Build the canonical review packet the worker consumes.

    ``range_base`` / ``range_head`` are frozen commit SHAs (40 hex), never
    mutable refs — the OCR ManifestInput pattern adopted for #102/#105.
    ``chapters`` are the resolved handbook chapters (#100), already digested
    into ``handbook_digest``; they travel by value so a receipt can name them.
    """

    if not isinstance(subject_digest, str) or not _DIGEST_RE.fullmatch(subject_digest):
        raise ValueError("subject_digest must be sha256:<64-hex>")
    if not isinstance(handbook_digest, str) or not _DIGEST_RE.fullmatch(handbook_digest):
        raise ValueError("handbook_digest must be sha256:<64-hex>")
    for label, value in (("base", range_base), ("head", range_head)):
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
            raise ValueError(f"range.{label} must be a 40-hex commit SHA, got {value!r}")
    if not isinstance(chapters, Sequence) or isinstance(chapters, (str, bytes)):
        raise ValueError("chapters must be a sequence of chapter objects")
    normalised: list[dict[str, object]] = []
    for index, chapter in enumerate(chapters):
        if not isinstance(chapter, Mapping):
            raise ValueError(f"chapters[{index}] must be an object")
        required = {"chapter_id", "layer", "pattern", "text"}
        if set(chapter) < required:
            raise ValueError(
                f"chapters[{index}] missing {sorted(required - set(chapter))}"
            )
        normalised.append(
            {
                "chapter_id": chapter["chapter_id"],
                "layer": chapter["layer"],
                "pattern": chapter["pattern"],
                "text": chapter["text"],
                "merged": bool(chapter.get("merged", False)),
                "sniffed": bool(chapter.get("sniffed", False)),
            }
        )
    return {
        "subject_digest": subject_digest,
        "range": {"base": range_base, "head": range_head},
        "handbook_digest": handbook_digest,
        "chapters": normalised,
    }


def packet_bytes(packet: Mapping[str, object]) -> bytes:
    """Canonical JSON bytes of a validated packet."""

    return canonical_json_bytes(validate_packet(packet))


def packet_digest(packet: Mapping[str, object]) -> str:
    """``sha256:`` digest over the canonical packet bytes."""

    return "sha256:" + hashlib.sha256(packet_bytes(packet)).hexdigest()


def validate_packet(packet: Mapping[str, object]) -> dict[str, object]:
    """Refuse anything that is not exactly the packet shape."""

    if not isinstance(packet, Mapping) or set(packet) != _PACKET_KEYS:
        raise ValueError(f"packet must contain exactly {sorted(_PACKET_KEYS)}")
    range_value = packet["range"]
    if not isinstance(range_value, Mapping) or set(range_value) != _RANGE_KEYS:
        raise ValueError(f"packet.range must contain exactly {sorted(_RANGE_KEYS)}")
    return build_packet(
        subject_digest=str(packet["subject_digest"]),
        range_base=str(range_value["base"]),
        range_head=str(range_value["head"]),
        handbook_digest=str(packet["handbook_digest"]),
        chapters=list(packet["chapters"]),  # type: ignore[arg-type]
    )


def prose_free_fingerprint(
    path: str, category: str, excerpt: str, *, occurrence: int = 0
) -> str:
    """sha256 over path|category|excerpt (+ occurrence), never over message prose.

    Occurrence disambiguates duplicate base fingerprints so trackers do not
    fold distinct alerts (OCR sarif.go:195–211 behaviour, adopted).
    """

    if occurrence < 0:
        raise ValueError("occurrence must be >= 0")
    material = canonical_json_bytes(
        {"path": path, "category": category, "excerpt": excerpt, "occurrence": occurrence}
    )
    return hashlib.sha256(material).hexdigest()


def finding_id(path: str, category: str, excerpt: str, *, occurrence: int = 0) -> str:
    return (
        f"{path}::{category}::"
        f"{prose_free_fingerprint(path, category, excerpt, occurrence=occurrence)}"
    )


def _normalise_excerpt(text: str) -> str:
    """Whitespace-normalise an excerpt: strip diff markers and blank lines."""

    lines: list[str] = []
    for line in text.splitlines():
        stripped = line[1:] if line[:1] in "+- " else line
        stripped = stripped.strip()
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def resolve_anchor(subject_root: Path, path: str, excerpt: str) -> tuple[int, int] | None:
    """Derive (start_line, end_line) from a verbatim excerpt, or None.

    Never trusts a producer-supplied line number. Searches the subject's file
    for the normalised excerpt; the first unique match wins. Ambiguity or
    absence returns None — callers treat that as absence (ADR-060 rule 6).
    """

    if not isinstance(excerpt, str) or not excerpt.strip():
        return None
    subject_file = subject_root / path
    try:
        raw = subject_file.read_text(encoding="utf-8")
    except OSError:
        return None
    needle = _normalise_excerpt(excerpt)
    if not needle:
        return None
    file_lines = raw.splitlines()
    normalised_lines = [_normalise_excerpt(line) for line in file_lines]
    compact: list[tuple[int, str]] = [
        (index, text) for index, text in enumerate(normalised_lines) if text
    ]
    needle_parts = needle.split("\n")
    matches: list[tuple[int, int]] = []
    for start in range(len(compact) - len(needle_parts) + 1):
        window = [compact[start + offset][1] for offset in range(len(needle_parts))]
        if window == needle_parts:
            first = compact[start][0] + 1
            last = compact[start + len(needle_parts) - 1][0] + 1
            matches.append((first, last))
    if len(matches) != 1:
        return None
    return matches[0]


def _excerpt_from_result(result: Mapping[str, Any]) -> str | None:
    """The verbatim code excerpt a finding carries — snippet preferred."""

    locations = result.get("locations")
    if isinstance(locations, list) and locations:
        physical = locations[0].get("physicalLocation") if isinstance(locations[0], dict) else None
        if isinstance(physical, dict):
            region = physical.get("region")
            if isinstance(region, dict):
                snippet = region.get("snippet")
                if isinstance(snippet, dict) and isinstance(snippet.get("text"), str):
                    return snippet["text"]
    properties = result.get("properties")
    if isinstance(properties, Mapping):
        for key in ("existing_code", "excerpt", "code"):
            value = properties.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return None


def _category_from_result(result: Mapping[str, Any]) -> str:
    rule_id = result.get("ruleId")
    if isinstance(rule_id, str) and rule_id:
        return rule_id
    properties = result.get("properties")
    if isinstance(properties, Mapping):
        category = properties.get("category")
        if isinstance(category, str) and category:
            return category
    raise ValueError("delegated-review result carries no ruleId/category")


def rederive_findings(
    sarif: Mapping[str, Any], subject_root: Path
) -> list[tuple[str, str, str]]:
    """Every result as ``(finding_id, path, level)`` with anchors re-derived.

    Producer startLine/endLine are ignored. An unresolvable excerpt refuses the
    whole artifact (absence): a finding that cannot be bound to the subject is
    not a finding about this subject.
    """

    if sarif.get("version") != _SARIF_VERSION:
        raise ValueError(f"SARIF artifact must declare version {_SARIF_VERSION}")
    runs = sarif.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("SARIF artifact carries no runs")

    findings: list[tuple[str, str, str]] = []
    base_counts: dict[str, int] = {}
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("SARIF runs entries must be objects")
        results = run.get("results", [])
        if not isinstance(results, list):
            raise ValueError("SARIF runs[].results must be a list when present")
        levels = _driver_levels(run)
        for result in results:
            if not isinstance(result, dict):
                raise ValueError("SARIF results entries must be objects")
            category = _category_from_result(result)
            level = result.get("level", levels.get(category, "warning"))
            if level not in SARIF_LEVELS:
                raise ValueError(f"SARIF result carries an unknown level: {level!r}")
            locations = result.get("locations")
            if not isinstance(locations, list) or len(locations) != 1:
                raise ValueError(
                    "delegated-review result must carry exactly one location"
                )
            physical = (
                locations[0].get("physicalLocation")
                if isinstance(locations[0], dict)
                else None
            )
            if not isinstance(physical, dict):
                raise ValueError("delegated-review location carries no physicalLocation")
            artifact_location = physical.get("artifactLocation")
            path = _subject_relative(
                artifact_location.get("uri") if isinstance(artifact_location, dict) else None,
                subject_root,
            )
            excerpt = _excerpt_from_result(result)
            if excerpt is None:
                raise ValueError(
                    f"delegated-review finding for {path!r} carries no verbatim excerpt; "
                    "absence blocks (ADR-060 rule 6)"
                )
            anchor = resolve_anchor(subject_root, path, excerpt)
            if anchor is None:
                raise ValueError(
                    f"delegated-review finding for {path!r} has an unresolvable "
                    "excerpt anchor; absence blocks (ADR-060 rule 6)"
                )
            base = prose_free_fingerprint(path, category, excerpt, occurrence=0)
            occurrence = base_counts.get(base, 0)
            base_counts[base] = occurrence + 1
            findings.append(
                (finding_id(path, category, excerpt, occurrence=occurrence), path, level)
            )
    return findings


def _expected_packet_digest(document: Mapping[str, Any]) -> str:
    """The packet digest the SARIF claims to answer, from run/top properties."""

    digest = _sarif_packet_digest(document)
    if digest is None:
        raise ValueError(
            "delegated-review SARIF must carry properties.packet_digest "
            "(sha256:<64-hex>); a review without a packet is not a review of this subject"
        )
    return digest


def _rewrite_with_rederived_regions(
    document: Mapping[str, Any], subject_root: Path
) -> dict[str, Any]:
    """Copy the SARIF with startLine/endLine replaced by re-derived anchors."""

    rewritten = copy.deepcopy(dict(document))
    for run in rewritten.get("runs", []):
        if not isinstance(run, dict):
            continue
        for result in run.get("results", []) if isinstance(run.get("results"), list) else []:
            if not isinstance(result, dict):
                continue
            result["ruleId"] = _category_from_result(result)
            excerpt = _excerpt_from_result(result)
            if excerpt is None:
                continue
            locations = result.get("locations")
            if not isinstance(locations, list) or not locations:
                continue
            physical = (
                locations[0].get("physicalLocation")
                if isinstance(locations[0], dict)
                else None
            )
            if not isinstance(physical, dict):
                continue
            artifact_location = physical.get("artifactLocation")
            path = _subject_relative(
                artifact_location.get("uri") if isinstance(artifact_location, dict) else None,
                subject_root,
            )
            anchor = resolve_anchor(subject_root, path, excerpt)
            if anchor is None:
                continue
            start, end = anchor
            region = physical.get("region")
            if not isinstance(region, dict):
                physical["region"] = {"startLine": start, "endLine": end, "snippet": {}}
                region = physical["region"]
            else:
                region["startLine"] = start
                region["endLine"] = end
            snippet = region.setdefault("snippet", {})
            if isinstance(snippet, dict):
                subject_file = subject_root / path
                lines = subject_file.read_text(encoding="utf-8").splitlines(keepends=True)
                region_text = "".join(lines[start - 1 : end]).rstrip("\n")
                snippet["text"] = region_text
    return rewritten


def delegated_review_results_from_sarif(
    sarif_bytes: bytes,
    manifest: Mapping[str, object],
    *,
    subject_root: Path,
    expected_packet_digest: str,
    require_review: bool = False,
) -> dict[str, object]:
    """Admit a delegated-review SARIF under the captain invariants.

    Packet substitution is refused. Anchors are re-derived. Fingerprints are
    prose-free. The reduction then reuses the #97 scan summary so ``evaluate()``
    learns nothing new.
    """

    if not isinstance(expected_packet_digest, str) or not _DIGEST_RE.fullmatch(
        expected_packet_digest
    ):
        raise ValueError("expected_packet_digest must be sha256:<64-hex>")
    if not isinstance(sarif_bytes, bytes):
        raise TypeError("sarif_bytes must be bytes")
    try:
        document = json.loads(sarif_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("SARIF artifact must use UTF-8 encoding") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"cannot parse SARIF artifact: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError("SARIF artifact must be a JSON object")

    findings, witnessed = validated_review_findings(
        document, subject_root, expected_packet_digest
    )
    return _reduce_scan_findings(
        findings, witnessed, validate_scan_manifest(dict(manifest)), subject_root, require_review=require_review
    )


def validated_review_findings(
    document: Mapping[str, Any], subject_root: Path, expected_packet_digest: str
) -> tuple[list[tuple[str, str, str]], set[str] | None]:
    """Bind the packet, re-derive identity, and validate SARIF coverage/regions."""

    claimed = _expected_packet_digest(document)
    if claimed != expected_packet_digest:
        raise ValueError(
            "delegated-review SARIF properties.packet_digest does not match the "
            f"bound packet ({claimed} != {expected_packet_digest}); substitution refused"
        )
    findings = rederive_findings(document, subject_root)
    rewritten = _rewrite_with_rederived_regions(document, subject_root)
    # Generic validation checks coverage and the actual re-derived regions;
    # only the review identities above enter the common outcome reduction.
    _, witnessed = _findings(rewritten, subject_root)
    return findings, witnessed


def empty_handbook_digest() -> str:
    """Digest of zero chapters — the packet's handbook field when none applied."""

    return "sha256:" + canonical_sha256([])


def parse_delegated_review_artifact(
    path: str | Path,
    manifest: Mapping[str, object],
    *,
    subject_root: Path,
    expected_packet_digest: str,
) -> dict[str, object]:
    """Read a present delegated-review SARIF and summarise it."""

    from ranex.foundation.suite_results import read_results_artifact

    return delegated_review_results_from_sarif(
        read_results_artifact(path),
        manifest,
        subject_root=subject_root,
        expected_packet_digest=expected_packet_digest,
    )


def emit_worker_sarif(
    *,
    root: Path,
    path: str,
    category: str,
    excerpt: str,
    level: str = "warning",
    message: str = "delegated-review finding",
    forged_lines: tuple[int, int] | None = None,
) -> bytes:
    """Deterministic worker: packet in → SARIF out (no model, for proofs)."""

    packet_path = root / "governance" / "review-packet.json"
    payload = json.loads(packet_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("governance/review-packet.json must be an object")
    digest = packet_digest(validate_packet(payload))
    anchor = resolve_anchor(root, path, excerpt)
    if forged_lines is not None:
        start, end = forged_lines
    elif anchor is not None:
        start, end = anchor
    else:
        raise ValueError(f"excerpt does not uniquely resolve in {path!r}")
    document = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "ranex-delegated-review",
                        "rules": [
                            {"id": category, "shortDescription": {"text": category}}
                        ],
                    }
                },
                "properties": {"packet_digest": digest},
                "results": [
                    {
                        "ruleId": category,
                        "level": level,
                        "message": {"text": message},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": path},
                                    "region": {
                                        "startLine": start,
                                        "endLine": end,
                                        "snippet": {"text": excerpt},
                                    },
                                }
                            }
                        ],
                    }
                ],
            }
        ],
    }
    return canonical_json_bytes(document)


def main(argv: list[str] | None = None) -> int:
    """``python -m ranex.foundation.delegated_review`` — bound-command worker."""

    import argparse

    parser = argparse.ArgumentParser(prog="ranex.foundation.delegated_review")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-format", choices=["sarif"], required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--category", default="review.finding")
    parser.add_argument("--excerpt", required=True)
    parser.add_argument(
        "--level", default="warning", choices=["error", "warning", "note", "none"]
    )
    parser.add_argument("--message", default="delegated-review finding")
    parser.add_argument(
        "--forge-lines",
        metavar="START:END",
        help="write untrusted producer line numbers (admission must re-derive)",
    )
    args = parser.parse_args(argv)
    forged: tuple[int, int] | None = None
    if args.forge_lines:
        start_s, end_s = args.forge_lines.split(":", 1)
        forged = (int(start_s), int(end_s))
    artifact = emit_worker_sarif(
        root=args.root.resolve(),
        path=args.path,
        category=args.category,
        excerpt=args.excerpt,
        level=args.level,
        message=args.message,
        forged_lines=forged,
    )
    Path(args.output_file).write_bytes(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

