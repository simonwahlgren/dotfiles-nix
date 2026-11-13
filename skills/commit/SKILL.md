---
name: commit
description: Stages and commits all tracked changes in the current repository, with one Conventional Commit per related logical change. Use when asked to commit changes, draft commit messages, or "commit and push"; pushes only when the request says push. Never adds untracked files.
allowed-tools: Bash, Read
---

# Commit tracked changes

Invoking this skill authorizes the commits below without another confirmation, unless repository or higher-priority instructions require approval. A request only for messages or a proposal is read-only: draft messages without staging or committing.

## Inspect and group

1. Find the repository root with `git rev-parse --show-toplevel` and work from it. Read applicable repository instructions. Inspect `git status --short` and check for conflicts or an in-progress merge, rebase, cherry-pick, revert, or bisect. Stop if any are present. Do not recurse into submodules to commit; stop if completing the task would require it.
2. List changed paths before reading content: use `git diff --name-status`, `git diff --cached --name-status`, and `git ls-files`. Include staged additions already tracked in the index, tracked modifications, and tracked deletions. Exclude every untracked path, even if it belongs with a tracked change. If there are no tracked changes, report that and stop.
3. Screen paths for secrets before any content inspection. Do not read or print likely secret-bearing files or diffs, such as `.env`, credentials, private keys, or secret-bearing configuration. Stop and request safe handling when uncertain. Commit authorization is not permission to expose secrets. If a secret appears unexpectedly, stop and report only affected paths, never values.
4. Inspect both staged and unstaged diffs using only explicit, screened paths: `git diff --cached -- <paths>` and `git diff -- <paths>`. Account for index and working-tree versions separately; a combined HEAD-to-working-tree diff can hide staged-only edits or reversals.
5. Group changes by purpose, not file or directory. Keep related code, tests, and documentation together; separate unrelated changes, including hunks in the same file. Plan one commit per logical group. Stop for ambiguous grouping or any split that cannot safely preserve every staged-only and working-tree change.

## Stage, verify, and commit

For each group:

1. Isolate exactly that group in the index. Existing staged changes are not automatically part of it. Use explicit tracked paths with `git add -- <paths>` only when the whole file belongs to the group and replacing its index version loses no staged-only content. Otherwise use selective hunk staging or reviewed index-only patches. Use literal pathspecs for names containing pathspec metacharacters. Never use blanket `git add .`, `git add -A`, or commands that can add untracked files.
2. Before removing unrelated pre-staged paths or hunks from the index, retain their exact patches and versions so they can be staged for their own groups later. Use only non-destructive index-only operations; leave working-tree content intact. Do not unstage a new index-tracked file and later treat it as an untracked file to add. If preservation or replay is uncertain, stop rather than flattening index and working-tree versions. Do not discard staged-only changes, even when the working tree reverses them.
3. Review the entire staged path list and staged diff, after the secret guard, to confirm that only this group is staged and no untracked file was added. Check that the diff matches the intended message. Run `git diff --cached --check` and appropriate repository checks. If checks use the working tree, ensure unrelated changes do not mask failures in the staged version. Stop on validation failure; do not make unrelated fixes.
4. Commit with `git commit` using `type(optional scope): imperative summary`. Choose the type and scope from the actual change. Mark breaking changes with `!` and explain them in a `BREAKING CHANGE:` footer when applicable. Add a body only when useful. Never amend, force-push, push without an explicit push request, bypass hooks, reset destructively, discard changes, create worktrees, or generate helper scripts or evaluation artifacts. Stop if the commit or its hooks fail.
5. Inspect status and remaining staged and unstaged changes before continuing. Reconcile hook-generated or unexpected changes with the plan; stop if their purpose or safety is unclear. Ensure unrelated pre-staged groups cannot leak into the next commit.

## Push

Only when the request explicitly says to push (for example "commit and push"): after the last commit succeeds and the final status check passes, run `git push`, or `git push -u origin HEAD` when the branch has no upstream. Never force-push. If the push is rejected, stop and report; do not pull, rebase, or force. Without an explicit push request, do not push.

## Report

Verify final tracked status against the original inventory, including retained staged-only changes. All intended tracked changes must be committed; untracked files must remain untouched. Report each commit hash and message, the push result if a push was made, checks and results, and any remaining tracked changes or untracked paths. If stopped, state the blocker and the safe next action without claiming completion.
