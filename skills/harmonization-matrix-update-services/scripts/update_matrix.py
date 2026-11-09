#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Reconcile the "Harmonization matrix" sheet against fyndiq/infrastructure.

Row identity is the GitHub repo name. Two sections:

  * main section (rows 3..sep-1)  -- repos referenced by services.yaml,
    i.e. repos that have at least one Datadog Software Catalog entry.
  * "Not in Datadog catalog" section -- every other repo already present in
    the sheet. Rows are only ever moved here, never deleted, so they can be
    handled by hand.

Owner comes from repos.yaml `codeowners:` (the source of truth). The
`owner:` override in services.yaml is deliberately ignored: it is per
Datadog service, and a sheet row is a repo, which may deploy several
services with conflicting overrides. A disagreement is reported as a
warning instead.

Only columns A and B are written unless the section layout changes (a row
added, moved, or re-sorted). When it does, the whole grid is rewritten so
status cells travel with their repo; brand-new rows get NEW in every
status column.

Column A also carries a link to the repo's GitHub page, applied as rich text
so the cell value stays the plain repo name.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

import yaml

SPREADSHEET_ID = "18xz-mqyLpdZQNn1CQ_-iyIn8fSuiCDeMiIsTRE_UEhU"
GH_REPO = "fyndiq/infrastructure"
SERVICES_PATH = "platforms/fyndiq/datadog_software_catalog/services.yaml"
REPOS_PATH = "platforms/fyndiq/github/repos.yaml"
GH_ORG_URL = "https://github.com/fyndiq"

SEPARATOR = "Not in Datadog catalog"
NEW = "NEW"
UNKNOWN = "Unknown"
# Team slug in repos.yaml codeowners -> label used in the sheet's Owner dropdown.
OWNER_LABELS = {
    "mase": "MASE",
    "pade": "PADE",
    "platform": "Platform",
    "fullstack": "Fullstack",
    "data": "Data",
}


# --------------------------------------------------------------------------- io


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{proc.stderr or proc.stdout}")
    return proc.stdout


def gh_raw(path: str, ref: str) -> str:
    """Fetch one file from GitHub at `ref` using the user's gh credentials."""
    return _run(
        [
            "gh",
            "api",
            f"repos/{GH_REPO}/contents/{path}?ref={ref}",
            "-H",
            "Accept: application/vnd.github.raw",
        ]
    )


def gws(*args: str, params: dict | None = None, body: dict | None = None) -> dict:
    """Call the gws CLI and decode its JSON reply.

    gws prefixes stdout with a keyring notice, so decode from the first brace
    rather than parsing the whole stream.
    """
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


def col_letter(index0: int) -> str:
    letters = ""
    n = index0
    while True:
        letters = chr(ord("A") + n % 26) + letters
        n = n // 26 - 1
        if n < 0:
            return letters


# ------------------------------------------------------------------- inputs


def owner_of(repo: str, repos: dict, warnings: list[str]) -> str:
    entry = repos.get(repo)
    if entry is None:
        warnings.append(f"{repo}: not in repos.yaml -- owner set to {UNKNOWN}")
        return UNKNOWN
    for line in (entry.get("codeowners") or "").splitlines():
        token = line.strip()
        # codeowners may hold raw CODEOWNERS lines; a bare team slug is the
        # only form that maps to an owner.
        if not token or token.startswith(("#", "@")) or "/" in token or " " in token:
            continue
        if token in OWNER_LABELS:
            return OWNER_LABELS[token]
        warnings.append(f"{repo}: codeowner team '{token}' has no label -- using {UNKNOWN}")
        return UNKNOWN
    warnings.append(f"{repo}: no codeowners team -- owner set to {UNKNOWN}")
    return UNKNOWN


