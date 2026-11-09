#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# ///
"""Collect the facts needed to fill in the Harmonization matrix's statuses.

Emits one JSON document: the heuristics as authored in the sheet, the list of
cells that need a verdict, and a fingerprint per repo. The judgement itself is
deliberately left to the caller -- the heuristics are prose and change between
runs, so nothing here decides TODO/DONE/N/A.

Every cell that is not already DONE is offered for judging. NEW has no verdict
yet; TODO and N/A both describe work a repo can grow out of -- a service that
installs qlty-monitoring moves from N/A straight to TODO or DONE without its
cell ever passing through NEW. DONE is held back behind --recheck-heuristics
because it is the one value a wrong verdict can destroy rather than improve.

Repos are resolved by walking bounded_contexts/ for directories holding a
.git, keyed on directory basename. Run `just update-repos` first; this reads
the working tree exactly as it finds it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

SPREADSHEET_ID = "18xz-mqyLpdZQNn1CQ_-iyIn8fSuiCDeMiIsTRE_UEhU"
REPO_ROOT = Path("/home/simon/dev/fyndiq/fyndiq-2.0")
SERVICES_TAB = "Services"
HEURISTICS_TAB = "Heuristics"

SEPARATOR = "Not in Datadog catalog"
NEW = "NEW"
DONE = "DONE"
FIRST_DATA_ROW = 3  # 1-based; rows 1-2 are headers
FIRST_STATUS_COL = 2  # 0-based; A = Service, B = Owner

# Reported in `deps` on top of whatever a heuristic asks for. Emitting every
# resolved dependency would be megabytes across the fleet; the matrix tracks
# internal library adoption, so those are the useful default.
DEP_WATCHLIST_DEFAULT = ("ddtrace",)
DEP_WATCH_PREFIXES = ("qlty-", "qlty_")

# Never hold signal and are expensive to walk.
PRUNE = {".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
         ".pytest_cache", ".ruff_cache", ".direnv", "dist", "build", ".next"}

MAX_PROBE_FILES = 500
MAX_PROBE_BYTES = 2_000_000


# --------------------------------------------------------------------------- io


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"command failed: {' '.join(cmd)}\n{proc.stderr or proc.stdout}")
    return proc.stdout


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
    letters, n = "", index0
    while True:
        letters = chr(ord("A") + n % 26) + letters
        n = n // 26 - 1
        if n < 0:
            return letters


# -------------------------------------------------------------------- the sheet


def read_grid(sid: str) -> tuple[list[list[str]], dict[int, list[str]]]:
    """Return the Services grid plus each status column's allowed values.

    Allowed values come from the column's own data validation, so a verdict
    can never be written that the dropdown would flag as invalid.
    """
    payload = gws(
        "sheets", "spreadsheets", "get",
        params={"spreadsheetId": sid, "includeGridData": True,
                "ranges": f"{SERVICES_TAB}!A1:Z400"},
    )
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
    return grid, allowed


def parse_probes(text: str) -> tuple[dict[str, dict], list[str], list[str]]:
    """Parse the Probes cell. Two line forms, blank lines and # ignored:

        name = <regex> @ <glob>, <glob>   -- named grep over matching files
        dep <package>                     -- add <package> to the dep watchlist
    """
    probes: dict[str, dict] = {}
    deps: list[str] = []
    problems: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("dep "):
            deps.append(line[4:].strip())
            continue
        m = re.match(r"^(\w+)\s*=\s*(.+?)\s*@\s*(.+)$", line)
        if not m:
            problems.append(f"unparseable probe line: {line!r}")
            continue
        name, pattern, globs = m.group(1), m.group(2).strip(), m.group(3)
        if len(pattern) > 1 and pattern[0] == pattern[-1] and pattern[0] in "\"'":
            pattern = pattern[1:-1]
        try:
            re.compile(pattern)
        except re.error as exc:
            problems.append(f"probe {name}: bad regex {pattern!r} ({exc})")
            continue
        probes[name] = {"pattern": pattern,
                        "globs": [g.strip() for g in globs.split(",") if g.strip()]}
    return probes, deps, problems


def read_heuristics(sid: str) -> tuple[dict[str, dict], list[str], list[str]]:
    payload = gws(
        "sheets", "spreadsheets", "values", "get",
        params={"spreadsheetId": sid, "range": f"{HEURISTICS_TAB}!A1:G100"},
    )
    values = payload.get("values", [])
    if not values:
        sys.exit(f"the '{HEURISTICS_TAB}' tab is empty -- nothing to judge against")

    out: dict[str, dict] = {}
    watchlist: list[str] = []
    problems: list[str] = []
    for row in values[1:]:
        def cell(i: int) -> str:
            return (row[i] if i < len(row) else "").strip()

        name = cell(0)
        if not name:
            continue
        probes, deps, probs = parse_probes(cell(2))
        problems += [f"heuristic '{name}': {p}" for p in probs]
        watchlist += deps
        out[name] = {"applies_to": cell(1) or "all", "probes": probes,
                     "N/A": cell(3), "DONE": cell(4), "TODO": cell(5),
                     "notes": cell(6)}
    return out, watchlist, problems


# ------------------------------------------------------------------ the repos


def index_repos(root: Path) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Map repo directory name -> checkout paths under bounded_contexts/."""
    index: dict[str, list[str]] = {}
    bc = root / "bounded_contexts"
    if not bc.is_dir():
        sys.exit(f"no bounded_contexts/ under {root}")
    for context in sorted(p for p in bc.iterdir() if p.is_dir()):
        for repo in sorted(p for p in context.iterdir() if p.is_dir()):
            if (repo / ".git").exists():
                index.setdefault(repo.name, []).append(str(repo.relative_to(root)))

    # .gitrepos is the declared layout. It does not drive resolution -- the
    # working tree does -- but it breaks ties between duplicate checkouts, and
    # a row missing from it is reported separately from a row merely not
    # cloned yet, because the two need different fixes.
    declared: dict[str, str] = {}
    manifest = root / ".gitrepos"
    if manifest.is_file():
        for line in manifest.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 2:
                continue
            declared[parts[0].rsplit("/", 1)[-1].removesuffix(".git")] = \
                parts[1].rstrip("/")
    return index, declared


