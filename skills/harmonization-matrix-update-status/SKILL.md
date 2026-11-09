---
name: harmonization-matrix-update-status
description: Fill in the status cells of the "Harmonization matrix" Google Sheet by judging each service repo against the per-column heuristics stored in the sheet's Heuristics tab. Reads the local fyndiq-2.0 checkout under bounded_contexts/ as the source of truth. Use when asked to update, fill in, judge, or refresh the harmonization matrix statuses / the TODO-DONE-N/A columns.
disable-model-invocation: false
user-invocable: true
argument-hint: "[--recheck-heuristics] [--repo-root <path>] [--spreadsheet-id <id>]"
---

# Fill in the Harmonization matrix statuses

Set every status cell to `TODO`, `DONE`, or `N/A` by judging the repo against
its column's heuristic. **Always show the dry-run table and get explicit
confirmation before writing.**

By default every cell that is not already `DONE` is re-judged — `NEW` because
it has no verdict yet, `TODO` and `N/A` because both describe work a repo can
grow out of. `N/A` matters here as much as `TODO`: in a version-floor column it means
*"not a dependency at all"*, so a service that has just installed the library
sits in `N/A`, not `TODO`, and would never be picked up if the default only
looked at `TODO`.

`DONE` is the exception, re-judged only under `--recheck-heuristics`. It is
the one value where a wrong verdict destroys information instead of improving
it: everything else is a not-done state that re-judging can only sharpen,
whereas a `DONE` knocked back to `TODO` by a stale checkout or a probe that
failed to fire loses a real result. Reach for the flag when a heuristic has
actually changed.

Companion to `harmonization-matrix-update-services`, which owns the row list
and the Owner column and is what puts `NEW` there in the first place. Run
that one first if the service list is stale.

## Prerequisite

The local checkout is the source of truth, so it must be current:

```sh
cd /home/simon/dev/fyndiq/fyndiq-2.0 && just update-repos
```

The scripts do not pull, but they do check. `fingerprint.py` asks GitHub for
each repo's default-branch head in a single GraphQL query and warns about
every checkout sitting on an older commit — a stale tree is the one failure
mode with no local symptom, since the probes read cleanly and the pins resolve
and the verdicts are merely out of date. Needs an authenticated `gh`; if that
is missing the run continues with a warning rather than failing.
`--no-staleness-check` skips the round trip.

**A stale repo in that list needs `just update-repos` before its verdicts mean
anything** — unless every one of its cells came from a rule that never reads
the tree (`owner is Fullstack`, say), in which case say so and move on.

## Run it

```sh
S=~/.claude/skills/harmonization-matrix-update-status/scripts

# 1. Facts. Fast (~2s over ~60 repos), writes nothing.
#    Add --recheck-heuristics to re-judge DONE cells as well.
$S/fingerprint.py > /tmp/fp.json

# 2. You judge — see "The judging pass" below — and write /tmp/verdicts.json

# 3. Dry run. Prints the full table, writes nothing.
$S/apply_status.py --verdicts /tmp/verdicts.json --fingerprint /tmp/fp.json

# 4. Only after the user confirms:
$S/apply_status.py --verdicts /tmp/verdicts.json --fingerprint /tmp/fp.json --apply
```

`--fingerprint` is required. It is what `apply_status.py` trusts for the value
each cell held when it was judged, and it carries the warnings about repos that
failed to resolve — without it those rows would fail silently.

`fingerprint.py` flags: `--recheck-heuristics` (also offer `DONE` cells for
judging), `--repo-root <path>` (default `/home/simon/dev/fyndiq/fyndiq-2.0`),
`--spreadsheet-id <id>` (override to rehearse against a copy), `--dep <pkg>`
(report an extra package in `deps`), `--no-staleness-check` (skip the GitHub
round trip).

`apply_status.py` flags: `--rare N` (name the services behind a reason used at
most N times, default 5), `--no-stamp` (skip refreshing the `Last updated`
cell), `--apply`.

Needs `gws` (Google Workspace CLI). PEP 723 headers, so `uv` handles the rest.

## The judging pass

`fingerprint.py` emits one JSON document and deliberately decides nothing:

| Key | What it holds |
|---|---|
| `columns` | status columns that have a heuristic, with their A1 letter and dropdown values |
| `heuristics` | the Heuristics tab, verbatim — `applies_to`, `probes`, `N/A`, `DONE`, `TODO`, `notes` |
| `cells` | every cell needing a verdict: `a1`, `repo`, `column`, `current` |
| `repos` | one fingerprint per repo (below) |
| `warnings` | unresolved repos, duplicate checkouts, malformed probe lines |

Read the heuristic for a column, read each repo's fingerprint, emit:

```json
[{"a1": "Services!C3", "verdict": "DONE",
  "why": "uv.lock + [project]", "reason": "uv + PEP 621"}]
```

- `why` — the evidence for *this* cell, one short clause. It fills the
  dry-run table and is what makes the table reviewable, so never leave it blank.
- `reason` — the coarse bucket, i.e. which branch of the heuristic fired.
  The dry run groups on it. Keep it stable across repos: `"below 8.1.0"`,
  not `"pinned 7.2.0"`, or the breakdown degenerates into one line per repo.
  Falls back to `why` when omitted.

Judge **every cell the fingerprint offers, on every run** — including the ones
whose verdict will come out the same as what is already there. Restating an
unchanged value is not wasted work: `apply_status.py` counts those separately
and drops them from the write batch, and they are what makes the breakdown a
picture of the whole estate rather than of the diff. Skipping a cell because
you expect it to be unchanged just makes it invisible.

The heuristics are prose and the user changes them between runs; there is no
cache and no incremental mode. Two runs over an unchanged repo may
legitimately disagree — that is the design, not a bug.

### The fingerprint

```json
{"repo": "order-api-service", "path": "bounded_contexts/purchase/order-api-service",
 "owner": "PADE", "stack": ["python"], "dep_manager": "uv", "packaging": "pep621",
 "requires_python": ">=3.13", "deps": {"qlty-monitoring": "7.2.0", "ddtrace": "2.21.0"},
 "entrypoints": ["Dockerfile: CMD [\"tracer\", \"python\", \"run-api.py\"]"],
 "root_files": ["app/", "pyproject.toml", "uv.lock", "..."],
 "probes": {"ddtrace_run": false, "tracer": true}}
```

- `dep_manager` — `uv` | `poetry` | `pip-tools` | `null`, from which lockfile exists.
- `packaging` — `pep621` | `poetry` | `setup.py` | `null`. A `pyproject.toml`
  holding only `[tool.black]` gives `null`; many pip-tools repos look like that.
- `deps` — resolved pins, unified across `uv.lock`, `poetry.lock`,
  `requirements/*.txt` and `package.json`. Filtered to `ddtrace` plus
  anything named `qlty-*`, plus whatever the heuristics ask for via `dep`.
  These are *resolved* pins, so a library pulled in transitively is reported
  exactly like a directly declared one — which is the point, since the pin
  that runs is the one that matters. Compare versions with PEP 440 in mind:
  `7.2.1rc0 < 8.0.0`, and a bare `2.0` is 2.0.0. Match names PEP 503-style
  (`-`, `_` and `.` are all the same character, case-insensitively): the
  lockfiles, `requirements/*.txt` and `package.json` do not agree on spelling.
- `root_files` — the generic escape hatch when a new column keys off a
  file's mere presence.
- `probes` — see below.

## Editing the heuristics

They live in the **`Heuristics` tab**, one row per status column:

| A Column | B Applies to | C Probes | D N/A | E DONE | F TODO | G Notes |
|---|---|---|---|---|---|---|

`A Column` must match the Services header text exactly. A status column with
no row here is reported as a warning and its cells are left alone — so a new
column is opted in by adding its row, not by touching any script.

`C Probes` is the only field with syntax. One directive per line:

```
name = <regex> @ <glob>, <glob>     # named grep; result lands in probes.name
dep <package>                        # also report <package> in deps
```

Globs are relative to the repo root and may use `**`. Blank lines and `#`
lines are ignored. A malformed line is warned about, not fatal.