def load_sources(ref: str, warnings: list[str]) -> tuple[list[str], dict]:
    services = yaml.safe_load(gh_raw(SERVICES_PATH, ref)) or {}
    repos = yaml.safe_load(gh_raw(REPOS_PATH, ref)) or {}

    service_repos: dict[str, list[str]] = {}
    for name, spec in services.items():
        repo = (spec or {}).get("repo")
        if not repo:
            warnings.append(f"services.yaml: '{name}' has no repo: -- skipped")
            continue
        service_repos.setdefault(repo, []).append(name)

    # An owner: override disagreeing with the repo codeowner is worth knowing
    # about, but repos.yaml stays authoritative.
    for name, spec in services.items():
        override = (spec or {}).get("owner")
        if not override:
            continue
        repo = (spec or {}).get("repo")
        expected = owner_of(repo, repos, []) if repo else None
        label = OWNER_LABELS.get(override, override)
        if label != expected:
            warnings.append(
                f"services.yaml: '{name}' sets owner: {override} but repo {repo} "
                f"is owned by {expected} -- repos.yaml wins"
            )

    return sorted(service_repos, key=str.lower), repos


# --------------------------------------------------------------- sheet state


class Sheet:
    def __init__(self, spreadsheet_id: str):
        self.id = spreadsheet_id
        meta = gws(
            "sheets",
            "spreadsheets",
            "get",
            params={
                "spreadsheetId": spreadsheet_id,
                "fields": "sheets(properties(sheetId,title,index))",
            },
        )
        props = sorted(
            (s["properties"] for s in meta["sheets"]), key=lambda p: p.get("index", 0)
        )[0]
        self.tab = props["title"]
        self.sheet_id = props["sheetId"]

        got = gws(
            "sheets",
            "spreadsheets",
            "values",
            "get",
            params={"spreadsheetId": spreadsheet_id, "range": self.tab},
        )
        self.rows = got.get("values", [])
        if len(self.rows) < 2:
            sys.exit(f"tab '{self.tab}' has no header rows -- refusing to touch it")

        self.header = self.rows[0]
        self.service_header = self.rows[1]
        self.nstatus = max(1, len(self.header) - 2)
        self.width = 2 + self.nstatus

        grid = gws(
            "sheets",
            "spreadsheets",
            "get",
            params={
                "spreadsheetId": spreadsheet_id,
                "ranges": f"{self.tab}!A1:{col_letter(self.width - 1)}{len(self.rows) + 5}",
                "includeGridData": True,
                "fields": "sheets(data(rowData(values(dataValidation,hyperlink))),conditionalFormats)",
            },
        )["sheets"][0]
        self.conditional_formats = grid.get("conditionalFormats", [])
        self._cells = grid.get("data", [{}])[0].get("rowData", [])

    def _cell(self, row1: int, col0: int) -> dict:
        try:
            return self._cells[row1 - 1]["values"][col0]
        except (IndexError, KeyError):
            return {}

    def validation_at(self, row1: int, col0: int) -> dict | None:
        return self._cell(row1, col0).get("dataValidation")

    def last_validated_row(self, col0: int) -> int | None:
        """Last 1-based row in `col0` carrying a data-validation rule."""
        last = None
        for i, row in enumerate(self._cells, start=1):
            cells = row.get("values", [])
            if col0 < len(cells) and cells[col0].get("dataValidation"):
                last = i
        return last

    def link_at(self, row1: int, col0: int) -> str | None:
        return self._cell(row1, col0).get("hyperlink") or None

    def sections(self, warnings: list[str]) -> tuple[list, list, int | None]:
        sep = None
        for i, row in enumerate(self.rows):
            if row and row[0].strip() == SEPARATOR:
                sep = i
                break
        if sep is None:
            warnings.append(f"no '{SEPARATOR}' row found -- it will be appended")
        main_chunk = self.rows[2 : sep if sep is not None else len(self.rows)]
        bottom_chunk = self.rows[sep + 1 :] if sep is not None else []

        def entries(chunk):
            out = []
            for row in chunk:
                name = row[0].strip() if row else ""
                if name:
                    out.append((name, list(row[2 : self.width])))
            return out

        return entries(main_chunk), entries(bottom_chunk), sep


# ------------------------------------------------------------------ planning


