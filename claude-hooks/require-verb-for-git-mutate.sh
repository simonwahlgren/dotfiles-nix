#!/usr/bin/env bash
# Claude Code PreToolUse hook: block mutating git/gh commands unless the
# user's most recent message contains an explicit action verb. Bridges
# Claude Code's tool-call layer with the per-action approval rule in
# ~/.claude/CLAUDE.md ("each commit, each push, each PR creation needs its
# own explicit approval … 'commit' / 'push' / '/commit' / '/pr' / 'create
# the PR'; bare 'yes' / 'approve' / 'looks good' don't count").
#
# Wired in ~/.claude/settings.json under hooks.PreToolUse[Bash].
# Exit codes:
#   0  — allow
#   2  — block, stderr is shown to Claude as the rejection reason

set -euo pipefail

input="$(cat)"

tool_name="$(printf '%s' "$input" | jq -r '.tool_name // ""')"
[[ "$tool_name" == "Bash" ]] || exit 0

command="$(printf '%s' "$input" | jq -r '.tool_input.command // ""')"
[[ -n "$command" ]] || exit 0

# Mutating subcommand patterns (PCRE). Tab-separated: <regex>\t<label>.
# First match wins for the user-facing label. Read-only verbs (git status /
# diff / log, gh pr view / list, gh api GET, …) are not listed and pass through.
read -r -d '' patterns <<'EOF' || true
\bgit\s+commit\b	git commit
\bgit\s+push\b	git push
\bgit\s+tag\b(?!\s+(-l|--list))	git tag
\bgit\s+reset\s+--hard\b	git reset --hard
\bgit\s+branch\s+(-[dD]|--delete)\b	git branch -d/-D
\bgit\s+merge\b(?!.*--abort)	git merge
\bgit\s+rebase\b(?!.*--abort)	git rebase
\bgit\s+clean\s+-[a-zA-Z]*f	git clean -f
\bgh\s+pr\s+(create|edit|merge|close|reopen|ready|review|comment)\b	gh pr <mutate>
\bgh\s+issue\s+(create|edit|close|reopen|comment|delete|transfer|pin|unpin)\b	gh issue <mutate>
\bgh\s+release\s+(create|edit|delete|upload)\b	gh release <mutate>
\bgh\s+secret\s+(set|delete|remove)\b	gh secret <mutate>
\bgh\s+variable\s+(set|delete|remove)\b	gh variable <mutate>
\bgh\s+repo\s+(create|edit|delete|fork|rename|archive|unarchive|sync)\b	gh repo <mutate>
\bgh\s+workflow\s+(run|enable|disable)\b	gh workflow <mutate>
\bgh\s+run\s+(cancel|delete|rerun)\b	gh run <mutate>
\bgh\s+label\s+(create|edit|delete|clone)\b	gh label <mutate>
\bgh\s+ruleset\s+(create|edit|delete)\b	gh ruleset <mutate>
\bgh\s+api\b[^|;&]*(-X|--method)\s*(POST|PATCH|PUT|DELETE)\b	gh api write-method
EOF

matched=""
while IFS=$'\t' read -r pat label; do
  [[ -n "$pat" ]] || continue
  if printf '%s' "$command" | grep -qP "$pat"; then
    matched="$label"
    break
  fi
done <<<"$patterns"

[[ -n "$matched" ]] || exit 0

# Explicit-verb whitelist. Word-bounded, case-insensitive. Bare 'yes' /
# 'approve' / 'looks good' deliberately excluded.
verb_pat='\b(commit|push|force[- ]push|/commit|/pr|create (the |a )?pr|open (the |a )?pr|merge (the )?pr|create (the )?(release|tag))\b'

transcript_path="$(printf '%s' "$input" | jq -r '.transcript_path // ""')"
last_user_msg=""
if [[ -n "$transcript_path" && -f "$transcript_path" ]]; then
  # Last user-typed message. Skip envelopes whose content array contains
  # only tool_result blocks (those have role=user but aren't user text).
  last_user_msg="$(jq -rs '
    map(select(.type == "user")) |
    map(
      .message.content as $c |
      if ($c | type) == "string" then $c
      else ($c | map(select(type == "object" and .type == "text") | .text) | join("\n"))
      end
    ) |
    map(select(length > 0)) |
    last // ""
  ' "$transcript_path" 2>/dev/null || true)"
fi

if printf '%s' "$last_user_msg" | grep -qiP "$verb_pat"; then
  exit 0
fi

cat >&2 <<EOF
Blocked: \`$matched\` mutates state and requires per-action approval per CLAUDE.md.

Your most recent user message contains no explicit verb ('commit', 'push',
'create the PR', '/pr', etc.). Bare 'yes', 'approve', or 'looks good' do
NOT count.

DO NOT retry this command. In your next response, summarise what you'd do
and ASK the user to approve with an explicit verb. The hook will pass
through on the next turn once that verb appears in their most recent
message.

Attempted: ${command:0:200}
EOF
exit 2