Probes read **tracked files only** — enumeration is `git ls-files`, not a
filesystem walk. A repo someone has run `uv sync` in matches thousands of
`.venv` files (one here globs 8,878 `.py` against 89 tracked); under a file
budget those crowd out the app's own source and the probe reports false,
silently, and only on machines where that `.venv` exists. Keep it that way:
the matrix judges committed code, and anything else makes a verdict depend on
who ran the skill. Tracked enumeration puts the largest repo at 228 files
against a 500 cap, so the budget stops being reachable rather than tuned.

### Version-floor columns

Most columns track one library against a minimum version. They share a shape,
and adding another is a sheet edit rather than a code change:

- Header and `A Column`: `<package> <floor>+`, e.g. `qlty-http 0.2.4+`. The
  `+` is load-bearing prose — it says the rule is `>=`, so a repo ahead of the
  floor stays `DONE` instead of flapping back to `TODO`.
- `C Probes`: `dep <package>`, using the name as it appears in the lockfile.
  `qlty-*` packages are collected without asking; everything else needs the
  line.
- `N/A` is *the service does not use the library*, not *the repo is
  irrelevant*.
- `DONE` / `TODO` split on the resolved pin against the floor.

**Installed is not the same as used, and the gap runs both ways.** A pin in
the lockfile can be someone else's baggage, and a library the service really
depends on can arrive without ever being named in its `pyproject.toml`. So
each column says for itself what puts a repo in scope:

- *Direct dependency* (`eventsourcing-helpers`, `qlty-monitoring`) — presence
  in `deps` is the test, because nothing else pulls them in.
- *Reached through another library* (`confluent-kafka-helpers`) — presence
  proves nothing, since avrocat and a `qlty-monitoring` extra both drag it in.
  Scope is the coupling that makes it matter: `eventsourcing-helpers` in
  `deps`, or a direct import.
- *Optional at the call site* (`qlty-http`) — an import probe decides, so a
  stale declaration nobody imports is not counted as work.

When a column is scoped by import, give it a probe over `**/*.py` and make
`N/A` name the case that fired, so the breakdown separates "never used it"
from "only has it transitively".

**Raising a floor is three edits and a flag.** Rename the Services header,
rename the matching `A Column` (they must be identical or the column is
skipped with a warning), move the version in `D`/`E`/`F` — then run with
`--recheck-heuristics`, because every cell that was `DONE` under the old floor
is now a lie the default pass would never look at. Expect a batch of
`DONE -> TODO`; check the pins in the table are all genuinely below the new
floor before confirming, since a stale checkout produces the same regression.

D/E/F are free prose — you are the one reading them. Write them as
conditions over fingerprint fields, and make them mutually exclusive; if a
repo satisfies none of the three, say so in the dry run rather than guessing.

## What the dry run prints

Three blocks, all of which the user needs to see:

1. **The table** — the cells that actually **change**, one row each: `a1`,
   service, column, `old -> new`, `why`. Cells whose verdict matches what is
   already there are counted in the summary line but kept out of the table,
   or a run that re-judges 144 cells to move 8 of them would bury those 8.
2. **`how the heuristics landed`** — per column, each `reason` with its
   count, over **every judged cell**, not just the changed ones. This is where a repo that
   is behind for an *unusual* reason becomes visible instead of being
   averaged into the pile: a service with no monitoring library at all, or
   one that is not traced at all rather than traced the old way. Read it out;
   these are the rows most likely to need a human decision.
3. **Warnings from the fingerprint run** — repos that did not resolve, and
   duplicate checkouts. These rows keep their `NEW` and are *not* in the
   table, so nothing else surfaces them.

It also names the `Last updated` cell it will refresh, so that write is
reviewed like any other.

## Write rules

`apply_status.py` re-reads the grid immediately before writing, so a human
edit made since the fingerprint run always wins. A verdict is refused, and
listed under "skipped", unless all of these hold:

- The cell is one the fingerprint offered for judging. This is also what keeps
  `DONE` safe without a second check: without `--recheck-heuristics` those
  cells are never in `cells`, so a verdict aimed at one is refused.
- The cell still holds the value the fingerprint recorded in `current`. That
  prior value is read from the fingerprint file, never from the verdict, so a
  verdict cannot misdeclare what it is about to overwrite.
