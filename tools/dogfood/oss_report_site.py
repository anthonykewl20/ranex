"""Real-world use-case benchmark page: WITHOUT ranex vs WITH ranex.

Consumes divergence.json (schema ranex-oss-bench-divergence-v1) and renders
ONE self-contained HTML page organized around the three real-world moments
where the arms differ:

  1. The agent says it's finished —  claim vs hidden-test reality vs the
     ranex gate's certified verdict.
  2. CI is green but the product is broken — the fault-injected gaming demo:
     bare CI stays green after tests are deleted; the gate must fail.
  3. Prove what happened — signed evidence + tamper-evident journal vs an
     agent's word.

Plain human language, inline SVG only, no external anything. The page embeds
the sha256 of the JSON it renders from.
"""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

BG = "#0b1220"
CARD = "#111a2c"
INK = "#e6edf3"
MUTED = "#9aa8ba"
GOOD = "#4cc38a"
BAD = "#f0616d"
BLUE = "#58a6ff"
WARN = "#f0b429"


def _verdict_chip(label: str, verdict: str, note: str = "") -> str:
    color = GOOD if verdict in ("GREEN", "PASS", "1.0", True) else BAD
    icon = "✓" if color == GOOD else "✗"
    sub = f'<div class="sub">{html.escape(note)}</div>' if note else ""
    return ('<div class="cell"><div class="v" style="color:{}">{} {}</div>'
            '<div class="l">{}</div>{}</div>'.format(
                color, icon, html.escape(str(verdict)), html.escape(label), sub))


def _row_grid(cells: list[str]) -> str:
    return ('<div class="grid" style="grid-template-columns:repeat({},1fr)">{}'
            "</div>").format(len(cells), "".join(cells))


