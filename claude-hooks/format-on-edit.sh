#!/usr/bin/env bash
# Claude Code PostToolUse hook: format the edited file in place.
# Python files use ruff format (project .venv first), Terraform files use
# terraform fmt. Formatting only, no lint fixes. Always exits 0 and prints
# nothing, so a formatter failure never affects the edit.
#
# Wired in ~/.claude/settings.json under hooks.PostToolUse[Edit|Write|MultiEdit].

file=$(jq -r '.tool_input.file_path // empty' 2>/dev/null) || exit 0
[[ -n "$file" && -f "$file" ]] || exit 0

case "$file" in
  *.py)
    ruff=""
    root=$(git -C "$(dirname "$file")" rev-parse --show-toplevel 2>/dev/null) || root=""
    if [[ -n "$root" && -x "$root/.venv/bin/ruff" ]]; then
      ruff="$root/.venv/bin/ruff"
    elif command -v ruff >/dev/null 2>&1; then
      ruff=ruff
    fi
    [[ -n "$ruff" ]] && "$ruff" format -q "$file" >/dev/null 2>&1
    ;;
  *.tf | *.tfvars)
    command -v terraform >/dev/null 2>&1 && terraform fmt "$file" >/dev/null 2>&1
    ;;
esac
exit 0
