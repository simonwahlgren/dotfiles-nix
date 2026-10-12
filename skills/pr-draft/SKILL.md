---
name: pr-draft
description: Sonnet-assisted PR prep. Offloads the read/draft work (git state, diff reading, commit message + full PR body) to a Sonnet subagent, then commits/pushes/creates the PR from the main session after your explicit approval. Use when you want /pr's output without spending Opus tokens on diff-reading and body-drafting, while keeping the push/PR gate.
disable-model-invocation: false
user-invocable: true
argument-hint: "[title or instructions]"
---

# Sonnet-assisted Pull Request

A token-efficient split of `/pr`: a Sonnet subagent does all the **read-only** work and drafts the artifacts; the **main session** performs every mutation (branch, commit, push, PR create/update) after you approve.

Why split: subagents run autonomously and cannot ask you free-form questions — only the main session can gate mutations and confirm assumptions. So the subagent drafts and surfaces its assumptions; you confirm; the main session mutates.

## Step 1 — Dispatch the Sonnet draft (read-only)

Spawn one subagent with the **Agent** tool: `subagent_type: "general-purpose"`, `model: "sonnet"`. Give it this self-contained prompt (substitute `$ARGUMENTS` if provided):

> You are preparing, not creating, a pull request. Run only read-only commands, because the main session performs every mutation after the user approves: no `git checkout -b`, `add`, `commit`, `push`, `gh pr create`, or `gh pr edit`.
>
> Read `/home/simon/.claude/skills/pr/SKILL.md` and follow its template-selection logic (step 5) and all of its "Writing guidelines" for the body. Do the read-only parts of its flow: inspect branch (`git branch --show-current`), `git status`, detect existing PR (`gh pr view --json number,title,body 2>/dev/null`), determine base branch (`main`/`master`), pick the PR template, and gather context (`git log --oneline $(git merge-base HEAD <base>)..HEAD`, `git diff $(git merge-base HEAD <base>)..HEAD --stat`, and the full `git diff $(git merge-base HEAD <base>)..HEAD`). Extra guidance for title/instructions: `$ARGUMENTS`.
>
> Then return EXACTLY these sections as markdown, nothing else:
>
> ```
> ## Branch
> <current branch>. If it is main/master, propose a kebab-case feature branch name: <name>
> ## Commit
> <Conventional Commits message for the pending changes, or "clean — skip commit" if working tree is clean>
> ## PR action
> create  — OR —  update #<number>
> ## Base
> <main|master>
> ## Template
> <path of the template you used, or "global fallback">
> ## PR title
> <title>
> ## PR body
> <full body, ready to paste verbatim, including the [claude:skip-draft] marker>
> ## Asks / assumptions
> <Every point where /pr says "ask the user" or where you had to guess: template choice among several, tracker/ticket base URL, branch name, which files to stage, create-vs-update ambiguity. State what you assumed so the main session can confirm. If none, write "none".>
> ```

## Step 2 — Present and confirm

When the subagent returns, show the user: proposed branch (if any), commit message, create-vs-update + PR number, chosen template, PR title, and the full PR body. **Call out the `Asks / assumptions` section explicitly** — these are the questions the subagent could not ask you directly. Resolve them now (ask the user if any are load-bearing).

## Step 3 — Wait for explicit approval

Do not mutate anything until the user names the action ("commit", "push", "create the PR", "go ahead and push"). A bare "looks good" approves the *draft*, not the push: each commit, push, and PR creation needs its own explicit verb.

## Step 4 — Mutate from the main session

On approval, run the mutations here (not in a subagent — these need your permission prompts), using the subagent's drafted message and body **verbatim**:

1. If on `main`/`master`: `git checkout -b <proposed name>`.
2. Stage only modified/newly-created files from this work (never pre-existing untracked files); `git commit` with the drafted message. Skip if clean.
3. `git push -u origin HEAD` (or `git push` if upstream exists).
4. **Create:** `gh pr create --draft --title "<title>" --body "<body>"`. **Update:** `gh pr edit <number> --body "<body>"`, preserving manual edits per `/pr`'s update rules.

If any mutation needs a decision the subagent assumed wrong, stop and fix before continuing — a denied push mid-flow leaves an unpushed branch with a dangling PR step.
