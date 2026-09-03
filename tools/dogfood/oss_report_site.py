"""Story page: the difference between WITH and WITHOUT ranex, told simply.

Layered design (no dumbing down, no jargon wall):
  LAYER 1 — the story anyone can follow: the problem, the one-sentence
  difference, the attack demo as a visual checklist, and the three-part
  "how it works" — all in everyday words (checklist, signed proof,
  record book) with inline SVG diagrams, no decorative fluff.
  LAYER 2 — the receipts: one collapsed section holds the audit ledger
  (per-run table + raw terminal transcripts + fingerprint + reproduce
  commands) for anyone who wants proof, not story.

Every number in layer 1 is the same number layer 2 proves. Nothing is
decorative data. Self-contained HTML; inline SVG/CSS only.
"""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

BG = "#0b1220"
PANEL = "#111a2c"
HAIR = "#1f2a3d"
INK = "#e8eef5"
MUTED = "#93a1b4"
GOOD = "#4cc38a"
BAD = "#f0616d"
BLUE = "#58a6ff"
AMBER = "#f0b429"
TERM = "#060a12"

DELETED_TESTS = ("test_construct", "test_autocommit_without_transaction",
                 "test_rollback_restores_prior_value_and_absence",
                 "test_rollback_restores_deleted_key")
KEPT_TESTS = ("test_commit_keeps_changes", "test_nested_commit",
              "test_rollback_reverse_order", "test_commit_without_txn",
              "test_keys_reflects_txn")


def _esc(value: any) -> str:
    return html.escape(str(value))


def _hero_svg() -> str:
    """The one-sentence difference, drawn: same claim, two worlds."""
    def bubble(x, y, w, text, fill, stroke, tcol):
        lines = text.split("\n")
        tspans = "".join(
            '<tspan x="{}" dy="{}">{}</tspan>'.format(x + 14, 22 + i * 17, _esc(line))
            for i, line in enumerate(lines))
        h = 26 + 17 * len(lines)
        return ('<rect x="{}" y="{}" width="{}" height="{}" rx="10" fill="{}" '
                'stroke="{}"/>' .format(x, y, w, h, fill, stroke)
                + '<text x="{}" y="{}" fill="{}" font-size="12.5">{}</text>'
                .format(x, y, tcol and 0 or 0, tcol, "")  # placeholder
                + '<text fill="{}" font-size="12.5">{}</text>'.format(tcol, tspans))
    # simpler explicit layout
    left = """
    <text x="20" y="34" fill="{MUTED}" font-size="13" font-weight="700">WITHOUT RANEX</text>
    <rect x="20" y="52" width="300" height="62" rx="12" fill="{PANEL}" stroke="{HAIR}"/>
    <text x="40" y="78" fill="{INK}" font-size="13.5">🤖 “Done! All tests pass.”</text>
    <text x="40" y="98" fill="{MUTED}" font-size="12">its word. nothing else attached.</text>
    <path d="M170 122 v34" stroke="{MUTED}" stroke-width="2" marker-end="url(#arr)"/>
    <rect x="20" y="164" width="300" height="78" rx="12" fill="{PANEL}" stroke="{HAIR}"/>
    <text x="40" y="192" fill="{INK}" font-size="13.5">😃 “Great — merging it.”</text>
    <text x="40" y="214" fill="{MUTED}" font-size="12">if the agent was wrong or gamed</text>
    <text x="40" y="230" fill="{MUTED}" font-size="12">the tests, you find out in production.</text>
    """.replace("{MUTED}", MUTED).replace("{INK}", INK).replace("{PANEL}", PANEL).replace("{HAIR}", HAIR)
    right = """
    <text x="460" y="34" fill="{GOOD}" font-size="13" font-weight="700">WITH RANEX</text>
    <rect x="460" y="52" width="300" height="62" rx="12" fill="{PANEL}" stroke="{HAIR}"/>
    <text x="480" y="78" fill="{INK}" font-size="13.5">🤖 “Done! All tests pass.”</text>
    <text x="480" y="98" fill="{MUTED}" font-size="12">same agent, same claim.</text>
    <path d="M610 122 v34" stroke="{MUTED}" stroke-width="2" marker-end="url(#arr)"/>
    <rect x="460" y="164" width="300" height="78" rx="12" fill="{PANEL}" stroke="{GOOD}" stroke-opacity="0.55"/>
    <text x="480" y="192" fill="{INK}" font-size="13.5">🔒 the claim must pass a frozen</text>
    <text x="480" y="210" fill="{INK}" font-size="13.5">checklist with signed proof —</text>
    <text x="480" y="228" fill="{GOOD}" font-size="12.5">verified ✓ or blocked ✗, in writing.</text>
    """
    right = right.replace("{GOOD}", GOOD).replace("{MUTED}", MUTED).replace("{INK}", INK) \
                 .replace("{PANEL}", PANEL).replace("{HAIR}", HAIR)
    return ('<svg viewBox="0 0 780 260" xmlns="http://www.w3.org/2000/svg" '
            'font-family="ui-sans-serif,system-ui,sans-serif" role="img" '
            'aria-label="same claim, two worlds">'
            '<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="4" refY="4" '
            'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="' + MUTED + '"/></marker></defs>'
            + left
            + '<line x1="410" y1="30" x2="410" y2="230" stroke="' + HAIR + '" stroke-dasharray="4 5"/>'
            + right + "</svg>")