def plan(sheet: Sheet, service_repos: list[str], repos: dict, warnings: list[str]):
    main, bottom, _ = sheet.sections(warnings)

    existing: dict[str, tuple[str, list[str]]] = {}
    for section, chunk in (("catalog", main), ("not-in-catalog", bottom)):
        for name, status in chunk:
            if name in existing:
                warnings.append(f"{name}: listed more than once -- keeping the first row")
                continue
            existing[name] = (section, status)

    # A repo archived in Terraform is gone: its row is dropped from whichever
    # section it sits in rather than moved, so the sheet only ever tracks
    # repos that still exist. repos.yaml is the authority -- an archived repo
    # usually keeps its services.yaml entry long after the fact.
    archived = {r for r, e in repos.items() if (e or {}).get("archived")}
    for repo in sorted(set(service_repos) & archived, key=str.lower):
        warnings.append(
            f"{repo}: archived in repos.yaml but still referenced by "
            f"services.yaml -- prune the catalog entry"
        )

    in_catalog = set(service_repos)
    target_main = [r for r in service_repos if r not in archived]
    target_bottom = sorted(
        (r for r in existing if r not in in_catalog and r not in archived),
        key=str.lower,
    )

    def make(repo: str, section: str):
        owner = owner_of(repo, repos, warnings)
        prev = existing.get(repo)
        if prev is None:
            status = [""] * sheet.nstatus
            action = "add"
        else:
            status = (prev[1] + [""] * sheet.nstatus)[: sheet.nstatus]
            action = f"move {prev[0]} -> {section}" if prev[0] != section else ""
        # Every blank status cell in the catalog section becomes NEW: that
        # covers brand-new rows and existing rows under a newly added status
        # column alike. Rows parked in the not-in-catalog section are left
        # alone -- there is no work to track until they are triaged.
        filled: list[int] = []
        if section == "catalog":
            filled = [i for i, v in enumerate(status) if not v.strip()]
            status = [v if v.strip() else NEW for v in status]
        return {
            "repo": repo,
            "section": section,
            "owner": owner,
            # No link for a repo absent from repos.yaml -- the URL would 404.
            "url": f"{GH_ORG_URL}/{repo}" if repo in repos else None,
            "status": status,
            "action": action,
            "filled": filled,
            "prev_section": prev[0] if prev else None,
        }

    rows_main = [make(r, "catalog") for r in target_main]
    rows_bottom = [make(r, "not-in-catalog") for r in target_bottom]

    # Current owner and repo link per repo, to report A/B-column changes.
    current_owner = {}
    current_link = {}
    for i, row in enumerate(sheet.rows[2:], start=3):
        name = row[0].strip() if row else ""
        if name and name != SEPARATOR:
            current_owner[name] = row[1].strip() if len(row) > 1 else ""
            current_link[name] = sheet.link_at(i, 0)
    for row in rows_main + rows_bottom:
        was = current_owner.get(row["repo"])
        row["owner_was"] = was
        if was is not None and was != row["owner"]:
            row["owner_change"] = f"{was or '(blank)'} -> {row['owner']}"
        if row["repo"] in current_link and current_link[row["repo"]] != row["url"]:
            row["link_change"] = "link added" if row["url"] else "link removed"

    # Built after current_owner so a removal can report the owner and statuses
    # it is discarding -- once the row is gone that data is unrecoverable.
    removed = [
        {"repo": r, "section": existing[r][0], "owner": current_owner.get(r, ""),
         "status": existing[r][1]}
        for r in sorted(existing, key=str.lower) if r in archived
    ]

    layout_now = [
        (sec, name)
        for sec, chunk in (("catalog", main), ("not-in-catalog", bottom))
        for name, _ in chunk
    ]
    layout_next = [(r["section"], r["repo"]) for r in rows_main + rows_bottom]

    target, links = build_grid(sheet, rows_main, rows_bottom)
    # A layout change shifts rows, so the grid has to be rewritten wholesale.
    # Otherwise every row keeps its place and only individual cells change.
    structural = layout_now != layout_next or len(sheet.rows) != len(target)
    diffs: list[tuple[int, int]] = []
    if structural:
        # Rows move, so every link below the headers is (re)written in place.
        link_rows = list(range(2, len(target)))
    else:
        current = [(row + [""] * sheet.width)[: sheet.width] for row in sheet.rows]
        diffs = [
            (r, c)
            for r in range(len(target))
            for c in range(sheet.width)
            if target[r][c] != current[r][c]
        ]
        link_rows = [
            r for r in range(len(target)) if links[r] != sheet.link_at(r + 1, 0)
        ]

    return rows_main, rows_bottom, removed, structural, target, diffs, links, link_rows


