"""Render the workflow-insights HTML report.

Usage: render.py <datadir> <findings_dir> <overview.json> <output.html> <window_start> <window_end>

findings_dir holds q1.json..q4.json (shape documented in findings-schema.md). overview.json holds
{"at_a_glance": [{"title", "text"}], "limits": ["..."]}; a leftover "top10" key is ignored.
The report lists every recommendation except kind "leave-as-is" under "All proposed fixes", with its
impact as the priority, linked to its card. The output is one self-contained file: inline CSS and JS, no external requests.
"""
import collections
import datetime as dt
import html
import json
import os
import sys

DATA, FIND, OVERVIEW, OUTPUT, W_START, W_END = sys.argv[1:7]

SECTIONS = [
    ("q1", "Repeated patterns", "Requests and procedures you repeat, and whether a skill or a hook should own them."),
    ("q2", "AGENTS.md rules", "Rules that are missing, rules agents ignore, and rules that cost more than they return."),
    ("q3", "Inline scripts", "What the inlined Python, jq, and shell snippets do, and which a CLI or a saved script replaces."),
    ("q4", "Tooling and friction", "Escalations, failures, missing programs, and unused skills, plugins, and MCP servers."),
]
PRIORITY = {"high": 0, "medium": 1, "low": 2}
KIND_LABEL = {"skill": "Skill", "hook": "Hook", "rule": "Rule", "tool": "Tool", "script": "Script", "mcp": "MCP",
              "config": "Config", "cleanup": "Cleanup", "leave-as-is": "Leave as is"}


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def load_jsonl(name):
    with open(os.path.join(DATA, name + ".jsonl"), encoding="utf-8") as fh:
        return [json.loads(x) for x in fh]