def _checklist_svg() -> str:
    """The attack story: one checklist, two readers."""
    def slot(y, name, state):
        if state == "gone":
            return (f'<rect x="40" y="{y}" width="440" height="34" rx="6" fill="none" '
                    f'stroke="{HAIR}" stroke-dasharray="5 5"/>'
                    f'<text x="58" y="{y + 22}" fill="{MUTED}" font-size="12.5" '
                    f'text-decoration="line-through">{_esc(name)}</text>')
        icon, col, label = {
            "ok": ("✓", GOOD, ""), "missing": ("✗", BAD, "  ← MISSING"),
        }[state]
        return (f'<text x="58" y="{y + 23}" fill="{col}" font-size="15" '
                f'font-weight="700">{icon}</text>'
                f'<text x="84" y="{y + 22}" fill="{BAD if state == "missing" else INK}" '
                f'font-size="12.5">{_esc(name)}</text>'
                f'<text x="330" y="{y + 22}" fill="{col}" font-size="12" '
                f'font-weight="700">{label}</text>')
    states = {"gone": ("test_construct", "gone"),
              "missing": ("test_autocommit_without_transaction", "missing"),
              "missing2": ("test_rollback_restores_prior_value_and_absence", "missing"),
              "missing3": ("test_rollback_restores_deleted_key", "missing"),
              "ok1": ("test_commit_keeps_changes", "ok"),
              "ok2": ("test_keys_reflects_txn", "ok")}
    rows_svg = ""
    y = 96
    for key in ("gone", "missing", "missing2", "missing3", "ok1", "ok2"):
        name, state = states[key]
        rows_svg += slot(y, name, state) + "\n"
        y += 44
    return ('<svg viewBox="0 0 780 420" xmlns="http://www.w3.org/2000/svg" '
            'font-family="ui-monospace,monospace" role="img" aria-label="the deleted '
            'test checklist seen two ways">'
            f'<text x="20" y="30" fill="{INK}" font-size="15" font-weight="700" '
            'font-family="ui-sans-serif,system-ui">The same repository, after the agent '
            '\u201ccleaned up\u201d some tests</text>'
            f'<text x="20" y="52" fill="{MUTED}" font-size="12.5" '
            'font-family="ui-sans-serif,system-ui">A genuinely solved task — then 4 of its '
            '9 tests were deleted. Both worlds look at the result:</text>'
            f'<text x="40" y="84" fill="{GOOD}" font-size="12.5" font-weight="700">'
            'YOUR CI (without ranex) sees:</text>'
            + rows_svg +
            f'<text x="520" y="84" fill="{BAD}" font-size="12.5" font-weight="700">'
            'RANEX sees:</text>'
            f'<rect x="510" y="96" width="250" height="128" rx="8" fill="{BAD}" '
            'fill-opacity="0.08" stroke="{BAD}" stroke-opacity="0.5"/>'
            f'<text x="528" y="124" fill="{BAD}" font-size="26" font-weight="800">BLOCKED</text>'
            f'<text x="528" y="150" fill="{INK}" font-size="12.5">the checklist frozen BEFORE the'
            '</text>'
            f'<text x="528" y="168" fill="{INK}" font-size="12.5">agent started names all 4</text>'
            f'<text x="528" y="186" fill="{INK}" font-size="12.5">missing tests.</text>'
            f'<text x="528" y="210" fill="{MUTED}" font-size="11.5">CI said: green ✓</text>'
            f'<text x="40" y="{y + 8}" fill="{MUTED}" font-size="12" '
            'font-family="ui-sans-serif,system-ui">CI runs whatever tests are still in the '
            'tree — the ones that vanished can\u2019t fail. Ranex compares against the frozen '
            'list, so they can\u2019t hide.</text>'
            "</svg>")


