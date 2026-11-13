"""Filter, count, and sample records from an extracted dataset. Output is already redacted by extract.py.

Usage:
  sample.py <datadir> <dataset> [filters] [--count-by FIELD] [-n N] [--width W] [--fields a,b,c]

Datasets: prompts, bash, inline, errors, sessions.
Filters (all optional, combined with AND):
  --src claude|codex        --sub yes|no            --kind VALUE (prompts/inline)
  --grep REGEX              case-insensitive, matched against text/cmd/body/out/inp
  --not-grep REGEX          --purpose TAG (inline)  --interp NAME (inline)
  --prog NAME               bash: a program (base name or "git diff") appears in progs
  --err yes|no              bash: failed commands   --min-len N / --max-len N
  --eq FIELD=VALUE          exact match on any field
--count-by prints a frequency table of FIELD (list fields are exploded) with distinct-session counts.
Without --count-by, prints N evenly spread samples (default 12), each truncated to --width chars (default 400).
"""
import argparse
import collections
import datetime as dt
import json
import os
import re


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("datadir")
    ap.add_argument("dataset")
    for f in ("src", "sub", "kind", "grep", "not-grep", "purpose", "interp", "prog", "err", "count-by", "fields"):
        ap.add_argument("--" + f)
    ap.add_argument("--eq", action="append", default=[])
    ap.add_argument("--min-len", type=int)
    ap.add_argument("--max-len", type=int)
    ap.add_argument("-n", type=int, default=12)
    ap.add_argument("--width", type=int, default=400)
    a = ap.parse_args()

    with open(os.path.join(a.datadir, a.dataset + ".jsonl"), encoding="utf-8") as fh:
        rows = [json.loads(x) for x in fh]

    def blob(r):
        return "\n".join(str(r.get(k) or "") for k in ("text", "cmd", "body", "out", "inp", "desc"))

    g = re.compile(a.grep, re.I | re.S) if a.grep else None
    ng = re.compile(a.not_grep, re.I | re.S) if a.not_grep else None
    out = []
    for r in rows:
        if a.src and r.get("src") != a.src:
            continue
        if a.sub and bool(r.get("sub")) != (a.sub == "yes"):
            continue
        if a.kind and r.get("kind") != a.kind:
            continue
        if a.purpose and a.purpose not in (r.get("purpose") or []):
            continue
        if a.interp and r.get("interp") != a.interp:
            continue
        if a.prog and not any(p == a.prog or p.split()[0] == a.prog for p in r.get("progs") or []):
            continue
        if a.err and bool(r.get("err")) != (a.err == "yes"):
            continue
        ln = r.get("len") or r.get("nchars") or 0
        if a.min_len is not None and ln < a.min_len:
            continue
        if a.max_len is not None and ln > a.max_len:
            continue
        if any(str(r.get(e.split("=", 1)[0])) != e.split("=", 1)[1] for e in a.eq):
            continue
        b = blob(r) if (g or ng) else ""
        if g and not g.search(b):
            continue
        if ng and ng.search(b):
            continue
        out.append(r)

    print(f"# matched {len(out)} of {len(rows)} records in {len({r.get('sid') for r in out})} sessions")
    if a.count_by:
        c = collections.Counter()
        sess = collections.defaultdict(set)
        for r in out:
            v = r.get(a.count_by)
            for x in (v if isinstance(v, list) else [v]):
                x = str(x)[:80]
                c[x] += 1
                sess[x].add(r.get("sid"))
        for k, v in c.most_common(a.n if a.n != 12 else 40):
            print(f"{v:>6} {len(sess[k]):>5}  {k}")
        return
    if not out:
        return
    step = max(1, len(out) // a.n)
    fields = a.fields.split(",") if a.fields else None
    for r in out[::step][: a.n]:
        ts = dt.datetime.fromtimestamp(r["ts"], dt.timezone.utc).strftime("%Y-%m-%d") if isinstance(r.get("ts"), (int, float)) else "?"
        head = f"--- {r.get('src')} {ts} sid={str(r.get('sid'))[:8]} cwd={str(r.get('cwd') or '')[-40:]}"
        if fields:
            print(head)
            for f in fields:
                print(f"  {f}: {str(r.get(f))[: a.width]}")
            continue
        extra = " ".join(f"{k}={r[k]}" for k in ("kind", "interp", "nlines", "purpose", "tool", "err", "classes", "escalation", "denied") if r.get(k))
        print(head, extra)
        body = r.get("text") or r.get("body") or r.get("cmd") or r.get("inp") or ""
        print(str(body)[: a.width])
        if r.get("out"):
            print("  OUT:", str(r["out"])[: a.width // 2])


if __name__ == "__main__":
    main()
