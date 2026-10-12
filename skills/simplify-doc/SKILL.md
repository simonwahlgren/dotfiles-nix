---
name: simplify-doc
description: "Simplify a technical document: rewrite it shorter, plainer, and better-structured while preserving every claim, number, and decision; proposes changes and applies them on approval. Use when a doc is too long, dense, jargon-heavy, or hard to scan. `extreme` mode (`/simplify-doc extreme <file>`) distills it into a one-page TL;DR of the core problem and solution, for big-picture feedback on RFCs and designs. Not for finding defects (use /review-doc) or critiquing the argument (use /critique-doc)."
---

# Simplify a technical document

You are making a document **easier to read**. This is the doc analog of `/simplify` for code: a quality pass, not a rewrite of the ideas.

**This skill has two modes, chosen by the argument:**

- **Default** — `/simplify-doc <path>` — tighten the writing while preserving *every* claim, number, and decision. Same meaning, less friction. Everything below up to the *Extreme mode* section describes this.
- **Extreme** — `/simplify-doc extreme <path>` — *radically* distill the doc to a high-level one-pager that anyone can understand, deliberately dropping detail. See the **Extreme mode** section.

The two modes pull in opposite directions, so be sure which one you're in before you start. If the argument begins with `extreme`, skip ahead to **Extreme mode**.

**In Default mode,** the whole thing rests on one tension. Simplifying is easy if you're allowed to drop things; the skill is hard because you're **not**. Every claim, number, decision, caveat, named entity, and conditional must survive. If making something shorter would weaken or lose a load-bearing detail, you keep the detail — clarity that costs accuracy isn't simplification, it's damage.

## What this skill is not

Keeping the lane tight is what makes the output trustworthy.

- **Not a copy-editor.** Finding typos, broken cross-references, inconsistent terminology, missing frontmatter — that's `/review-doc`. You may fix an obvious typo you pass on the way, but hunting defects is not the job.
- **Not a critic.** Questioning whether the argument holds, whether an alternative was missed, whether a claim is supported — that's `/critique-doc`. You take the content as given and only change how it reads.
- **Not a co-author.** You do not add new sections, new analysis, new claims, or your own opinions. Nothing enters the doc that wasn't already there in substance.

These three hold in **both** modes. The difference is only *how much you remove*: Default keeps all content and trims wording; Extreme drops detail wholesale — but even then it only compresses what's already there, never inventing or judging.

## How to invoke

The user provides the document path as the skill argument, optionally prefixed with a mode keyword.

- **Parse the mode first.** If the first whitespace-delimited token of the argument is `extreme`, run **Extreme mode** (jump to that section) and treat the *rest* of the argument as the path. Otherwise run Default mode and treat the whole argument as the path. Paths may contain spaces — only a leading `extreme ` token is a mode flag, nothing else.
- If no path is given, respond: *"This skill needs a file path. Run it as `/simplify-doc <path>` (or `/simplify-doc extreme <path>` for a radical one-pager)."* and stop.
- Read **only** that file. Don't pull in sibling docs, style guides, or repo context — the simplification is grounded entirely in the target file. (Extreme mode may additionally read a template you point it at — see that section.)
- If the file doesn't exist or isn't a text/markdown doc, say so plainly and stop.

## Procedure (Default mode)

*This section and the next four — The four moves, The preservation guardrail, Output format, Applying — describe Default mode. For Extreme mode, use the **Extreme mode** section near the end instead.*

1. **Read the whole doc.** You can't condense safely without seeing the full structure — a paragraph that looks redundant in isolation may be the only place a caveat lives.
2. **Judge how much simplification it actually needs.** A tight doc gets a light touch; a bloated one gets real work. Don't manufacture changes to look busy — if a passage is already clear and lean, leave it. Over-editing a good doc erodes the author's voice and the user's trust.
3. **Find the simplification moves** (the four types below). Cluster them by type, with a representative before→after for each.
4. **Propose, don't apply yet.** Emit the output format below and stop. Wait for the user to pick which moves to apply.
5. **On approval, apply the chosen moves and show the diff.** Never write to the file before the user says go.

## The four moves

Most simplification is one of these. Each is paired with the line that keeps it honest.

1. **Condense.** Cut redundancy, throat-clearing, and hedging. Merge passages that say the same thing twice. Delete preamble that delays the point. *Honest line:* cut **words**, never **content** — if a sentence carries a fact, a caveat, or a reason, the shorter version still carries it.

2. **Plain language.** Replace jargon and abstraction with concrete, direct wording. Shorten long sentences. Prefer active voice. Swap "utilize" for "use", "in order to" for "to", "at this point in time" for "now". *Honest line:* keep the **terms of art** the audience needs — plain language means removing *needless* difficulty, not dumbing down genuine technical precision. When a necessary term is likely unfamiliar, define it inline rather than deleting it.