def build_grid(
    sheet: Sheet, rows_main: list[dict], rows_bottom: list[dict]
) -> tuple[list[list[str]], list[str | None]]:
    def pad(cells):
        return (list(cells) + [""] * sheet.width)[: sheet.width]

    grid = [pad(sheet.header), pad(sheet.service_header)]
    links: list[str | None] = [None, None]
    for row in rows_main:
        grid.append(pad([row["repo"], row["owner"], *row["status"]]))
        links.append(row["url"])
    grid += [pad([]), pad([SEPARATOR])]
    links += [None, None]
    for row in rows_bottom:
        grid.append(pad([row["repo"], row["owner"], *row["status"]]))
        links.append(row["url"])
    return grid, links


# -------------------------------------------------------------------- report


def report(sheet: Sheet, rows_main, rows_bottom, removed, structural, diffs, link_rows, warnings) -> None:
    headers = sheet.header[2 : sheet.width]
    name_w = max([len(r["repo"]) for r in rows_main + rows_bottom] + [7])
    status_w = [max(len(h), 9) for h in headers]

    def line(flag, rownum, repo, owner, status):
        cells = "  ".join(
            f"{(s or '-'):{w}s}" for s, w in zip(status + [""] * len(status_w), status_w)
        )
        return f"{flag:2s} {rownum:>3} {repo:{name_w}s}  {owner:10s}  {cells}"

    print(f"tab: {sheet.tab}   status columns: {', '.join(headers)}")
    print(
        f"legend: * new row   > moved section   ! owner change   "
        f"+ blank -> {NEW}   @ repo link\n"
    )
    print(line("", "row", "Service", "Owner", list(headers)))
    print("-" * (name_w + 20 + sum(status_w) + 2 * len(status_w)))

    row_no = 3
    for group, label in ((rows_main, None), (rows_bottom, SEPARATOR)):
        if label is not None:
            print(line("", "", "", "", [""] * len(status_w)).rstrip())
            row_no += 1
            print(f"   {row_no:>3} {label}")
            row_no += 1
        for r in group:
            flag = "*" if r["action"] == "add" else ">" if r["action"] else ""
            if r.get("owner_change"):
                flag = (flag + "!") if flag else "!"
            elif r["filled"] and r["action"] != "add":
                flag = (flag + "+") if flag else "+"
            elif r.get("link_change"):
                flag = (flag + "@") if flag else "@"
            owner = r.get("owner_change") or r["owner"]
            print(line(flag, row_no, r["repo"], owner, r["status"]))
            row_no += 1

    everything = rows_main + rows_bottom
    adds = [r for r in everything if r["action"] == "add"]
    moves = [r for r in everything if r["action"].startswith("move")]
    owner_fixes = [r for r in everything if r.get("owner_change")]
    fills = [r for r in everything if r["filled"] and r["action"] != "add"]
    relinks = [r for r in everything if r.get("link_change")]
    print(
        f"\ncatalog: {len(rows_main)}   not-in-catalog: {len(rows_bottom)}   "
        f"new: {len(adds)}   removed: {len(removed)}   moved: {len(moves)}   "
        f"owner changes: {len(owner_fixes)}   "
        f"rows gaining {NEW}: {len(fills)}   link changes: {len(relinks)}"
    )
    # Listed first, and with the statuses spelled out: this is the only change
    # the script makes that destroys data rather than moving it.
    for r in removed:
        status = " | ".join(v or "(blank)" for v in r["status"]) or "(none)"
        print(f"  - {r['repo']} ({r['owner'] or UNKNOWN}) removed from "
              f"{r['section']}, archived in repos.yaml -- discards: {status}")
    for r in adds:
        print(f"  * {r['repo']} ({r['owner']}) -> {r['section']}, all status columns {NEW}")
    for r in moves:
        print(f"  > {r['repo']}: {r['action']}")
    for r in owner_fixes:
        print(f"  ! {r['repo']}: {r['owner_change']}")
    for r in fills:
        cols = ", ".join(headers[i] for i in r["filled"])
        print(f"  + {r['repo']}: {NEW} in {cols}")
    for r in relinks:
        print(f"  @ {r['repo']}: {r['link_change']} ({r['url'] or 'not in repos.yaml'})")
    scope = (
        "full grid rewrite (rows shift; statuses travel with their repo)"
        if structural
        else f"{len(diffs)} individual cell(s) (layout unchanged)"
    )
    if link_rows:
        scope += f" + column A links on {len(link_rows)} row(s)"
    print(f"\nwrite scope: {scope}")
    if warnings:
        print("\nwarnings:")
        for w in dict.fromkeys(warnings):
            print(f"  - {w}")
    if not structural and not diffs and not link_rows:
        print("\nnothing to do -- sheet already matches the source of truth.")


