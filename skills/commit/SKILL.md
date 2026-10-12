---
name: commit
description: Stage-aware commit helper. Runs git status and git diff --staged, summarizes the changes, proposes a Conventional Commits message, and waits for explicit user approval before running git commit. Use when the user asks to commit, prepare a commit, or wants a commit message drafted.
allowed-tools: Bash(git:*), Read
---

Run `git status` and `git diff --staged`. Summarize the staged changes, propose a Conventional Commits–style message, and wait for the user's approval before running `git commit`. Do not commit unstaged changes and do not run `git add` unless the user asks for it.