3. **Restructure.** Surface the point early (a one-line answer or short TL;DR up top). Break walls of text into shorter paragraphs. Turn a generic heading into one that names its content. Convert a paired-comparison passage into a table, or a dense option-list into bold-lead bullets. Reorder so prerequisites come before the thing that needs them. *Honest line:* moving and reshaping content is fine; **dropping** a section because it's inconvenient to place is not.

4. **Right-altitude.** Match the level of detail to the reader. For an expert audience, trim over-explanation of things they already know; for a broad audience, unpack a leap that assumes too much. *Honest line:* adjust the **expression** of detail, not the **facts** — "trim over-explanation" means fewer words on a point, not deleting the point. When unsure whether detail is load-bearing, keep it and flag it.

## The preservation guardrail

This is the part to get right. Before proposing any cut or merge, check it against these — anything here is preserved verbatim in substance, even at the cost of brevity:

- **Claims and numbers** — every assertion, metric, threshold, date, version, percentage.
- **Decisions and recommendations** — what the doc decides, advocates, or rules out, and the stated reason.
- **Caveats and conditionals** — "only if", "except when", "unless", warnings, edge cases. These are the first casualties of careless condensing and often the most important sentences in the doc.
- **Named entities** — people, teams, systems, products, file paths, links, ticket/issue references.
- **Scope statements** — what's in scope, out of scope, non-goals.

If you can't tell whether a detail is load-bearing, **keep it** and note it under "Preserved deliberately". A doc that's slightly longer than ideal beats one that's lost a constraint.

## Output format

Lead with a short read on the doc, then the proposed moves grouped by type, then what you deliberately left alone. Keep it scannable — the user should grasp the shape of the change before approving it.

```markdown
## Simplify: <doc path>

| Field | Value |
|---|---|
| **Genre** | <RFC / design / process / general prose> |
| **Current state** | <one line: e.g. "dense, heavy hedging, buries the point"> |
| **Plan** | <light tightening | moderate condense + restructure | heavy rewrite> |

### Proposed moves

The table is the scannable index — one line per move, the change stated *briefly*. Phrase-level swaps and structural moves fit here. Anything longer than one sentence goes in **Details** below, referenced by ID, so the table stays readable.

| ID | Move | Loc | Change |
|---|---|---|---|
| C1 | Condense | L40 | `<short original>` → `<tighter>` |
| C2 | Condense | L10–18 | Tighten the verbose intro — see Details |
| P1 | Plain language | L24 | `<jargon phrase>` → `<plain phrase>` |
| R1 | Restructure | top | Add 3-bullet TL;DR; move "Background" (L5–20) below "Proposal" |
| A1 | Right-altitude | L60–75 | Trim the over-explained walk-through — see Details |

### Details

*(Only for moves too long for the table. Show the passage as before/after blocks, not crammed into a cell.)*

**C2** — L10–18
> before: `<the verbose original passage>`
> after: `<the tighter version>`

**A1** — L60–75
> before: `<the over-explained original>`
> after: `<the condensed version, with a pointer to the detail>`

### Preserved deliberately

- L52 caveat ("only valid when X") — load-bearing, kept verbatim despite the surrounding cut.
- <anything you left long on purpose, and why>

### Apply?

Tell me which IDs to apply — e.g. `apply C1, P1`, `apply all condense`, `apply all`, or `skip`.
I won't touch the file without your go-ahead, and I'll show the diff after applying.
```

**Formatting rules:**

- **ID scheme:** prefix by move — `C`=Condense, `P`=Plain language, `R`=Restructure, `A`=Right-altitude — numbered from 1 within each type (`C1, C2, P1, R1`). Dense, no gaps.
- **Cluster, don't enumerate.** If the same move repeats across the doc (e.g. ten verbose sentences), show 2–3 representative examples and add one roll-up row: `| C3 | Condense | — | …plus N more similar trims |`. The user approves the *pattern*, not every instance. A roll-up row names only real proposed changes — never commentary on passages you decided to leave alone (that belongs in "Preserved deliberately", or nowhere).
- Put literal text in backticks so the change is obvious.
- **Keep the table cell to one line.** A cell holds a phrase-level `before → after` or a one-line description of the move. The moment a change needs a full sentence or paragraph to show, put `see Details` in the cell and write the before/after as blocks in the Details section — a paragraph stuffed into a table cell defeats the whole point of a scannable index.

### When the rewrite is heavy