# --------------------------------------------------------------------- apply


def apply_cells(sheet: Sheet, target: list[list[str]], diffs: list[tuple[int, int]]) -> None:
    """Write just the cells that differ, leaving every other cell untouched."""
    if not diffs:
        print("no cell changes needed.")
        return
    data = [
        {
            "range": f"{sheet.tab}!{col_letter(c)}{r + 1}",
            "values": [[target[r][c]]],
        }
        for r, c in diffs
    ]
    gws(
        "sheets",
        "spreadsheets",
        "values",
        "batchUpdate",
        params={"spreadsheetId": sheet.id},
        body={"valueInputOption": "USER_ENTERED", "data": data},
    )
    cols = sorted({col_letter(c) for _, c in diffs})
    print(f"updated {len(data)} cell(s) in column(s) {', '.join(cols)}.")


def apply_links(
    sheet: Sheet, grid: list[list[str]], links: list[str | None], rows: list[int]
) -> None:
    """Point column A at each repo's GitHub page.

    A rich-text link rather than =HYPERLINK: the cell value stays the plain
    repo name, so it still sorts and diffs as text and doesn't depend on the
    spreadsheet locale's formula argument separator.
    """
    if not rows:
        return

    def cell(row: int) -> dict:
        text, uri = grid[row][0], links[row]
        out: dict = {}
        if text:
            out["userEnteredValue"] = {"stringValue": text}
        if uri:
            out["textFormatRuns"] = [{"startIndex": 0, "format": {"link": {"uri": uri}}}]
        return out

    runs: list[list[int]] = []
    for row in sorted(rows):
        if runs and row == runs[-1][1]:
            runs[-1][1] = row + 1
        else:
            runs.append([row, row + 1])

    gws(
        "sheets",
        "spreadsheets",
        "batchUpdate",
        params={"spreadsheetId": sheet.id},
        body={
            "requests": [
                {
                    "updateCells": {
                        "range": {
                            "sheetId": sheet.sheet_id,
                            "startRowIndex": start,
                            "endRowIndex": end,
                            "startColumnIndex": 0,
                            "endColumnIndex": 1,
                        },
                        "rows": [{"values": [cell(r)]} for r in range(start, end)],
                        # Both fields listed so a row without a link has any
                        # stale run cleared instead of inherited.
                        "fields": "userEnteredValue,textFormatRuns",
                    }
                }
                for start, end in runs
            ]
        },
    )
    linked = sum(1 for r in rows if links[r])
    print(f"linked {linked} of {len(rows)} rewritten column A cell(s) to GitHub.")


