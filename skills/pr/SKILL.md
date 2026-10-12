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

     **Preserve-vs-regenerate decision, per section:**
     - **Background** — re-read the existing prose against the current diff. If the user rewrote it manually and it still accurately describes the current branch state, keep their wording verbatim. Only rewrite if scope drifted, motivation changed, or the existing framing is now wrong/incomplete. Never replace user prose with skill-generated prose just because the skill would phrase it differently.
     - **Changes** — rebuild the bullet list from the current diff, but reconcile with the existing list: if a bullet in the existing body still describes behavior in the branch, keep its wording (the user may have edited it). Add bullets for new behavior, remove bullets for behavior no longer in the branch, merge bullets that now describe the same coherent change.
     - **Open items** — treat as user-owned. Preserve every existing item as-is (including any `[x]`/`[ ]` state and any custom prefixes the user introduced). Only mutate items the skill itself originally added, and only if the underlying work has clearly resolved (e.g. a `Post-merge` item the user marked `[x]` stays as the user left it). Append any genuinely new items at the bottom of the appropriate phase group.
     - **Linked tickets / refs** — keep them if still relevant, drop them if the scope no longer touches that work, add new ones if the branch now relates to other tickets. If the user added a ticket link manually, keep it.
     - **Any custom sections the user added** (sections that aren't in the template and weren't generated by the skill) — preserve verbatim. The user added them on purpose.
     - **Stale sections from earlier iterations** (test plan, screenshots, etc.) — drop only if clearly no longer accurate. If unsure, keep.

     **Heuristic for spotting manual edits:** content in the existing body that doesn't map to any commit message, doesn't appear in the diff, and reads like reviewer-context prose (qualifications, caveats, decisions, links to discussions) is almost certainly a manual edit — preserve it. Section headings the skill wouldn't have generated, items with `[x]`/`[ ]` checkbox state changes, and inline notes in parentheses are also strong signals.

     Then compare the regenerated body against the existing one and run `gh pr edit <number> --body "<body>"` if they differ meaningfully. If the branch state is already accurately described and manual edits are preserved, skip the edit. Preserve the title unless the user asked to change it. If `$ARGUMENTS` was provided, treat it as an explicit instruction to update the body (and may override preservation — ask if unclear).

## Writing guidelines

- **Focus on Why and What, not How.** The diff already shows the How — the PR description's job is to give a reviewer enough context to know what to look for. If a sentence in the body could be replaced by reading the diff, cut it.
- **Background**: explain the problem from a user/business perspective, not implementation details. **Lead with the ticket reference.** Start the section with the PR's own ticket key; if the work is one phase of a larger umbrella ticket, say so inline — e.g. `[PLA-228](url) — Phase 1 of [PLA-227](url). <short high-level why/what>`. Keep the inline explanation high-level — reviewers needing detail should follow the ticket links. Derive the ticket(s) from `$ARGUMENTS`, the branch name, or commit messages; if an umbrella/phase relationship isn't evident there, ask the user once rather than inventing one. Hyperlink every ticket key (see the hyperlink rule below).
- **Changes**: each bullet describes a meaningful behavioral change — not a file edit. Use verb phrases ("Add X", "Fix Y", "Remove Z"). Aim for 3-6 bullets. Group related file changes into a single bullet.
- **Be extremely concise. Sacrifice grammar for the sake of concision.** Applies equally to new PRs and to any update to an existing PR. Drop articles (a/an/the), drop linking verbs (is/are/was), drop hedges ("we", "this PR", "in order to"), drop adverbs that don't carry information ("simply", "just", "currently"). Prefer sentence fragments over full sentences when they're clearer. Keep the body readable in about a minute. If you need more than a few short paragraphs, link to the ticket or a design doc instead of inlining it. Examples:
  - Verbose: "This PR replaces the manually-installed nginx ingress controller with the Google-managed GKE Gateway because the old controller has been out of git for over two years."
  - Concise: "Replace manually-installed nginx ingress with GKE Gateway. Old controller out of git 2+ years."
