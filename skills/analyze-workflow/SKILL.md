---
name: analyze-workflow
description: "Analyze Claude Code and Codex session history and write an HTML report recommending skills, hooks, AGENTS.md rules, CLI tools to replace inline scripts, and other tooling. Use for /analyze-workflow or requests like 'analyze my sessions', 'workflow insights', 'what should I automate'. The default window is the last 6 months."
---

# Analyze workflow from session history

Analyze the user's Claude Code and Codex sessions across all projects and recommend workflow improvements. This is read-only analysis: apart from the report file, do not change any config, skills, or instructions. Pi sessions are out of scope.

## Arguments

Both are optional.

- Window: default is 6 months back from the run date. Accept forms like "3 months" or an explicit start date.
- Output directory: default is `~/.agents/workflow-insights/`, created if missing.

The output file is always `<run date as YYYY-MM-DD>-workflow-insights.html`. Compute dates at run time. If the file already exists, ask before overwriting.

## Sources

- Claude Code transcripts: `~/.claude/projects/**/*.jsonl`.
- Codex sessions: `~/.codex/sessions/` and `~/.codex/history.jsonl`.
- Current setup, to avoid suggesting what already exists: `~/.dotfiles` (`agents/AGENTS.md`, `skills/`, `claude/settings.json`, `rtk/config.toml`), plus installed plugins and MCP servers.

Start by reporting the date range and session count each source actually covers. If coverage is shorter than the window, say so and continue.

## Scripts

Reuse the scripts in `bin/` next to this file instead of writing new ones. They need only `python3` and `zstd`. Each has a usage docstring.

- `extract.py <start YYYY-MM-DD> <datadir>`: parses both sources and writes redacted datasets (`sessions`, `prompts`, `bash`, `inline`, `errors` as JSONL, plus `agg.json` counters). It skips headless `sdk-cli` runs and claude-mem observer sessions, and flags subagent activity with `sub`.
- `summarize.py <datadir> [coverage|tools|bash|inline|errors|prompts|misc]`: prints aggregates.
- `sample.py <datadir> <dataset> [filters] [--count-by FIELD]`: filters, counts, and samples records.
- `render.py <datadir> <findings_dir> <overview.json> <output.html> <start> <end>`: builds the report from `q1.json` to `q4.json` and an overview file. The JSON shapes are in its docstring and in `bin/findings-schema.md`.

## Extract

1. Create a temporary working directory with `mktemp -d` and run `extract.py` into a `data/` directory inside it. Keep datasets and scratch files there, not in a repository.
2. Check the result with `summarize.py <datadir> coverage tools`. The transcript formats are undocumented and change. If counts look wrong (no sessions, `codex_exec_unparsed` high, unknown tool names), inspect a few transcript files for the new schema and fix `extract.py` in place.
3. Work from aggregates first, then sample representative examples per cluster.
4. Never print or store secret values or full transcript content. `extract.py` redacts and truncates what it stores; keep excerpts in findings short. The report must contain no secrets and no full transcript content.

## Questions

Cost is not a constraint. After the shared extraction step, if the harness supports subagents, use them in parallel, one per question, on the workhorse model (`sonnet` in Claude Code) at medium effort. Otherwise run the questions in sequence. Give each subagent the data directory, the script paths, the coverage numbers and caveats from `summarize.py`, the setup paths under Sources, and `bin/findings-schema.md`. Each writes one findings file (`q1.json` to `q4.json`). Spot-check the highest-impact claims against the data before reporting them.

1. Repeated patterns: which requests, corrections, or multi-step procedures are repeated that a skill or hook would handle? For each, say which one (skill, hook, or neither) and why.
2. AGENTS.md rules: which rules are missing, based on corrections given repeatedly or mistakes agents repeated? Also flag existing rules that agents routinely ignore or that are never relevant.
3. Inline scripts: cluster all inline code tool calls (`python - <<'PY'`, `python -c`, `node -e`, long jq or awk pipelines) by what they accomplish, such as PDF extraction, JSON or YAML reshaping, or API calls. For each cluster, recommend an existing CLI that replaces it, or a small reusable script if no tool exists, or say the inlining is fine.
4. Other tooling: which tools, plugins, or MCP servers would remove friction visible in the data (failed commands, retries, permission prompts, long manual sequences)? Only suggest things tied to observed evidence. Also list installed skills, plugins, and MCP servers that are never or rarely used.

## Recommendations

Every recommendation includes:

- Evidence: occurrence count, number of distinct sessions, and 1 or 2 examples.
- Proposal: concrete, such as rule text, skill name and trigger, hook event and command, or tool name with its NixOS install method.
- Expected benefit and cost or tradeoff.

Rank by impact within each section. Skip anything seen fewer than 3 times across 2 or more sessions, unless a single occurrence was costly. Separate verified findings from assumptions. Compare Claude and Codex where they differ.

## Report

Write the overview file (at a glance and limits only) yourself after reading all findings, then run `render.py`. It produces one self-contained HTML file, modeled on the Claude Code `/insights` report, with these properties:

- Inline CSS and JS only. No external assets or network requests.
- Header with the analyzed window, per-source session counts, and headline stat cards.
- An "at a glance" summary and a list of all proposed fixes with priority, each linked to its card.
- One section per question, with simple bar charts for the counts and a card per recommendation (evidence, proposal, benefit, tradeoff).
- Copy buttons on proposed rule text, hook config, and install commands.
- A sticky table of contents, readable in light and dark mode.

In chat, reply only with the file path, the coverage numbers, and the top 5 findings: the five the analyst judges most valuable, since the report does not rank.
