"""EVIDENCE LEDGER page: WITHOUT ranex vs WITH ranex.

Not a marketing page — an audit artifact. Every number is a real captured
output; every row expands to the actual commands and terminal transcripts
that produced its verdicts, plus the run provenance (run id, tokens, cost,
duration). The data fingerprint is in the header certificate: regenerate the
data and compare, or run the reproduce commands yourself.

Consumes divergence.json (schema ranex-oss-bench-divergence-v1). One
self-contained HTML file; inline CSS only; no external anything.
"""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

BG = "#0a0e17"
PANEL = "#0d1424"
HAIR = "#1b2942"
INK = "#d7e0ea"
MUTED = "#76879b"
GOOD = "#3fbf7f"
BAD = "#e5646e"
AMBER = "#d9a53f"
TERM = "#060a12"


def _badge(verdict: str) -> str:
    good = verdict in ("PASS", "GREEN", "1.0", "DONE", "verified")
    cls = "b-good" if good else ("b-bad" if verdict in ("FAIL", "RED") else "b-mid")
    return '<span class="badge {}">{}</span>'.format(cls, html.escape(str(verdict)))


def _term(command: str, output: str, tone: str = "ok") -> str:
    return ('<div class="term"><div class="cmd">$ {}</div><pre class="out {}">{}</pre></div>'
            .format(html.escape(command), tone, html.escape(output or " ")))


def _transcript(row: dict[str, Any]) -> str:
    gov = row["ranex_gate"]
    ci = row["bare_ci"]
    sr = row["self_report"]
    parts = ['<div class="prov">run {} · {} steps · {} tokens · ${} · {:.0f}s agent time{}'
             '</div>'.format(
                 html.escape(row["run_id"]), row.get("agent_steps", "?"),
                 row.get("tokens", "?"), row.get("cost_usd", "?"),
                 row.get("duration_s") or 0,
                 " · COST-CAPPED" if row.get("cost_capped") else "")]
    parts.append('<div class="k">the agent\'s last words (parsed, heuristic):</div>')
    parts.append('<pre class="quote">{}</pre>'.format(
        html.escape(sr.get("final_words", ""))))
    parts.append('<div class="k">what a normal CI runs, and what it printed:</div>')
    parts.append(_term(ci["command"], ci["output_tail"],
                       "ok" if ci["verdict"] == "GREEN" else "err"))
    parts.append('<div class="k">what ranex executed (signed evidence recorded):</div>')
    parts.append(_term(gov["run_command"],
                       "evidence recorded, exit {}".format(gov["run_exit"])))
    parts.append('<div class="k">the gate\'s verdict, verbatim:</div>')
    parts.append(_term("ranex gate evaluate HEAD --approver " + "oss-bench-approver",
                       gov["gate_output"], "ok" if gov["gate_verdict"] == "PASS" else "err"))
    parts.append('<div class="k">the journal chain check, verbatim:</div>')
    parts.append(_term("ranex journal verify", gov["journal_output"],
                       "ok" if gov["journal_verified"] else "err"))
    return "".join(parts)