If the doc needs near-total rewriting, a row-per-change table becomes noise. Instead, say so, then **offer the full simplified doc** as a single proposal: *"This needs a heavy pass — rather than 40 rows, here's the simplified version in full; want me to write it over the original?"* Show it (or the most-changed sections as before→after blocks), and apply wholesale on approval. Use judgment: light/moderate → the moves table; heavy → the full rewrite.

## Applying

- Apply only the IDs the user named. `apply all` means every move; `apply all condense` means every `C` row; `skip` means write nothing.
- After writing, show a concise diff or summary of what changed so the user can verify the meaning survived.
- If, while applying, you realize a chosen cut would drop a load-bearing detail, **don't apply it silently** — flag it and ask.

## Extreme mode — `/simplify-doc extreme <path>`

Extreme mode is the opposite of Default. Default preserves everything and trims wording; **Extreme deliberately throws detail away** to produce a high-level one-pager that *anyone* — with zero prior context — can read in a minute and grasp the core idea. It exists for one job: circulating an RFC, design, or proposal when you want feedback on **the problem and the solution shape**, not the implementation details (those live in the code and PRs later). The shorter the doc, the easier it is for a reader to engage — so aim for **one page** (a soft target, not a hard limit).

Everything in the Default-mode sections (the four moves, the preservation guardrail, the moves-table output) **does not apply here.** Extreme mode has its own rules below.

### First: ask about a template

Radical cutting can destroy a document's *shape*, and shape is often a contract — an RFC has required sections and a reviewer expects to find them. So before you distill, **ask the user whether there's a template for this kind of document** (skip the question only if they already pointed you at one in the invocation):

> *"Before I gut this down — is there a template for this doc (e.g. an RFC template)? Point me to it and I'll keep its section structure; otherwise I'll infer the sections that matter."*

- **Template provided.** Read it — this is the one time Extreme mode reads a second file. Your output mirrors the template's sections exactly — same headers, same order — plus the title line and the document's top matter. Under each section, put the distilled high-level content. **Drop any source section the template doesn't define.**
- **No template.** Infer the required sections from the doc's genre and keep those; use the default Output shape below.

**Top matter** is the document's identity header, and it's preserved **verbatim** when you're keeping structure — don't condense it, drop entries, or trim lists inside it; it's identity, not detail. Target it by position and form, not by field name: it's the YAML frontmatter block if the doc has one, otherwise the run of short label/value or byline lines directly under the title (date, authors, owner, status, and the like) before the first body paragraph. A full sentence or paragraph is body, not top matter — that still gets distilled or dropped.

Either way, **keep a required header even when the content under it shrinks to one sentence** — a reviewer scanning for "Risks" should still find it. The radical cutting happens *inside* the sections, not to the section list. **If the source never filled a required section** (it's empty or absent), keep the header and write a short honest marker — `*(not addressed in the source)*` — rather than inventing content to fill it.

### What survives

The structure — title, metadata block, required headers — is preserved per *First: ask about a template*. **Within** those sections, keep only what a newcomer needs to understand and react to the core idea:

- **The problem** — why this matters and what's wrong today, high level, in plain language. A reader with no context should get it.
- **The proposal** — what's being done about it: the solution *shape* (the how), high level. Not how it's built — *what it is*.
- **One illustrative example, if the doc has one** — a small before/after, sample snippet, or worked example that makes the proposal *concrete* (e.g. "here's what a service's config shrinks to"). It's technically a detail, but a reader grasps a proposal far faster from one tangible example than from prose alone, so it earns its place. Keep the single most illustrative one, trimmed to the shortest form that still reads clearly; drop any others.
- **The decision / ask** — if it's a decision doc, what's being decided and by when.
- **Meaning-shaping caveats** — any scope line or non-goal that, if dropped, would make the reader *misunderstand* the proposal (e.g. "this is **not** auto-rollback"). Keep these, compressed to one line. They aren't "details" — they're part of the core.

### What goes

Drop aggressively — within each kept section, and whole sections the structure doesn't require:

- **Entire *detail-bearing* sections not required by the template** (or, with no template, not essential): spelled-out success criteria, detailed scope lists, appendices, deep-dive walkthroughs. *(Short signpost sections are the exception — see below.)*
- Implementation detail, configs, code/YAML blocks, specific filenames and version pins — **except one small illustrative example** kept per *What survives*; that single example stays (trimmed), everything else of this kind goes.
- Numbers — *unless a number is itself the argument*. (If the doc says cost is explicitly **not** the justification, the cost figures go.)
- Quotes, attributions, meeting notes, boilerplate. (But keep the document's top matter — that's identity, not detail; see *First: ask about a template*.)
- All filler, hedging, and repetition.

A required-but-heavy section (typically Alternatives, Risks) is **kept but collapsed**, not cut — keeping the header with a distilled body beats dropping it. See *Output* for how to format it and the *comprehension floor* for how far to compress.

A short **signpost section** — one that records what the doc still leaves open (pending questions, undecided points) or that points the reader onward (links, related decisions, sources of truth) — is **kept but collapsed** too, even when it isn't template-required. It costs only a few bullets, and for a draft you're circulating for feedback it's exactly what a reviewer wants: what's settled, what isn't, and where the detail lives. Trim it to the bare bullets; don't drop the section.

### The one guardrail that stays

You may delete anything; you may **not** misrepresent. The one-pager must stay *true* to the original — never invent a benefit, never assert something the source doesn't support, never turn a non-goal into a goal or soften a firm decision into a maybe. If cutting a detail would leave a *false impression*, keep a one-line version of it. When unsure whether something is "the point" or "a detail," keep a compressed version — but Extreme errs shorter than Default. (You're still not a co-author or critic: you compress what's there, you don't add ideas or judge them.)