def _how_cards() -> str:
    steps = [
        ("1", "The checklist is frozen first",
         "Before the agent touches anything, the owner commits the exact list of "
         "checks that will count as done. The goalposts are in the record book "
         "before the game starts — the agent cannot move them."),
        ("2", "\u201cDone\u201d must arrive signed",
         "A completion isn\u2019t a sentence, it\u2019s a signed test run: the exact "
         "commands, bound to the exact version of the code, with results that "
         "must match the frozen checklist. Faked or stale runs don\u2019t count."),
        ("3", "The record book is chained",
         "Every decision is appended to a hash chain — each entry seals the "
         "previous one. Editing history leaves visible damage, and anyone can "
         "re-verify the whole chain in milliseconds."),
    ]
    cards = []
    for number, title, body in steps:
        cards.append(
            '<div class="how"><div class="how-n">{}</div><div class="how-t">{}</div>'
            '<div class="how-b">{}</div></div>'.format(
                number, _esc(title), _esc(body)))
    return "".join(cards)


def _stale_exhibit(report: dict[str, Any]) -> str:
    stale = report.get("stale_demo")
    if not stale:
        return ""
    before, after = stale["before"], stale["after"]
    return """
<h2>The proof test: \u201ctests pass\u201d is a sentence. This is a machine.</h2>
<p class="note">The trap every agent falls into eventually: it runs the tests
(green), pastes the happy output, then makes <strong>one more small fix</strong>
and says done — without re-running. The old green output still looks perfectly
valid. Nothing in the bare world can tell it stopped being evidence. The gate
can: proof is digest-bound to the exact code.</p>
<div class="x2">
 <div>
  <div class="k">the proof, right after the green run:</div>
  <div class="term"><pre class="ok">{b_out}</pre></div>
 </div>
 <div>
  <div class="k">the same proof, after ONE comment-line edit (no re-run):</div>
  <div class="term"><pre class="err">{a_out}</pre></div>
 </div>
</div>
<p class="note">The agent\u2019s screenshot still says green. The gate says the
truth: that evidence describes a tree that no longer exists. Re-run the tests
and it passes again — the point isn’t to block work, it\u2019s to refuse proof
that stopped being proof.</p>""".format(
        b_out=_esc(before["gate_output"]),
        a_out=_esc(after["gate_output"]))