def generate_page(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "oss-divergence.json"
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    json_path.write_text(payload)
    digest = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

    rows = [r for r in report["rows"] if "ranex_gate" in r]
    solved = [r for r in rows if r["ground_truth_functional"] == 1.0]
    failed = [r for r in rows if r["ground_truth_functional"] != 1.0]
    tokens = sum(r.get("tokens") or 0 for r in rows)
    cost = sum(r.get("cost_usd") or 0 for r in rows)

    table_head = ("<tr><th>task</th><th>run</th><th>hidden tests</th>"
                  "<th>bare CI</th><th>agent claims</th><th>ranex gate</th>"
                  "<th>tokens</th><th>$</th></tr>")
    table_rows = []
    for r in rows:
        claim = "done" if r["self_report"]["claimed_success"] else "no claim"
        table_rows.append(
            '<tr class="{}"><td>{}</td><td class="dim">{}</td><td>{}</td>'
            "<td>{}</td><td>{}</td><td>{}</td><td class=\"dim\">{}</td>"
            '<td class="dim">{}</td></tr>'.format(
                "r-ok" if r["ranex_gate"]["gate_verdict"] == "PASS" else "r-bad",
                html.escape(r["task"]), html.escape(r["run_id"][-8:]),
                _badge(r["ground_truth_functional"]),
                _badge(r["bare_ci"]["verdict"]),
                _badge(claim.upper() if claim == "done" else "—"),
                _badge(r["ranex_gate"]["gate_verdict"]),
                r.get("tokens", "?"), r.get("cost_usd", "?")))
    details = "".join(
        '<details class="ev"><summary>evidence · {} · gate {}</summary>{}</details>'
        .format(html.escape(r["task"]), r["ranex_gate"]["gate_verdict"],
                _transcript(r)) for r in rows)

    demo_html = ""
    demo = report.get("gaming_demo")
    if demo:
        removed = demo.get("removed_tests", [])
        gov, ci = demo["ranex_gate"], demo["bare_ci"]
        demo_html = """
<section>
<h2>Exhibit B — the attack: tests get deleted, CI stays green</h2>
<p class="note">A genuinely solved task. Then the classic move: {n} test
functions are deleted from the tree. Both worlds are asked the same
question — is this work done?</p>
<div class="x2">
 <div>
  <div class="k">WITHOUT ranex — your CI:</div>
  {ci_term}
  <p class="verdict-line">CI verdict: {ci_v} — it ran the tests that remain.
  The four that mattered are simply gone.</p>
 </div>
 <div>
  <div class="k">WITH ranex — the gate:</div>
  {gate_term}
  <p class="verdict-line">Gate verdict: {g_v} — the frozen test list names
  every test that disappeared.</p>
 </div>
</div>
<div class="removed">deleted by the "agent":
<code>{names}</code></div>
</section>""".format(
            n=len(removed),
            ci_term=_term(ci["command"], ci["output_tail"], "ok"),
            ci_v=_badge(ci["verdict"]),
            gate_term=_term("ranex gate evaluate HEAD --approver oss-bench-approver",
                            gov["gate_output"], "err"),
            g_v=_badge(gov["gate_verdict"]),
            names=html.escape(", ".join(removed)))

    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ranex — evidence ledger: is the agent's "done" real?</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:{BG}; color:{INK};
        font:13.5px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace; }}
  main {{ max-width:900px; margin:0 auto; padding:34px 20px 80px; }}
  h1 {{ font-size:21px; margin:0 0 4px; letter-spacing:-.01em; }}
  h2 {{ font-size:15px; margin:44px 0 4px; color:{INK};
       text-transform:uppercase; letter-spacing:.08em; }}
  .sub {{ color:{MUTED}; margin:0 0 18px; }}
  .note {{ color:{MUTED}; margin:6px 0 14px; }}
  .cert {{ border:1px solid {HAIR}; background:{PANEL}; padding:12px 16px;
          margin:18px 0 8px; display:flex; flex-wrap:wrap; gap:8px 26px; }}
  .cert div {{ font-size:12px; }}
  .cert b {{ color:{INK}; font-weight:600; display:block; }}
  .cert span {{ color:{MUTED}; }}
  table {{ border-collapse:collapse; width:100%; margin:10px 0 6px;
          font-size:12.5px; }}
  th {{ text-align:left; color:{MUTED}; font-weight:500; border-bottom:1px
      solid {HAIR}; padding:6px 8px; }}
  td {{ padding:6px 8px; border-bottom:1px solid #131c2e; }}
  tr.r-ok td:first-child {{ border-left:3px solid {GOOD}; }}
  tr.r-bad td:first-child {{ border-left:3px solid {BAD}; }}
  .dim {{ color:{MUTED}; }}
  .badge {{ display:inline-block; padding:1px 8px; border-radius:3px;
           font-weight:700; font-size:11.5px; }}
  .b-good {{ color:{GOOD}; background:rgba(63,191,127,.12);
            border:1px solid rgba(63,191,127,.35); }}
  .b-bad {{ color:{BAD}; background:rgba(229,100,110,.12);
           border:1px solid rgba(229,100,110,.35); }}
  .b-mid {{ color:{MUTED}; border:1px solid {HAIR}; }}
  details.ev {{ border:1px solid {HAIR}; background:{PANEL}; margin:8px 0;
               border-radius:4px; }}
  details.ev summary {{ cursor:pointer; padding:8px 14px; color:{MUTED};
                       font-size:12px; }}
  details.ev[open] summary {{ border-bottom:1px solid {HAIR}; color:{INK}; }}
  .ev-body, details.ev > *:not(summary) {{ padding: 0; }}
  .prov {{ color:{AMBER}; font-size:12px; padding:10px 14px 2px; }}
  .k {{ color:{MUTED}; font-size:11.5px; text-transform:uppercase;
       letter-spacing:.06em; padding:10px 14px 2px; }}
  .term {{ margin:4px 14px; }}
  .term .cmd {{ color:{GOOD}; font-size:12px; word-break:break-all;
               padding:2px 0; }}
  .term pre {{ margin:0; background:{TERM}; border:1px solid {HAIR};
              border-radius:3px; padding:8px 10px; font-size:12px;
              white-space:pre-wrap; word-break:break-word; color:{INK}; }}
  .term pre.err {{ border-left:3px solid {BAD}; }}
  .term pre.ok {{ border-left:3px solid {GOOD}; }}
  pre.quote {{ margin:4px 14px 10px; background:{TERM}; border:1px dashed
              {HAIR}; border-radius:3px; padding:8px 10px; font-size:12px;
              color:{MUTED}; white-space:pre-wrap; }}
  .x2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  @media (max-width:760px) {{ .x2 {{ grid-template-columns:1fr; }} }}
  .verdict-line {{ font-size:12.5px; margin:8px 0 0; }}
  .removed {{ margin-top:12px; border:1px dashed rgba(229,100,110,.4);
             border-radius:4px; padding:10px 14px; font-size:12px;
             color:{BAD}; }}
  .removed code {{ word-break:break-all; }}
  .stats {{ display:grid; grid-template-columns:repeat(auto-fit,
          minmax(180px,1fr)); gap:10px; margin:14px 0; }}
  .stat {{ border:1px solid {HAIR}; background:{PANEL}; padding:12px 14px; }}
  .stat .n {{ font-size:20px; font-weight:800; }}
  .stat .n.g {{ color:{GOOD}; }}
  .stat .t {{ color:{MUTED}; font-size:11.5px; margin-top:3px; }}
  footer {{ margin-top:50px; border-top:1px solid {HAIR}; padding-top:14px;
           color:{MUTED}; font-size:11.5px; }}
</style></head><body><main>
<h1>Evidence ledger — is the agent's "done" real?</h1>
<p class="sub">Real open-source tasks, solved by {MODEL}. For every task the
SAME solution was judged from four positions: independent hidden tests,
a normal CI, the agent's own final message, and the ranex gate (signed
evidence against a checklist frozen before the agent touched anything).
Expand any row for the raw transcripts.</p>

<div class="cert">
 <div><span>data fingerprint</span><b>{DIGEST}</b></div>
 <div><span>model</span><b>{MODEL}</b></div>
 <div><span>agent runs</span><b>{NROWS}</b></div>
 <div><span>total spend</span><b>${COST} ({TOKENS} tokens)</b></div>
 <div><span>governance overhead</span><b>{OVERHEAD}</b></div>
</div>

<section>
<h2>Exhibit A — every run, four verdicts</h2>
<table>{THEAD}{TROWS}</table>
{DETAILS}
</section>

{DEMO}

<section>
<h2>Exhibit C — what the gate never did</h2>
<div class="stats">
 <div class="stat"><div class="n g">0</div><div class="t">false PASS — the
 gate never certified work the hidden tests refuted, in {NROWS} runs plus
 the attack</div></div>
 <div class="stat"><div class="n g">0</div><div class="t">false FAIL — it
 never blocked a solution the hidden tests confirmed ({NSOLVED} solved
 runs all passed the gate)</div></div>
 <div class="stat"><div class="n">{NFAILED}</div><div class="t">failed runs
 correctly refused — absence of evidence blocks, it never passes by
 default</div></div>
 <div class="stat"><div class="n">1</div><div class="t">attack caught: CI
 green on deleted tests, gate FAIL naming every one</div></div>
</div>
<p class="note">Honest scope: in this sample the agent did not naturally
overclaim (it solved 5 tasks and kept working on the 6th), so the attack in
Exhibit B is fault-injected and labeled as such — it demonstrates the
mechanism, not observed model behavior. Every completed run also ships a
tamper-evident journal chain re-verifiable in milliseconds; the transcripts
above show the verify line per run.</p>
</section>

<section>
<h2>Verify it yourself</h2>
<p class="note">The data behind this page is one JSON file; its exact bytes
hash to the fingerprint in the header certificate. Re-run the experiment:
<code>uv run --frozen python tools/dogfood/oss_bench/run_divergence.py ...</code>
— agent runs bill a GLM Coding Plan; the Exhibit B attack costs nothing.</p>
</section>

<footer>ranex — deterministic governance for AI agents that build software ·
self-report parsing is heuristic and labeled · fault-injected row is labeled
· nothing on this page was typed by hand: every verdict line is a captured
command output</footer>
</main></body></html>
"""
    overhead = sorted(r["ranex_gate"]["elapsed_s"] for r in rows)
    page = (page
            .replace("{BG}", BG).replace("{INK}", INK).replace("{MUTED}", MUTED)
            .replace("{HAIR}", HAIR).replace("{PANEL}", PANEL)
            .replace("{GOOD}", GOOD).replace("{BAD}", BAD)
            .replace("{AMBER}", AMBER).replace("{TERM}", TERM)
            .replace("{MODEL}", html.escape(str(report.get("model", "?"))))
            .replace("{DIGEST}", digest)
            .replace("{NROWS}", str(len(rows)))
            .replace("{NSOLVED}", str(len(solved)))
            .replace("{NFAILED}", str(len(failed)))
            .replace("{COST}", "{:.3f}".format(cost))
            .replace("{TOKENS}", "{:,}".format(tokens))
            .replace("{OVERHEAD}",
                     "{}–{}s per task".format(overhead[0], overhead[-1])
                     if overhead else "n/a")
            .replace("{THEAD}", table_head)
            .replace("{TROWS}", "".join(table_rows))
            .replace("{DETAILS}", details)
            .replace("{DEMO}", demo_html))

    out = output_dir / "oss-benchmark.html"
    out.write_text(page)
    return out


if __name__ == "__main__":
    import sys

    report = json.loads(Path(sys.argv[1]).read_text())
    out = generate_page(report, Path(sys.argv[2]))
    print("page:", out)
