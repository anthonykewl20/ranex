"""Pure, plain-text verdict presentation from a verified projection."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ranex.governed_execution.domain.admission import Admission
from ranex.governed_execution.domain.verdict import Evaluation, Verdict
from ranex.governed_execution.verdict_projection import presentation_partition


def render_verdict_stdout(result: Evaluation, admission: Admission,
                          projected: Mapping[str, Any]) -> str:
    lines: list[str] = []
    emit = lines.append
    if result.verdict is Verdict.PASS:
        emit(f"PASS  gate={result.gate_id}  subject={result.subject_digest}")
    else:
        emit(f"FAIL  gate={result.gate_id}  rule={result.failing_rule}")

    # Reported whatever the verdict. A forgery the gate happened to pass without
    # is still a forgery, and returning early on PASS made a probe that leaves no
    # trace — which is a probe worth repeating.
    for rejection in admission.rejections:
        emit(
            f"      REFUSED record {rejection.index} "
            f"[{rejection.reason}] {rejection.detail}"
        )

    if result.verdict is Verdict.PASS:
        return "\n".join(lines) + "\n"

    # Three different events arrive as `missing_claims`, and the operator must
    # not have to guess which one happened: a record was refused (an attack), a
    # record describes another tree (a replay), or the work was never done. The
    # kernel names them in one sentence because it judges claims, not causes;
    # partitioning per claim here is what keeps a forgery from being printed
    # under the phrasing reserved for honest absence.

    # A rejection carries the claim it names, and `claim_id` is read off the
    # record with `_text_or_none` — so changing that one field to a non-string
    # produces a rejection naming no claim at all. None intersects no required
    # claim, so the claim used to fall through into `absent` and print under the
    # kernel's phrasing for honest absence: the attacker chose the wording of
    # the report by choosing which field to tamper with. Counted separately, and
    # the absence sentence is withheld while any of them exist.
    # A claim some admitted record names is not work never done, whatever else
    # is wrong with that record: it may describe another tree, another command,
    # or a run that failed. Each of those is an event an operator must be able
    # to tell from silence, and the kernel already names which one it was — so
    # the absence sentence is spent only on claims nothing was recorded for, and
    # the kernel's diagnosis is printed for the rest. A digest mismatch reported
    # as absence is the reporting defect SLICE-002 was reopened to fix, one
    # field further along.
    unattributable, refused, absent, observed = presentation_partition(projected, admission)
    missing = set(result.missing_claims)

    # The absence sentence this block prints, verbatim, when it prints one.
    # The kernel's own diagnosis follows and restates that same absence as its
    # final clause; a sentence printed twice reads as two separate problems.
    absence_sentence: str | None = None
    if refused:
        emit(
            f"      {len(admission.rejections)} record(s) were refused above; "
            f"no verifying evidence remains for: {', '.join(refused)}"
        )
    if absent and unattributable:
        emit(
            f"      {unattributable} record(s) above were refused without a usable "
            "claim_id, so these required claims cannot be called work never "
            f"done: {', '.join(absent)}"
        )
    elif absent:
        absence_sentence = f"no evidence for required claim: {', '.join(absent)}"
        emit(f"      {absence_sentence}")
    # RISK-11: name restored deletions before the kernel's own diagnosis so an
    # operator cannot read a vanished FAIL as work never done.
    for cause in projected["causes"]:
        if cause.get("cause") != "removed-observation":
            continue
        detail = cause.get("detail")
        suffix = f"  {detail}" if isinstance(detail, str) and detail else ""
        emit(f"      removed-observation: {cause['claim_id']}{suffix}")
    if result.reason and (observed or not missing):
        # The kernel's own diagnosis, kept whenever it says something the
        # partition cannot: which of the four ways a record failed to satisfy
        # the claim it names, a contradiction between two records, or a
        # self-approval refusal that names no claim at all. Withheld when every
        # missing claim is genuinely absent, because then it would only repeat
        # the sentence printed above — possibly for claims that were refused.
        #
        # That withholding covered the all-absent case only. In the mixed case
        # — one claim stale, another genuinely absent — the reason carries both
        # clauses and the absence one was already printed above, so it appeared
        # twice in a single verdict. The genuine absence clause is always the
        # reason's FINAL clause (_diagnosis appends it last), so the repeat is
        # removed by anchored suffix comparison — never by splitting the
        # reason, whose "; " separator a claim ID may legally contain. When
        # any missing claim ID carries "; ", the string is ambiguous and dedup
        # steps aside entirely: the full reason prints verbatim, duplicate and
        # all — fail toward repetition, never toward loss. The reason string
        # itself is unchanged — it is the recorded diagnosis and what the
        # journal and verdict record carry. This is presentation only.
        reason = result.reason
        if absence_sentence is not None and not any(
            "; " in claim_id for claim_id in missing
        ):
            suffix = f"; {absence_sentence}"
            if reason == absence_sentence:
                reason = ""
            elif reason.endswith(suffix):
                reason = reason[: -len(suffix)]
        if reason:
            emit(f"      {reason}")

    emit(f"      subject={result.subject_digest}")
    return "\n".join(lines) + "\n"