def _ledger(report: dict[str, Any], digest: str) -> str:
    rows = [r for r in report["rows"] if "ranex_gate" in r]
    head = ("<tr><th>task</th><th>run</th><th>hidden tests</th><th>bare CI</th>"
            "<th>agent claims</th><th>ranex gate</th><th>tokens</th><th>$</th></tr>")
    body = ""
    for r in rows:
        claim = "done" if r["self_report"]["claimed_success"] else "—"
        def badge(v):
            good = str(v) in ("PASS", "GREEN", "1.0", "done")
            cls = "bg" if good else ("bb" if str(v) in ("FAIL", "RED") else "bm")
            return f'<span class="bd {cls}">{_esc(v)}</span>'
        body += ('<tr><td>{}</td><td class="dim">{}</td><td>{}</td><td>{}</td>'
                 "<td>{}</td><td>{}</td><td class=\"dim\">{}</td>"
                 '<td class="dim">{}</td></tr>').format(
                     _esc(r["task"]), _esc(r["run_id"][-8:]),
                     badge(r["ground_truth_functional"]), badge(r["bare_ci"]["verdict"]),
                     badge(claim), badge(r["ranex_gate"]["gate_verdict"]),
                     r.get("tokens", "?"), r.get("cost_usd", "?"))
    details = ""
    for r in rows:
        gov, ci = r["ranex_gate"], r["bare_ci"]
        details += (
            '<details class="ev"><summary>evidence · {} · gate {}</summary>'
            '<div class="prov">run {} · {} steps · {} tokens · ${} · {:.0f}s</div>'
            '<div class="k">the agent\u2019s last words (parsed, heuristic):</div>'
            '<pre class="quote">{}</pre>'
            '<div class="k">what a normal CI ran, and printed:</div>'
            '<div class="term"><div class="cmd">$ {}</div><pre class="{}">{}</pre></div>'
            '<div class="k">what ranex executed:</div>'
            '<div class="term"><div class="cmd">$ {}</div><pre class="ok">evidence recorded, exit {}</pre></div>'
            '<div class="k">the gate\u2019s verdict, verbatim:</div>'
            '<div class="term"><pre class="{}">{}</pre></div>'
            '<div class="k">the journal chain check:</div>'
            '<div class="term"><pre class="ok">{}</pre></div>'
            "</details>").format(
                _esc(r["task"]), gov["gate_verdict"], _esc(r["run_id"]),
                r.get("agent_steps", "?"), r.get("tokens", "?"),
                r.get("cost_usd", "?"), r.get("duration_s") or 0,
                _esc(r["self_report"].get("final_words", "")),
                _esc(ci["command"]),
                "ok" if ci["verdict"] == "GREEN" else "err",
                _esc(ci["output_tail"]),
                _esc(gov["run_command"]), gov["run_exit"],
                "ok" if gov["gate_verdict"] == "PASS" else "err",
                _esc(gov["gate_output"]),
                _esc(gov["journal_output"]))
    demo = report.get("gaming_demo") or {}
    demo_gate = _esc(demo.get("ranex_gate", {}).get("gate_output", ""))
    return (
        f'<details class="receipts"><summary>Show me the receipts — every run, '
        f'raw transcripts, and how to reproduce</summary>'
        f'<p class="note">Data fingerprint <code>{digest}</code> — the page is '
        f'rendered from one JSON file whose exact bytes hash to this. Re-run the '
        f'experiment yourself: <code>uv run --frozen python '
        f'tools/dogfood/oss_bench/run_divergence.py ...</code></p>'
        f'<table>{head}{body}</table>'
        f'<p class="note">The attack\u2019s gate verdict, verbatim:</p>'
        f'<div class="term"><pre class="err">{demo_gate}</pre></div>'
        + details + "</details>")