### Distilled, not cryptic (the comprehension floor)

Extreme mode's promise is that *anyone* can understand the doc — and that test applies to **every surviving line**, not just the doc overall. When you collapse a list, dropping detail is fine; dropping comprehensibility is not. A bare label with a jargon parenthetical fails it.

Give each surviving item a short, **self-contained** plain sentence: for a **risk**, *what can go wrong and why it matters, then how it's handled*; for an **alternative**, *what it is and why it was rejected*.

- ❌ `WIF misconfiguration (per-env validation + security review)` — meaningless to a reader without the source.
- ✅ `Workload Identity Federation (the new keyless GCP auth), if bound wrong, could break deploys or grant too-broad access — mitigated by per-environment validation and a security review before the bulk migration.`

If explaining every item clearly would push well past a page, keep the few that matter most, explain those well, and note how many you set aside — never a long list of fragments no one can parse. Order of priority within a kept section: **clear > complete > short.**

### Output

Draft the one-pager and **show it in full in the chat first.** Render enumerable sections (alternatives, risks, options, requirements) as **bullet lists — one item per line**; keep narrative sections (problem/need, proposal) as prose. A wall of semicolons in a list-like section defeats the purpose — and so does a wall of sentences in a narrative one.

**Break up large paragraphs (readability beats compactness).** Prose sections are not exempt from scannability just because they aren't lists. Any paragraph that runs past ~3–4 sentences, or covers more than one idea, gets split into several shorter ones — one beat per paragraph (e.g. *what's wrong* / *why it persists* / *what it'd buy us*). Splitting only inserts a blank line, never changes a word, so meaning is untouched; the doc gets slightly taller but far easier to skim. When brevity and readability trade off, choose readability — a reader who can skim the shape will engage; one facing a monolith won't.

- **With a template,** your output's headers *are* the template's headers — the title line, the metadata block (real values), and each required section — filled with distilled content. Match the template's heading style and order.
- **Without a template,** use this default shape — adapt it to the doc, don't force it:

```markdown
# <Title> — TL;DR

**Problem.** <2–4 plain sentences: what's wrong today and why it matters.>

**Proposal.** <2–4 plain sentences: the solution shape — what we'll do, high level.>

**Scope / not doing.** <0–2 lines: only the caveats that change how the proposal is understood.>

**Decision.** <if a decision doc: what's being asked, and by when.>
```

Keep it to a page if you can. If the doc genuinely contains two distinct proposals, two short Problem/Proposal pairs are fine — but resist re-growing it. The test: could a smart person who has never seen the project read this once and correctly say back what the problem is and what you want to do about it?

**Before you show it, self-check against the source** — Extreme mode cuts a lot, so verify nothing important broke: every required section is present (or marked absent); no cut left a *false impression* of the problem, the proposal, or a meaning-shaping caveat; every bullet is self-contained; and the **title and headers you kept verbatim still use the same word for a concept as your plain-language body does** — if the rewrite renamed something, either carry the plainer name up into the title and headers, or tie the two names together once, so the reader never meets two labels for one thing. Fix what fails, then present.

### Applying

Extreme mode is **non-destructive.** It writes to a sibling file `<path-without-extension>.tldr.md` (e.g. `design.md` → `design.tldr.md`), leaving the original untouched — so the detailed version survives and you circulate the short one. Show the draft, and on the user's go-ahead write the sibling file. Because the original is never touched, approval is light: if the user says "write it" / "looks good," create the file; if they want changes, revise the draft first. Report the path you wrote.

## Tone

Match the author's voice — simplification shouldn't make every doc sound the same. The goal is the author's meaning, expressed with less friction. If the doc is already clear, say so and propose little; a one-line "this is already tight, only minor trims available" is a perfectly good result. (In Extreme mode, voice matters less than brevity and clarity — but the rule against inventing or editorializing still holds.)
