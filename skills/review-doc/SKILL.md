---
name: review-doc
description: Review a technical document (RFC, solution design, process doc, policy, etc.) for audience fit, substance, writing style, grammar, structure, scannability, duplication, cross-references, and heading quality. Produces a structured review with findings ranked by severity and category, plus concrete edits. Use when the user asks to review a doc, check a doc's writing, or mentions "review this RFC/design/doc".
---

# Review a technical document

You are reviewing a markdown document for **internal consistency, clarity, and a clean reading experience**. The goal is not to rewrite the author's ideas — it's to catch friction that breaks the reader: drifting tone, vague headings, duplicated information, broken cross-references, and grammar defects.

## How to invoke

The user **must** provide the document path as the skill argument. The path is mandatory.

- If the user invokes this skill with no argument, respond with: *"This skill needs a file path. Run it as `/review-doc <path-to-doc>`."* and stop. Do not guess, do not ask follow-up questions about which doc, do not pick a doc from the working directory.
- Read **only** the file the user provided. Do not read sibling docs, style guides, README files, parent directories, repository configuration, or any other context. The review is grounded entirely in the single target file.
- If the file does not exist or is not a markdown / text document, say so plainly and stop.

## Procedure

1. **Read the target doc in full.** Do not skim — review quality depends on seeing the whole structure. This is the only file you read.
2. **Detect the genre** from the doc's content and shape. Style rules differ by genre:
    - **RFC / proposal** — argumentative, opinionated. Proposes a decision; frontmatter and cross-references expected.
    - **Solution / technical design** — RFC-shaped but implementation-focused. Goals, requirements, proposed solution.
    - **Way-of-working / process** — procedural voice, checklists, expectations.
    - Anything else → treat as general technical prose and apply the universal checks only.
3. **Run the review checklist below.** Tag each finding with a severity and a category, then cluster similar findings into groups. Conventions (em-dash spacing, Oxford comma, heading hierarchy) are checked for *internal consistency within the doc*, not against any external reference.
4. **Produce the output in the format at the end of this skill** — grouped by finding type, sorted by severity then category.
5. **Never edit the file.** The review is read-only. Even after the user sees the review, you must wait for explicit approval before touching the file — and you must show the planned edits before writing. No automatic application under any circumstances.

## Severity scale

Each severity has a **letter prefix** used in finding IDs (see Output format). Findings become addressable as `A1`, `A2`, `B1`, etc., so the user can say things like `apply A1-3, B2, C4`.

- **A — Blocker** — breaks the reading experience, misleads the reader, or makes the doc factually wrong. Must fix before shipping.
- **B — Major** — significantly degrades readability, consistency, or trust. Should fix.
- **C — Minor** — noticeable friction, worth fixing when convenient.
- **D — Nit** — preference or judgment call. Author decides.

## Categories

Every finding gets one of these tags. Categories help the author batch the edit pass.

- **Structure** — heading hierarchy, section order, frontmatter, missing or misplaced sections.
- **Style & grammar** — tone, voice, typos, acronyms, terminology, punctuation, weasel phrases.
- **Scannability** — paragraph density, bold-lead bullets, tables, heading descriptiveness, list choice, TL;DR / opening clarity.
- **Substance & clarity** — audience calibration, expert blindness, trade-off honesty, unexplained jargon.
- **Duplication & cross-references** — repeated content within the doc, broken in-doc anchors, broken section numbers, rotting URLs.

## Review checklist

Apply everything in *Universal* to every doc. Apply the genre sections only to that genre. Each finding must name a location (line number, line range, or section) and a concrete fix, not vague advice.

### Universal — writing style and grammar

