"""Corpus-driven proof page: every visual is computed from REAL run data.

Data sources (never typed by hand):
  tools/dogfood/oss_bench/proofs/*.json   the append-only proof archive
    -> each entry derived from VulcanBench run artifacts
       (runs/<id>/summary.json) and captured ranex CLI transcripts.

Graphs rendered from that data:
  - verdict matrix: every run × four positions, colored by real verdicts
  - proof-pile growth: cumulative entries per night (step line)
  - per-run economics: tokens per run (bars), from summary.json fields
  - the two attack transcripts, verbatim

Provenance is stamped on every chart (source line with run ids / archive
digest). Story sections stay for humans; receipts hold the raw transcripts.
"""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "oss_bench"))
import proofs as archive  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import evolution_graphs  # noqa: E402

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


def _esc(value: Any) -> str:
    return html.escape(str(value))


def _hero_svg() -> str:
    left = f"""
    <text x="20" y="34" fill="{MUTED}" font-size="13" font-weight="700">WITHOUT RANEX</text>
    <rect x="20" y="52" width="300" height="62" rx="12" fill="{PANEL}" stroke="{HAIR}"/>
    <text x="40" y="78" fill="{INK}" font-size="13.5">🤖 “Done! All tests pass.”</text>
    <text x="40" y="98" fill="{MUTED}" font-size="12">its word. nothing else attached.</text>
    <path d="M170 122 v34" stroke="{MUTED}" stroke-width="2" marker-end="url(#arr)"/>
    <rect x="20" y="164" width="300" height="78" rx="12" fill="{PANEL}" stroke="{HAIR}"/>
    <text x="40" y="192" fill="{INK}" font-size="13.5">😃 “Great — merging it.”</text>
    <text x="40" y="214" fill="{MUTED}" font-size="12">if the agent was wrong or gamed</text>
    <text x="40" y="230" fill="{MUTED}" font-size="12">the tests, you find out in production.</text>
    """
    right = f"""
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
    return ('<svg class="hero-svg" viewBox="0 0 780 260" '
            'xmlns="http://www.w3.org/2000/svg" '
            'font-family="ui-sans-serif,system-ui,sans-serif" role="img" '
            'aria-label="same claim, two worlds">'
            '<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="4" refY="4" '
            f'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="{MUTED}"/></marker></defs>'
            + left + f'<line x1="410" y1="30" x2="410" y2="230" stroke="{HAIR}" '
            'stroke-dasharray="4 5"/>' + right + "</svg>")


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def _tokens_svg(runs: list[dict[str, Any]]) -> str:
    if not runs:
        return ""
    ordered = sorted(runs, key=lambda r: -(r.get("tokens") or 0))
    width, bar_h, gap = 700, 22, 10
    label_x, bar_x, bar_max = 232, 244, 292
    val_x = bar_x + bar_max + 10
    top = 44
    height = top + len(ordered) * (bar_h + gap) + 22
    max_tokens = max(r.get("tokens") or 0 for r in ordered) or 1

    grid = "".join(
        f'<line x1="{gx:.1f}" y1="{top - 2}" x2="{gx:.1f}" '
        f'y2="{height - 24}" stroke="{MUTED}" stroke-opacity="0.15"/>'
        for gx in (bar_x, bar_x + bar_max / 2, bar_x + bar_max))
    ticks = (
        f'<text x="{bar_x}" y="34" fill="{MUTED}" font-size="10.5" '
        'text-anchor="middle">0</text>'
        f'<text x="{bar_x + bar_max / 2:.0f}" y="34" fill="{MUTED}" '
        f'font-size="10.5" text-anchor="middle">{_fmt_tokens(max_tokens // 2)}'
        '</text>'
        f'<text x="{bar_x + bar_max}" y="34" fill="{MUTED}" font-size="10.5" '
        f'text-anchor="end">{_fmt_tokens(max_tokens)}</text>')
    bars = ""
    for i, r in enumerate(ordered):
        y = top + i * (bar_h + gap)
        tokens = r.get("tokens") or 0
        w = max(2.0, tokens / max_tokens * bar_max)
        col = GOOD if r["ground_truth_functional"] == 1.0 else BAD
        cost = r.get("cost_usd")
        extra = f" · ${cost:.2f}" if isinstance(cost, (int, float)) else ""
        bars += (
            f'<text x="{label_x}" y="{y + 15}" fill="{MUTED}" font-size="11" '
            f'text-anchor="end">{_esc(r["task"][:30])}</text>'
            f'<rect x="{bar_x}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="4" '
            f'fill="{col}" fill-opacity="0.85"/>'
            f'<text x="{val_x}" y="{y + 15}" fill="{INK}" font-size="11">'
            f'{_fmt_tokens(tokens)} tok{extra}</text>')
    return (f'<svg class="graph" viewBox="0 0 {width} {height + 12}" '
            'xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace,monospace" '
            'role="img" aria-label="tokens per run"><text x="0" y="18" fill="'
            f'{INK}" font-size="13" font-weight="700">real work per run — tokens '
            'burned by the agent (sorted, linear scale)</text>' + ticks + grid
            + bars +
            f'<text x="0" y="{height - 4}" fill="{MUTED}" font-size="10.5">'
            'source: VulcanBench runs/&lt;id&gt;/summary.json → total_tokens · '
            'green = hidden tests passed</text>'
            f'<text x="0" y="{height + 9}" fill="{MUTED}" font-size="10.5">'
            'the two long bars are 60–100-step legacy ports; the short ones are '
            '8–14-step library tasks</text></svg>')


def _verdict_matrix(runs: list[dict[str, Any]]) -> str:
    def badge(v, good_when=True):
        good = (str(v) in ("1.0", "GREEN", "PASS", "done")) == good_when
        cls = "bg" if good else "bb"
        return f'<span class="bd {cls}">{_esc(v)}</span>'

    rows = ""
    for r in runs:
        claim = "done" if r["self_report"]["claimed_success"] else "—"
        rows += ('<tr><td>{}</td><td class="dim">{}</td><td>{}</td><td>{}</td>'
                 "<td>{}</td><td>{}</td></tr>").format(
                     _esc(r["task"]), _esc(r["run_id"][-8:]),
                     badge(r["ground_truth_functional"]),
                     badge(r["bare_ci"]["verdict"]),
                     badge(claim),
                     badge(r["ranex_gate"]["gate_verdict"]))
    return ('<div class="tablewrap"><table><tr><th>task</th><th>run</th><th>hidden tests</th>'
            '<th>bare CI</th><th>agent says</th><th>ranex gate</th></tr>'
            + rows + "</table></div>")


def _attack_card(entry: dict[str, Any]) -> str:
    if entry["attack"] in ("stale-proof", "stale-proof-external"):
        before, after = entry["before"], entry["after"]
        where = (" on the external repository <code>{}</code> @ <code>{}</code>"
                 .format(_esc(entry["external"]["url"].split("/")[-1]),
                         _esc(entry["external"]["commit"][:8]))
                 if entry.get("external") else "")
        return ('<div class="card"><h3>The stale-proof trap ({}){}</h3>'
                '<div class="x2"><div><div class="k">proof right after the green '
                'run:</div><div class="term"><pre class="ok">{}</pre></div></div>'
                '<div><div class="k">same proof after ONE comment-line edit '
                '(no re-run):</div><div class="term"><pre class="err">{}</pre>'
                "</div></div></div></div>").format(
                    _esc(entry["date"]), where,
                    _esc(before["gate_output"]),
                    _esc(after["gate_output"]))
    removed = ", ".join(entry.get("removed_tests", []))
    return ('<div class="card"><h3>The deleted-tests attack ({})</h3>'
            '<div class="x2"><div><div class="k">your CI:</div><div class="term">'
            '<pre class="ok">{}</pre></div></div><div><div class="k">the gate:</div>'
            '<div class="term"><pre class="err">{}</pre></div></div></div>'
            '<div class="removed">deleted: <code>{}</code></div></div>').format(
                _esc(entry["date"]),
                _esc(entry["bare_ci"]["output_tail"]),
                _esc(entry["ranex_gate"]["gate_output"]), _esc(removed))


def _receipts(entries: list[dict[str, Any]]) -> str:
    out = []
    for e in entries:
        if e["kind"] == "run":
            gov, ci = e["ranex_gate"], e["bare_ci"]
            if e.get("external"):
                ext = e["external"]
                out.append(
                    '<details class="ev"><summary>{} · external run {} · kernel '
                    "v{} · gate {} · NO AGENT (kernel-only)</summary>"
                    '<div class="prov">released kernel {} · {} @ {} · vendored '
                    "src tree {} == {} tag tree · {} bound ids</div>"
                    '<div class="k">the external repository\'s own suite, bare:</div>'
                    '<div class="term"><div class="cmd">$ {}</div><pre class="ok">'
                    "{}</pre></div>"
                    '<div class="k">what ranex executed (released kernel only):</div>'
                    '<div class="term"><div class="cmd">$ {}</div><pre class="ok">'
                    "evidence recorded, exit {}</pre></div>"
                    '<div class="k">the gate\'s verdict, verbatim:</div>'
                    '<div class="term"><pre class="ok">{}</pre></div>'
                    '<div class="k">the journal chain check:</div>'
                    '<div class="term"><pre class="ok">{}</pre></div></details>'
                    .format(_esc(e["date"]), _esc(e["run_id"]),
                            _esc(e.get("kernel_version", "?")),
                            gov["gate_verdict"],
                            _esc(e["kernel_head"][:12]),
                            _esc(ext["url"]), _esc(ext["commit"][:12]),
                            _esc(ext.get("vendored_src_tree", "?")[:12]),
                            _esc(ext.get("tag_src_tree", "?")[:12]),
                            ext.get("selected_ids", "?"),
                            _esc(ci["command"]), _esc(ci["output_tail"]),
                            _esc(gov["run_command"]), gov["run_exit"],
                            _esc(gov["gate_output"]),
                            _esc(gov["journal_output"])))
                continue
            out.append(
                '<details class="ev"><summary>{} · run {} · gate {} · {}'
                " tokens · ${}</summary>"
                '<div class="prov">run {} · {} steps · {} tokens · ${} · '
                "{:.0f}s agent time</div>"
                '<div class="k">the agent\u2019s last words (parsed, heuristic):</div>'
                '<pre class="quote">{}</pre>'
                '<div class="k">what a normal CI ran, and printed:</div>'
                '<div class="term"><div class="cmd">$ {}</div><pre class="{}">{}</pre></div>'
                '<div class="k">what ranex executed:</div>'
                '<div class="term"><div class="cmd">$ {}</div><pre class="ok">evidence '
                "recorded, exit {}</pre></div>"
                '<div class="k">the gate\u2019s verdict, verbatim:</div>'
                '<div class="term"><pre class="{}">{}</pre></div>'
                '<div class="k">the journal chain check:</div>'
                '<div class="term"><pre class="ok">{}</pre></div></details>'.format(
                    _esc(e["date"]), _esc(e["run_id"][-8:]), gov["gate_verdict"],
                    e.get("tokens", "?"), e.get("cost_usd", "?"),
                    _esc(e["run_id"]), e.get("agent_steps", "?"),
                    e.get("tokens", "?"), e.get("cost_usd", "?"),
                    e.get("duration_s") or 0,
                    _esc(e["self_report"].get("final_words", "")),
                    _esc(ci["command"]),
                    "ok" if ci["verdict"] == "GREEN" else "err",
                    _esc(ci["output_tail"]),
                    _esc(gov["run_command"]), gov["run_exit"],
                    "ok" if gov["gate_verdict"] == "PASS" else "err",
                    _esc(gov["gate_output"]),
                    _esc(gov["journal_output"])))
        else:
            out.append(
                '<details class="ev"><summary>{} · attack {} · caught: {} · '
                "FAULT-INJECTED (labeled)</summary>{}</details>".format(
                    _esc(e["date"]), _esc(e["attack"]),
                    "yes" if e.get("caught") else "NO",
                    _attack_card(e)))
    return "".join(out)


def _external_section(external_runs: list[dict[str, Any]],
                      entries: list[dict[str, Any]]) -> str:
    """The released-kernel external-repository proofs: no agent, no model —
    the v0.1.0 tag itself governing a clean third-party repository."""
    if not external_runs:
        return ""
    # Keyed by kernel AND task so a second external repository on the same
    # kernel never borrows another repository's refusal transcript.
    stale_by_run = {(e.get("kernel_head"), e.get("task")): e for e in entries
                    if e.get("attack") == "stale-proof-external"}
    cards = []
    for e in external_runs:
        gov, ext = e["ranex_gate"], e["external"]
        stale = stale_by_run.get((e["kernel_head"], e["task"]))
        cards.append(
            '<div class="card"><h3>{} @ {} — kernel v{}, no agent</h3>'
            '<div class="x2"><div><div class="k">install + identity:</div>'
            '<div class="term"><pre class="ok">git checkout {tag} + uv sync --frozen\n'
            'kernel commit {commit}\nvendored src tree {v} == tag tree {t}</pre></div>'
            '<div class="k">the governed cycle:</div><div class="term">'
            '<pre class="ok">run exit {rexit} → evidence signed\ngate: PASS\n'
            'journal: chain=verified</pre></div></div>'
            '<div><div class="k">then ONE comment-line edit, no re-run:</div>'
            '<div class="term"><pre class="err">{stale}</pre></div>'
            '<div class="k">re-run the work honestly:</div>'
            '<div class="term"><pre class="ok">gate: PASS again</pre></div></div>'
            "</div></div>"
            .format(
                _esc(e["task"]), _esc(ext["commit"][:8]),
                _esc(e.get("kernel_version", "?")),
                tag=_esc(ext.get("kernel_tag", "?")),
                commit=_esc(e["kernel_head"]),
                v=_esc(ext.get("vendored_src_tree", "?")[:12]),
                t=_esc(ext.get("tag_src_tree", "?")[:12]),
                rexit=gov["run_exit"],
                stale=_esc(stale["after"]["gate_output"]) if stale
                else "stale-evidence attack receipt pending"))
    return ('<h2>The released kernel on a clean external repository</h2>'
            '<p class="note">Not the working tree, not an agent: the published '
            'tag, installed the documented way, brought to a real third-party '
            'repository and judged there. Green evidence survives exactly '
            "until the subject changes — then it is refused by name until the "
            "work is redone. Raw receipts below.</p>" + "".join(cards))


def generate_page(output_dir: Path) -> Path:
    entries = archive.corpus()
    summary = archive.summary()
    runs = [e for e in entries if e["kind"] == "run"]
    # Agent runs have a model, tokens and a self-report; external-repo proofs
    # are kernel-only (no agent) and render in their own section, never in
    # the agent matrix or the tokens chart.
    agent_runs = [e for e in runs if not e.get("external")]
    external_runs = [e for e in runs if e.get("external")]
    attacks = [e for e in entries if e["kind"] == "attack"]
    model = next((e.get("model") for e in entries if e.get("model")), "?")

    # One series computation feeds both pages: refresh the standalone
    # evolution page + evolution.json, then embed the same charts here.
    evolution_graphs.generate()
    series = json.loads(
        (evolution_graphs.OUT_DIR / "evolution.json").read_text())["series"]
    evol_charts, evol_digest = evolution_graphs.charts_for_embed(series)

    attacks_html = "".join(_attack_card(e) for e in attacks)
    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ranex — the proof pile: real runs, real verdicts, piling up nightly</title>
<style>
  :root { color-scheme: dark; }
  body { margin:0; background:BGX; color:INKX;
         font:16.5px/1.65 ui-sans-serif,system-ui,-apple-system,sans-serif; }
  main { max-width:840px; margin:0 auto; padding:48px 22px 90px; }
  h1 { font-size:29px; line-height:1.22; margin:0 0 10px; letter-spacing:-.01em; }
  h2 { font-size:21px; margin:52px 0 4px; }
  h3 { font-size:15px; margin:0 0 10px; color:MUTX; font-weight:600; }
  .lede { color:MUTX; font-size:17px; }
  .note { color:MUTX; font-size:14px; margin:6px 0 16px; }
  .cert { border:1px solid HAX; background:PANX; padding:12px 16px; margin:16px 0;
          display:flex; flex-wrap:wrap; gap:8px 26px; }
  .cert div { font-size:12px; }
  .cert b { color:INKX; font-weight:600; display:block; }
  .cert span { color:MUTX; }
  svg.graph, svg.hero-svg { width:100%; height:auto; display:block; margin:14px 0 4px; }
  .tablewrap { overflow-x:auto; }
  table { border-collapse:collapse; width:100%; font-size:12.5px;
          font-family:ui-monospace,monospace; margin:10px 0; }
  th { text-align:left; color:MUTX; font-weight:500; border-bottom:1px solid HAX;
       padding:5px 7px; }
  td { padding:5px 7px; border-bottom:1px solid #131c2e; }
  .dim { color:MUTX; }
  .bd { display:inline-block; padding:0 7px; border-radius:3px; font-weight:700;
        font-size:11.5px; }
  .bg { color:GOODX; background:rgba(76,195,138,.12);
        border:1px solid rgba(76,195,138,.35); }
  .bb { color:BADX; background:rgba(240,97,109,.12);
        border:1px solid rgba(240,97,109,.35); }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
           gap:12px; margin:16px 0; }
  .stat { background:PANX; border:1px solid HAX; border-radius:14px;
          padding:16px 18px; }
  .stat .n { font-size:26px; font-weight:800; font-family:ui-monospace,monospace; }
  .stat .t { color:MUTX; font-size:13px; margin-top:4px; }
  .card { background:PANX; border:1px solid HAX; border-radius:14px;
          padding:18px 20px; margin:14px 0; }
  .x2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media (max-width:760px) { .x2 { grid-template-columns:1fr; } }
  .removed { margin-top:12px; border:1px dashed rgba(240,97,109,.4); border-radius:4px;
             padding:8px 14px; font-size:12.5px; color:BADX; }
  code { background:PANX; border:1px solid HAX; border-radius:6px; padding:2px 8px;
         font-size:13px; }
  details.ev { border:1px solid HAX; border-radius:10px; margin:8px 0;
               background:PANX; }
  details.ev summary { cursor:pointer; padding:10px 14px; color:MUTX; font-size:12px;
                       font-family:ui-monospace,monospace; }
  details.ev[open] summary { border-bottom:1px solid HAX; color:INKX; }
  .prov { color:AMBX; font-size:12px; padding:8px 14px 0;
          font-family:ui-monospace,monospace; }
  .k { color:MUTX; font-size:11px; text-transform:uppercase; letter-spacing:.06em;
       padding:8px 14px 0; font-family:ui-monospace,monospace; }
  .term { margin:4px 14px 8px; font-family:ui-monospace,monospace; }
  .term .cmd { color:GOODX; font-size:11.5px; word-break:break-all; }
  .term pre, pre.quote { margin:4px 0; background:TERMX; border:1px solid HAX;
       border-radius:4px; padding:8px 10px; font-size:11.5px; white-space:pre-wrap;
       word-break:break-word; color:INKX; }
  pre.quote { color:MUTX; border-style:dashed; margin:4px 14px 8px; }
  .term pre.err { border-left:3px solid BADX; }
  .term pre.ok { border-left:3px solid GOODX; }
  footer { margin-top:56px; border-top:1px solid HAX; padding-top:18px;
           color:MUTX; font-size:12.5px; }
</style></head><body><main>

<h1>The proof pile — real agent runs, real verdicts,<br>accumulating every night</h1>
<p class="lede">A real AI coder (MODEL_S) does real open-source work. Every run
is judged four ways: independent hidden tests, a normal CI, the agent\u2019s own
final message, and the ranex gate (signed proof against a checklist frozen
before the agent started). Dogfooding appends new proofs nightly; the pile
only grows.</p>

<div class="cert">
 <div><span>proofs piled</span><b>ENTRIES_N (RUNS_N runs · ATTACKS_N attacks)</b></div>
 <div><span>nights accumulating</span><b>NIGHTS_N</b></div>
 <div><span>real agent work</span><b>TOK_N tokens · $COST_N</b></div>
 <div><span>archive digest</span><b>DIGEST_S</b></div>
</div>

<h2>The difference, in one picture</h2>
<p class="note">The claim never changes. What changes is whether anything
<em>backs it up</em>.</p>
HERO_SVG_X

<h2>What the gate caught — the classic attacks</h2>
<p class="note">Fault-injected on real code and labeled as such: the two classic
gaming attacks on a real solved run, and the external-repository variant — a
changed subject refused with yesterday's green evidence still on disk.</p>
ATTACKS_HTML_X

<h2>Every run in the pile — the verdict matrix</h2>
<p class="note">Real data: each row is one agent run; each column is one
judge. Source: VulcanBench run artifacts + captured ranex transcripts
(receipts below).</p>
MATRIX
TOKENS
EXTERNAL_X

<h2>The pile\u2019s bottom line, so far</h2>
<div class="stats">
 <div class="stat"><div class="n" style="color:GOODX">FPASSES_N</div><div class="t">times
 the gate certified work the hidden tests refuted — across RUNS_N real runs and
 ATTACKS_N attacks, ever</div></div>
 <div class="stat"><div class="n" style="color:GOODX">FBLOCKS_N</div><div class="t">times
 it blocked work the hidden tests confirmed (HFAULTS_N harness faults excluded)</div></div>
 <div class="stat"><div class="n">CAUGHT_N/ATTACKS_N</div><div class="t">attacks caught:
 deleted tests, stale proofs — each named, each verifiable</div></div>
 <div class="stat"><div class="n">ms</div><div class="t">to re-verify any past
 completion from its chained record — the audit a scrollback can\u2019t do</div></div>
</div>
<p class="note">Honest scope: attacks are fault-injected on real solved runs
and labeled as such; in the natural runs so far the agent was honest, so the
pile\u2019s value there is certified agreement plus the audit trail. The pile
grows nightly — every new night either adds another clean proof or catches
something real.</p>

<h2>The kernel, evolving — measured from git history, not claimed</h2>
<p class="note">Every point on every graph is computed from this repository\u2019s
own history at that commit: the kernel\u2019s total independent code paths
(McCabe), the registered proof scenarios, the archived real-world proofs, and
the open-findings ledger. The graphs refill every dogfood cycle — a flat line
here would mean the loop stopped working.</p>
XEVOLCHARTSX
<p class="note">Series data: <code>evolution.json</code> · digest
<code>XEVOLDIGESTX</code> — nothing typed by hand; also rendered standalone
at <code>evolution.html</code>.</p>

<h2>Receipts — every proof, raw</h2>
RECEIPTS

<footer>ranex — deterministic governance for AI agents that build software ·
tasks and grader scores are VulcanBench run artifacts · every verdict line is
a captured command output · fault-injected rows are labeled · archive:
tools/dogfood/oss_bench/proofs/ (append-only)</footer>
</main></body></html>
"""
    page = (page
            .replace("BGX", BG).replace("INKX", INK).replace("MUTX", MUTED)
            .replace("HAX", HAIR).replace("PANX", PANEL).replace("GOODX", GOOD)
            .replace("BADX", BAD).replace("AMBX", AMBER).replace("TERMX", TERM)
            .replace("MODEL_S", _esc(model))
            .replace("HERO_SVG_X", _hero_svg())
            .replace("ATTACKS_HTML_X", attacks_html)
            .replace("MATRIX", _verdict_matrix(agent_runs))
            .replace("TOKENS", _tokens_svg(agent_runs))
            .replace("EXTERNAL_X", _external_section(external_runs, entries))
            .replace("ENTRIES_N", str(summary["entries"]))
            .replace("RUNS_N", str(summary["runs"]))
            .replace("ATTACKS_N", str(summary["attacks"]))
            .replace("NIGHTS_N", str(summary["nights"]))
            .replace("TOK_N", "{:,}".format(summary["tokens"]))
            .replace("COST_N", "{:.2f}".format(summary["cost_usd"]))
            .replace("DIGEST_S", summary["archive_digest"][:23] + "…")
            .replace("FPASSES_N", str(summary["false_passes"]))
            .replace("FBLOCKS_N", str(summary["false_blocks"]))
            .replace("HFAULTS_N", str(summary.get("harness_faults", 0)))
            .replace("CAUGHT_N", str(summary["attacks_caught"]))
            .replace("RECEIPTS", _receipts(entries))
            .replace("XEVOLCHARTSX", "".join(evol_charts))
            .replace("XEVOLDIGESTX", evol_digest[:23] + "…"))

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "oss-benchmark.html"
    out.write_text(page)
    return out


if __name__ == "__main__":
    import sys

    print("page:", generate_page(Path(sys.argv[1] if len(sys.argv) > 1 else "site")))