- **Do not hard-wrap lines.** Write each paragraph and each bullet as a single unbroken line — no 80-char wrapping, no manual line breaks mid-sentence. GitHub renders prose with soft wrap; hard wraps just make the body harder to edit and produce ugly diffs when text is revised. Only use newlines to separate paragraphs, list items, or markdown blocks.
- **No blank lines between bullets in the same list.** Bullets in a list go on consecutive lines (one newline between them, never two). A blank line between bullets makes GitHub render the list as loose/spaced-out, which wastes vertical space and makes scanning harder. This applies to every list in the body — Changes, Open items, sub-lists, everything. Only insert a blank line when actually ending the list and starting a new paragraph or heading.
- **Avoid these common verbosity traps:**
  - Code blocks or snippets showing what changed (reviewers read the diff)
  - File-by-file or commit-by-commit walkthroughs
  - "How it works" sections explaining the new code's internal flow
  - Before/after examples that just restate the diff
  - Step-by-step migration or rollout instructions (link to a runbook instead)
  - Restating context the linked ticket already covers
  - Numbered sub-lists of every function, class, hook, or config option touched
  - "Notes for reviewers" paragraphs that re-explain bullets already in the Changes list
- Do NOT list individual files, function names, or variable changes
- Do NOT add sections like "Test plan", "Checklist", or "Screenshots" unless the user asks or the template requests them
- **Keep routine validation in the final chat response.** Do not add test counts, execution summaries, or notes like "Diff checks passed" in or after the Changes section, including standalone "Validation:" paragraphs, unless the user explicitly asks or the template requests them.
- **Group every open thread under a single `## Open items` section.** Anything that's not part of the merged change but the reviewer needs to be aware of — open questions for the reviewer, decisions still being made, things to do at merge time, follow-ups after merge, rejected alternatives kept for context, speculative experiments — goes in one section, never scattered across "Notes", "TODO", "Follow-ups", "Open questions", "Future work", etc. One section keeps the reviewer's scan path linear: read Why, read Changes, read Open items, decide.
  - **Order items by when the reader will act on them**, earliest first: things needed before merge → at merge → after merge → speculative.
  - **Prefix each bullet with a bolded category tag** so the eye can skim. The exact tags are flexible — pick whatever fits the PR — but follow the chronological ordering above. Common ones:
    - `**Decision**` — reviewer input needed, or a choice the author punted on, before merge
    - `**At merge**` — must happen atomically with merge (ruleset edits, flag flips, coordinated deploys)
    - `**Post-merge**` — concrete follow-up scheduled after merge
    - `**Experiment**` — speculative idea, or a rejected alternative kept for context
  - **Use checkboxes to signal item status.** `[x]` when the item is already decided, rejected, or scheduled away (linked ticket, follow-up PR, won't-do with rationale). `[ ]` when it is still open or pending action — including `At merge` and `Post-merge` items the author/reviewer will physically do, and `Decision` items still awaiting an answer. Open questions and experiments still under consideration get `[ ]`; rejected alternatives kept for context get `[x]`.
  - Keep each item to one line where possible; if context is needed, two short sentences. Don't write a paragraph per item.
- Never use emojis in the title or body. Keep the tone professional and matter-of-fact — no exclamation marks, no marketing language, no celebratory phrasing
- **Always hyperlink references.** Never write a bare ticket key, PR number, commit SHA, or URL-looking string as plain text. Convert it to a markdown link:
  - Linear/Jira-style tickets (e.g. `PLA-150`, `ABC-1234`): link to the ticket. If the repo's existing PRs or README reveal the tracker URL (e.g. `https://linear.app/<org>/issue/PLA-150` or `https://<org>.atlassian.net/browse/PLA-150`), use that base. If unknown, ask the user once for the tracker base URL and reuse it for the rest of the body.
  - GitHub PRs/issues in the same repo: use `#123` shorthand (GitHub auto-links it) or a full URL for cross-repo references like `owner/repo#123`.
  - Commit SHAs: link to the full GitHub commit URL, or use the `org/repo@sha` shorthand which GitHub auto-links.
  - Any other URL: render as `[descriptive text](url)`, not as a bare URL.
  - If a reference appears multiple times in the body, link it on first mention; subsequent mentions can be plain.
- If the repo's template has its own structure or conventions, follow those instead of the writing guidelines above (but the no-emoji and professional-tone rules still apply)