def _load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except Exception:
        return {}


def collect_deps(path: Path, watchlist: set[str]) -> dict[str, str]:
    """Resolved dependency pins, unified across uv / poetry / pip-tools / npm."""
    def wanted(name: str) -> bool:
        low = name.lower()
        return low in watchlist or low.startswith(DEP_WATCH_PREFIXES)

    deps: dict[str, str] = {}
    for lock in ("uv.lock", "poetry.lock"):
        f = path / lock
        if f.is_file():
            for pkg in _load_toml(f).get("package", []):
                name = pkg.get("name", "")
                if name and wanted(name) and pkg.get("version"):
                    deps.setdefault(name, str(pkg["version"]))

    reqs = path / "requirements"
    if reqs.is_dir():
        for f in sorted(reqs.glob("*.txt")):
            for line in f.read_text(errors="ignore").splitlines():
                m = re.match(r"^([A-Za-z0-9._-]+)(\[[^\]]*\])?==([^\s;#]+)",
                             line.strip())
                if m and wanted(m.group(1)):
                    deps.setdefault(m.group(1), m.group(3))

    pkg_json = path / "package.json"
    if pkg_json.is_file():
        try:
            data = json.loads(pkg_json.read_text())
        except Exception:
            data = {}
        for key in ("dependencies", "devDependencies"):
            for name, spec in (data.get(key) or {}).items():
                if wanted(name):
                    deps.setdefault(name, str(spec))
    return deps


def probe_text(path: Path, globs: list[str]) -> str:
    """Concatenate every *tracked* file under `path` matching any of `globs`.

    Enumeration goes through `git ls-files`, never the filesystem. A repo
    someone has run `uv sync` in holds thousands of .venv files that a
    `**/*.py` glob matches; they crowd the app's own source out of the file
    budget, so the probe reports false -- silently, and only on machines where
    that .venv happens to exist. Tracked files are also the right definition:
    the matrix judges what is committed, not what is lying around.

    `:(glob)` pathspec magic gives git the same `*`-stops-at-/ and `**`-spans-
    directories semantics pathlib.glob has, so the patterns authored in the
    Heuristics tab keep their meaning.
    """
    if not globs:
        return ""
    out = _run(["git", "-C", str(path), "ls-files", "-z", "--",
                *(f":(glob){g}" for g in globs)])
    # A file matching two globs is listed twice; dict keeps first-seen order.
    rels = list(dict.fromkeys(r for r in out.split("\0") if r))

    chunks: list[str] = []
    total = 0
    for rel in rels[:MAX_PROBE_FILES]:
        # Vendored code is normally untracked and already gone, but some repos
        # commit it; nothing there is evidence about this service.
        if any(part in PRUNE for part in rel.split("/")):
            continue
        try:
            chunk = (path / rel).read_text(errors="ignore")
        except OSError:
            continue
        chunks.append(chunk)
        total += len(chunk)
        if total > MAX_PROBE_BYTES:
            break
    return "\n".join(chunks)