def generate_page(report: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "oss-divergence.json"
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    json_path.write_text(payload)
    digest = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

    rows = [r for r in report["rows"] if "ranex_gate" in r]
    solved = sum(1 for r in rows if r["ground_truth_functional"] == 1.0)
    overhead = sorted(r["ranex_gate"]["elapsed_s"] for r in rows)
    tokens = sum(r.get("tokens") or 0 for r in rows)
    cost = sum(r.get("cost_usd") or 0 for r in rows)

    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ranex — what changes when your AI agent's "done" has to be proven</title>
<style>
  :root { color-scheme: dark; }
  body { margin:0; background:BGX; color:INKX;
         font:16.5px/1.65 ui-sans-serif,system-ui,-apple-system,sans-serif; }
  main { max-width:820px; margin:0 auto; padding:48px 22px 90px; }
  h1 { font-size:30px; line-height:1.22; margin:0 0 12px; letter-spacing:-.01em; }
  h2 { font-size:21px; margin:54px 0 4px; }
  .lede { color:MUTX; font-size:17.5px; margin:0 0 10px; }
  .note { color:MUTX; font-size:14px; margin:6px 0 16px; }
  .x2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media (max-width:760px) { .x2 { grid-template-columns:1fr; } }
  .hero-svg, .check-svg { width:100%; height:auto; display:block;
                          margin:18px 0 6px; }
  .how { display:grid; grid-template-columns:52px 1fr; gap:4px 14px;
         background:PANX; border:1px solid HAIX; border-radius:14px;
         padding:18px 20px; margin:12px 0; }
  .how-n { grid-row:span 2; font-size:26px; font-weight:800; color:BLUX;
           font-family:ui-monospace,monospace; }
  .how-t { font-weight:700; font-size:16px; }
  .how-b { color:MUTX; font-size:14.5px; }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
           gap:12px; margin:16px 0; }
  .stat { background:PANX; border:1px solid HAIX; border-radius:14px;
          padding:16px 18px; }
  .stat .n { font-size:26px; font-weight:800;
             font-family:ui-monospace,monospace; }
  .stat .t { color:MUTX; font-size:13px; margin-top:4px; }
  code { background:PANX; border:1px solid HAIX; border-radius:6px;
         padding:2px 8px; font-size:13px; }
  details.receipts { border:1px solid HAIX; background:PANX; border-radius:14px;
                     margin:20px 0; }
  details.receipts summary { cursor:pointer; padding:16px 20px; font-weight:600;
                             color:BLUX; }
  details.receipts[open] summary { border-bottom:1px solid HAIX; }
  details.receipts > *:not(summary) { padding:2px 18px 14px; }
  table { border-collapse:collapse; width:100%; font-size:12.5px;
          font-family:ui-monospace,monospace; margin:8px 0; }
  th { text-align:left; color:MUTX; font-weight:500; border-bottom:1px solid HAIX;
       padding:5px 7px; }
  td { padding:5px 7px; border-bottom:1px solid #131c2e; }
  .dim { color:MUTX; }
  .bd { display:inline-block; padding:0 7px; border-radius:3px; font-weight:700;
        font-size:11.5px; }
  .bg { color:GOODX; background:rgba(76,195,138,.12);
        border:1px solid rgba(76,195,138,.35); }
  .bb { color:BADX; background:rgba(240,97,109,.12);
        border:1px solid rgba(240,97,109,.35); }
  .bm { color:MUTX; border:1px solid HAIX; }
  details.ev { border:1px solid HAIX; border-radius:8px; margin:8px 0; }
  details.ev summary { cursor:pointer; padding:8px 14px; color:MUTX; font-size:12px;
                       font-family:ui-monospace,monospace; }
  .prov { color:AMBX; font-size:12px; padding:8px 14px 0;
          font-family:ui-monospace,monospace; }
  .k { color:MUTX; font-size:11px; text-transform:uppercase; letter-spacing:.06em;
       padding:8px 14px 0; font-family:ui-monospace,monospace; }
  .term { margin:4px 14px 8px; font-family:ui-monospace,monospace; }
  .term .cmd { color:GOODX; font-size:11.5px; word-break:break-all; }
  .term pre, pre.quote { margin:4px 0; background:TERMX; border:1px solid HAIX;
       border-radius:4px; padding:8px 10px; font-size:11.5px; white-space:pre-wrap;
       word-break:break-word; color:INKX; }
  pre.quote { color:MUTX; border-style:dashed; margin:4px 14px 8px; }
  .term pre.err { border-left:3px solid BADX; }
  .term pre.ok { border-left:3px solid GOODX; }
  footer { margin-top:56px; border-top:1px solid HAIX; padding-top:18px;
           color:MUTX; font-size:12.5px; }
</style></head><body><main>

<h1>Your AI agent says \u201cdone, tests pass.\u201d<br>What if that had to be <em>proven</em>?</h1>
<p class="lede">We ran a real AI coder (GLM&nbsp;5.3) on real open-source tasks
twice — once the normal way, and once where \u201cdone\u201d only counts with
signed proof. Same model, same tasks. This is the difference.</p>
HEROSVG

<h2>The difference, in one picture</h2>
<p class="note">The claim never changes. What changes is whether anything
<em>backs it up</em>.</p>
HEROSVG2

STALEEXHIBIT

<h2>The problem it solved: \u201cbut the tests were green!\u201d</h2>
<p class="note">The scariest failure in AI-assisted coding isn\u2019t a crash —
it\u2019s a <strong>green checkmark on broken work</strong>. Here\u2019s that
exact scenario, built from our runs: a solved task where the agent then
\u201ccleans up\u201d four inconvenient tests.</p>
CHECKSVG

<h2>How it works — three moves, no magic</h2>
HOWCARDS

<h2>The numbers, plainly</h2>
<div class="stats">
  <div class="stat"><div class="n" style="color:GOODX">0</div><div class="t">times
  the gate certified work that hidden tests refuted — across NRUNS real runs
  plus the attack above</div></div>
  <div class="stat"><div class="n" style="color:GOODX">0</div><div class="t">times
  it blocked work the hidden tests confirmed (NSOLVED solved tasks, all
  verified)</div></div>
  <div class="stat"><div class="n">7–12s</div><div class="t">what the proving
  cost per task — the price of not trusting, measured</div></div>
  <div class="stat"><div class="n">ms</div><div class="t">to re-verify any past
  completion from its chained record — the audit your CI can\u2019t do at
  any price</div></div>
</div>
<p class="note">Honest scope: in our runs the agent didn\u2019t lie on its own
— it solved 5 tasks and kept honestly working on the hard one. The deleted-tests
scenario above is staged on a real run to show the mechanism, and it\u2019s
labeled as staged. Real runs: NRUNS · TOK tokens · $COST.</p>

LEDGER

<footer>ranex — deterministic governance for AI agents that build software ·
every number above comes from the receipts section\u2019s captured outputs ·
the staged attack is labeled · nothing here was typed by hand</footer>
</main></body></html>
"""
    page = (page
            .replace("BGX", BG).replace("INKX", INK).replace("MUTX", MUTED)
            .replace("PANX", PANEL).replace("HAIX", HAIR).replace("GOODX", GOOD)
            .replace("BADX", BAD).replace("BLUX", BLUE).replace("AMBX", AMBER)
            .replace("TERMX", TERM)
            .replace("HEROSVG2", _hero_svg())
            .replace("HEROSVG", "")
            .replace("STALEEXHIBIT", _stale_exhibit(report))
            .replace("CHECKSVG", _checklist_svg())
            .replace("HOWCARDS", _how_cards())
            .replace("LEDGER", _ledger(report, digest))
            .replace("NRUNS", str(len(rows)))
            .replace("NSOLVED", str(solved))
            .replace("TOK", "{:,}".format(tokens))
            .replace("COST", "{:.2f}".format(cost)))

    out = output_dir / "oss-benchmark.html"
    out.write_text(page)
    return out


if __name__ == "__main__":
    import sys

    report = json.loads(Path(sys.argv[1]).read_text())
    print("page:", generate_page(report, Path(sys.argv[2])))