- **Typos, duplicate words, and broken sentences.** Flag with line numbers. Do not fix silently.
- **Tone drift.** Engineering docs are direct and concrete. Flag colloquialisms, hedges without purpose ("simply", "easily", "just", "basically"), and marketing voice ("leverage", "robust", "seamless").
- **Voice consistency within the doc.** A doc that opens imperative ("Run the command…") should not switch to descriptive ("The operator then runs…") mid-document.
- **Active voice by default.** Passive is fine for genuine emphasis on the object, but not as padding ("It is recommended that you…").
- **Em dash vs hyphen vs en dash.** Use em dash `—` for asides, hyphen `-` only for compound words and bullets. Flag `- ` used as an aside separator when `—` is meant. Whatever spacing convention the doc starts with (with or without surrounding spaces) must hold throughout — flag drift.
- **Acronyms.** Expand on first use, then reuse the short form. Flag unexpanded acronyms.
- **Terminology.** Capitalize proper nouns consistently within the doc. Flag inconsistent casing of the same term across the doc.
- **Brand and product names.** Use one spelling and casing throughout the doc. Flag drift between occurrences.
- **Weasel phrases and filler.** "in order to" → "to". "at this point in time" → "now". "it should be noted that" → cut.
- **Oxford comma.** Pick one convention (use it or don't) and apply it consistently throughout the doc. Flag mixed usage.

### Universal — structure and scannability

- **Descriptive headings.** A reader should be able to scan ONLY the headings and get the gist. Flag generic headings ("Overview", "Background", "Notes", "Details", "Information"). Suggest a concrete replacement that names the actual content.
- **Heading depth.** Do not skip levels (`##` → `####` is a defect). Whatever top-level convention the doc uses (`#` or `##`) must hold throughout — flag mid-doc shifts.
- **Opening clarity.** The first paragraph should let the reader state the doc's core ask, outcome, or purpose in one sentence. Flag openings that bury the point behind preamble, history, or context.
- **TL;DR for long docs.** For docs roughly over 150 lines or with a lot of nested detail, flag if there is no explicit short summary at the top (TL;DR, Summary, In brief). Three to five bullets or two sentences is enough.
- **Paragraph length.** Walls of text break scannability. Flag paragraphs over ~6 lines that aren't deliberately dense prose.
- **Bold-lead bullets.** For bullets that list distinguishable items (options, risks, problems), prefer `**Lead phrase.** Explanation.` over undifferentiated prose bullets. Flag dense bullet lists that would read better with bold leads.
- **Tables for contrasts.** Two-column comparisons (before vs after, active vs legacy, pros vs cons) read better as tables. Flag long paired-bullet sections that should be a table.
- **Numbered lists only when order matters.** Steps, rankings, sequences — numbered. Options, risks, examples — bulleted.
- **Code blocks have language tags.** Triple-backtick fences should name the language.

### Universal — audience and substance

- **Audience calibration.** Is the target reader named or clearly derivable from the opening? Flag docs where the audience is ambiguous — where a new hire, a senior engineer, and a non-technical stakeholder would all read it but only one of them is served. Fix: add a one-line "Audience:" note at the top, or rewrite the opening to make the reader visible.
- **Expert blindness.** For each instruction, claim, or piece of guidance, can a competent outsider execute or follow it without the author's tacit knowledge? The test is *"would a capable engineer who joined three days ago get stuck here?"* Flag steps that assume access to private channels, undocumented tools, or in-head context; flag claims whose justification lives only in the author's head. Fix: inline the missing link, add the missing prerequisite, or cite where to find what was assumed.
- **Trade-off honesty.** When the doc advocates for a choice, change, approach, or process, does it acknowledge the real costs and failure modes proportional to the benefits? Flag one-sided arguments: long Pros list with a thin Cons list, Risks sections that only list mitigations-of-strawmen, procedures whose downsides are hand-waved. This applies to any advocating doc, not just RFCs — a runbook's trade-offs are procedural risks, a design's are architectural compromises, a process doc's is the friction it adds.
- **Jargon without definition.** Terms that are common within the author's sub-team but not across the broader audience should be defined or linked on first use, even when they're not acronyms. Flag un-defined internal project names, product-specific nouns, and domain-specific verbs.

### Universal — duplication and cross-references

- **Duplicate information within the doc.** If a fact, rationale, or rule appears in more than one place inside this file, keep the canonical statement in one section and replace the duplicate with a cross-reference. Flag every duplication with both locations.
- **Cross-reference format.** Pick one style per doc and stick with it. Flag inconsistent styles within this doc.
- **Broken in-doc anchors.** Every `#anchor` whose target should be in this file must resolve to an actual heading in the doc. GitHub slugifies headings as: lowercase, spaces to hyphens, non-alphanumerics stripped (except hyphens). Verify each in-doc anchor matches its target heading. **Do not attempt to verify external links (URLs to other repos, files, or sites) — that requires reading outside the doc.**
- **Broken section numbers.** If the doc uses `### 1.`, `### 2.`, `### 4.`, flag the missing `§3`. If body text references `§N <name>` but the actual section is `§M <name>`, flag it.
- **Rotting URL patterns.** Flag commit-SHA permalinks (e.g. `github.com/.../blob/<sha>/...`) and suggest swapping to a default-branch or tagged link. This is a pattern check on the URL string, not a fetch — do not follow the link.

### Genre-specific — RFCs and proposals

- **Frontmatter.** Expected fields typically include: published date, authors, decision-makers, status (with lifecycle), and a link to the resulting decision record once made. Flag missing or incomplete frontmatter against this baseline.
- **Top-level sections.** Expected shape typically includes: motivation / need, proposal, alternatives, risks, open questions, references. Flag missing sections against this baseline; do not invent ones the doc didn't promise.
- **Pros/cons bullets** under each proposal and alternative — concise, not essays.
- **Contrast patterns** (current state vs proposed state) work well for example sections; recommend them when the doc has concrete scenarios.
- **Negative framing done well** ("This is not *X*") clarifies scope. Allow and preserve.

### Genre-specific — solution / technical designs

- **Frontmatter**, mirroring RFC-style metadata (date, author, status). Flag if missing.
- **Expected shape** typically includes: background, problem, goals, non-goals (where relevant), requirements, proposed solution, impact on existing systems, risks / open questions. Flag missing sections against this baseline.
- **Avoid repeating requirement bodies under Proposed Solution.** Reference requirements by ID instead. This is the most common duplication pattern in design docs.
- **Heading depth consistency.** Do not jump levels.

### Genre-specific — way-of-working / process docs

- **Purpose sentence up top.** One sentence naming the audience and what the doc governs.
- **Checklists over prose** for actionable gates.
- **Imperative voice** for instructions ("Run the command", not "The operator runs the command").
- **Stable links.** Flag commit-SHA permalinks; suggest default-branch or tagged links.
- **Stale registries.** Ownership lists, team rosters, and membership maps rot fast. Recommend linking to an external source of truth rather than duplicating in a doc.

## Output format

Do not emit one bullet per finding. **Cluster similar findings into groups**, one row per group, with one concrete example. The author reads the pattern, not every instance.

Sort groups by severity (Blocker → Major → Minor → Nit), then by category, then by instance count descending. Keep groups tight — one sentence of description, one example, one list of other affected locations.

### ID scheme

Every group gets an ID of the form `<LETTER><NUMBER>`, where the letter is the severity (A=Blocker, B=Major, C=Minor, D=Nit) and the number is its position within that severity, counting from 1. This makes groups addressable: `A1`, `A2`, `B1`, `C3`, `D1`. Keep IDs dense (`A1, A2`, not `A1, A3`).

### Shape

Emit three tables: a metadata header, a group legend, and a findings list. The legend lets the reader scan the patterns at a glance; the findings list is where the fixes live. The ID column ties the two together.

```
## Review: <doc path>

| Field | Value |
|---|---|
| **Genre** | <detected genre> |
| **Verdict** | <ships as-is \| needs light polish \| needs structural work \| needs a rewrite> |
| **Groups** | <N total (A:x, B:y, C:z, D:w) · M instances> |

### Groups

| ID | Sev | Category | Pattern |
|---|---|---|---|
| A1 | Blocker | <category> | <short pattern name> |
| A2 | Blocker | <category> | <short pattern name> |
| B1 | Major | <category> | <short pattern name> |
| C1 | Minor | <category> | <short pattern name> |
| D1 | Nit | <category> | <short pattern name> |

### Findings

| ID | Loc | Current → Fix |
|---|---|---|
| A1 | L<loc> | `<current>` → `<fix>` |
| A1 | L<loc> | `<current>` → `<fix>` |
| A2 | L<loc> | `<current>` → `<fix>` |
| B1 | L<loc> | `<issue>` → `<fix>` |
| C1 | <section> | `<issue>` → `<fix>` |
| D1 | L<loc> | `<issue>` → `<fix>` |
```

**Formatting rules:**
- Sort by severity (A → D), then by category, then by instance count descending.
- In the Groups table, omit severities that have zero groups (e.g. skip Nit rows entirely if nothing is a Nit). Do not keep the header row in isolation.
- In the Findings table, keep rows for the same ID together. Repeat the ID on every row — do not elide it.
- One group per *kind* of issue, not per *location*. All generic-heading problems are one group; all weasel phrases are one group.
- If a group has >5 instances, list the 5 most illustrative and add a final row `| <ID> | — | …plus N more similar |`.
- Use backticks around literal text (headings, phrases, anchors) so the diff is obvious.
- Keep the **Pattern** cell short (≤8 words). The detail lives in the Findings rows.
- Never exceed ~10 groups total. If the doc needs more, the verdict is `needs a rewrite` — say so instead of drowning the author.

### Close with

```
### Apply?

Tell me which IDs to fix — e.g. `apply A1, A2, B1`, `apply A1-3, C2`, `apply all blockers`, `apply all`, or `skip`. I won't touch the file without your go-ahead and I'll show the planned diff before writing.
```

Then stop. Wait for the user's response.

### Interpreting the user's apply request

- `apply A1-3` → groups A1, A2, A3.
- `apply A*` / `apply all blockers` → every A group.
- `apply A1, C2` → exactly those two groups.
- `apply all` → every group across every severity.
- `apply A1 except L205` → the group minus a specific instance.
- If ambiguous, ask — don't guess.

## Review tone

Be direct and specific. "L42: duplicate word 'the the' → delete one" not "there might be a typo around L42". "Replace 'Background' with 'Why this matters now'" not "consider a more descriptive heading". Vague feedback wastes the author's time.

Flag issues you're confident about. When a call is judgment, tag it `Nit` and let the author decide.

**Never rewrite the author's argument.** You're a copy editor, not a co-author.

**Never write to the file without explicit user approval.** The review step is read-only. Even on approval, show the planned edits before applying. If in doubt, ask.
