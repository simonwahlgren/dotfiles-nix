---
name: harmonization-matrix-update-services
description: Reconcile the "Harmonization matrix" Google Sheet against the fyndiq/infrastructure repo — make sure every service repo is listed with the right Owner and linked to its GitHub repo, move repos with no Datadog Software Catalog entry into the "Not in Datadog catalog" section for manual handling, and delete rows for repos archived in Terraform. Reads services.yaml and repos.yaml from GitHub master, so it runs from any directory. Use when asked to update, sync, or refresh the harmonization matrix / the services sheet / the service owner list.
disable-model-invocation: false
user-invocable: true
argument-hint: "[--ref <git-ref>] [--spreadsheet-id <id>]"
---

# Update the Harmonization matrix

Sync the sheet's service list and Owner column with `fyndiq/infrastructure`.
**Always show the plan and get explicit confirmation before writing.**

## Run it

```sh
# 1. Dry run — prints the full proposed table, writes nothing.
~/.claude/skills/harmonization-matrix-update-services/scripts/update_matrix.py

# 2. Only after the user confirms:
~/.claude/skills/harmonization-matrix-update-services/scripts/update_matrix.py --apply
```

Flags: `--ref <git-ref>` (default `master`), `--spreadsheet-id <id>` (defaults to
the live matrix — override to rehearse against a copy).

The script needs `gh` (authenticated, for the private repo) and `gws`
(Google Workspace CLI, for the sheet). Dependencies come from a PEP 723
header, so `uv` fetches PyYAML on first run.

## Workflow

1. Run the dry run.
2. **Relay the printed table to the user verbatim**, plus the summary counts
   and any warnings. Do not summarise the table away — the whole point is
   that the user reviews the rows before they land.
3. Ask for explicit confirmation.
4. On confirmation, re-run with `--apply` and report what was written.

If the dry run says `nothing to do`, say so and stop — don't run `--apply`.

Investigate warnings before applying rather than passing them along silently:

- `not in repos.yaml` — the repo was renamed, deleted, or was never TF-managed.
  Owner becomes `Unknown`; the row is kept so the user can decide.
- `archived in repos.yaml but still referenced by services.yaml` — the row is
  being deleted, and the Datadog catalog entry that still points at the repo
  should be pruned too. Until it is, every run reports the same disagreement.
- `codeowner team '<slug>' has no label` — a new team exists in `repos.yaml`.
  Add it to `OWNER_LABELS` in the script *and* to the sheet's Owner dropdown.
- `listed more than once` — a duplicate row in the sheet; only the first
  survives, so check the loser wasn't carrying real status data.
- `services.yaml sets owner: X but repo Y is owned by Z` — see the rule below.

## What the script does

**Row identity is the GitHub repo name**, not the Datadog service name. One
repo may deploy many Datadog services; they collapse into a single row.

**A repo archived in Terraform loses its row.** `repos.yaml` carries
`archived: true`, and that outranks everything else: the row is deleted from
whichever section it sits in rather than moved, so the sheet only ever tracks
repos that still exist. An archived repo usually keeps its `services.yaml`
entry long after the fact, so this is the one place the skill deliberately
disagrees with the catalog — and it warns for each one, because the real fix
is to prune the stale entry upstream.

This is the only change the skill makes that **destroys data**: the row's
statuses go with it, and a repo that is later un-archived comes back as a new
row with every status `NEW`. The dry run therefore lists each removal with the
owner and status values it is discarding. Read that block before confirming.

Two other sections, and rows are **only ever moved between them**:

- **Main section** (rows 3 .. separator) — every repo referenced by a
  `repo:` in `services.yaml`, i.e. repos with at least one Datadog Software
  Catalog entry. This is the definition of a "service repo": `repos.yaml`
  alone can't distinguish a service from a library or a tool.
- **`Not in Datadog catalog`** — every other repo already in the sheet.
  These need a human: either the repo needs a catalog entry, or it isn't a
  service and the row should go.

Both sections are sorted alphabetically, case-insensitively.

**Owner** comes from `repos.yaml` `codeowners:` — the source of truth — via
`OWNER_LABELS` (`mase`→MASE, `pade`→PADE, `platform`→Platform,
`fullstack`→Fullstack, `data`→Data), falling back to `Unknown`. Only a bare
team slug counts; raw CODEOWNERS lines (path globs, `@handle`, comments) are
skipped.

**Column A links to the repo** — `https://github.com/fyndiq/<repo>`, applied
as a rich-text link (not `=HYPERLINK`), so the cell value stays the plain repo
name: it still sorts, copies, and diffs as text, and it doesn't depend on the
spreadsheet locale's formula argument separator. Rows in both sections get a
link; a row whose repo isn't in `repos.yaml` is left unlinked rather than
pointing at a 404. Existing links are read back off the sheet, so a run with
nothing else to do is still a no-op.

The per-service `owner:` override in `services.yaml` is **deliberately
ignored**: it is scoped to one Datadog service, but a sheet row is a repo
that may deploy several services with conflicting overrides. A disagreement
is reported as a warning rather than silently applied.

## Write rules

Idempotent: a second run with no upstream change reports `nothing to do`.

- **Layout unchanged** (no rows added, moved, or re-sorted) → writes only the
  individual cells that differ. Nothing else is touched.
- **Layout changed** → rewrites the whole grid, because rows shift position.
  Existing status values travel with their repo, so no status is altered —
  only relocated.
- Rows past the new end are cleared, so a shrinking list leaves no orphans —
  this is what makes an archived repo's row actually disappear.
- Column A links are written separately, only for rows whose link is missing,
  stale, or (on a layout change) has moved. The report flags these with `@`.

**Blank status cells in the main section become `NEW`.** This covers both
cases with one rule: a brand-new row (every cell blank → all `NEW`), and an
existing row under a newly added status column (only that cell → `NEW`).
Cells that already hold a value are never overwritten. Rows in the
not-in-catalog section are left blank — there's no work to track until
someone triages them.

Adding a status column to the sheet therefore needs no script change: add the
header, run the skill, and every main-section row picks up `NEW` in it.

**Data validation is never written.** The dropdown rules — their value lists
and the row ranges they cover — belong to whoever set up the sheet. The script
reads them (to check `NEW` is allowed, and to warn about uncovered rows) and
never issues `setDataValidation`.

An earlier version did reapply them after a layout change, and it was wrong in
two ways worth remembering: it cleared `B:E` across the whole row span before
re-applying, which silently narrowed the validated range to just the two data
blocks; and it sampled one cell (`C3`) and stamped that rule across every
status column, which would flatten any column whose dropdown legitimately
differed. Don't reintroduce either.

The cost of not writing them: Sheets does not extend validation to rows added
past the existing range, so a growing list can leave new rows without
dropdowns. The script detects this and prints which rows need extending by
hand — relay that note.

Conditional-format rules covering the status columns *are* still extended to
the new last row. The sheet has none today, so this is currently a no-op.

`NEW` must be one of the status dropdown's allowed values or new rows show
an invalid-entry flag; the script warns if it isn't.

## Structural assumptions

The script bails out rather than guessing if these don't hold. It targets the
**first tab** by index, so renaming the tab is safe.

| Cell | Content |
|---|---|
| Row 1 | `''`, `Owner`, then one header per status column |
| Row 2 | `Service` in column A |
| Rows 3+ | main section, one repo per row |
| Separator | a row whose column A is exactly `Not in Datadog catalog` |
| Below it | the not-in-catalog section |

Status-column count is derived from row 1, so adding or removing a status
column needs no script change — a new column's cells fill with `NEW`. If the
separator row is missing it gets appended.