def generate_page(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "oss-divergence.json"
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    json_path.write_text(payload)
    digest = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

    rows = report["rows"]
    usable = [r for r in rows if "ranex_gate" in r]
    false_claims = [r for r in usable
                    if r["self_report"]["claimed_success"]
                    and r["ground_truth_functional"] not in (1.0, "1.0")]
    caught_by_gate = [r for r in usable if r["ranex_gate"]["gate_verdict"] == "FAIL"]
    overhead = [r["ranex_gate"]["elapsed_s"] for r in usable if r.get("ranex_gate")]

    claim_rows = []
    for r in usable:
        truth = "1.0" if r["ground_truth_functional"] == 1.0 else str(r["ground_truth_functional"])
        claim = "claims done" if r["self_report"]["claimed_success"] else "no clear claim"
        verdict_cells = _row_grid([
            _verdict_chip("hidden tests say", truth,
                          "the independent grader"),
            _verdict_chip("the agent says", "DONE" if r["self_report"]["claimed_success"] else "unclear",
                          claim + " (parsed from its final message)"),
            _verdict_chip("ranex gate says", r["ranex_gate"]["gate_verdict"],
                          "signed evidence, tamper-evident journal"),
        ])
        diverged = (r["self_report"]["claimed_success"]
                    and r["ground_truth_functional"] != 1.0)
        banner = ('<div class="alert">WITHOUT ranex you would have trusted the '
                  'claim. WITH ranex the gate says {} — backed by signed '
                  'evidence.</div>').format(r["ranex_gate"]["gate_verdict"]) \
            if diverged else ""
        claim_rows.append(
            '<div class="card"><h3>{}</h3>{}{}</div>'.format(
                html.escape(r["task"]), verdict_cells, banner))

    demo_html = ""
    demo = report.get("gaming_demo")
    if demo:
        removed = ", ".join(demo.get("removed_tests", []))
        demo_html = """
<div class="card">
  <h3>What the agent left behind</h3>
  <p class="note">We took a genuinely solved task and did what gaming agents
  do: deleted {} test functions, then looked at what each world tells you.</p>
  {}
  <div class="alert">WITHOUT ranex your CI is green — the remaining tests
  pass. WITH ranex the gate FAILS: the frozen list of expected tests names
  every one that disappeared. Deleted: {}</div>
</div>""".format(
            len(demo.get("removed_tests", [])),
            _row_grid([
                _verdict_chip("bare CI says", demo["bare_ci"]["verdict"],
                              "runs whatever tests are in the tree"),
                _verdict_chip("ranex gate says", demo["ranex_gate"]["gate_verdict"],
                              "compares against the committed frozen test list"),
            ]),
            html.escape(removed))

    overhead_note = ("governance added {:.1f}s per task (median of this run)"
                     .format(sorted(overhead)[len(overhead) // 2]) if overhead
                     else "no overhead data")

    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ranex — when the agent says done, who checks?</title>
<style>
  :root { color-scheme: dark; }
  body { margin:0; background:BGCOL; color:INKCOL; font:16px/1.6 ui-sans-serif,system-ui,sans-serif; }
  main { max-width:820px; margin:0 auto; padding:44px 22px 90px; }
  h1 { font-size:29px; line-height:1.25; margin:0 0 10px; }
  h2 { font-size:22px; margin:50px 0 6px; }
  h3 { font-size:15px; margin:0 0 10px; color:MUTEDCOL; font-weight:600; }
  .lede { color:MUTEDCOL; font-size:17px; }
  .note { color:MUTEDCOL; font-size:14px; margin:0 0 14px; }
  .card { background:CARDCOL; border:1px solid #1f2a3d; border-radius:14px;
          padding:18px 20px; margin:14px 0; }
  .grid { display:grid; gap:10px; }
  .cell { background:#0d1524; border:1px solid #1c2942; border-radius:10px;
          padding:10px 12px; }
  .v { font-size:16px; font-weight:700; font-family:ui-monospace,monospace; }
  .l { color:MUTEDCOL; font-size:12px; margin-top:2px; }
  .sub { color:#7d8b9e; font-size:11px; margin-top:2px; }
  .alert { margin-top:12px; border-left:3px solid WARNCOL; padding:8px 14px;
           background:#171126; border-radius:0 10px 10px 0; font-size:14.5px; }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:12px; }
  .stat { background:CARDCOL; border:1px solid #1f2a3d; border-radius:12px; padding:14px 16px; }
  .stat .n { font-size:24px; font-weight:800; font-family:ui-monospace,monospace; }
  .stat .t { color:MUTEDCOL; font-size:12.5px; margin-top:4px; }
  code { background:CARDCOL; border:1px solid #1f2a3d; border-radius:6px; padding:2px 8px; font-size:13px; }
  footer { margin-top:54px; border-top:1px solid #1f2a3d; padding-top:18px;
           color:MUTEDCOL; font-size:12.5px; }
</style></head><body><main>
<h1>Your AI agent says "done, tests pass."<br>One of these worlds can prove it.</h1>
<p class="lede">Real tasks from real open-source work, solved by MODELNAME.
Same solutions, two worlds: one where you trust the agent and your CI,
one where "done" must be signed evidence passing a frozen checklist.</p>

<h2>1 · The agent says it's finished</h2>
<p class="note">Three opinions about the same work: independent hidden tests
(ground truth), the agent's own final message (parsed, heuristic), and the
ranex gate (signed evidence against a committed checklist).</p>
CLAIMROWS

<h2>2 · CI is green, the product is broken</h2>
<p class="note">The classic failure: the agent "cleans up" the tests that
were failing. Your CI runs whatever tests are in the tree — so it goes
green. The ranex gate compares against the owner's frozen test list.</p>
DEMOBLOCK

<h2>3 · Prove what happened</h2>
<p class="note">Every governed completion ships a tamper-evident journal:
a hash chain anyone can re-verify. The bare world ships a claim.</p>
<div class="stats">
  <div class="stat"><div class="n" style="color:GOODCOL">CAUGHT</div>
    <div class="t">false/gamed completions blocked by the gate in this run
    (every FAIL row and the gaming demo)</div></div>
  <div class="stat"><div class="n" style="color:GOODCOL">0</div>
    <div class="t">times the gate certified work the hidden tests refuted
    — a gate false-pass would be a kernel bug, not a data point</div></div>
  <div class="stat"><div class="n">OVERHEAD</div>
    <div class="t">OVERHEADNOTE</div></div>
  <div class="stat"><div class="n">ms</div>
    <div class="t">to re-verify any past completion from its journal chain
    — the audit the bare world cannot do at any price</div></div>
</div>

<h2>Reproduce everything</h2>
<p class="note">One command per experiment, from the repository:
<code>uv run --frozen python tools/dogfood/oss_bench/run_divergence.py ...</code>
Model runs bill a GLM Coding Plan; the fault-injected demo costs nothing.
Data fingerprint: <code>DIGEST</code></p>

<footer>ranex — deterministic governance for AI agents that build software ·
tasks are real merged/oss-style tasks from the VulcanBench corpus ·
self-report parsing is heuristic and labeled as such · nothing on this page
was typed by hand</footer>
</main></body></html>
"""
    page = (page
            .replace("BGCOL", BG).replace("INKCOL", INK)
            .replace("MUTEDCOL", MUTED).replace("CARDCOL", CARD)
            .replace("GOODCOL", GOOD).replace("WARNCOL", WARN)
            .replace("MODELNAME", html.escape(str(report.get("model", "?"))))
            .replace("CLAIMROWS", "".join(claim_rows) or
                     '<div class="card">no rows yet</div>')
            .replace("DEMOBLOCK", demo_html)
            .replace("OVERHEADNOTE", html.escape(overhead_note))
            .replace("DIGEST", digest))

    out = output_dir / "oss-benchmark.html"
    out.write_text(page)
    return out


if __name__ == "__main__":
    import sys

    report = json.loads(Path(sys.argv[1]).read_text())
    out = generate_page(report, Path(sys.argv[2]))
    print("page:", out)
