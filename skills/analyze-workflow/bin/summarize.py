"""Print compact aggregates from the extracted datasets.

Usage: summarize.py <datadir> [section ...]
Sections: coverage tools bash inline errors prompts misc (default: all)
"""
import collections
import datetime as dt
import json
import os
import sys

D = sys.argv[1]
SECTIONS = set(sys.argv[2:]) or {"coverage", "tools", "bash", "inline", "errors", "prompts", "misc"}


def load(name):
    with open(os.path.join(D, name + ".jsonl"), encoding="utf-8") as fh:
        return [json.loads(x) for x in fh]


def day(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d") if ts else "?"


def top(counter, n=25, width=70):
    return "  " + "\n  ".join(f"{v:>6}  {str(k)[:width]}" for k, v in counter.most_common(n))


def proj(cwd):
    if not cwd:
        return "?"
    home = os.path.expanduser("~")
    p = cwd.replace(home, "~")
    parts = p.split("/")
    return "/".join(parts[:4]) if p.startswith("~/dev") or p.startswith("~/work") else "/".join(parts[:3])


agg = json.load(open(os.path.join(D, "agg.json")))
A = {k: collections.Counter(v) for k, v in agg.items()}

if "coverage" in SECTIONS:
    sessions = load("sessions")
    print("== COVERAGE")
    for src in ("claude", "codex"):
        ss = [s for s in sessions if s["src"] == src]
        main = [s for s in ss if s.get("kind", "main") == "main"]
        human = [s for s in main if s["prompts"] > 0]
        firsts = [s["first"] for s in human if s["first"]]
        lasts = [s["last"] for s in human if s["last"]]
        print(f"{src}: session records={len(ss)} main={len(main)} with human prompts={len(human)} "
              f"range={day(min(firsts)) if firsts else '?'}..{day(max(lasts)) if lasts else '?'} "
              f"prompts={sum(s['prompts'] for s in human)} tool calls(main)={sum(s['tools'] for s in main)} compacts={sum(s['compacts'] for s in ss)}")
        months = collections.Counter(day(s["first"])[:7] for s in human)
        print("  sessions by month:", dict(sorted(months.items())))
        print("  entrypoints:", dict(collections.Counter(s.get("entry") for s in human)))
        print("  top projects:\n" + top(collections.Counter(proj(s["cwd"]) for s in human), 15))
        models = collections.Counter()
        for s in ss:
            models.update(s["models"])
        print("  models:\n" + top(models, 10))
    print("codex session kinds:", dict(A["codex_session_kind"]))
    print("codex originator:", dict(A["codex_originator"]))
    print("extract failures:", dict(A.get("extract_failures", {})), "| codex history w/o rollout:", dict(A.get("codex_history_without_rollout", {})))

if "tools" in SECTIONS:
    print("\n== TOOLS")
    for k in sorted(A):
        if k.startswith(("tool:", "mcp_server:", "skill_tool:", "slash:", "agent_type:", "codex_exec_method", "codex_exec_shape", "codex_exec_complex",
                         "codex_exec_unparsed", "bang_cmd", "file_ext:", "webfetch_host")):
            print(f"-- {k} (total {sum(A[k].values())})\n" + top(A[k], 30))
    for k in ("mcp_server_sessions:claude", "skill_sessions:claude", "slash_sessions:claude"):
        c = collections.Counter(x.split("|")[0] for x in A.get(k, {}))
        print(f"-- distinct sessions per {k}\n" + top(c, 40))
    print("-- mcp_tool:claude\n" + top(A.get("mcp_tool:claude", collections.Counter()), 40))
    print("-- mcp_tool:codex\n" + top(A.get("mcp_tool:codex", collections.Counter()), 40))

if "misc" in SECTIONS:
    print("\n== MISC")
    for k in sorted(A):
        if k.startswith(("hook:", "perm_decision", "tool_denial", "interrupt", "system:", "permission-mode", "mode:", "codex_event", "codex_approval",
                         "codex_escalation", "codex_exec_js_logic", "claude_automated", "rtk_escape", "codex_out_prefix", "nonhuman_user", "attachment:", "tool_error")):
            print(f"-- {k} (total {sum(A[k].values())})\n" + top(A[k], 25, 90))

if "bash" in SECTIONS or "errors" in SECTIONS:
    bash = load("bash")

if "bash" in SECTIONS:
    print("\n== BASH")
    for src in ("claude", "codex"):
        b = [r for r in bash if r["src"] == src]
        progs = collections.Counter()
        base = collections.Counter()
        sess = collections.defaultdict(set)
        for r in b:
            for p in r["progs"]:
                progs[p] += 1
                base[p.split()[0]] += 1
                sess[p.split()[0]].add(r["sid"])
        print(f"-- {src}: commands={len(b)} sub-agent share={sum(r['sub'] for r in b)} avg len={sum(r['len'] for r in b) // max(len(b), 1)} "
              f">1000 chars={sum(r['len'] > 1000 for r in b)}")
        print("  programs (base, count, sessions):\n  " + "\n  ".join(f"{v:>6} {len(sess[k]):>5}  {k}" for k, v in base.most_common(70)))
        print("  program+subcommand:\n" + top(collections.Counter({k: v for k, v in progs.items() if " " in k}), 60))
        eph = collections.Counter()
        for r in b:
            eph.update(r["eph"])
        print("  ephemeral tool use:\n" + top(eph, 50))

if "errors" in SECTIONS:
    print("\n== ERRORS")
    for src in ("claude", "codex"):
        b = [r for r in bash if r["src"] == src]
        errs = [r for r in b if r["err"]]
        print(f"-- {src}: bash errors={len(errs)}/{len(b)} unresolved(no output seen)={sum(r['err'] is None for r in b)} denied={sum(1 for r in b if r.get('denied'))}")
        cls = collections.Counter()
        mc = collections.Counter()
        mcs = collections.defaultdict(set)
        mm = collections.Counter()
        ep = collections.Counter()
        for r in b:
            cls.update(r["classes"])
            for x in set(r["missing_cmd"]):
                mc[x] += 1
                mcs[x].add(r["sid"])
            mm.update(set(r["missing_mod"]))
            if r["err"]:
                ep.update({p.split()[0] for p in r["progs"][:1]})
        print("  error classes:\n" + top(cls, 20))
        print("  missing commands (count, sessions):\n  " + "\n  ".join(f"{v:>6} {len(mcs[k]):>4}  {k}" for k, v in mc.most_common(50)))
        print("  missing modules:\n" + top(mm, 40))
        print("  failing first program:\n" + top(ep, 30))
        print("  denial kinds:\n" + top(collections.Counter(r.get("denied") for r in b if r.get("denied")), 10))

if "inline" in SECTIONS:
    inline = load("inline")
    print("\n== INLINE")
    for src in ("claude", "codex"):
        il = [r for r in inline if r["src"] == src]
        print(f"-- {src}: inline items={len(il)} distinct sessions={len({r['sid'] for r in il})}")
        print("  kind/interp:\n" + top(collections.Counter(f"{r['kind']} / {r['interp']}" for r in il), 30))
        scripts = [r for r in il if r["kind"] in ("heredoc-script", "dash-c", "codex-js-tool")]
        print(f"  scripts={len(scripts)} median lines={sorted(r['nlines'] for r in scripts)[len(scripts) // 2] if scripts else 0} "
              f">30 lines={sum(r['nlines'] > 30 for r in scripts)}")
        pur = collections.Counter()
        purs = collections.defaultdict(set)
        imp = collections.Counter()
        for r in scripts:
            for p in r["purpose"] or ["(untagged)"]:
                pur[p] += 1
                purs[p].add(r["sid"])
            imp.update(r["imports"])
        print("  purpose tags (count, sessions):\n  " + "\n  ".join(f"{v:>6} {len(purs[k]):>4}  {k}" for k, v in pur.most_common(40)))
        print("  imports:\n" + top(imp, 45))
        print("  heredoc-write targets by ext:\n" + top(collections.Counter(os.path.splitext(r["target"])[1] or "(none)" for r in il if r["kind"] == "heredoc-write"), 15))
        print("  heredoc-stdin consumers:\n" + top(collections.Counter(r["interp"] for r in il if r["kind"] == "heredoc-stdin"), 20))
        print("  long filters:\n" + top(collections.Counter(r["interp"] for r in il if r["kind"] == "long-filter"), 10))

if "prompts" in SECTIONS:
    prompts = load("prompts")
    print("\n== PROMPTS")
    for src in ("claude", "codex"):
        ps = [r for r in prompts if r["src"] == src and r["kind"] == "prompt"]
        lens = sorted(r["len"] for r in ps)
        print(f"-- {src}: prompts={len(ps)} sessions={len({r['sid'] for r in ps})} median len={lens[len(lens) // 2] if lens else 0} "
              f"<=40 chars={sum(x <= 40 for x in lens)} >1000={sum(x > 1000 for x in lens)}")
        short = collections.Counter(r["text"].strip().lower()[:60] for r in ps if r["len"] <= 60)
        print("  most repeated short prompts:\n" + top(short, 60, 62))
        first = collections.Counter(" ".join(r["text"].strip().lower().split()[:3]) for r in ps)
        print("  most common 3-word openings:\n" + top(first, 50))
