---
name: pr
description: Create or update a pull request for the current branch
disable-model-invocation: false
user-invocable: true
argument-hint: "[title or instructions]"
---

# Create or Update Pull Request

Create or update a PR for the current branch. If `$ARGUMENTS` is provided, use it as guidance for the title or any special instructions.

## Steps

1. **Check current branch** — run `git branch --show-current`. If it is the default branch (`master` or `main`), create a new feature branch before doing anything else. Pick a short, kebab-case name from the staged/unstaged diff or `$ARGUMENTS`, and run `git checkout -b <branch-name>`.

2. **Commit pending changes** — run `git status` to see what is modified. Stage and commit any tracked file modifications and any staged changes (including staged new files). Do NOT add untracked files that already existed before this session's edits — only stage files you have modified or files you newly created during this work. When in doubt, ask. Use a Conventional Commits message. Skip this step if the working tree is clean.

3. **Detect existing PR** — run `gh pr view --json number,title,body 2>/dev/null`. If a PR exists, you are updating it. Otherwise you are creating a new one.

4. **Determine the base branch** — use `master` or `main`, whichever exists as the default branch.

5. **Pick the PR template — repo first, local fallback.** Always prefer a template that lives in the current repo. Check these paths in order and use the FIRST one that exists:
   1. `.github/PULL_REQUEST_TEMPLATE.md`
   2. `.github/pull_request_template.md`
   3. `docs/PULL_REQUEST_TEMPLATE.md`
   4. `PULL_REQUEST_TEMPLATE.md`
   5. Any file under `.github/PULL_REQUEST_TEMPLATE/` (multi-template directory — if there are several, pick the one whose name best matches the change type, or ask the user)

   Only if none of those exist, fall back to `~/.dotfiles/github/pull_request_template.md`. Never use the local fallback when a repo template is present, even if the repo template looks sparse.

6. **Gather context** — run these in parallel:
   - `git log --oneline $(git merge-base HEAD <base>)..HEAD` to get all commits on this branch
   - `git diff $(git merge-base HEAD <base>)..HEAD --stat` for a file-level summary
   - `git diff $(git merge-base HEAD <base>)..HEAD` for the full diff
   - If updating, read the existing PR body

7. **Push the branch** — run `git push -u origin HEAD` if the branch has no upstream yet, or `git push` if it does.

8. **Write the PR** — fill in the sections from the chosen template. Follow the HTML comments in the template for guidance on what to write in each section.

   **Always include the `[claude:skip-draft]` marker.** This marker tells the code-review automation to skip the PR while it is a draft. Since every PR is created as a draft (step 9), the marker must always be present in the body, regardless of which template was chosen. Keep it verbatim if the chosen template already contains it (the global fallback does); if the chosen template lacks it (e.g. a repo template), append `[claude:skip-draft]` as the final line of the body. When updating an existing PR, preserve the marker — never strip it.

9. **Create or update**:
   - **New PR**: always create as draft — `gh pr create --draft --title "<title>" --body "<body>"`. The user promotes to ready-for-review manually; never pass `--draft=false` or use `gh pr ready`.
   - **Existing PR**: regenerate the body from the full branch context (all commits since the merge-base, not just commits added this session — the user may have made commits outside the skill), but **preserve manual edits the user made to the existing PR body**. The user often hand-edits the description between skill runs (adds reviewer-context notes, refines wording, adds Open items, etc.) and those edits must not be silently overwritten.

     **Reconcile the existing body with the final branch scope:**
     - Preserve actual user edits, explicit user-owned checklists, and user-added custom sections. Keep accurate user wording rather than replacing it for style. If changed scope makes user-authored content inaccurate or incomplete, update only as authorized; ask before a material change when authorization is unclear.
     - Determine authorship from available editing history or explicit context. Caveats, parentheses, checkbox states, and context absent from the diff do not by themselves establish manual authorship. When authorship is uncertain, preserve the substance and ask only before a material change to potentially user-authored content.
     - Revise known agent-generated prose into a coherent description of the final problem and behavior. Consolidate overlapping bullets and remove obsolete sections or development history as scope evolves; do not retain a section merely because it is still technically true.
     - Keep Open items for genuinely pending actions or questions. Remove resolved agent-owned items, or fold their still-relevant decisions into the final rationale with links when useful. Preserve actual user-authored items and their checkbox states unless authorized to change them. Retain necessary rollout actions and meaningful review evidence.
     - Keep relevant ticket and reference links, add useful new ones, and drop irrelevant agent-added references. Preserve links the user added unless authorized to change them.

     To edit the body, write it to a file with `gh pr view <number> --json body --jq .body > <tmpfile>`, edit that file with the edit tool, then run `gh pr edit <number> --body-file <tmpfile>`. Do not script the replacement in Python.

     Then compare the regenerated body against the existing one and update it as above if they differ meaningfully. If the branch state is already accurately described and manual edits are preserved, skip the edit. Preserve the title unless the user asked to change it. If `$ARGUMENTS` was provided, treat it as an explicit instruction to update the body (and may override preservation — ask if unclear).