def apply_full(sheet: Sheet, grid: list[list[str]], rows_main, rows_bottom) -> None:
    last_col = col_letter(sheet.width - 1)
    n = len(grid)
    gws(
        "sheets",
        "spreadsheets",
        "values",
        "update",
        params={
            "spreadsheetId": sheet.id,
            "range": f"{sheet.tab}!A1:{last_col}{n}",
            "valueInputOption": "USER_ENTERED",
        },
        body={"values": grid},
    )
    old_n = len(sheet.rows)
    if old_n > n:
        gws(
            "sheets",
            "spreadsheets",
            "values",
            "clear",
            params={"spreadsheetId": sheet.id, "range": f"{sheet.tab}!A{n + 1}:{last_col}{old_n}"},
            body={},
        )
    print(f"wrote {n} rows (A1:{last_col}{n})" + (f", cleared rows {n + 1}-{old_n}" if old_n > n else ""))

    # Data validation is NEVER written. An earlier version cleared B:E over the
    # whole row span and re-applied a rule sampled from one cell, which
    # silently narrowed the validated range and would have flattened any status
    # column whose dropdown differed from column C's. The rules are the user's
    # to own; this script only reads them.
    owner_rule = sheet.validation_at(3, 1)
    status_rule = sheet.validation_at(3, 2)

    # Rows are only ever written inside the existing validated span, so a
    # shrinking list is fine. A growing one can run past it, and Sheets does
    # not extend validation on its own -- so say which rows need it by hand.
    # Compared against the last main-section row, not the last row of the
    # grid: the status dropdowns deliberately stop at the separator.
    last_main_row = 2 + len(rows_main)
    last_validated = sheet.last_validated_row(2)
    if status_rule and last_validated and last_main_row > last_validated:
        print(f"note: status dropdowns cover rows 3-{last_validated}, but the "
              f"catalog section now ends at row {last_main_row} -- extend the "
              f"validation over rows {last_validated + 1}-{last_main_row} by hand.")

    reqs: list[dict] = []
    for index, rule in enumerate(sheet.conditional_formats):
        ranges = rule.get("ranges") or []
        if not any(r.get("startColumnIndex", 0) >= 2 for r in ranges):
            continue
        updated = dict(rule)
        updated["ranges"] = [{**r, "endRowIndex": n} for r in ranges]
        reqs.append(
            {
                "updateConditionalFormatRule": {
                    "sheetId": sheet.sheet_id,
                    "index": index,
                    "rule": updated,
                }
            }
        )

    if reqs:
        gws(
            "sheets",
            "spreadsheets",
            "batchUpdate",
            params={"spreadsheetId": sheet.id},
            body={"requests": reqs},
        )
        print(f"extended {len(reqs)} conditional-format rule(s).")

    if status_rule:
        allowed = [v.get("userEnteredValue") for v in status_rule.get("condition", {}).get("values", [])]
        if NEW not in allowed:
            print(f"note: '{NEW}' is not in the status dropdown {allowed} -- new rows will flag as invalid.")


# ----------------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write to the sheet (default: dry run)")
    ap.add_argument("--spreadsheet-id", default=SPREADSHEET_ID)
    ap.add_argument("--ref", default="master", help="git ref to read the YAML sources from")
    args = ap.parse_args()

    warnings: list[str] = []
    service_repos, repos = load_sources(args.ref, warnings)
    sheet = Sheet(args.spreadsheet_id)
    rows_main, rows_bottom, removed, structural, target, diffs, links, link_rows = plan(
        sheet, service_repos, repos, warnings
    )

    report(sheet, rows_main, rows_bottom, removed, structural, diffs, link_rows, warnings)

    if not args.apply:
        print("\ndry run -- nothing written. Re-run with --apply to update the sheet.")
        return

    print()
    if structural:
        apply_full(sheet, target, rows_main, rows_bottom)
    else:
        apply_cells(sheet, target, diffs)
    apply_links(sheet, target, links, link_rows)


if __name__ == "__main__":
    main()
