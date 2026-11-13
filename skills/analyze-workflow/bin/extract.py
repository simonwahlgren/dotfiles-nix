"""Extract redacted, structured datasets from Claude Code and Codex transcripts.

Usage: extract.py <start YYYY-MM-DD> <outdir>
Writes sessions.jsonl, prompts.jsonl, bash.jsonl, inline.jsonl, errors.jsonl, agg.json.
All stored text is truncated and passed through redact().
"""
import collections
import datetime as dt
import glob
import io
import json
import multiprocessing as mp
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
START = sys.argv[1] if len(sys.argv) > 2 else "1970-01-01"
OUT = sys.argv[2] if len(sys.argv) > 2 else "."
START_EPOCH = dt.datetime.fromisoformat(START).replace(tzinfo=dt.timezone.utc).timestamp()

# ---------------------------------------------------------------- redaction
_RED = [
    (re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?(-----END [^-]*PRIVATE KEY-----|$)"), "[PRIVATE_KEY]"),
    (re.compile(r"\beyJ[\w-]{8,}\.[\w-]{8,}\.[\w-]+"), "[JWT]"),
    (re.compile(r"\b(sk|pk|rk)-[A-Za-z0-9_-]{16,}"), "[KEY]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "[GH_TOKEN]"),
    (re.compile(r"\bgithub_pat_\w{20,}"), "[GH_TOKEN]"),
    (re.compile(r"\bxox[abeprs]-[\w-]{10,}"), "[SLACK_TOKEN]"),
    (re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"), "[AWS_KEY]"),
    (re.compile(r"\blin_api_\w{10,}"), "[LINEAR_KEY]"),
    (re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{12,}"), r"\1 [REDACTED]"),
    (re.compile(r"(?i)([\w-]*(api[_-]?key|token|secret|passwd|password|credential|private[_-]?key)[\w-]*)(\"?\s*[:=]\s*\"?)([^\s\"',;&|)}]{6,})"), r"\1\3[REDACTED]"),
    (re.compile(r"://[^/\s:@]+:[^/\s:@]+@"), "://[REDACTED]@"),
    (re.compile(r"(?<![\w/.-])[A-Za-z0-9+/_-]{48,}={0,2}(?![\w/.-])"), "[LONG]"),
]


def redact(s, n=None):
    if not isinstance(s, str):
        s = str(s)
    if n and len(s) > n * 3:
        s = s[: n * 3]
    for rx, rep in _RED:
        s = rx.sub(rep, s)
    if n and len(s) > n:
        s = s[:n] + "…"
    return s


# ---------------------------------------------------------------- helpers
def lines(path):
    if path.endswith(".zst"):
        p = subprocess.run(["zstd", "-dc", path], capture_output=True)
        return io.StringIO(p.stdout.decode("utf-8", "replace"))
    return open(path, encoding="utf-8", errors="replace")


def epoch(ts):
    if isinstance(ts, (int, float)):
        return ts / 1000 if ts > 1e11 else ts
    if isinstance(ts, str):
        try:
            return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except Exception:
            return None
    return None


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for c in content:
            if isinstance(c, dict):
                t = c.get("text")
                if isinstance(t, str):
                    out.append(t)
                elif isinstance(c.get("content"), (str, list)):
                    out.append(text_of(c["content"]))
            elif isinstance(c, str):
                out.append(c)
        return "\n".join(out)
    return ""


INTERP = {"python", "python3", "node", "ruby", "perl", "bash", "sh", "zsh", "deno", "bun", "php", "lua", "Rscript", "nix-instantiate", "nix"}
WRAP = {"sudo", "rtk", "bypass", "proxy", "time", "nohup", "command", "exec", "env", "nice", "stdbuf", "builtin", "noglob", "then", "do", "else", "if", "while", "!", "{", "("}
SKIP = {"fi", "done", "for", "esac", "case", "}", ")", "function", "elif", "in", "select", "until"}
SUBCMD = {"git", "gh", "nix", "docker", "kubectl", "npm", "pnpm", "yarn", "uv", "cargo", "go", "poetry", "pip", "pip3", "systemctl", "journalctl", "terraform", "tofu", "helm", "aws", "gcloud", "gws", "rtk", "home-manager", "nixos-rebuild", "make", "just", "pytest", "circleci", "dd", "codex", "claude", "brew", "argocd", "kustomize", "sops", "bq", "dbt", "psql", "tmux", "linear", "pre-commit", "ruff", "ty", "mise", "direnv", "docker-compose", "podman", "flux", "stern", "k9s", "glab", "jj", "npx", "uvx", "pipx", "bunx"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
QUOTED = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"")
SPLIT = re.compile(r"&&|\|\||[;|\n]|(?<![>&\d])&(?![>&])")
ENVASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
DASH_C = re.compile(r"\b(python3?|node|ruby|perl|deno|bun|php)\b((?:\s+-[A-Za-z]\b)*?)\s+(-c|-e|--eval|-pe|-ne|-lne|-p)\s+(['\"])")
LONG_FILTER = re.compile(r"\b(jq|awk|gawk|sed|yq)\b((?:\s+-{1,2}[\w-]+(?:[ =][\w./-]+)?)*)\s+'([^']{70,})'")
EPHEMERAL = [
    (re.compile(r"\bnix\s+(?:run|shell)\s+((?:(?:nixpkgs|github:[\w./-]+)#[\w.\-]+\s*)+)"), "nix run/shell"),
    (re.compile(r"\b(npx|bunx|pnpx)\s+(?:--?[\w-]+\s+)*(@?[\w./-]+)"), "npx"),
    (re.compile(r"\b(uvx|pipx run)\s+(?:--?[\w-]+(?:[ =][\w.<>=-]+)?\s+)*([\w.\-\[\]]+)"), "uvx"),
    (re.compile(r"\buv run\s+(?:--?[\w-]+\s+)*--with[ =]([\w.\-\[\],<>=]+)"), "uv run --with"),
    (re.compile(r"\bpip3?\s+install\s+(?:--?[\w-]+\s+)*([\w.\-\[\]<>=]+)"), "pip install"),
]
MISSING_CMD = [
    re.compile(r"(?:^|\n)(?:\S+: )?(?:line \d+: )?([\w.+-]+): command not found"),
    re.compile(r"command not found: ([\w.+-]+)"),
    re.compile(r"(?:^|\n)(?:env: )?[‘'\"]?([\w.+-]+)[’'\"]?: No such file or directory\s*(?:\n|$)"),
    re.compile(r"The program '([\w.+-]+)' is not in your PATH"),
]
MISSING_MOD = [
    re.compile(r"ModuleNotFoundError: No module named '([\w.]+)'"),
    re.compile(r"Cannot find (?:module|package) '([^']+)'"),
    re.compile(r"ImportError: No module named ([\w.]+)"),
]
ERR_CLASS = [
    ("timeout", re.compile(r"(?i)timed out|timeout after|Command timed out")),
    ("permission denied", re.compile(r"(?i)permission denied|operation not permitted|EACCES")),
    ("sandbox/approval", re.compile(r"(?i)sandbox|was rejected|requires approval|auto mode classifier|not allowed|denied by")),
    ("no such file", re.compile(r"(?i)no such file or directory|cannot access|ENOENT")),
    ("syntax/parse error", re.compile(r"(?i)syntax ?error|parse error|unexpected token|unexpected EOF|unmatched")),
    ("python traceback", re.compile(r"Traceback \(most recent call last\)")),
    ("auth/network", re.compile(r"(?i)unauthorized|401|403 forbidden|could not resolve host|connection refused|authentication|not logged in")),
    ("git error", re.compile(r"(?m)^(fatal|error): ")),
    ("nix error", re.compile(r"(?m)^error: .*(nix|flake|derivation|attribute)|error: attribute '")),
    ("no matches (zsh glob)", re.compile(r"no matches found")),
    ("test failure", re.compile(r"(?i)\bFAILED\b|\d+ failed|AssertionError")),
    ("user rejected", re.compile(r"(?i)user doesn't want to proceed|rejected by user|user denied|interrupted by user")),
]
PURPOSE = [
    ("pdf", r"pypdf|PyPDF2|fitz|pdfplumber|pdfminer|\.pdf\b"),
    ("office docs (xlsx/docx/pptx)", r"openpyxl|python-docx|\bdocx\b|\bpptx\b|\.xlsx\b|xlrd"),
    ("json read/reshape", r"json\.(load|loads|dump|dumps)|JSON\.(parse|stringify)"),
    ("jsonl/transcript analysis", r"\.jsonl\b"),
    ("yaml", r"\byaml\.|ruamel|safe_load"),
    ("toml", r"tomllib|\btoml\b|tomli"),
    ("csv/tsv", r"\bcsv\.|DictReader|\.csv\b|\.tsv\b"),
    ("http/api call", r"\brequests\.|urllib\.request|urlopen|httpx|fetch\(|http\.client|aiohttp"),
    ("in-place file edit", r"write_text\(|\.write\(|open\([^)]*['\"][wa]['\"]|writeFileSync|re\.sub\(|\.replace\("),
    ("read/print file slices", r"read_text\(\)|readlines\(\)|splitlines\(\)|enumerate\(.*lines|readFileSync"),
    ("filesystem walk/search", r"os\.walk|\bglob\b|rglob|iterdir|scandir|os\.listdir"),
    ("regex search/extract", r"re\.(search|findall|finditer|match|compile)"),
    ("subprocess orchestration", r"subprocess\.|child_process|execSync|spawnSync"),
    ("sqlite/db", r"sqlite3|psycopg|sqlalchemy|duckdb|pymysql"),
    ("xml/html parse", r"xml\.etree|\bbs4\b|BeautifulSoup|lxml|html\.parser|HTMLParser"),
    ("markdown/doc processing", r"\.md\b|markdown"),
    ("date/time math", r"datetime|timedelta|time\.time|zoneinfo"),
    ("counting/stats", r"Counter\(|statistics\.|defaultdict|sorted\(.*key="),
    ("base64/hash/crypto", r"base64|hashlib|hmac\b|secrets\."),
    ("archive (zip/tar/gz)", r"zipfile|tarfile|gzip|zstd"),
    ("code analysis (ast)", r"\bast\.|tokenize|libcst"),
    ("image", r"\bPIL\b|cv2|Pillow"),
    ("diff/compare", r"difflib|unified_diff"),
    ("google workspace", r"googleapis|gspread|\bgws\b|spreadsheets"),
    ("env/config inspect", r"os\.environ|process\.env|sys\.path|shutil\.which|importlib"),
    ("test/assert snippet", r"\bassert\b|unittest|pytest"),
    ("pty/terminal/tmux", r"\bpty\b|termios|pexpect|tmux"),
    ("socket/port", r"\bsocket\.|listen\(|bind\("),
    ("struct/binary", r"\bstruct\.|bytes\.fromhex|\.hex\("),
]
PURPOSE = [(n, re.compile(p)) for n, p in PURPOSE]
PY_IMPORT = re.compile(r"(?m)^\s*(?:import|from)\s+([A-Za-z_][\w]*)")
JS_IMPORT = re.compile(r"require\(['\"]([^'\"]+)['\"]\)|from\s+['\"]([^'\"]+)['\"]")


def strip_heredocs(cmd):
    """Return (command without heredoc bodies, [(prefix_line, tag, body)])."""
    docs = []
    out = []
    pos = 0
    while True:
        m = HEREDOC.search(cmd, pos)
        if not m:
            out.append(cmd[pos:])
            break
        tag = m.group(2)
        eol = cmd.find("\n", m.end())
        if eol == -1:
            out.append(cmd[pos:])
            break
        endm = re.compile(r"\n[ \t]*" + re.escape(tag) + r"[ \t]*(?=\n|$)").search(cmd, eol)
        if not endm:
            body = cmd[eol + 1:]
            nxt = len(cmd)
        else:
            body = cmd[eol + 1: endm.start()]
            nxt = endm.end()
        line_start = cmd.rfind("\n", 0, m.start()) + 1
        docs.append((cmd[line_start: eol], tag, body))
        out.append(cmd[pos:eol])
        pos = nxt
    return "".join(out), docs


def programs(cmd_nodoc):
    flat = QUOTED.sub(" Q ", cmd_nodoc)
    flat = re.sub(r"\$\([^)]*\)", " S ", flat)
    flat = re.sub(r"\d*>>?&?\d*(/dev/null)?", " ", flat)
    progs = []
    for seg in SPLIT.split(flat):
        toks = seg.split()
        i = 0
        while i < len(toks):
            t = toks[i]
            if ENVASSIGN.match(t) or t in WRAP:
                i += 1
                continue
            if t == "timeout" and i + 1 < len(toks):
                i += 2
                continue
            if t.startswith("-"):
                i += 1
                continue
            if t == "cd" or t in SKIP:
                i = len(toks)
                continue
            break
        if i >= len(toks):
            continue
        p = os.path.basename(toks[i])
        if not re.match(r"^[A-Za-z0-9_.+-]+$", p) or p in ("Q", "S"):
            continue
        sub = None
        if p in SUBCMD:
            for t in toks[i + 1:]:
                if t in ("Q", "S"):
                    break
                if not t.startswith("-") and re.match(r"^[a-z][a-z0-9-]*$", t):
                    sub = t
                    break
                if not t.startswith("-"):
                    break
        progs.append(p + (" " + sub if sub else ""))
    return progs


def consumer(prefix):
    flat = QUOTED.sub(" Q ", prefix[: prefix.rfind("<<")] if "<<" in prefix else prefix)
    seg = re.split(r"&&|\|\||[;|]", flat)[-1]
    toks = [t for t in seg.split() if not ENVASSIGN.match(t)]
    names = [os.path.basename(t) for t in toks if re.match(r"^[\w./+-]+$", t)]
    for n in names:
        if n in INTERP:
            return n
    for n in names:
        if n not in WRAP and n != "timeout" and not n.isdigit():
            return n
    return "?"


def tag_purpose(body):
    return [n for n, rx in PURPOSE if rx.search(body)]


def analyze_cmd(cmd):
    nodoc, docs = strip_heredocs(cmd)
    info = {"progs": programs(nodoc), "inline": [], "eph": []}
    for prefix, tag, body in docs:
        c = consumer(prefix)
        target = None
        m = re.search(r">>?\s*([^\s<>|;&]+)", prefix)
        if m:
            target = m.group(1)
        if c in ("python", "python3", "node", "ruby", "perl", "bash", "sh", "zsh", "deno", "bun", "php"):
            kind = "heredoc-script"
        elif c in ("cat", "tee") and target:
            kind = "heredoc-write"
        else:
            kind = "heredoc-stdin"
        info["inline"].append({"kind": kind, "interp": c, "body": body, "target": target, "prefix": prefix})
    for m in DASH_C.finditer(nodoc):
        q = m.group(4)
        start = m.end()
        j = start
        while j < len(nodoc):
            if nodoc[j] == "\\" and q == '"':
                j += 2
                continue
            if nodoc[j] == q:
                break
            j += 1
        body = nodoc[start:j]
        info["inline"].append({"kind": "dash-c", "interp": m.group(1), "body": body, "target": None, "prefix": m.group(0)})
    for m in LONG_FILTER.finditer(nodoc):
        info["inline"].append({"kind": "long-filter", "interp": m.group(1), "body": m.group(3), "target": None, "prefix": m.group(1)})
    for rx, label in EPHEMERAL:
        for m in rx.finditer(nodoc):
            arg = m.group(m.lastindex).strip()
            for a in arg.split():
                if re.match(r"^[@\w]", a):
                    info["eph"].append(label + ": " + a[:60])
    for m in re.finditer(r"\bnix-shell\b([^\n|;&]*)", nodoc):
        toks = m.group(1).split()
        for i, t in enumerate(toks):
            if t in ("-p", "--packages"):
                for a in toks[i + 1:]:
                    if a.startswith("-") or not re.match(r"^[\w.]+[\w.\-]*$", a):
                        break
                    info["eph"].append("nix-shell -p: " + a[:60])
    return info


def scan_output(out):
    head = out[:6000] if out else ""
    res = {"missing_cmd": [], "missing_mod": [], "classes": []}
    for rx in MISSING_CMD:
        res["missing_cmd"] += rx.findall(head)
    for rx in MISSING_MOD:
        res["missing_mod"] += rx.findall(head)
    for name, rx in ERR_CLASS:
        if rx.search(head):
            res["classes"].append(name)
    return res


class Acc:
    def __init__(self):
        self.C = collections.defaultdict(collections.Counter)
        self.sessions = {}
        self.prompts = []
        self.bash = []
        self.inline = []
        self.errors = []

    def dump(self):
        return {"C": {k: dict(v) for k, v in self.C.items()}, "sessions": self.sessions, "prompts": self.prompts,
                "bash": self.bash, "inline": self.inline, "errors": self.errors}


def add_bash(acc, src, sid, ts, cwd, sub, cmd, desc, key):
    info = analyze_cmd(cmd)
    for m in re.finditer(r"\brtk (proxy|bypass)\b", cmd):
        acc.C["rtk_escape:" + src]["rtk " + m.group(1)] += 1
    if re.search(r"(^|[;&|]\s*)rtk\b", cmd):
        acc.C["rtk_escape:" + src]["commands using rtk"] += 1
    acc.C["rtk_escape:" + src]["all commands"] += 1
    rec = {"k": key, "src": src, "sid": sid, "ts": ts, "cwd": cwd, "sub": bool(sub), "cmd": redact(cmd, 3000),
           "len": len(cmd), "desc": redact(desc or "", 200), "progs": info["progs"], "eph": info["eph"],
           "err": None, "classes": [], "missing_cmd": [], "missing_mod": [], "out": ""}
    for i, il in enumerate(info["inline"]):
        body = il["body"]
        imports = sorted(set(PY_IMPORT.findall(body))) if il["interp"].startswith("python") else sorted({a or b for a, b in JS_IMPORT.findall(body)})
        acc.inline.append({"k": key, "i": i, "src": src, "sid": sid, "ts": ts, "cwd": cwd, "sub": bool(sub), "kind": il["kind"],
                           "interp": il["interp"], "target": redact(il["target"] or "", 150), "nlines": body.count("\n") + 1,
                           "nchars": len(body), "imports": imports[:25], "purpose": tag_purpose(body),
                           "prefix": redact(il["prefix"], 200), "body": redact(body, 2500), "desc": redact(desc or "", 200)})
    return rec


def finish_bash(rec, out, is_err):
    sc = scan_output(out or "")
    rec["err"] = bool(is_err)
    rec["classes"] = sc["classes"] if (is_err or sc["missing_cmd"] or sc["missing_mod"]) else []
    rec["missing_cmd"] = sc["missing_cmd"][:5]
    rec["missing_mod"] = sc["missing_mod"][:5]
    if is_err or sc["missing_cmd"] or sc["missing_mod"]:
        rec["out"] = redact(out or "", 400)


# ---------------------------------------------------------------- Claude
CMD_NAME = re.compile(r"<command-name>\s*(/?[\w:.\-]+)\s*</command-name>")
CMD_ARGS = re.compile(r"<command-args>([\s\S]*?)</command-args>")
REMINDER = re.compile(r"<system-reminder>[\s\S]*?</system-reminder>")
NONHUMAN = ("<local-command", "<task-notification", "[SYSTEM NOTIFICATION", "<bash-stdout", "<bash-stderr", "Another Claude session",
            "<user-prompt-submit-hook", "Caveat:", "<teammate-message", "[Subagent hand-back]", "<agent-message", "This session is being continued",
            "<tools-used-before-summary", "Base directory for this skill", "<command-message", "[Request interrupted", "<new-diagnostics")


def claude_file(path):
    acc = Acc()
    C = acc.C
    subfile = "/subagents/" in path
    pending = {}
    if "claude-mem" in path:
        # Sessions started by the claude-mem plugin's observer, not by the user.
        C["claude_automated_files"]["claude-mem observer"] += 1
        return acc.dump()
    try:
        fh = lines(path)
    except Exception:
        return acc.dump()
    for ln in fh:
        try:
            o = json.loads(ln)
        except Exception:
            continue
        t = o.get("type")
        ts = epoch(o.get("timestamp"))
        if ts is not None and ts < START_EPOCH:
            continue
        if o.get("entrypoint") == "sdk-cli":
            # Headless runs (skill evals, scripted `claude -p`), not interactive work.
            acc = Acc()
            acc.C["claude_automated_files"]["headless sdk-cli"] += 1
            return acc.dump()
        sid = o.get("sessionId")
        sub = subfile or o.get("isSidechain")
        cwd = o.get("cwd")
        if sid and ts and not sub:
            s = acc.sessions.setdefault("claude:" + sid, {"src": "claude", "sid": sid, "first": ts, "last": ts, "cwd": cwd, "prompts": 0,
                                                          "tools": 0, "models": {}, "entry": o.get("entrypoint"), "compacts": 0})
            s["first"] = min(s["first"], ts)
            s["last"] = max(s["last"], ts)
            if cwd and not s.get("cwd"):
                s["cwd"] = cwd
        else:
            s = None
        if t == "assistant":
            m = o.get("message") or {}
            if s is not None and m.get("model"):
                s["models"][m["model"]] = s["models"].get(m["model"], 0) + 1
            for x in m.get("content") or []:
                if not isinstance(x, dict) or x.get("type") != "tool_use":
                    continue
                name = x.get("name") or "?"
                inp = x.get("input") if isinstance(x.get("input"), dict) else {}
                key = "c:" + str(x.get("id"))
                C["dedup_tool"][key] += 1
                if C["dedup_tool"][key] > 1:
                    continue
                C["tool:claude" + (":sub" if sub else "")][name] += 1
                if s is not None:
                    s["tools"] += 1
                if name.startswith("mcp__"):
                    C["mcp_server:claude"][name.split("__")[1]] += 1
                    C["mcp_tool:claude"][name] += 1
                    C["mcp_server_sessions:claude"][name.split("__")[1] + "|" + str(sid)] = 1
                if name == "Skill":
                    C["skill_tool:claude"][str(inp.get("skill"))] += 1
                    C["skill_sessions:claude"][str(inp.get("skill")) + "|" + str(sid)] = 1
                if name in ("Agent", "Task"):
                    C["agent_type:claude"][str(inp.get("subagent_type")) + " / model=" + str(inp.get("model")) + " / effort=" + str(inp.get("effort"))] += 1
                if name == "Bash":
                    rec = add_bash(acc, "claude", sid, ts, cwd, sub, str(inp.get("command") or ""), inp.get("description"), key)
                    rec["bg"] = bool(inp.get("run_in_background"))
                    pending[x.get("id")] = rec
                    acc.bash.append(rec)
                else:
                    pending[x.get("id")] = {"tool": name, "sid": sid, "ts": ts, "inp": inp}
                if name in ("Read", "Edit", "Write"):
                    ext = os.path.splitext(str(inp.get("file_path") or ""))[1].lower()[:8]
                    C["file_ext:" + name][ext or "(none)"] += 1
                if name == "WebFetch":
                    host = re.sub(r"^https?://([^/]+).*", r"\1", str(inp.get("url") or ""))
                    C["webfetch_host"][host[:60]] += 1
        elif t == "user":
            m = o.get("message") or {}
            c = m.get("content")
            if isinstance(c, list) and any(isinstance(x, dict) and x.get("type") == "tool_result" for x in c):
                pd = o.get("permissionDecision")
                if isinstance(pd, dict):
                    C["perm_decision:claude"][f"{pd.get('decision')}|{pd.get('source')}|{pd.get('reasonType')}"] += 1
                if o.get("toolDenialKind"):
                    C["tool_denial_kind:claude"][str(o.get("toolDenialKind"))] += 1
                for x in c:
                    if not isinstance(x, dict) or x.get("type") != "tool_result":
                        continue
                    rec = pending.pop(x.get("tool_use_id"), None)
                    if rec is None:
                        continue
                    out = text_of(x.get("content"))
                    is_err = bool(x.get("is_error"))
                    if "cmd" in rec:
                        finish_bash(rec, out, is_err)
                        if o.get("toolDenialKind"):
                            rec["denied"] = str(o.get("toolDenialKind"))
                    elif is_err:
                        sc = scan_output(out)
                        C["tool_error:claude"][rec["tool"]] += 1
                        for cl in sc["classes"]:
                            C["tool_error_class:claude"][rec["tool"] + " | " + cl] += 1
                        acc.errors.append({"src": "claude", "sid": rec["sid"], "ts": rec["ts"], "tool": rec["tool"], "sub": bool(sub),
                                           "denied": str(o.get("toolDenialKind") or ""),
                                           "inp": redact(json.dumps(rec["inp"])[:600], 300), "out": redact(out, 400)})
                continue
            if sub or o.get("isMeta") or o.get("isCompactSummary"):
                continue
            txt = text_of(c)
            txt = REMINDER.sub("", txt).strip()
            if not txt:
                continue
            for m2 in CMD_NAME.finditer(txt):
                C["slash:claude"][m2.group(1)] += 1
                C["slash_sessions:claude"][m2.group(1) + "|" + str(sid)] = 1
            if "[Request interrupted" in txt:
                C["interrupt:claude"]["interrupted" + (" for tool use" if "tool use" in txt else "")] += 1
                continue
            if txt.startswith("<bash-input>"):
                C["bang_cmd:claude"][(programs(txt[12:].split("</bash-input>")[0]) or ["?"])[0]] += 1
                continue
            slash = CMD_NAME.search(txt)
            if slash:
                a = CMD_ARGS.search(txt)
                args = a.group(1).strip() if a else ""
                acc.prompts.append({"src": "claude", "sid": sid, "ts": ts, "cwd": cwd, "kind": "slash", "cmd": slash.group(1),
                                    "text": redact(args, 1500), "len": len(args), "origin": bool(o.get("origin"))})
                continue
            if txt.startswith(NONHUMAN):
                C["nonhuman_user:claude"][txt[:22].split("\n")[0]] += 1
                continue
            if s is not None:
                s["prompts"] += 1
            acc.prompts.append({"src": "claude", "sid": sid, "ts": ts, "cwd": cwd, "kind": "prompt", "cmd": "",
                                "text": redact(txt, 1500), "len": len(txt), "origin": False, "uuid": o.get("uuid")})
        elif t == "attachment":
            a = o.get("attachment") or {}
            at = str(a.get("type"))
            if at.startswith("hook"):
                C["hook:claude"][f"{at}|{a.get('hookEvent')}|{str(a.get('hookName'))[:50]}|exit={a.get('exitCode')}"] += 1
                if at not in ("hook_success", "hook_additional_context", "hook_system_message"):
                    acc.errors.append({"src": "claude", "sid": sid, "ts": ts, "tool": "HOOK:" + at, "sub": bool(sub), "denied": "",
                                       "inp": redact(str(a.get("command") or a.get("hookName")), 300),
                                       "out": redact(str(a.get("stderr") or a.get("content") or a.get("stdout") or ""), 400)})
            else:
                C["attachment:claude"][at] += 1
        elif t == "system":
            C["system:claude"][str(o.get("subtype"))] += 1
            if o.get("subtype") == "compact_boundary" and s is not None:
                s["compacts"] += 1
        elif t in ("permission-mode", "mode"):
            C[t + ":claude"][str(o.get("permissionMode") or o.get("mode"))] += 1
    return acc.dump()


# ---------------------------------------------------------------- Codex
TOOLCALL = re.compile(r"tools\.([A-Za-z_][\w]*)\(\s*")
DEC = json.JSONDecoder()
EXIT_RX = [re.compile(r"(?i)exit[ _]?code[\"']?\s*[:=]\s*(-?\d+)"), re.compile(r"(?i)exited with (?:code|status) (-?\d+)"),
           re.compile(r"(?i)Process exited with code (-?\d+)")]


def codex_exit(out):
    head = out[:1500]
    for rx in EXIT_RX:
        m = rx.search(head)
        if m:
            return int(m.group(1))
    return None


def js_object_fields(raw, pos):
    """Parse a JS object literal ({cmd:"...", "workdir":"..."}) at pos; return its string/JSON-valued fields."""
    n = len(raw)
    out = {}
    if pos >= n or raw[pos] != "{":
        return out
    i = pos + 1
    while i < n:
        while i < n and raw[i] in " \t\r\n,":
            i += 1
        if i >= n or raw[i] == "}":
            break
        m = re.compile(r"""(?:"([^"]+)"|'([^']+)'|([A-Za-z_$][\w$]*))\s*:\s*""").match(raw, i)
        if not m:
            break
        key = m.group(1) or m.group(2) or m.group(3)
        i = m.end()
        if i >= n:
            break
        ch = raw[i]
        if ch in '"[{' or ch.isdigit() or raw.startswith(("true", "false", "null"), i):
            try:
                val, i = DEC.raw_decode(raw, i)
                out[key] = val
                continue
            except Exception:
                pass
        if ch in "'`":
            j = i + 1
            while j < n and raw[j] != ch:
                j += 2 if raw[j] == "\\" else 1
            out[key] = raw[i + 1: j]
            i = j + 1
            continue
        depth = 0
        while i < n:
            c = raw[i]
            if c in "([{":
                depth += 1
            elif c in ")]}":
                if depth == 0:
                    break
                depth -= 1
            elif c == "," and depth == 0:
                break
            i += 1
        out.setdefault(key, None)
    return out


def codex_outputs(output):
    """Return [(exit_code, text)] per exec result found in a Codex tool output, plus the flattened text."""
    items = output if isinstance(output, list) else [output]
    res = []
    flat = []
    for it in items:
        t = it.get("text") if isinstance(it, dict) else it
        if not isinstance(t, str):
            continue
        flat.append(t)
        if t.startswith("{") and '"exit_code"' in t[:300]:
            try:
                d = json.loads(t)
                res.append((d.get("exit_code"), str(d.get("output") or "")))
            except Exception:
                pass
    return res, "\n".join(flat)


def codex_file(path):
    acc = Acc()
    C = acc.C
    sid = None
    cwd = None
    sub = False
    s = None
    pending = {}
    try:
        fh = lines(path)
    except Exception:
        return acc.dump()
    for ln in fh:
        try:
            o = json.loads(ln)
        except Exception:
            continue
        t = o.get("type")
        p = o.get("payload") if isinstance(o.get("payload"), dict) else {}
        pt = p.get("type")
        ts = epoch(o.get("timestamp"))
        if t == "session_meta" and sid is None:
            sid = p.get("id") or p.get("session_id")
            cwd = p.get("cwd")
            src = p.get("source")
            sub = isinstance(src, dict)
            kind = "main"
            if sub:
                inner = src.get("subagent")
                kind = "sub:" + (str(inner.get("other")) if isinstance(inner, dict) and inner.get("other") else (list(inner.keys())[0] if isinstance(inner, dict) and inner else str(inner)))
            C["codex_session_kind"][kind] += 1
            C["codex_originator"][str(p.get("originator"))] += 1
            mts = epoch(p.get("timestamp")) or ts
            s = {"src": "codex", "sid": sid, "first": mts, "last": mts, "cwd": cwd, "prompts": 0, "tools": 0, "models": {},
                 "entry": str(p.get("originator")), "compacts": 0, "kind": kind, "forked": bool(p.get("forked_from_id"))}
            acc.sessions["codex:" + str(sid)] = s
            continue
        if ts is not None and ts < START_EPOCH:
            continue
        if s is not None and ts:
            s["last"] = max(s["last"] or ts, ts)
        C["codex_kind"][f"{t}/{pt}"] += 1
        if t == "turn_context":
            if s is not None and p.get("model"):
                k = f"{p.get('model')} / effort={p.get('effort')}"
                s["models"][k] = s["models"].get(k, 0) + 1
            if p.get("cwd"):
                cwd = p["cwd"]
            C["codex_approval_policy"][str(p.get("approval_policy")) + " | " + str((p.get("sandbox_policy") or {}).get("type"))] += 1
            continue
        if t in ("compacted",) and s is not None:
            s["compacts"] += 1
        if t != "response_item":
            if pt in ("turn_aborted", "error", "stream_error", "exec_approval_request", "apply_patch_approval_request"):
                C["codex_event"][pt + ":" + str(p.get("reason") or "")[:40]] += 1
            continue
        if pt in ("function_call", "custom_tool_call", "local_shell_call"):
            name = p.get("name") or pt
            cid = p.get("call_id") or p.get("id")
            key = "x:" + str(cid)
            C["dedup_tool"][key] += 1
            if C["dedup_tool"][key] > 1:
                continue
            kindsub = ":sub" if sub else ""
            C["tool:codex" + kindsub][name] += 1
            if s is not None:
                s["tools"] += 1
            raw = p.get("arguments") if pt == "function_call" else p.get("input")
            raw = raw if isinstance(raw, str) else json.dumps(raw or p.get("action") or {})
            cmds = []
            if name == "exec":
                calls = list(TOOLCALL.finditer(raw))
                C["codex_exec_shape"]["calls=" + str(min(len(calls), 5)) + ("+" if len(calls) > 5 else "")] += 1
                for m in calls:
                    meth = m.group(1)
                    C["codex_exec_method" + kindsub][meth] += 1
                    arg = js_object_fields(raw, m.end())
                    if meth in ("exec_command", "shell", "exec", "local_shell"):
                        cmd = arg.get("cmd") or arg.get("command")
                        if isinstance(cmd, list):
                            cmd = " ".join(str(x) for x in cmd)
                        if isinstance(cmd, str):
                            cmds.append((cmd, arg))
                        else:
                            C["codex_exec_unparsed"][meth] += 1
                    elif meth.startswith("mcp__") or "__" in meth:
                        C["mcp_tool:codex"][meth] += 1
                        srv = meth.split("__")[1] if meth.startswith("mcp__") else meth.split("__")[0]
                        C["mcp_server:codex"][srv] += 1
                        C["mcp_server_sessions:codex"][srv + "|" + str(sid)] = 1
                for f in re.findall(r"\*\*\* (?:Update|Add|Delete) File: ([\w./~+-]+)", raw):
                    C["file_ext:codex_patch"][os.path.splitext(f)[1].lower()[:8] or "(none)"] += 1
                glue = len(raw) - sum(len(c) for c, _ in cmds)
                if not re.search(r"\*\*\* Begin Patch", raw) and (glue > 600 or re.search(r"\b(for|while|if|function|=>|\.map\(|\.filter\()\b", QUOTED.sub("Q", raw))):
                    C["codex_exec_js_logic" + kindsub]["exec cells with JS control flow or >600 chars of glue"] += 1
            elif name in ("shell", "exec_command", "local_shell_call", "container.exec", "shell_command"):
                try:
                    arg = json.loads(raw)
                    cmd = arg.get("cmd") or arg.get("command")
                    if isinstance(cmd, list):
                        cmd = " ".join(str(x) for x in cmd[2:]) if len(cmd) > 2 and cmd[1] in ("-lc", "-c") else " ".join(str(x) for x in cmd)
                    if isinstance(cmd, str):
                        cmds.append((cmd, arg))
                except Exception:
                    C["codex_exec_unparsed"][name] += 1
            elif name == "js":
                try:
                    code = json.loads(raw).get("code") or ""
                except Exception:
                    code = raw
                acc.inline.append({"k": key, "i": 0, "src": "codex", "sid": sid, "ts": ts, "cwd": cwd, "sub": sub, "kind": "codex-js-tool",
                                   "interp": "js", "target": "", "nlines": code.count("\n") + 1, "nchars": len(code),
                                   "imports": sorted({a or b for a, b in JS_IMPORT.findall(code)})[:25], "purpose": tag_purpose(code),
                                   "prefix": "js tool", "body": redact(code, 2500), "desc": ""})
            elif name.startswith("mcp__") or "__" in name:
                C["mcp_tool:codex"][name] += 1
                C["mcp_server:codex"][name.split("__")[1] if name.startswith("mcp__") else name.split("__")[0]] += 1
            elif name == "spawn_agent":
                try:
                    a = json.loads(raw)
                    C["agent_type:codex"][f"model={a.get('model')} / effort={a.get('reasoning_effort')}"] += 1
                except Exception:
                    pass
            recs = []
            for j, (cmd, arg) in enumerate(cmds):
                rec = add_bash(acc, "codex", sid, ts, arg.get("workdir") or cwd, sub, cmd, arg.get("justification") or "", key + ":" + str(j))
                if arg.get("sandbox_permissions"):
                    rec["escalation"] = str(arg.get("sandbox_permissions"))
                    C["codex_escalation" + kindsub][str(arg.get("sandbox_permissions"))] += 1
                    C["codex_escalation_prog" + kindsub][(rec["progs"] or ["?"])[0]] += 1
                recs.append(rec)
                acc.bash.append(rec)
            pending[cid] = (name, recs, raw[:600])
        elif pt in ("function_call_output", "custom_tool_call_output", "local_shell_call_output"):
            item = pending.pop(p.get("call_id"), None)
            if item is None:
                continue
            name, recs, raw = item
            results, out = codex_outputs(p.get("output"))
            C["codex_out_prefix"][re.sub(r"\d+", "N", out[:28]).replace("\n", "\\n")] += 1
            code = codex_exit(out)
            is_err = code not in (None, 0) or out.startswith("Script failed")
            if recs and len(results) == len(recs):
                for rec, (ec, otext) in zip(recs, results):
                    finish_bash(rec, otext, ec not in (None, 0))
            elif recs:
                for rec in recs:
                    finish_bash(rec, out, is_err)
            elif is_err or re.match(r"(?i)\s*(error|failed|exec error)", out[:40]):
                C["tool_error:codex"][name] += 1
                acc.errors.append({"src": "codex", "sid": sid, "ts": ts, "tool": name, "sub": sub, "denied": "",
                                   "inp": redact(raw, 300), "out": redact(out, 400)})
    return acc.dump()


def run(job):
    kind, path = job
    try:
        return (claude_file if kind == "claude" else codex_file)(path)
    except Exception as e:  # keep going; count failures
        return {"C": {"extract_failures": {kind + ":" + type(e).__name__: 1}}, "sessions": {}, "prompts": [], "bash": [], "inline": [], "errors": []}


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [("claude", f) for f in glob.glob(HOME + "/.claude/projects/**/*.jsonl", recursive=True)]
    jobs += [("codex", f) for f in glob.glob(HOME + "/.codex/sessions/**/*.jsonl*", recursive=True)]
    jobs.sort(key=lambda j: -os.path.getsize(j[1]))
    C = collections.defaultdict(collections.Counter)
    sessions = {}
    seen = set()
    outs = {n: open(os.path.join(OUT, n + ".jsonl"), "w") for n in ("prompts", "bash", "inline", "errors")}
    n = collections.Counter()
    with mp.Pool(max(2, (os.cpu_count() or 4) - 2)) as pool:
        for res in pool.imap_unordered(run, jobs, chunksize=2):
            for k, v in res["C"].items():
                if k == "dedup_tool":
                    continue
                C[k].update(v)
            for k, s in res["sessions"].items():
                if k in sessions:
                    a = sessions[k]
                    a["first"] = min(a["first"], s["first"])
                    a["last"] = max(a["last"], s["last"])
                    a["prompts"] += s["prompts"]
                    a["tools"] += s["tools"]
                    a["compacts"] += s["compacts"]
                    for m, c in s["models"].items():
                        a["models"][m] = a["models"].get(m, 0) + c
                else:
                    sessions[k] = s
            for name in ("prompts", "bash", "inline", "errors"):
                for r in res[name]:
                    key = None
                    if name in ("bash", "inline"):
                        key = (name, r["k"], r.get("i"))
                    elif name == "prompts" and r.get("uuid"):
                        key = (name, r["uuid"])
                    if key:
                        if key in seen:
                            n["dup_" + name] += 1
                            continue
                        seen.add(key)
                    outs[name].write(json.dumps(r, ensure_ascii=False) + "\n")
                    n[name] += 1
    # Codex user prompts come from history.jsonl (the rollouts mix injected context into user messages).
    hp = HOME + "/.codex/history.jsonl"
    if os.path.exists(hp):
        with open(hp, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                ts = epoch(r.get("ts"))
                if ts is None or ts < START_EPOCH:
                    continue
                sid = r.get("session_id")
                s = sessions.get("codex:" + str(sid))
                txt = str(r.get("text") or "")
                if s:
                    s["prompts"] += 1
                else:
                    C["codex_history_without_rollout"]["prompts"] += 1
                kind, cmd = "prompt", ""
                m = re.match(r"^(/[\w:.\-]+|\$[\w:.\-]+)\s*", txt)
                if m:
                    kind, cmd = "slash", m.group(1)
                    C["slash:codex"][cmd] += 1
                outs["prompts"].write(json.dumps({"src": "codex", "sid": sid, "ts": ts, "cwd": s.get("cwd") if s else None, "kind": kind,
                                                  "cmd": cmd, "text": redact(txt, 1500), "len": len(txt), "origin": False}, ensure_ascii=False) + "\n")
                n["prompts"] += 1
    for f in outs.values():
        f.close()
    with open(os.path.join(OUT, "sessions.jsonl"), "w") as fh:
        for s in sessions.values():
            fh.write(json.dumps(s) + "\n")
    with open(os.path.join(OUT, "agg.json"), "w") as fh:
        json.dump({k: dict(v.most_common()) for k, v in C.items()}, fh, indent=1)
    print("files", len(jobs), dict(n), "sessions", len(sessions))


if __name__ == "__main__":
    main()