def day(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")


def fmt(n):
    return f"{n:,}" if isinstance(n, (int, float)) else e(n)


def coverage():
    sessions = load_jsonl("sessions")
    bash = load_jsonl("bash")
    inline = load_jsonl("inline")
    prompts = load_jsonl("prompts")
    cov = {}
    for src in ("claude", "codex"):
        human = [s for s in sessions if s["src"] == src and s.get("kind", "main") == "main" and s["prompts"] > 0]
        cov[src] = {
            "sessions": len(human),
            "first": day(min(s["first"] for s in human)) if human else "n/a",
            "last": day(max(s["last"] for s in human)) if human else "n/a",
            "prompts": sum(1 for p in prompts if p["src"] == src),
            "commands": sum(1 for b in bash if b["src"] == src),
            "failed": sum(1 for b in bash if b["src"] == src and b["err"]),
            "scripts": sum(1 for i in inline if i["src"] == src and i["kind"] in ("heredoc-script", "dash-c", "codex-js-tool")),
            "months": collections.Counter(day(s["first"])[:7] for s in human),
        }
    return cov


def bar_chart(chart):
    bars = [b for b in chart.get("bars", []) if isinstance(b.get("value"), (int, float))][:12]
    if not bars:
        return ""
    top = max(b["value"] for b in bars) or 1
    unit = chart.get("unit", "")
    rows = []
    trs = []
    for b in bars:
        pct = max(0.6, 100 * b["value"] / top)
        tip = f"{b['label']}: {fmt(b['value'])} {unit}" + (f". {b['note']}" if b.get("note") else "")
        rows.append(
            f'<div class="bar-row" tabindex="0" data-tip="{e(tip)}"><div class="bar-label" title="{e(b["label"])}">{e(b["label"])}</div>'
            f'<div class="bar-track"><div class="bar" style="width:{pct:.1f}%"></div><span class="bar-value">{fmt(b["value"])}</span></div></div>')
        trs.append(f"<tr><td>{e(b['label'])}</td><td class=\"num\">{fmt(b['value'])}</td><td>{e(b.get('note', ''))}</td></tr>")
    return (f'<figure class="chart"><figcaption>{e(chart.get("title", ""))}'
            f'<span class="unit">{e(unit)}</span></figcaption>{"".join(rows)}'
            f'<details class="table-view"><summary>Show as table</summary><table><thead><tr><th>Item</th><th class="num">{e(unit) or "Value"}</th>'
            f'<th>Note</th></tr></thead><tbody>{"".join(trs)}</tbody></table></details></figure>')


def month_chart(cov):
    months = sorted(set(cov["claude"]["months"]) | set(cov["codex"]["months"]))
    top = max([cov[s]["months"].get(m, 0) for s in cov for m in months] or [1]) or 1
    rows = []
    trs = []
    for m in months:
        c, x = cov["claude"]["months"].get(m, 0), cov["codex"]["months"].get(m, 0)
        rows.append(
            f'<div class="bar-row pair"><div class="bar-label">{e(m)}</div><div class="pair-tracks">'
            f'<div class="bar-track" tabindex="0" data-tip="{e(m)} Claude Code: {c} sessions"><div class="bar s1" style="width:{max(0.6, 100 * c / top):.1f}%"></div><span class="bar-value">{c}</span></div>'
            f'<div class="bar-track" tabindex="0" data-tip="{e(m)} Codex: {x} sessions"><div class="bar s2" style="width:{max(0.6, 100 * x / top):.1f}%"></div><span class="bar-value">{x}</span></div>'
            f'</div></div>')
        trs.append(f'<tr><td>{e(m)}</td><td class="num">{c}</td><td class="num">{x}</td></tr>')
    return ('<figure class="chart"><figcaption>Interactive sessions per month<span class="unit">sessions</span></figcaption>'
            '<div class="legend"><span><i class="sw s1"></i>Claude Code</span><span><i class="sw s2"></i>Codex</span></div>'
            + "".join(rows) +
            '<details class="table-view"><summary>Show as table</summary><table><thead><tr><th>Month</th><th class="num">Claude Code</th>'
            f'<th class="num">Codex</th></tr></thead><tbody>{"".join(trs)}</tbody></table></details></figure>')


def rec_card(r, sid, n):
    ev = r.get("evidence") or {}
    impact = str(r.get("impact", "medium")).lower()
    kind = str(r.get("kind", "")).lower()
    verified = bool(r.get("verified"))
    examples = "".join(f"<li>{e(x)}</li>" for x in (ev.get("examples") or [])[:2])
    snippet = ""
    if r.get("snippet"):
        snippet = (f'<div class="snippet"><div class="snippet-head"><span>{e(r.get("snippet_label") or "Copy")}</span>'
                   f'<button type="button" class="copy">Copy</button></div><pre>{e(r["snippet"])}</pre></div>')
    stats = []
    if ev.get("count") not in (None, ""):
        stats.append(f"<b>{fmt(ev['count'])}</b> occurrences")
    if ev.get("sessions") not in (None, ""):
        stats.append(f"<b>{fmt(ev['sessions'])}</b> sessions")
    if ev.get("split"):
        stats.append(e(ev["split"]))
    return (
        f'<article class="rec" id="{sid}-r{n}" data-impact="{e(impact)}">'
        f'<header><h4>{e(r.get("title"))}</h4><div class="badges"><span class="badge impact-{e(impact)}">{e(impact)} impact</span>'
        f'<span class="badge kind">{e(KIND_LABEL.get(kind, kind or "Other"))}</span>'
        f'<span class="badge {"ok" if verified else "assume"}">{"Verified" if verified else "Assumption"}</span></div></header>'
        f'<dl><dt>Evidence</dt><dd><div class="ev-stats">{" · ".join(stats)}</div>{"<ul class=examples>" + examples + "</ul>" if examples else ""}</dd>'
        f'<dt>Proposal</dt><dd>{e(r.get("proposal"))}{snippet}</dd>'
        f'<dt>Benefit</dt><dd>{e(r.get("benefit"))}</dd><dt>Tradeoff</dt><dd>{e(r.get("tradeoff"))}</dd></dl></article>')


def fix_list(findings):
    rows = []
    skipped = 0
    for sid, title, _ in SECTIONS:
        for i, r in enumerate(findings[sid]["recommendations"]):
            kind = str(r.get("kind", "")).lower()
            if kind == "leave-as-is":
                skipped += 1
                continue
            impact = str(r.get("impact", "medium")).lower()
            rows.append((PRIORITY.get(impact, 3), (
                f'<li class="fix" data-impact="{e(impact)}"><span class="badge impact-{e(impact)}">{e(impact)} priority</span>'
                f'<a href="#{sid}-r{i + 1}">{e(r.get("title"))}</a>'
                f'<span class="where">{e(KIND_LABEL.get(kind, kind or "Other"))} · {e(title)}</span></li>')))
    rows.sort(key=lambda x: x[0])
    note = (f'<p class="fix-note">{skipped} "leave as is" conclusion{"s" if skipped != 1 else ""} not listed. '
            'These are conclusions, not fixes.</p>')
    return f'<section id="fixes"><h2>All proposed fixes</h2><ul class="fixes">{"".join(x[1] for x in rows)}</ul>{note}</section>'


def main():
    cov = coverage()
    with open(OVERVIEW, encoding="utf-8") as fh:
        ov = json.load(fh)
    findings = {}
    for sid, _, _ in SECTIONS:
        p = os.path.join(FIND, sid + ".json")
        findings[sid] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"summary": "No findings file was produced for this section.", "recommendations": []}
    for f in findings.values():
        f["recommendations"] = sorted(f.get("recommendations") or [], key=lambda r: PRIORITY.get(str(r.get("impact")).lower(), 3))

    total_recs = sum(len(f["recommendations"]) for f in findings.values())
    cards = [
        ("Sessions", cov["claude"]["sessions"] + cov["codex"]["sessions"], f"{cov['claude']['sessions']} Claude Code, {cov['codex']['sessions']} Codex"),
        ("Prompts", cov["claude"]["prompts"] + cov["codex"]["prompts"], f"{fmt(cov['claude']['prompts'])} Claude Code, {fmt(cov['codex']['prompts'])} Codex"),
        ("Shell commands", cov["claude"]["commands"] + cov["codex"]["commands"], f"{fmt(cov['claude']['failed'] + cov['codex']['failed'])} failed"),
        ("Inline scripts", cov["claude"]["scripts"] + cov["codex"]["scripts"], f"{fmt(cov['claude']['scripts'])} Claude Code, {fmt(cov['codex']['scripts'])} Codex"),
        ("Recommendations", total_recs, "across four sections"),
    ]
    toc = ['<a href="#glance">At a glance</a>', '<a href="#fixes">All proposed fixes</a>']
    body = []
    for sid, title, blurb in SECTIONS:
        f = findings[sid]
        toc.append(f'<a href="#{sid}">{e(title)}<span>{len(f["recommendations"])}</span></a>')
        charts = "".join(bar_chart(c) for c in f.get("charts") or [])
        recs = "".join(rec_card(r, sid, i + 1) for i, r in enumerate(f["recommendations"]))
        notes = "".join(f"<li>{e(n)}</li>" for n in f.get("notes") or [])
        body.append(
            f'<section id="{sid}"><h2>{e(title)}</h2><p class="blurb">{e(blurb)}</p><p class="lead">{e(f.get("summary"))}</p>'
            + (f'<p class="versus"><b>Claude Code and Codex:</b> {e(f["claude_vs_codex"])}</p>' if f.get("claude_vs_codex") else "")
            + (f'<div class="charts">{charts}</div>' if charts else "")
            + f'<div class="recs">{recs}</div>'
            + (f'<details class="notes"><summary>Assumptions and limits</summary><ul>{notes}</ul></details>' if notes else "")
            + "</section>")
    toc.append('<a href="#method">Method and limits</a>')

    glance = "".join(f'<div class="glance-item"><h3>{e(g.get("title"))}</h3><p>{e(g.get("text"))}</p></div>' for g in ov.get("at_a_glance", []))
    limits = "".join(f"<li>{e(x)}</li>" for x in ov.get("limits", []))
    cov_rows = "".join(
        f'<tr><td>{name}</td><td>{c["first"]} to {c["last"]}</td><td class="num">{c["sessions"]}</td><td class="num">{fmt(c["prompts"])}</td>'
        f'<td class="num">{fmt(c["commands"])}</td><td class="num">{fmt(c["scripts"])}</td></tr>'
        for name, c in (("Claude Code", cov["claude"]), ("Codex", cov["codex"])))
    stat_cards = "".join(f'<div class="stat"><div class="stat-label">{e(a)}</div><div class="stat-value">{fmt(b)}</div><div class="stat-sub">{e(c)}</div></div>' for a, b, c in cards)

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Workflow insights, {e(W_START)} to {e(W_END)}</title>
<style>{CSS}</style></head>
<body><div class="layout viz-root">
<nav class="toc" aria-label="Contents"><div class="toc-title">Workflow insights</div>{"".join(toc)}
<div class="filter" role="group" aria-label="Filter by impact"><div class="filter-title">Show impact</div>
<button type="button" data-f="all" class="on">All</button><button type="button" data-f="high">High</button><button type="button" data-f="medium">Medium</button><button type="button" data-f="low">Low</button></div></nav>
<main>
<header class="top"><h1>Workflow insights</h1>
<p class="window">Claude Code and Codex sessions, {e(W_START)} to {e(W_END)}. Generated {e(dt.date.today().isoformat())}.</p>
<div class="stats">{stat_cards}</div>
<table class="coverage"><thead><tr><th>Source</th><th>Coverage found</th><th class="num">Sessions</th><th class="num">Prompts</th><th class="num">Shell commands</th><th class="num">Inline scripts</th></tr></thead><tbody>{cov_rows}</tbody></table>
{month_chart(cov)}</header>
<section id="glance"><h2>At a glance</h2><div class="glance">{glance}</div></section>
{fix_list(findings)}
{"".join(body)}
<section id="method"><h2>Method and limits</h2><ul class="limits">{limits}</ul></section>
</main></div><div id="tip" role="tooltip"></div>
<script>{JS}</script></body></html>"""
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("wrote", OUTPUT, len(page), "bytes;", total_recs, "recommendations")


CSS = """
:root{color-scheme:light;--bg:#f6f5f2;--surface-1:#fcfcfb;--surface-2:#f0efec;--border:#e2e0da;--text-primary:#0b0b0b;--text-secondary:#52514e;--text-muted:#7a7872;
--series-1:#2a78d6;--series-2:#eb6834;--track:#ebe9e4;--good:#1a7f37;--warn:#9a6700;--crit:#b3261e;--accent:#2a78d6}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#111110;--surface-1:#1a1a19;--surface-2:#232321;--border:#33322f;--text-primary:#f0efec;--text-secondary:#c3c2b7;--text-muted:#8f8d85;
--series-1:#3987e5;--series-2:#d95926;--track:#2a2a28;--good:#4cc26a;--warn:#d9a530;--crit:#f0736c;--accent:#6aa6f0}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text-primary);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.layout{display:grid;grid-template-columns:230px minmax(0,1fr);gap:32px;max-width:1180px;margin:0 auto;padding:28px 24px 80px}
.toc{position:sticky;top:20px;align-self:start;display:flex;flex-direction:column;gap:2px;font-size:14px;max-height:calc(100vh - 40px);overflow:auto}
.toc-title{font-weight:650;margin-bottom:8px}
.toc a{display:flex;justify-content:space-between;gap:8px;padding:6px 10px;border-radius:6px;color:var(--text-secondary);text-decoration:none}
.toc a:hover,.toc a:focus-visible{background:var(--surface-2);color:var(--text-primary)}
.toc a span{color:var(--text-muted);font-variant-numeric:tabular-nums}
.filter{margin-top:16px;padding-top:12px;border-top:1px solid var(--border);display:flex;flex-wrap:wrap;gap:6px}
.filter-title{width:100%;font-size:12px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.04em}
button{font:inherit;color:var(--text-secondary);background:var(--surface-1);border:1px solid var(--border);border-radius:6px;padding:3px 10px;cursor:pointer}
button:hover{color:var(--text-primary)}button.on{background:var(--text-primary);color:var(--surface-1);border-color:var(--text-primary)}
h1{font-size:30px;line-height:1.2;margin:0 0 4px}h2{font-size:22px;margin:0 0 6px;padding-top:8px}h3{font-size:15px;margin:0 0 4px}h4{font-size:16px;margin:0;line-height:1.35}
.window,.blurb{color:var(--text-secondary);margin:0 0 18px}.lead{font-size:16px;margin:0 0 10px;max-width:75ch}.versus{color:var(--text-secondary);margin:0 0 18px;max-width:75ch}
section{margin-top:44px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}
.stat,.glance-item,.rec,.chart,.coverage,.fixes li{background:var(--surface-1);border:1px solid var(--border);border-radius:10px}
.stat{padding:14px 16px}.stat-label{font-size:12px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.04em}
.stat-value{font-size:28px;font-weight:650;font-variant-numeric:tabular-nums;line-height:1.2}.stat-sub{font-size:12.5px;color:var(--text-secondary)}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--border)}
th{font-weight:600;color:var(--text-secondary);font-size:12.5px}tr:last-child td{border-bottom:0}.num{text-align:right;font-variant-numeric:tabular-nums}
.coverage{border-spacing:0;overflow:hidden;margin-bottom:14px;display:table}
.glance{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}.glance-item{padding:14px 16px}.glance-item p{margin:0;color:var(--text-secondary)}
.fixes{list-style:none;padding:0;margin:0;display:grid;gap:8px}
.fixes li{display:flex;align-items:center;flex-wrap:wrap;gap:6px 12px;padding:10px 16px}.fixes li[hidden]{display:none}
.fixes .badge{min-width:112px;text-align:left}
.fixes a{font-weight:600;color:var(--text-primary);text-decoration:none;flex:1 1 280px}.fixes a:hover{text-decoration:underline}
.fixes .where{font-size:12.5px;color:var(--text-muted)}.fix-note{margin:10px 0 0;color:var(--text-secondary);font-size:13.5px}
.rec,section{scroll-margin-top:20px}.rec:target{border-color:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 35%,transparent);animation:flash 1.6s ease-out}
@keyframes flash{from{background:color-mix(in srgb,var(--accent) 22%,var(--surface-1))}to{background:var(--surface-1)}}
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:12px;margin:16px 0}
.chart{margin:0;padding:14px 16px}figcaption{font-weight:600;margin-bottom:10px;display:flex;justify-content:space-between;gap:12px}
.unit{font-weight:400;font-size:12.5px;color:var(--text-muted)}
.bar-row{display:grid;grid-template-columns:minmax(90px,44%) 1fr;gap:10px;align-items:center;padding:3px 0;border-radius:4px}
.bar-row:hover,.bar-row:focus-visible,.pair .bar-track:hover,.pair .bar-track:focus-visible{background:var(--surface-2);outline:none}
.bar-label{font-size:13px;line-height:1.3;color:var(--text-secondary);overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow-wrap:anywhere}
.bar-track{display:flex;align-items:center;gap:8px;min-width:0}
.bar{height:14px;background:var(--series-1);border-radius:0 4px 4px 0;flex:0 0 auto;max-width:calc(100% - 56px)}
.bar.s2{background:var(--series-2)}.bar-value{font-size:12.5px;font-variant-numeric:tabular-nums;color:var(--text-primary)}
.pair-tracks{display:grid;gap:2px}.pair .bar{height:10px}
.legend{display:flex;gap:16px;font-size:12.5px;color:var(--text-secondary);margin-bottom:8px}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;background:var(--series-1)}.sw.s2{background:var(--series-2)}
details{margin-top:10px;font-size:13px}summary{cursor:pointer;color:var(--text-muted)}details table{margin-top:6px;font-size:13px}
.recs{display:grid;gap:12px;margin-top:16px}.rec{padding:16px 18px}.rec[hidden]{display:none}
.rec header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;margin-bottom:10px}
.badges{display:flex;gap:6px;flex-wrap:wrap}.badge{font-size:11.5px;padding:2px 8px;border-radius:999px;border:1px solid var(--border);color:var(--text-secondary);white-space:nowrap}
.badge::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px;background:var(--text-muted)}
.badge.kind::before{display:none}.impact-high::before{background:var(--crit)}.impact-medium::before{background:var(--warn)}.impact-low::before{background:var(--text-muted)}
.badge.ok::before{background:var(--good)}.badge.assume::before{background:var(--warn)}
dl{display:grid;grid-template-columns:86px minmax(0,1fr);gap:8px 14px;margin:0}dt{font-size:12px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.04em;padding-top:3px}
dd{margin:0;min-width:0}.ev-stats{color:var(--text-secondary)}.ev-stats b{color:var(--text-primary);font-variant-numeric:tabular-nums}
.examples{margin:6px 0 0;padding:0;list-style:none}.examples li{font:12.5px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--text-secondary);
border-left:2px solid var(--border);padding:2px 0 2px 10px;margin-top:4px;overflow-wrap:anywhere}
.snippet{margin-top:10px;border:1px solid var(--border);border-radius:8px;overflow:hidden;background:var(--surface-2)}
.snippet-head{display:flex;justify-content:space-between;align-items:center;padding:5px 8px 5px 12px;font-size:12px;color:var(--text-muted);border-bottom:1px solid var(--border)}
.snippet pre{margin:0;padding:10px 12px;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;overflow-wrap:anywhere}
.copy{font-size:12px;padding:1px 9px}.limits,.notes ul{color:var(--text-secondary);padding-left:20px}.limits li,.notes li{margin:4px 0}
#tip{position:fixed;pointer-events:none;background:var(--text-primary);color:var(--surface-1);font-size:12.5px;padding:5px 9px;border-radius:6px;max-width:320px;opacity:0;transition:opacity .08s;z-index:10}
@media (max-width:860px){.layout{grid-template-columns:1fr}.toc{position:static;flex-direction:row;flex-wrap:wrap;max-height:none}.toc-title{width:100%}dl{grid-template-columns:1fr}}
@media (max-width:860px){.rec,section{scroll-margin-top:12px}}
@media print{.toc,#tip,.copy{display:none}.layout{display:block}}
"""

JS = """
const tip=document.getElementById('tip');
function show(el,x,y){tip.textContent=el.dataset.tip;tip.style.opacity=1;const r=tip.getBoundingClientRect();
tip.style.left=Math.min(x+12,innerWidth-r.width-8)+'px';tip.style.top=Math.max(8,y-r.height-10)+'px';}
document.querySelectorAll('[data-tip]').forEach(el=>{
el.addEventListener('mousemove',ev=>show(el,ev.clientX,ev.clientY));el.addEventListener('mouseleave',()=>tip.style.opacity=0);
el.addEventListener('focus',()=>{const r=el.getBoundingClientRect();show(el,r.left+r.width/2,r.top);});el.addEventListener('blur',()=>tip.style.opacity=0);});
document.querySelectorAll('.copy').forEach(b=>b.addEventListener('click',()=>{
const text=b.closest('.snippet').querySelector('pre').textContent;
const done=()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1400);};
if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(text).then(done,fallback);}else{fallback();}
function fallback(){const t=document.createElement('textarea');t.value=text;t.style.position='fixed';t.style.opacity=0;document.body.appendChild(t);t.select();
try{document.execCommand('copy');done();}catch(e){b.textContent='Select and copy';}t.remove();}}));
document.querySelectorAll('.filter button').forEach(b=>b.addEventListener('click',()=>{
document.querySelectorAll('.filter button').forEach(x=>x.classList.toggle('on',x===b));
document.querySelectorAll('.rec,.fix').forEach(r=>{r.hidden=b.dataset.f!=='all'&&r.dataset.impact!==b.dataset.f;});}));
"""

if __name__ == "__main__":
    main()
