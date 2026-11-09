#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# ///
"""Write judged status verdicts back into the Harmonization matrix.

Reads a verdicts JSON list on stdin or via --verdicts:

    [{"a1": "Services!C3", "repo": "...", "column": "...",
      "verdict": "DONE", "why": "uv.lock + [project]",
      "reason": "uv + PEP 621"}, ...]

`why` is the evidence for that one cell; `reason` is the coarse bucket the
breakdown groups on, and falls back to `why` when omitted.

Prints a dry-run table by default. `--apply` writes, but only after re-reading
the grid and confirming every target cell still holds the value the
fingerprint recorded -- a concurrent human edit always wins. The prior value
comes from the fingerprint file rather than from the verdicts, so a verdict
cannot misdeclare what it is overwriting; that is why --fingerprint is
required. A verdict equal to the value already in the cell is counted and
dropped, not written.

Nothing but individual status cells is ever touched: no rows, columns,
headers, owners, or bottom-section cells.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime

SPREADSHEET_ID = "18xz-mqyLpdZQNn1CQ_-iyIn8fSuiCDeMiIsTRE_UEhU"
SERVICES_TAB = "Services"
SEPARATOR = "Not in Datadog catalog"
FIRST_DATA_ROW = 3
FIRST_STATUS_COL = 2  # 0-based; A = Service, B = Owner

# The corner cell above "Service": blank by default, always on screen, and
# writing it does not change len(row 1) -- which the sibling
# harmonization-matrix-update-services skill uses to count status columns.
STAMP_CELL = f"{SERVICES_TAB}!A1"
STAMP_PREFIX = "Last updated "


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{proc.stderr or proc.stdout}")
    return proc.stdout


def gws(*args: str, params: dict | None = None, body: dict | None = None) -> dict:
    cmd = ["gws", *args]
    if params is not None:
        cmd += ["--params", json.dumps(params)]
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    out = _run(cmd)
    start = out.find("{")
    if start < 0:
        sys.exit(f"no JSON in gws output: {out!r}")
    payload, _ = json.JSONDecoder().raw_decode(out[start:])
    if "error" in payload:
        sys.exit(f"sheets API error: {json.dumps(payload['error'])}")
    return payload


def col_index(letter: str) -> int:
    n = 0
    for ch in letter:
        n = n * 26 + (ord(ch.upper()) - ord("A") + 1)
    return n - 1


def parse_a1(a1: str) -> tuple[str, int, int]:
    """'Services!C3' -> ('C', 2, 3): letter, 0-based column, 1-based row."""
    ref = a1.split("!", 1)[-1]
    m = re.fullmatch(r"([A-Za-z]+)(\d+)", ref)
    if not m:
        sys.exit(f"not a single-cell A1 reference: {a1!r}")
    return m.group(1).upper(), col_index(m.group(1)), int(m.group(2))


def read_state(sid: str) -> tuple[list[list[str]], dict[int, list[str]], int, list[str]]:
    payload = gws("sheets", "spreadsheets", "get",
                  params={"spreadsheetId": sid, "includeGridData": True,
                          "ranges": f"{SERVICES_TAB}!A1:Z400"})
    sheet = next((s for s in payload.get("sheets", [])
                  if s["properties"]["title"] == SERVICES_TAB), None)
    if sheet is None:
        sys.exit(f"no '{SERVICES_TAB}' tab in the spreadsheet")

    grid: list[list[str]] = []
    allowed: dict[int, list[str]] = {}
    for row in sheet.get("data", [{}])[0].get("rowData", []):
        cells = row.get("values", [])
        grid.append([(c.get("formattedValue") or "") for c in cells])
        for c, cell in enumerate(cells):
            if c < FIRST_STATUS_COL or c in allowed:
                continue
            cond = (cell.get("dataValidation") or {}).get("condition") or {}
            if cond.get("type") == "ONE_OF_LIST":
                allowed[c] = [v.get("userEnteredValue", "")
                              for v in cond.get("values", [])]

    sep = next((i for i, row in enumerate(grid)
                if row and row[0].strip() == SEPARATOR), None)
    if sep is None:
        sys.exit(f"no '{SEPARATOR}' separator row -- refusing to guess where "
                 f"the main section ends")
    header = [h.strip() for h in (grid[0] if grid else [])]
    return grid, allowed, sep, header


def cell_value(grid: list[list[str]], row1: int, col0: int) -> str:
    row = grid[row1 - 1] if row1 - 1 < len(grid) else []
    return (row[col0] if len(row) > col0 else "").strip()


def report_reasons(judged: list[dict], rare: int) -> None:
    """Break each column down by which branch of its heuristic fired.

    Covers every cell that was judged, not just the ones that changed -- a
    column where nothing moved is still a fact worth showing, and reading only
    the diff would hide the shape of the remaining work.

    Grouped on `reason` (the coarse bucket) rather than `why` (the per-cell
    evidence), so "below 8.0.0" is one line instead of one line per pin. A
    reason that only a handful of services hit is the interesting one -- it
    is usually a repo that fell through the middle of the rule rather than a
    repo that is simply behind -- so those get named.
    """
    if not judged:
        return
    by_col: dict[str, dict[tuple[str, str], list[str]]] = {}
    for w in judged:
        by_col.setdefault(w["column"], {}).setdefault(
            (w["verdict"], w["reason"]), []).append(w["repo"])

    print("\nhow the heuristics landed (every judged cell, not just changes)")
    for column, reasons in by_col.items():
        print(f"\n  {column}")
        for (verdict, why), repos in sorted(
            reasons.items(), key=lambda kv: (-len(kv[1]), kv[0])
        ):
            print(f"    {verdict:6}{len(repos):>4}  {why}")
            if rare and len(repos) <= rare:
                for repo in sorted(repos):
                    print(f"              - {repo}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spreadsheet-id", default=SPREADSHEET_ID)
    ap.add_argument("--verdicts", help="verdicts JSON file (default: stdin)")
    ap.add_argument("--fingerprint", required=True,
                    help="fingerprint.py output. Required: it is the authority "
                         "on what each cell held when it was judged, and it "
                         "carries the warnings (unresolved repos, duplicate "
                         "checkouts) shown at review time")
    ap.add_argument("--rare", type=int, default=5,
                    help="name the services behind a reason used at most this "
                         "many times (default 5, 0 to never name them)")
    ap.add_argument("--no-stamp", action="store_true",
                    help=f"do not refresh the '{STAMP_PREFIX.strip()}' cell "
                         f"at {STAMP_CELL}")
    ap.add_argument("--apply", action="store_true",
                    help="write the cells; without it this is a dry run")
    args = ap.parse_args()

    with open(args.verdicts) if args.verdicts else sys.stdin as fh:
        verdicts = json.load(fh)
    if isinstance(verdicts, dict):
        verdicts = verdicts.get("verdicts", [])

    with open(args.fingerprint) as fh:
        fp = json.load(fh)
    # What each cell held when it was judged. A verdict for a cell the
    # fingerprint never offered is refused outright -- that is how DONE stays
    # untouched unless fingerprint.py ran with --recheck-heuristics.
    expected = {c["a1"]: (c.get("current") or "").strip()
                for c in fp.get("cells", [])}

    grid, allowed, sep, header = read_state(args.spreadsheet_id)

    writes: list[dict] = []
    unchanged: list[dict] = []
    skipped: list[str] = []
    for v in verdicts:
        a1 = v.get("a1", "")
        letter, col0, row1 = parse_a1(a1)
        repo = cell_value(grid, row1, 0) or v.get("repo", "?")
        verdict = (v.get("verdict") or "").strip()
        name = header[col0] if col0 < len(header) else ""
        label = f"{repo} / {name or letter}"

        if col0 < FIRST_STATUS_COL:
            skipped.append(f"{label}: column {letter} is not a status column")
            continue
        # A column with an empty header in row 1 is not a status column even
        # if it sits inside the status range: the space past the last header
        # is free for hand-written marks, and nothing here may overwrite it.
        if col0 >= len(header) or not header[col0]:
            skipped.append(f"{label}: column {letter} has no header -- not a "
                           f"status column")
            continue
        if not (FIRST_DATA_ROW <= row1 <= sep):
            skipped.append(f"{label}: row {row1} is outside the main section")
            continue
        if a1 not in expected:
            skipped.append(f"{label}: not one of the cells the fingerprint "
                           f"offered for judging")
            continue
        current = cell_value(grid, row1, col0)
        if current != expected[a1]:
            skipped.append(f"{label}: cell now reads '{current}', was "
                           f"'{expected[a1]}' when judged -- edited since")
            continue
        ok = allowed.get(col0)
        if ok and verdict not in ok:
            skipped.append(f"{label}: '{verdict}' is not in the dropdown {ok}")
            continue
        if not verdict:
            skipped.append(f"{label}: no verdict given")
            continue
        why = v.get("why", "")
        record = {"a1": a1, "repo": repo, "column": label.split(" / ", 1)[1],
                  "verdict": verdict, "why": why, "from": current,
                  "reason": v.get("reason") or why}
        # Re-judging every non-DONE cell means most verdicts restate what is
        # already there; listing those would bury the handful that moved.
        (unchanged if verdict == current else writes).append(record)

    by_col: dict[str, int] = {}
    for w in writes:
        by_col[w["column"]] = by_col.get(w["column"], 0) + 1

    width_repo = max([len(w["repo"]) for w in writes] + [7])
    width_col = max([len(w["column"]) for w in writes] + [6])
    print(f"{'cell':10}{'service':{width_repo + 2}}"
          f"{'column':{width_col + 2}}{'change':17}why")
    print("-" * (10 + width_repo + width_col + 4 + 17 + 40))
    for w in sorted(writes, key=lambda w: (w["repo"], w["a1"])):
        ref = w["a1"].split("!", 1)[-1]
        move = f"{w['from'] or '(blank)'} -> {w['verdict']}"
        print(f"{ref:10}{w['repo']:{width_repo + 2}}"
              f"{w['column']:{width_col + 2}}{move:17}{w['why']}")

    print(f"\n{len(writes) + len(unchanged)} cell(s) judged, "
          f"{len(writes)} changing" +
          (": " + ", ".join(f"{k} {n}" for k, n in sorted(by_col.items()))
           if by_col else "") +
          f", {len(unchanged)} already correct")

    report_reasons(writes + unchanged, args.rare)

    if skipped:
        print(f"\n{len(skipped)} skipped:")
        for s in skipped:
            print(f"  - {s}")

    warnings = fp.get("warnings", [])
    if warnings:
        print(f"\n{len(warnings)} warning(s) from the fingerprint run "
              f"-- these need a human, the cells above do not cover them:")
        for w in warnings:
            print(f"  ! {w}")

    stamp = None
    if not args.no_stamp:
        existing = cell_value(grid, 1, 0)
        if existing and not existing.startswith(STAMP_PREFIX):
            print(f"\n{STAMP_CELL} holds {existing!r} -- leaving the "
                  f"timestamp alone rather than overwriting it.")
        else:
            stamp = f"{STAMP_PREFIX}{datetime.now():%Y-%m-%d %H:%M}"
            print(f"\n{STAMP_CELL} -> {stamp!r}")

    if not args.apply:
        print("\ndry run -- nothing written. Re-run with --apply to write.")
        return
    if not writes and not stamp:
        print("\nnothing to do.")
        return

    # A run that changes no cell still verified every repo against the
    # heuristics, which is exactly what the timestamp records -- so the stamp
    # goes in even when `writes` is empty.
    data = [{"range": w["a1"], "values": [[w["verdict"]]]} for w in writes]
    if stamp:
        data.append({"range": STAMP_CELL, "values": [[stamp]]})
    gws("sheets", "spreadsheets", "values", "batchUpdate",
        params={"spreadsheetId": args.spreadsheet_id},
        body={"valueInputOption": "RAW", "data": data})
    print(f"\nwrote {len(writes)} cell(s)" +
          (f" and refreshed {STAMP_CELL}." if stamp else "."))


if __name__ == "__main__":
    main()
