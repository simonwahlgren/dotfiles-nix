---
name: sdlc-create-tickets-from-plan
description: Create or update an umbrella Linear ticket plus per-phase sub-issues from a phased implementation plan. Use whenever the user wants to turn a plan into Linear tickets — phrases like "create tickets from this plan", "open Linear issues for these phases", "make an umbrella ticket and subtickets", "split this plan into Linear", or any time a phased/multi-step plan has been produced (e.g. by the make-plan skill) and the next step is to track it in Linear. Also use when refreshing an existing umbrella to reflect a revised plan.
disable-model-invocation: false
user-invocable: true
argument-hint: "[path to plan file or short description]"
---

# Create SDLC tickets from a plan

Turn a phased implementation plan into a Linear **umbrella ticket** plus one **sub-issue per phase**. Modelled on the PLA-150 family of tickets — the umbrella owns the problem framing and the deployment-plan table; each sub-issue owns one slice of the work.

If `$ARGUMENTS` is provided, treat it as either the path to a markdown plan file or a short hint about which plan to use.

## Mental model

There are up to four artefacts in play, and they each own a different layer:

1. **Solution design doc** (optional, usually for larger features — often warrants a Linear project too). Lives in Google Docs, Notion, or similar. Long-form, ~design-review-grade. If one exists, the umbrella *links* to it; the umbrella does not duplicate it.
2. **Plan** (markdown file, doc, or in-conversation outline). Source of truth for *How* — files to touch, commands to run, technical sequencing. Local to the engineer, not version-controlled or attached to the ticket. Do **not** assume the plan is published anywhere, and never reference it from a ticket — no link, no plain-text path or filename. The tickets must stand on their own; the plan is consulted later, at implementation time, for the detail they deliberately omit.
3. **Tickets** (this skill's output). Carry **Why** (the problem and motivation), **What** (the outcome and the phase breakdown), and — in the umbrella — a **high-level architecture sketch** showing the shape of the end state. Sub-issues stay thinner; only the umbrella carries the architecture sketch.
4. **PRs**. Source of truth for the actual diff and implementation detail.

Keeping tickets thin matters because they get read by people who aren't doing the work — stakeholders, reviewers checking status, your future self months later. Dense kubectl snippets and Terraform paths in a ticket body rot fast and bury the thing the reader actually came for: *what problem is this solving, and where is it in the sequence*.

## Steps

1. **Locate the plan.** In order:
   1. If `$ARGUMENTS` looks like a path and the file exists, read it.
   2. Otherwise search the current working directory for a likely candidate (`plan.md`, `PLAN.md`, `docs/plan*.md`, anything with `plan` in the name modified recently). If exactly one fits, use it; if several, ask which.
   3. Otherwise treat the most recent assistant turn in this conversation as the plan — common when the user just ran `/make-plan` or sketched a plan inline.
   4. If you still can't find one, ask the user to point you at it.

   **While reading the plan, capture the umbrella reference if it has one.** Plan files often have a `Linear: <url>` line near the top pointing at the umbrella ticket (or the ticket the plan was started from). Grab the ticket key from that URL — it's the single most reliable signal for step 6 and matters for re-runs. If the plan file has a name like `pla-86-foo.md`, that's a weaker hint pointing at the *original* ticket (which may have been superseded); treat the `Linear:` line as authoritative when present.

2. **Ask about a solution design doc.** Before drafting, ask the user once: *"Is there a solution design doc (Google Doc, Notion, etc.) for this work? If yes, paste the link and I'll include it in the umbrella."* Bigger features sometimes have one drafted before the tickets — when it exists, the umbrella links to it instead of re-explaining the design. Don't assume one exists; don't invent a link. If the user says no, move on.

3. **Parse the plan into umbrella + phases.** Extract:
   - **Title** for the umbrella — a short verb-first summary of the whole change.
   - **Context / problem statement** — what's broken or missing, in user/business terms.
   - **Why this approach** — the reasoning behind the chosen direction, especially anything non-obvious (sunset tools, platform constraints, prior incidents).
   - **High-level architecture** — a sketch of the end state. Default to **always include this** in the umbrella; it's how a reader new to the work sees the shape of the change in one glance. Acceptable forms: a short directory-tree sketch (with one-line "← what this is" annotations), a small box-and-arrow diagram, or a paragraph naming the new and renamed pieces and how they relate. **Skip the section only when a solution design doc exists** — then add `## Solution design` with a link to the doc instead. Implementation-level detail still doesn't belong here: no commands, no step-by-step, no code snippets, no per-file diff descriptions. Names of directories, modules, files, and key fields *are* fine because they communicate shape, not steps.
   - **Phases** — the discrete units of work the plan calls out. Each phase becomes one sub-issue. Capture for each: a short title, the *purpose* (one or two sentences), the *done definition* (a few bullets — what observable thing is true when it's finished), and any *prerequisites* (which sibling phase must land first, if sequencing matters).
   - **Out of scope** — anything the plan explicitly excludes.

   If the plan doesn't cleanly decompose into phases, ask the user how they want to slice it before going further. Don't invent phases.

4. **Pick the Linear team.** Use the Linear MCP `list_teams` to enumerate. Infer from:
   - The current working directory's repo name (e.g. a `fyndiq/*` or `platforms/*` repo on the Platform team).
   - Any team key mentioned in the plan itself (e.g. `PLA-` prefix → Platform).
   - The team of the most recent issue assigned to the current user (`list_issues` filtered by assignee).

   If there's a single confident match, state it and proceed. If ambiguous, ask once.

5. **Resolve the assignee.** Default to the current user (`simon.wahlgren@cdon.com`). Use `list_users` filtered by email to get the user ID. Apply the same assignee to umbrella and every sub-issue.

6. **Find the existing umbrella, if any.** Look in this order — first match wins:
   1. The `Linear:` URL captured from the plan in step 1.
   2. `$ARGUMENTS` if it names a ticket key like `PLA-150`.
   3. `list_issues` against the chosen team, filtered by the proposed umbrella title.

   If a candidate exists, read it with `get_issue` and `list_issues(parentId=...)` to get its current sub-issues. **Now decide: refresh in place, or supersede?**

   - **Refresh in place** — when the existing ticket's Context and title still substantively describe the work the plan proposes. This is the case for any normal re-run on an updated plan: the umbrella is the right umbrella, you just need to bring its description and sub-issues in line with the new plan.
   - **Supersede with a new umbrella** — when the existing ticket's framing is stale, vague, or covers a different problem from what the plan now addresses. See the *"Existing ticket: refresh, or supersede?"* section below for the full decision.

   When uncertain, **ask the user** before committing. The cost of asking is one sentence; the cost of overwriting an in-flight ticket's framing is real.

7. **Draft the ticket bodies.** Compose markdown for the umbrella and each sub-issue using the templates below.

8. **Show a dry-run preview and wait.** Print to the conversation:
   - The Linear team and assignee that will be used.
   - Whether you're creating a new umbrella or refreshing an existing one (and which).
   - The umbrella ticket title + full proposed description.
   - Each sub-issue title + full proposed description.
   - For a refresh, the diff against existing tickets (what's new, what's changed, what's untouched).

   Then **stop and wait** for explicit approval. This skill writes to a shared external system, so each create or update needs its own approval.

   - **Do not suggest exact phrasings in the wait prompt.** Don't say "reply with X to proceed" or "name the action — e.g. <verb>", because users sometimes quote the example back as a clarification rather than as an authorisation. Just say "I'll stop here and wait for your go-ahead before creating anything in Linear", and let the user phrase their own approval.
   - **What counts as approval:** an unambiguous, user-originated instruction to create or update the tickets in Linear. Bare "yes", "looks good", "approve", or a phrase the user is clearly *echoing back* from your own preview (e.g. responding to "name the action" with the example you offered) do not count. If you're at all unsure whether a reply is authorisation or clarification, ask: "Just to confirm — should I create these in Linear now, or are we still iterating on the draft?"
   - **What does not count even after several rounds of edits:** prior approval for a different draft. If the user revised the preview, the new draft needs its own approval.

9. **Create or update in Linear.** On approval:
   1. Create or update the umbrella issue first (you need its ID to set `parentId` on any new children).
   2. For each sub-issue, take the right action per the refresh buckets:
      - *Untouched*: do nothing.
      - *Body / title update*: `save_issue(id=..., description=..., title=...)`.
      - *New phase*: `save_issue(team=..., assignee=..., parentId=umbrella, ...)`.
      - *Terminal-state or orphaned*: do nothing.
   3. Update the umbrella description's phase table with the real sub-issue keys + URLs once any new children exist. (On a first run the table started with `TBD` placeholders; on a refresh the table is rebuilt from scratch using the reconciled keys.)
   4. **If the plan was read from a file, offer to write or update a `Linear:` line at the top pointing at the umbrella key.** This applies to every create *and* every supersede — not just supersedes. The `Linear:` line is what makes future re-runs deterministic: without it, step 6 falls back to title-matching, which silently misses when the umbrella title has drifted from the plan and proposes a duplicate umbrella instead of refreshing the right one. Ask before editing — the plan file may be tracked in git and the user may want to commit the change themselves. Skip this if the plan came from the conversation rather than a file.

10. **Report back.** Print the umbrella URL and each sub-issue URL as a markdown list, in phase order. Nothing else — the user can click through.

## Umbrella ticket template

```markdown
## Context

<2–4 short paragraphs framing the problem. What's broken / missing / wrong today, in user or business terms. Include the prior incident, the upstream sunset, the platform mismatch, etc. — the *reason* the work needs doing. No file paths, no commands, no module names.>

### Why <chosen approach>

<Numbered list, 2–5 items, each one short. The non-obvious reasons this is the right direction: tool lifecycle, platform-native, already-enabled, removes a class of bug. One sentence each; this is the section that justifies the whole umbrella.>

<One of the following two sections is required:>

<## Solution design — when a design doc exists>

<Include this when the user has a solution design doc. One line: "See [solution design](url) for the full design." Then omit the High-level architecture section below — the doc covers it.>

<## High-level architecture — when no design doc exists>

<Include this whenever there's no solution design doc. This is required, not optional — the umbrella's job is to give a reader the shape of the end state in one glance.>

<Acceptable forms:>
<- A small directory-tree sketch with one-line "← what this is" annotations, naming the new and renamed pieces.>
<- A short box-and-arrow diagram describing roles ("shared team-metadata source feeds GitHub CODEOWNERS, Datadog Service Catalog, future Sentry teams").>
<- A paragraph naming the components and how they relate.>

<What belongs: names of directories, modules, files, and key fields — these communicate shape. What doesn't belong: commands, step-by-step instructions, code snippets, per-file diffs, or anything a PR will own.>

<Optional: ## Supersedes>

<Include this section only when this umbrella replaces an older ticket whose framing has gone stale. One or two sentences: "Supersedes [OLD-KEY](url) — original framing was X; this umbrella covers Y that emerged once we started planning.">

---

# Deployment plan

This umbrella ticket tracks the end-to-end change. Each phase is its own sub-issue; this ticket stays open until **every** phase sub-issue is Done.

<If phases must run in order, say so explicitly: "Phases run strictly sequentially — do not start a phase before the previous one has validated cleanly." Otherwise drop the sentence.>

| # | Phase | Type | Ticket |
| -- | -- | -- | -- |
| A | <phase A title> | <PR / Ops / Ops gate> | <linked sub-issue> |
| B | <phase B title> | <…> | <linked sub-issue> |
| … |

Each phase sub-issue carries its own done definition and any prerequisites. Refer to the individual sub-issue — duplicating the detail here would just rot.

## Out of scope

- <Anything the plan explicitly excludes — sibling clusters, non-preview traffic, other environments, etc.>
- <One bullet per exclusion. Be specific so the umbrella can't quietly grow scope.>
```

**Notes on the template:**
- The phase **Type** column distinguishes PR work, ops runbooks, and ops gates (wait-and-verify steps). Use whatever vocabulary the plan uses; the column exists so a reader scanning the table immediately sees which phases produce code vs. which produce a checklist.
- Link sub-issues with Linear's native `<issue id="..." href="...">KEY</issue>` syntax — that's what makes them render as live status pills in the Ticket column, so the table shows each phase's status without a separate column. The Linear MCP renders this automatically when you paste a normal markdown link to a Linear URL, but the explicit `<issue>` tag is more robust.
- No Status column — status is owned at the sub-issue level and surfaces through the linked ticket's status pill. Don't add one.

## Sub-issue template

```markdown
## Parent

<linked umbrella issue> — <umbrella title>

## What

<One or two sentences: the outcome this phase delivers. Not the steps — the result. "By the end of this phase, X is true.">

## Done when

- <Observable thing #1 — something a reviewer could verify without reading the diff.>
- <Observable thing #2.>
- <Observable thing #3.>

<3–6 bullets. Resist the urge to write commands or file paths. "DNS resolves to the new IP" beats "Cloudflare A record updated via `cf-terraforming`".>

<Optional sections, include only when they carry weight:>

## Prerequisites

- <Sibling phase or external event that must land first. Link the ticket.>

## Out of scope

- <Things a reader might assume are part of this phase but aren't.>
```

**Notes:**
- Sub-issue bodies should fit on one screen. If a section starts running long, it's almost always implementation detail that belongs in the plan or the PR, not the ticket.
- No code blocks, no kubectl/gcloud/terraform snippets, no file paths. Those rot the moment the implementation diverges from the plan.
- "Done when" should describe the *world after the phase*, not the steps that produced it. A future reader who never saw the plan should be able to tell whether the phase succeeded just by reading these bullets.

## Writing guidelines

These mirror the pr skill's style — same project, same audience.

- **Why and What, not How.** The plan owns the How. The PRs own the diff. The ticket exists to tell a reader *what problem this solves* and *where this fits in the sequence*. If a sentence in the body could be replaced by reading the plan, cut it.
- **Be extremely concise. Sacrifice grammar for the sake of concision.** Drop articles, drop linking verbs, drop hedges. Sentence fragments are fine when they're clearer. The umbrella should read in a couple of minutes; a sub-issue should fit on one screen.
- **No hard-wrapping.** One line per paragraph or bullet. Linear renders prose with soft wrap; manual line breaks just produce ugly edit diffs.
- **No blank lines between bullets in the same list.** Loose lists render with extra vertical space and waste the reader's eye.
- **Always hyperlink references.** Never write a bare ticket key, PR number, commit SHA, or URL as plain text. Link Linear tickets to their `https://linear.app/<org>/issue/<KEY>/...` URL, GitHub PRs/issues to their full URL or `owner/repo#123`, commits to their GitHub URL. If a reference appears multiple times in a body, link it on first mention only.
- **No emojis. No marketing tone.** Matter-of-fact, professional. No exclamation marks, no celebratory phrasing.
- **Avoid these common verbosity traps — in any ticket body:**
  - Command snippets (`kubectl`, `gcloud`, `terraform`) — these belong in the plan or PR.
  - Step-by-step instructions or per-file diff descriptions.
  - Code snippets and full module/file contents.
  - Restating context the parent umbrella already covers.
  - Sections like "Implementation notes", "Notes for reviewers", "How it works".
- **Sub-issues stay thinner than the umbrella.** In a sub-issue body, also avoid: directory trees, file paths, module names, function names. The umbrella owns the architecture sketch; a sub-issue body should be one paragraph of *what outcome* and a short list of *done when*. If a sub-issue needs to refer to a specific module by name, do it inline ("the GitHub repo module learns to synthesise CODEOWNERS"), not as a tree or path.
- **Reference only durable artefacts:** solution design docs, source-data sheets, runbooks committed to the repo, upstream issues, and other Linear/GitHub tickets. Never the local plan file (see *Mental model*).
- **Don't duplicate the umbrella's framing into every sub-issue.** A sub-issue should add value over the umbrella, not repeat it. Two or three lines under "## Parent" pointing at the umbrella is enough.

## Mapping plan structure → ticket structure

Plans from `/make-plan` (and similar) commonly use one of these shapes. Map them like this:

- **Numbered phases (Phase 1, Phase 2, …)** — one sub-issue per phase. Title each sub-issue `Phase N — <phase title>`. The umbrella's deployment-plan table uses `1, 2, 3 …` (or `A, B, C …` if the plan does) as the `#` column.
- **Discrete deliverables with no ordering** — still one sub-issue per deliverable, but drop the sequential-execution language from the umbrella's "Deployment plan" intro and use a bullet list instead of a table if there are only 2–3 items.
- **A single big task that doesn't decompose** — don't force a split. Tell the user the plan looks like one ticket's worth of work and offer to create a single issue instead of an umbrella + children. Confirm before proceeding.
- **A plan that mixes phased work with one-off side tasks** — phased work becomes the umbrella + numbered sub-issues; side tasks become *related* sub-issues (also `parentId = umbrella`, but called out in a separate "## Related sub-issues (outside the phase sequence)" section in the umbrella, mirroring PLA-150).

## Existing ticket: refresh, or supersede?

Step 6 decides between two paths. The decision matters because the wrong call leaves stale framing on a live ticket — confusing for everyone who reads it later.

**Refresh in place** when the existing ticket's Context and title still substantively describe the work the plan proposes. A scope nudge (new phase added, target architecture refined, an exclusion clarified) is a refresh. The work is the same work; the ticket just needs to catch up.

**Create a new umbrella and supersede the old one** when any of these are true:

- The original ticket's framing was a vague idea — "we should look at X" — not a thought-through problem statement.
- The plan's chosen solution is materially different from what the original ticket implied.
- The plan covers a narrower slice of the original problem (one of several concerns the original lumped together), and the rest of the original may still be valid.
- The plan covers a *different* problem that emerged when someone tried to think the original through.

In all of these, refreshing the existing ticket would force the new plan to live under a framing it doesn't fit. Better to leave the old ticket as a historical artefact, write a fresh umbrella that matches the actual work, and add a short *Supersedes* reference so the trail is clear.

**When uncertain, ask.** "I found [OLD-KEY](url) which looks related but the framing has shifted — do you want me to refresh it in place, or create a new umbrella and reference it?" The user knows the political/historical context better than the skill does.

### Refresh-in-place mechanics (the re-run case)

This is the path the skill takes every time you re-run it on an updated plan. The umbrella exists, some sub-issues exist, the plan has shifted — the skill's job is to diff the new plan against the current ticket state and reconcile.

**Matching plan phases to existing sub-issues.** List the umbrella's children with `list_issues(parentId=<umbrella>)`. For each phase in the new plan, find its matching sub-issue using this priority:

1. **Exact title match** on the sub-issue's title (after stripping the `Phase N — ` prefix on both sides). This is the strongest signal.
2. **Phase-number match** (`Phase 1`, `Phase 2`, … or `Phase A`, `Phase B`, …) when titles have drifted but the position in the sequence hasn't. Strong, but flag any number-matched pair whose titles look meaningfully different — the user may have actually reordered phases, not just renamed.
3. **Fuzzy title similarity** (substantial word overlap, e.g. "Rename Datadog Agent units" ↔ "Phase 1 — Rename existing Datadog Agent units to free the `datadog` namespace") for cases where both number and exact title have drifted. Treat this as a *suggestion* — surface the proposed pairing in the dry-run and let the user confirm.
4. **No match** — the phase is new, or the sub-issue is orphaned. Both cases are surfaced separately below.

After matching, every plan phase falls into one of four buckets and every existing sub-issue falls into one of three. Surface all of them in the dry-run preview:

| Bucket | Action |
| -- | -- |
| Phase matched, sub-issue body unchanged | No-op. Note in preview as *"untouched"*. |
| Phase matched, sub-issue body needs update | Show the diff in the preview. On approval, update the sub-issue's description. Skip if the sub-issue's status is `Done`, `In Review`, or `Canceled` — that body is now history; don't overwrite. Surface the skip in the preview so the user knows. |
| Phase matched, sub-issue title needs update | Treat the same as a body update. Title changes are fine for `Backlog`/`Todo`/`In Progress` sub-issues; skip for terminal states. |
| Phase has no match (new phase in plan) | Create a new sub-issue with `parentId = umbrella.id`. Number it according to the plan's sequence — be careful if the renumbering shifts existing sub-issue titles (e.g. if a phase is inserted at position 2, the existing Phase 2 sub-issue title now reads as `Phase 3` in the new plan). Renumbering existing sub-issue titles is allowed but must be shown clearly in the diff. |
| Existing sub-issue has no matching phase in plan | **Never delete or cancel.** Surface in the preview as *"Phase from previous plan no longer present — sub-issue [PLA-XXX](url) left as-is. Cancel manually if intended, or restore the phase to the plan."* Cancelling is a human decision. |
| Existing sub-issue in terminal state (Done/In Review/Canceled) | Skip body and title updates regardless of plan changes; its description is now a historical record. Still include it in the umbrella phase table — its status pill will reflect reality. |

**Rebuilding the umbrella.** After settling sub-issues:

- Rewrite the umbrella's Context, Why, and High-level architecture sections against the current plan. Don't preserve stale framing just because it was there — but don't churn wording that's still accurate either. The aim is *fidelity to the current plan*, not maximum diff.
- Rebuild the phase table from scratch using the current plan's phase list and the reconciled sub-issue keys. Phases run in plan order. The table has no Status column — each linked sub-issue's status pill surfaces its actual Linear status.
- If existing sub-issues are orphaned (bucket 5 above), do **not** include them in the main phase table. Add them to a `## Sub-issues from previous plan iterations` section under the table so the trail is visible.

**Approval after a refresh diff.** The dry-run preview for a refresh is the most important one to land cleanly — there are many small changes, and "looks good" can hide a misread. Be explicit about what will and won't happen, group the changes by sub-issue, and wait for approval of each create or update, as usual.

### Supersede mechanics

When creating a new umbrella in place of an old one:

- Pick a fresh title that reflects the *new* framing, not the old.
- Add a `## Supersedes` section near the top of the umbrella body referencing the old ticket and explaining in one or two sentences how the framing shifted.
- Note in the dry-run preview that the old ticket is *not* being touched by this skill, and surface a recommendation: keep it open if part of its scope is still valid, otherwise the user may want to close it manually with a comment pointing at the new umbrella.
- **After the new umbrella is created, offer to update the plan file's `Linear:` line** to point at the new umbrella key (e.g. `Linear: https://linear.app/<org>/issue/<NEW-KEY>/...`). This is the supersede-specific case of the general rule in step 9.4: every create or supersede that came from a file should leave a `Linear:` line behind so re-runs are deterministic. Supersede is especially important — if the line still points at the superseded ticket, the next re-run will start from the wrong umbrella.

## Worked example

The PLA-150 family is the canonical reference for the format this skill produces:

- Umbrella: [PLA-150](https://linear.app/cdon-ab/issue/PLA-150/migrate-fyndiq-integration-previews-from-ingress-nginx-to-gke-gateway) — Context, Why pivot, Target architecture, Deployment plan table with six phases, Out of scope.
- Sub-issues: [PLA-160](https://linear.app/cdon-ab/issue/PLA-160) (Phase A) through PLA-163 (Phase F) — each one short, each one links back to the parent, each one's body describes outcome rather than steps.

PLA-150 is one illustrative example; where it differs from the templates above, follow the templates.
