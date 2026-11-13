# Findings and overview files

`render.py` reads one findings file per question and one overview file.

## Datasets written by extract.py

- `prompts.jsonl`: human prompts. Fields: `src` (claude or codex), `sid`, `ts`, `cwd`, `kind` (prompt or slash), `cmd` (slash name), `text`, `len`.
- `bash.jsonl`: every shell command. Fields: `src`, `sid`, `ts`, `cwd`, `sub` (run by a subagent), `cmd`, `len`, `desc`, `progs` (such as "git diff"), `eph` (ephemeral tool use such as "uv run --with: pyyaml"), `err`, `classes` (error classes), `missing_cmd`, `missing_mod`, `out` (output head, failures only), `escalation` (Codex sandbox escalation request), `denied` (Claude denial kind).
- `inline.jsonl`: inline code inside shell commands. Fields: `src`, `sid`, `ts`, `cwd`, `sub`, `kind` (heredoc-script, dash-c, heredoc-write, heredoc-stdin, long-filter, codex-js-tool), `interp`, `target`, `nlines`, `nchars`, `imports`, `purpose` (heuristic, multi-label tags), `prefix`, `body`, `desc`.
- `errors.jsonl`: failed non-shell tool calls and hook problems. Fields: `src`, `sid`, `ts`, `tool`, `inp`, `out`, `denied`.
- `sessions.jsonl`: one row per session. Fields: `src`, `sid`, `first`, `last`, `cwd`, `prompts`, `tools`, `models`, `kind`, `compacts`.
- `agg.json`: counters such as `tool:*`, `mcp_server:*`, `mcp_tool:*`, `skill_tool:claude`, `slash:*`, `agent_type:*`, `hook:claude`, `perm_decision:claude`, `tool_denial_kind:claude`, `codex_escalation*`, `rtk_escape:*`, `file_ext:*`.

Program counts for `echo`, `head`, `tail`, and `true` are inflated by separators and pipelines.

## Findings file (q1.json to q4.json)

```json
{
  "summary": "2-4 sentences answering the question",
  "claude_vs_codex": "1-3 sentences",
  "charts": [
    {"title": "...", "unit": "commands", "bars": [{"label": "...", "value": 123, "note": "optional"}]}
  ],
  "recommendations": [
    {
      "title": "short imperative title",
      "kind": "skill | hook | rule | tool | script | mcp | config | cleanup | leave-as-is",
      "impact": "high | medium | low",
      "verified": true,
      "evidence": {"count": 0, "sessions": 0, "split": "claude N / codex M", "examples": ["...", "..."]},
      "proposal": "what to do, concretely",
      "snippet_label": "label for the copyable block, or empty",
      "snippet": "copyable rule text, hook config, or install line, or empty",
      "benefit": "...",
      "tradeoff": "..."
    }
  ],
  "notes": ["assumptions and limitations"]
}
```

Use 1 to 3 charts with at most 12 bars each. Aim for 6 to 12 recommendations per question.

Rules for findings:

- Give an occurrence count, a distinct-session count, and 1 or 2 short redacted examples (160 characters at most).
- Set `verified` to true only when the count was checked and samples were read. Otherwise set it to false and say what is assumed.
- Make proposals concrete: exact rule text, skill name and trigger, hook event and command, or tool name with its NixOS install method.
- Check the current setup before recommending something that already exists.
- "Leave as is" is a valid conclusion for a cluster.

## Overview file

```json
{
  "at_a_glance": [{"title": "...", "text": "..."}],
  "limits": ["method notes and limitations"]
}
```

The report has no ranking. It lists every recommendation except `leave-as-is` under "All proposed fixes", showing `impact` as the priority and linking each row to its card. `render.py` ignores a leftover `top10` key.