## Writing guidelines

- **Explain the final problem and behavior.** Give reviewers the context they need to assess the change, including material risks and non-routine validation. Include implementation detail or examples when they explain a tradeoff, constrain rollout, or clarify behavior that is difficult to assess from the diff.
- **Background**: lead with the problem or outcome from the reader's perspective. Include useful ticket references without a phase-history preamble. Derive tickets from `$ARGUMENTS`, the branch name, or commit messages; do not invent ticket relationships. Hyperlink references as described below.
- **Changes**: each bullet describes a meaningful behavioral change, rather than a file edit. Group related changes and scale the list to the change; no minimum bullet count or padding.
- **Write concise, grammatical prose.** Remove repetition and filler before shortening sentences. Keep the conditions, caveats, and rationale reviewers need; link supporting detail when useful.
- **Do not hard-wrap lines.** Write each paragraph and each bullet as a single unbroken line — no 80-char wrapping, no manual line breaks mid-sentence. GitHub renders prose with soft wrap; hard wraps just make the body harder to edit and produce ugly diffs when text is revised. Only use newlines to separate paragraphs, list items, or markdown blocks.
- **No blank lines between bullets in the same list.** Bullets in a list go on consecutive lines (one newline between them, never two). A blank line between bullets makes GitHub render the list as loose/spaced-out, which wastes vertical space and makes scanning harder. This applies to every list in the body — Changes, Open items, sub-lists, everything. Only insert a blank line when actually ending the list and starting a new paragraph or heading.
- Avoid file-by-file or commit-by-commit walkthroughs, internal-flow explanations, code snippets, and examples that merely restate the diff. Include identifiers or technical detail only when reviewers need them to understand the behavior, risk, or verification.
- Use only sections needed for the review or required by the chosen template. Do not add optional template filler. Link an existing runbook for detailed rollout steps when useful, while keeping material rollout constraints and pending actions visible in the PR.
- **Keep routine validation in the final chat response.** Do not add test counts, execution summaries, or notes like "Diff checks passed" to the body unless the user asks or the template requests them. Include meaningful review evidence and explain non-routine validation where it helps assess a material risk.
- **Group genuinely pending actions and questions under `## Open items`.** Omit the section when none remain, unless the template requires it. Order items by when the reader must act: before merge, at merge, then after merge. Use unchecked Markdown checkboxes (`- [ ]`) for every pending item. Use category tags only when they help distinguish responsibilities or timing. Preserve actual user-authored checkbox states. Do not accumulate resolved decisions, rejected alternatives, or speculative ideas as completed checklist items; put any still-relevant rationale in the affected explanation. Preserve actual user-authored content as described in step 9.
- Never use emojis in the title or body. Keep the tone professional and matter-of-fact — no exclamation marks, no marketing language, no celebratory phrasing
- **Always hyperlink references.** Never write a bare ticket key, PR number, commit SHA, or URL-looking string as plain text. Convert it to a markdown link:
  - Linear/Jira-style tickets (e.g. `PLA-150`, `ABC-1234`): link to the ticket. If the repo's existing PRs or README reveal the tracker URL (e.g. `https://linear.app/<org>/issue/PLA-150` or `https://<org>.atlassian.net/browse/PLA-150`), use that base. If unknown, ask the user once for the tracker base URL and reuse it for the rest of the body.
  - GitHub PRs/issues in the same repo: use `#123` shorthand (GitHub auto-links it) or a full URL for cross-repo references like `owner/repo#123`.
  - Commit SHAs: link to the full GitHub commit URL, or use the `org/repo@sha` shorthand which GitHub auto-links.
  - Any other URL: render as `[descriptive text](url)`, not as a bare URL.
  - If a reference appears multiple times in the body, link it on first mention; subsequent mentions can be plain.
- If the repo's template has its own structure or conventions, follow those instead of the writing guidelines above (but the no-emoji and professional-tone rules still apply)
