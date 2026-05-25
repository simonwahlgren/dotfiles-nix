#!/usr/bin/env bash
# Claude Code PreToolUse hook: block bare package-manager installs in Bash
# tool calls and tell Claude to use `pkg-sandbox` instead. Re-runs of the
# same command via `pkg-sandbox <tool> ...` are passed through.
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

# Already sandboxed? allow.
if printf '%s' "$command" | grep -qE '(^|[[:space:];&|])pkg-sandbox([[:space:]]|$)'; then
  exit 0
fi

# Tools and verbs we want sandboxed. Run scripts (npm run / pnpm run) are
# included because lifecycle scripts execute arbitrary code too.
pm_re='(^|[;&|`(]|[[:space:]])'                         # start-of-cmd boundary
pm_re+='(npm|pnpm|yarn|bun|pip|pip3|uv|poetry|cargo)'   # package manager
pm_re+='[[:space:]]+'
pm_re+='(install|i|add|sync|ci|update|upgrade|run|exec|x|dlx|build|fetch)'
pm_re+='([[:space:]]|$)'

# uv has uv pip <verb> form too
uvpip_re='(^|[;&|`(]|[[:space:]])uv[[:space:]]+pip[[:space:]]+(install|sync|compile)'

# A few read-only verbs we DON'T want to block:
readonly_re='(^|[[:space:]])(npm|pnpm|yarn|bun|uv|pip|pip3|poetry|cargo)[[:space:]]+(list|ls|outdated|view|info|search|why|tree|show|audit|config|--version|-v|--help|-h)([[:space:]]|$)'

if printf '%s' "$command" | grep -qE "$readonly_re"; then
  exit 0
fi

if printf '%s' "$command" | grep -qE "$pm_re" \
   || printf '%s' "$command" | grep -qE "$uvpip_re"; then
  cat >&2 <<EOF
Blocked: bare package-manager install detected.

Wrap it with pkg-sandbox so postinstall / lifecycle scripts cannot read
\$HOME secrets (sops-decrypted CIRCLECI_TOKEN, GEMINI_API_KEY, ~/.ssh, etc.).

  pkg-sandbox $command

For a network-isolated run (already-cached deps only):
  PKG_SANDBOX_NONET=1 pkg-sandbox $command
EOF
  exit 2
fi

exit 0