- The row is between row 3 and the `Not in Datadog catalog` separator.
- The column is C or later — **column A (Service) and B (Owner) are never touched.**
- The column has a non-empty header in row 1. The space past the last header
  is free for hand-written marks — one column there holds `verified in
  datadog` notes — so a headerless column is not a status column even though
  it sits inside the status range, and `fingerprint.py` never offers its
  cells. A headerless column that holds values is reported as a warning.
- The verdict is one of that column's own data-validation values.

A verdict equal to the value already in the cell is counted as unchanged and
dropped from the batch, so a re-judging run writes only genuine moves.

The one write outside the status cells is the timestamp in **`Services!A1`**,
the corner cell above `Service`: `--apply` sets it to `Last updated
<YYYY-MM-DD HH:MM>`, local time. That cell is blank in the sheet's default
layout and is always on screen, and writing it does not change `len(row 1)` —
which `harmonization-matrix-update-services` uses to count status columns, so
a value there must never spill into B1 or beyond. If A1 already holds something
that isn't a `Last updated ` string, it is left alone and reported rather than
overwritten. `--no-stamp` skips it.

Nothing else is ever written: no rows added or removed, no headers, no
formatting, no data validation, no cells in the not-in-catalog section. Every
write goes through `values.batchUpdate` over individual A1 cell ranges, which
cannot carry a validation rule even in principle — the dropdowns are the
user's to own, and this skill only reads them to check that a verdict is
allowed. A row whose repo has no checkout keeps its `NEW` and is reported as
a warning.

## Tell the user about

Relay the dry-run table verbatim — it is the whole point of the review step
— then flag anything that needs a decision rather than deciding it yourself:

- **A row with no usable checkout.** Its cells keep whatever they hold and are
  absent from the table, so nothing else surfaces them — name these repos
  explicitly, because a silently skipped row looks identical to a judged one.
  The warning distinguishes three cases, and they need different fixes:
  - `in .gitrepos but not checked out` — the manifest declares it; `just
    update-repos` was not run, or the clone failed.
  - `not in .gitrepos and not checked out` — nothing declares it, so it stays
    invisible on every future run too. Either add it to `.gitrepos`, or the
    repo is archived and `harmonization-matrix-update-services` should be
    removing the row.
  - `checked out but absent from .gitrepos` — the repo *was* judged, but from
    a working tree nothing declares. The verdicts are only as trustworthy as
    that stray checkout.
- **`checkout is at <sha>, <branch> on GitHub is at <sha>`** — the tree is
  behind. Nothing about the verdicts looks wrong; they simply describe an
  older commit, so a repo fixed last week still reports `TODO`.
- **`N checkouts`** — the same repo name under two bounded contexts. The
  `.gitrepos` path wins, else the first alphabetically. Check the loser isn't
  the live one before accepting the verdicts.
- **A repo matching none of the three rules**, or matching more than one —
  the heuristic has a gap; it needs an edit in the Heuristics tab, not a
  guess from you.
- **Any `DONE -> TODO` or `DONE -> N/A` regression** under
  `--recheck-heuristics`. Under the default these cannot occur at all, so
  seeing one means either the repo genuinely went backwards or the heuristic
  now reads differently — and a stale checkout looks exactly like the former.
  Never wave one through; name the service and say which it is.
- **Any `reason` that only one or two services hit** — report it with the
  service names even when the verdict is uncontroversial. It usually means
  those repos are behind in a materially different way from the rest of the
  column, which is exactly what someone planning the work needs to know.

## Structural assumptions

Both scripts bail out rather than guess if these don't hold.

| Where | Content |
|---|---|
| `Services` A1 | blank, or the skill's own `Last updated <date>` stamp |
| `Services` row 1 | A1, `Owner`, then one header per status column |
| `Services` row 2 | `Service` in column A |
| `Services` rows 3+ | main section, one repo per row, column A = GitHub repo name |
| `Services` unheadered cols | past the last header in row 1: ignored, free for notes |
| `Services` separator | a row whose column A is exactly `Not in Datadog catalog` |
| `Heuristics` row 1 | headers; rows 2+ one per status column |
| Repo layout | `bounded_contexts/<context>/<repo>/.git` |
| `.gitrepos` | `<git-url> <path>` per line; declares the expected checkouts |