def dockerfile_entrypoints(path: Path) -> list[str]:
    out = []
    for f in sorted(path.glob("Dockerfile*")):
        if not f.is_file():
            continue
        for line in f.read_text(errors="ignore").splitlines():
            s = line.strip()
            if s.startswith(("CMD ", "ENTRYPOINT ")):
                out.append(f"{f.name}: {s}")
    return out


def fingerprint(root: Path, rel: str, repo: str, owner: str,
                probes: dict[str, dict], watchlist: set[str]) -> dict:
    path = root / rel

    def has(name: str) -> bool:
        return (path / name).exists()

    pyproject = _load_toml(path / "pyproject.toml") if has("pyproject.toml") else {}
    has_reqs = (path / "requirements").is_dir() and any(
        (path / "requirements").glob("*.txt")
    )
    dep_manager = ("uv" if has("uv.lock")
                   else "poetry" if has("poetry.lock")
                   else "pip-tools" if has_reqs
                   else None)
    # A pyproject.toml holding only [tool.black] etc. is not packaging.
    packaging = ("pep621" if "project" in pyproject
                 else "poetry" if "poetry" in pyproject.get("tool", {})
                 else "setup.py" if has("setup.py")
                 else None)
    stack = []
    if dep_manager or pyproject or has("setup.py"):
        stack.append("python")
    if has("package.json"):
        stack.append("node")

    return {
        "repo": repo,
        "path": rel,
        "owner": owner,
        "stack": stack,
        "dep_manager": dep_manager,
        "packaging": packaging,
        "requires_python": pyproject.get("project", {}).get("requires-python"),
        "deps": collect_deps(path, watchlist),
        "entrypoints": dockerfile_entrypoints(path),
        "root_files": sorted(p.name + ("/" if p.is_dir() else "")
                             for p in path.iterdir()
                             if not p.name.startswith("."))[:80],
        "probes": {name: bool(re.search(spec["pattern"],
                                        probe_text(path, spec["globs"]), re.M))
                   for name, spec in probes.items()},
    }


def check_staleness(root: Path, repos: dict[str, dict]) -> list[str]:
    """Warn about checkouts behind their GitHub default branch.

    A stale checkout is the one failure mode with no local symptom: every
    probe reads cleanly and every pin resolves, the verdicts are just out of
    date, and a repo that has since been fixed still reports TODO. The whole
    fleet fits in one aliased GraphQL query, so this costs a single request.

    Degrades to a warning rather than an error: gh may be absent or
    unauthenticated, and that must not cost the user the run.
    """
    targets: dict[str, tuple[str, str, str]] = {}
    for i, (repo, fp) in enumerate(sorted(repos.items())):
        url = subprocess.run(["git", "-C", str(root / fp["path"]),
                              "remote", "get-url", "origin"],
                             capture_output=True, text=True)
        m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", url.stdout.strip())
        if url.returncode == 0 and m:
            targets[f"r{i}"] = (m.group(1), m.group(2), repo)
    if not targets:
        return ["no git remotes resolved -- cannot check whether the "
                "checkouts are current"]

    fields = "\n".join(
        f'{alias}: repository(owner: "{owner}", name: "{name}") '
        f'{{ defaultBranchRef {{ name target {{ oid }} }} }}'
        for alias, (owner, name, _) in targets.items()
    )
    proc = subprocess.run(["gh", "api", "graphql", "-f", f"query={{{fields}}}"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip().splitlines()
        return [f"could not reach GitHub to check for stale checkouts "
                f"({detail[0] if detail else 'gh failed'}) -- verdicts may be "
                f"based on out-of-date working trees"]
    try:
        data = json.loads(proc.stdout).get("data") or {}
    except json.JSONDecodeError:
        return ["unreadable reply from gh -- could not check for stale checkouts"]

    warnings = []
    for alias, (_, _, repo) in targets.items():
        node = data.get(alias) or {}
        ref = node.get("defaultBranchRef") or {}
        remote = (ref.get("target") or {}).get("oid")
        if not remote:
            warnings.append(f"{repo}: GitHub returned no default branch -- "
                            f"renamed, archived, or not visible to this token")
            continue
        local = subprocess.run(["git", "-C", str(root / repos[repo]["path"]),
                                "rev-parse", "HEAD"],
                               capture_output=True, text=True).stdout.strip()
        if local and local != remote:
            warnings.append(
                f"{repo}: checkout is at {local[:8]}, {ref.get('name')} on "
                f"GitHub is at {remote[:8]} -- run `just update-repos`; its "
                f"verdicts describe an older tree")
    return warnings


# ----------------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spreadsheet-id", default=SPREADSHEET_ID)
    ap.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    ap.add_argument("--dep", action="append", default=[],
                    help="extra package to report in deps (repeatable)")
    ap.add_argument("--no-staleness-check", action="store_true",
                    help="skip the GitHub round trip that reports checkouts "
                         "behind their default branch")
    ap.add_argument("--recheck-heuristics", action="store_true",
                    help=f"also re-judge cells already marked {DONE}; without "
                         f"it every other value is re-judged but {DONE} is "
                         f"left alone")
    args = ap.parse_args()

    root = args.repo_root.resolve()
    if not root.is_dir():
        sys.exit(f"repo root not found: {root}")
    os.chdir(root)

    warnings: list[str] = []
    grid, allowed = read_grid(args.spreadsheet_id)
    heuristics, sheet_deps, problems = read_heuristics(args.spreadsheet_id)
    warnings += problems

    header = grid[0] if grid else []
    columns = []
    headerless: list[int] = []
    for c in range(FIRST_STATUS_COL, len(header)):
        name = header[c].strip()
        if not name:
            # No header in row 1 means no column, whatever the cells below
            # hold -- those are somebody's scratch marks, not statuses.
            headerless.append(c)
            continue
        if name not in heuristics:
            warnings.append(f"column '{name}' has no row in the "
                            f"{HEURISTICS_TAB} tab -- its cells are untouched")
            continue
        columns.append({"index": c, "letter": col_letter(c), "header": name,
                        "allowed_values": allowed.get(c, [])})
        if NEW not in allowed.get(c, [NEW]):
            warnings.append(f"column '{name}' has no {NEW} in its dropdown")

    sep = next((i for i, row in enumerate(grid)
                if row and row[0].strip() == SEPARATOR), None)
    if sep is None:
        sys.exit(f"no '{SEPARATOR}' separator row -- refusing to guess where "
                 f"the main section ends")

    for c in headerless:
        used = sum(1 for row in grid[FIRST_DATA_ROW - 1:sep]
                   if len(row) > c and row[c].strip())
        if used:
            warnings.append(f"column {col_letter(c)} has no header but holds "
                            f"values in {used} row(s) -- not a status column, "
                            f"left alone")

    watchlist = {d.lower() for d in
                 DEP_WATCHLIST_DEFAULT + tuple(sheet_deps) + tuple(args.dep)}
    all_probes: dict[str, dict] = {}
    for spec in heuristics.values():
        all_probes.update(spec["probes"])

    index, declared = index_repos(root)
    cells: list[dict] = []
    repos: dict[str, dict] = {}
    for r in range(FIRST_DATA_ROW - 1, sep):
        row = grid[r] if r < len(grid) else []
        repo = (row[0] if row else "").strip()
        if not repo:
            continue
        owner = (row[1] if len(row) > 1 else "").strip()

        def value(col: dict, row: list[str] = row) -> str:
            return (row[col["index"]] if len(row) > col["index"] else "").strip()

        todo = [col for col in columns
                if args.recheck_heuristics or value(col) != DONE]
        if not todo:
            continue

        paths = index.get(repo, [])
        if not paths:
            if repo in declared:
                warnings.append(f"{repo}: in .gitrepos but not checked out -- "
                                f"run `just update-repos`; {len(todo)} cell(s) "
                                f"left as-is")
            else:
                warnings.append(f"{repo}: not in .gitrepos and not checked out "
                                f"-- nothing declares it, so it stays invisible "
                                f"every run; {len(todo)} cell(s) left as-is")
            continue
        rel = declared[repo] if declared.get(repo) in paths else paths[0]
        if repo not in declared:
            warnings.append(f"{repo}: checked out at {rel} but absent from "
                            f".gitrepos -- its verdicts come from a tree "
                            f"nothing declares")
        if len(paths) > 1:
            warnings.append(f"{repo}: {len(paths)} checkouts {paths} -- using {rel}")

        if repo not in repos:
            repos[repo] = fingerprint(root, rel, repo, owner, all_probes, watchlist)
        for col in todo:
            cells.append({"a1": f"{SERVICES_TAB}!{col['letter']}{r + 1}",
                          "repo": repo, "column": col["header"],
                          "current": value(col)})

    if not args.no_staleness_check and repos:
        warnings += check_staleness(root, repos)

    json.dump({"spreadsheet_id": args.spreadsheet_id, "repo_root": str(root),
               "columns": columns, "heuristics": heuristics, "cells": cells,
               "repos": repos, "warnings": warnings},
              sys.stdout, indent=2, sort_keys=False)
    print()


if __name__ == "__main__":
    main()
