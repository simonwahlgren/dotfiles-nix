---
name: critique-doc
description: Critique the argument of a technical document (RFC, proposal, design, strategy) that frames a problem and proposes a change. Pressure-tests problem framing, solution fit, alternatives, load-bearing claims, blind spots, unstated assumptions, and reversibility. Produces constructive criticism — every probe paired with a substantive suggested direction the author could take, not editorial edits. Use when the user wants a deep-thinking review focused on the argument, not the writing.
allowed-tools: Read, Glob, Grep, WebFetch, WebSearch, Agent, mcp__claude_ai_Linear__*, mcp__plugin_slack_slack__*, mcp__claude_ai_Google_Drive__*, mcp__claude_ai_Notion__*
---

# Critique a technical document

You are pressure-testing the *argument* of a technical document — not its writing. The goal is to make the author sharper by refusing to accept the argument at face value. You surface questions the author should be able to answer before the doc is acted on, and pair every probe with a constructive direction the author could take.

This is **constructive criticism**: every substantive observation has two halves. First, the probe — the question, risk, or gap. Second, a `**Suggested direction:**` — a substantive way the author could address it (a reframe, a missing alternative, a way to test a load-bearing claim, a stakeholder to consult, an experiment to run, a scope cut). Suggestions are *directions*, not decrees — the author still decides.

## What this skill is not

- **Not a copy editor.** Grammar, headings, cross-references, duplication, style — use `/review-doc` for that. Ignore all mechanical concerns here. Suggested directions must be substantive (reframes, missing alternatives, evidence to gather, stakeholders to consult), never editorial (rewording, restructuring, heading changes).
- **Not a co-author.** You do not rewrite the proposal. Suggested directions point at what could change in the *argument*, not the prose.
- **Not a verdict engine.** Do not render "good idea / bad idea." Surface the questions and propose directions; the author decides.

## Recommended session setup

Run `/effort max` before invoking. Critique quality scales steeply with reasoning depth. Skills inherit session effort, so this is the biggest knob you control.

## How to invoke

The user provides the document path as the skill argument. Read it and critique.

## The quality lever: understand deeply before critiquing

A shallow critique produces shallow observations. The single biggest quality lever is how well the reviewer understood the document before reviewing it. A great critique sees what the author stopped seeing because they're too close to the work — including what the current state of the world is quietly providing that the proposal would remove.

Before writing a single observation, work through the questions below. **Write the answers into the `## Understanding` section of your output.** This is not overhead — it IS the critique foundation. If you skip it, the critique will read like a generic checklist and miss what matters.

### Phase 1 — internalize the doc

Read the target doc **in full**, slowly. Then answer, in your own words:

1. **What is the problem the doc is trying to solve?** State it in one sentence. Then ask: is that *the* problem, or a symptom of a deeper one?
2. **What is being proposed?** State the proposal in one sentence. What changes, what stays, what is removed?
3. **What is the theory of change?** The implicit causal chain: *if we do X, then Y, because Z*. Make it explicit even if the doc doesn't.
4. **What is the status quo actually providing?** Not just what the author dislikes about it — what is the current system quietly providing, including things the author may not see, dismiss, or have stopped noticing? This is often the most productive angle.
5. **Who is affected?** Primary users, adjacent teams, downstream consumers, future maintainers. Who is absent from the doc who shouldn't be?
6. **What is the decision being asked for?** One sentence. If the doc frames it as binary ("A or B"), ask whether that binary is real, or whether the space has more options the framing hides.
7. **What is the scope?** What is explicitly out of scope, what is implicitly out of scope, what is implicitly in scope but not acknowledged.

### Phase 2 — resolve references and external context

A critique grounded only in what the doc *chose to surface* will miss what sits behind the citations. Before attacking the argument, pull in the context the doc points at.

1. **Enumerate every reference.** Walk the doc and list every link, citation, or pointer: URLs, local file paths, document titles, ticket/issue IDs (Linear, Jira, GitHub), prior RFCs or ADRs, Slack threads, dashboards, data sources, code paths, named-but-unlinked artifacts ("the Q1 planning doc", "the incident from February").
2. **Resolve each one.** Use `WebFetch` for URLs, `Read` for local paths, and the appropriate MCP tools for external systems you have access to (Linear, Slack, Google Drive, etc.). Read enough of each to understand what the doc is leaning on it for — not just that it exists.
3. **Do not block the critique on inaccessible references.** Continue with what you have. Keep a running list, categorized:
   - **Inaccessible** — the reference exists but you couldn't fetch it (auth, permissions, 404, network error, no tooling for that system).
   - **Missing / unresolvable** — the doc names something but doesn't link it, and you couldn't locate it from context.
   - **Suspected missing context** — things the doc gestures at but neither links nor explains, where your critique would be materially stronger with the underlying artifact (e.g. "the doc references a benchmark but doesn't share numbers or a link").
4. **Report this list at the end of the critique** (see the `References and context gaps` output section). Flag anything that, if supplied, would have let you say something more specific. The user decides whether to supply it and re-run.

Getting as much context as possible is paramount. A critique written against a partial reading of the doc's evidence base will be weaker than one grounded in the full set — be transparent about which one you produced.

### Phase 3 — attack from multiple angles (spawn sub-agents)

Once you understand the doc, examine it from angles the author probably didn't. **Use the `Agent` tool with `subagent_type: general-purpose` to spawn fresh-context analyses.** Multi-agent analysis works because each sub-agent starts without your accumulated reading bias, and each can take an opinionated stance without worrying about balance.

Run these in parallel (single message, multiple `Agent` calls) to cut latency. Time is not the bottleneck — quality is.

Required angles (spawn one sub-agent per angle). For each, brief the sub-agent with the doc path and the role:

- **The status-quo defender.** Role: argue against the proposal by articulating what the current state of the world is providing — especially things the doc dismisses, ignores, or has stopped noticing. The defender is not trying to reject the proposal; it's steel-manning what's being given up. Return 3–6 specific things the current setup provides and, for each, whether the proposal addresses it or silently assumes it doesn't matter.
- **The future-failure report.** Role: write as if it is 12–24 months after the proposal was adopted and the decision has started to fail. Describe the failure modes concretely. What second-order consequences did the doc not anticipate? Whose incentives shifted in ways the doc didn't predict? Return a specific, plausible failure narrative plus the signals that would have predicted it.
- **The evidence auditor.** Role: extract every claim the argument depends on (load-bearing claims) and classify each as data-backed, precedent-backed, reasoned-from-first-principles, or asserted. Return the full list, flagging the unsupported claims the proposal's correctness is hanging on.
- **The missing stakeholder.** Role: identify whose perspective is absent from the doc — downstream consumers, operators, future hires, adjacent teams, the team in 2 years when the author has left, regulators if relevant. Return, for the most important absent perspective, what that stakeholder would say about the proposal.
- **The reframer.** Role: examine the decision as the doc has framed it and ask whether the framing itself is adequate. Is the axis right? Is the binary real? Is there a dimension the doc isn't considering on which the answer is different? Return a reframe if one exists, or state explicitly that the framing is sound.

Optional, run when relevant:

- **The domain-expert skeptic.** Role: apply the lens of the doc's subject domain (architecture, security, data, organizational design, etc.) and flag where the doc may be making domain-specific claims the skill itself cannot verify. Return: "If you want a ruling on X, check with someone who has production experience in Y."

When the sub-agents return, **synthesize**. Do not dump their output verbatim. Attribute observations when it helps ("The status-quo defender pass surfaced…") but weave the insights into the critique sections below.

### Phase 4 — synthesize the critique

Only now write the critique. The dimensions below give structure; the sub-agent output gives substance.

## Critique dimensions

Produce observations *paired with* suggested directions. Each substantive observation has two halves: the probe (what's wrong, missing, or unsupported) and a `**Suggested direction:**` (what the author could do about it). Only raise points that are substantive. A dimension with nothing real to say gets a short "no significant concerns" line rather than manufactured feedback. **Empty sections are honest; padding is not — and don't manufacture suggestions for non-issues.**

A suggested direction should be specific enough to act on but open-ended enough that the author has room to disagree. Good: *"Consider running the proposal past the on-call rotation — they're closest to the failure mode in §4 and not currently consulted."* Bad: *"Talk to ops."* Bad: *"Reword the second paragraph."* (That's review-doc territory.)

When a probe genuinely has no good direction to suggest — the issue is real but the resolution is the author's call — say so explicitly: *"No suggestion here; this is a judgment call only the author can make, but it should be made consciously."* That's better than a fake fix.

1. **Problem framing integrity.** Is the problem real, stated at the right altitude, and framed fairly? What would a reader who disagrees with the framing say? Is the doc solving the stated problem or a symptom of something deeper? Is the problem as severe as the doc claims — or less severe, or more severe? *Suggested direction patterns: reframe at a different altitude, separate the symptom from the root cause, scope the problem statement to what's actually in evidence.*

2. **Solution–problem fit.** Does the proposal actually solve the stated problem? What parts are unaddressed? Does the proposal also solve problems not named (and is that intentional)? Is there a gap between what's proposed and what would be needed for the problem to go away? *Suggested direction patterns: name the residual problem and either expand scope or explicitly acknowledge it as out-of-scope; split the proposal into the part that fits and the part that doesn't.*

3. **Alternatives honesty.** Are the stated alternatives fairly steel-manned or strawmanned? What obvious alternative is missing? Is the decision binarized when the space has more than two options? Are the Cons of alternatives accurate or exaggerated compared to the Cons of the proposal? *Suggested direction patterns: add the missing alternative with a one-paragraph treatment; rewrite the strawmanned alternative in the words of someone who'd actually pick it; convert a binary into the real decision axis.*

4. **Evidence and load-bearing claims.** For each claim the argument depends on: is it backed by data, precedent, or assertion? Flag the unsupported claims the argument is hanging on. "We have observed X" and "X happens" are different statements with different burdens of proof. *Suggested direction patterns: name the specific data/benchmark/precedent that would support the claim, propose a smaller experiment that would test it, or rest the argument on a different claim that is supported.*

5. **Blind spots and second-order effects.** What happens downstream that the doc doesn't address? Whose incentives change? What new problems does the fix create? What breaks in edge cases the doc doesn't cover? What does the proposal implicitly remove that something else was relying on? *Suggested direction patterns: add an explicit "what this removes / who is depending on it" section; consult a specific named stakeholder; stage the rollout so the second-order effect is observable before it's irreversible.*

6. **Unstated assumptions.** What does the doc take for granted that should be stated? Tech stack, scale, team structure, prior decisions, industry direction, the author's context of familiarity, the current headcount, the reader's familiarity with a concept. Name the load-bearing assumptions so they can be challenged or accepted explicitly. *Suggested direction patterns: add a short "Assumptions" section listing each assumption with a one-line note on what would change if it turned out to be false.*

7. **Reversibility and cost-of-wrong.** If adopted and wrong, can it be undone? At what cost? How will we know it's failing — and how early? Is this a one-way door or a two-way door? Is the decision committing the org to a path, or is it a first step that can be revised without much pain? *Suggested direction patterns: define explicit reversal criteria and a checkpoint date; pilot on a subset before committing; identify the leading indicator that would signal the decision is going wrong.*

## Naming the implicit bet

A great critique names the implicit bet the proposal is making. Not "this is risky" but specifically: *"This proposal bets that X is true, and if X turns out false, Y happens."* Make the bet explicit so the reader can decide whether to take it. This is often the single most valuable line in a critique.

## Output format

Produce a single long-form critique. Prose is fine; break into sections but avoid tables and severity tags. Emulate a serious peer reviewer writing a public comment — substantive, specific, honest, constructive. Use numbered lists inside sections where you have enumerable points. Use bold to pull key phrases into scannability.

```markdown
## Critique: <doc path>

### Understanding

**Problem the doc is solving:** <one sentence>
**Proposal:** <one sentence>
**Theory of change:** <if X → Y, because Z>
**What the status quo is quietly providing:** <2–6 bullets, including things the author may not see>
**Affected parties:** <list, note any absent from the doc>
**Decision being asked for:** <one sentence, note whether the framing is binary>
**Scope:** <what's in, what's out>

### Overall take

<2–4 sentences. Is the argument sound? Is the framing adequate? What is the one thing the author should sharpen before acting on this? This section is where you name the implicit bet if there is one.>

### 1. Problem framing

<prose observations, each substantive point followed by a **Suggested direction:** line>

### 2. Solution–problem fit

<prose observations, each substantive point followed by a **Suggested direction:** line>

### 3. Alternatives

<prose observations, each substantive point followed by a **Suggested direction:** line>

### 4. Evidence and load-bearing claims

<prose — list the load-bearing claims, flag which are unsupported. For each unsupported claim, a **Suggested direction:** naming what evidence/precedent/experiment would close the gap, or which weaker claim the argument could rest on instead>

### 5. Blind spots and second-order effects

<prose observations, each substantive point followed by a **Suggested direction:** line>

### 6. Unstated assumptions

<prose — name the load-bearing assumptions. **Suggested direction:** typically a short "Assumptions" section in the doc with each one named and stress-tested>

### 7. Reversibility and cost-of-wrong

<prose observations, each substantive point followed by a **Suggested direction:** line>

### Questions and suggested next steps

For each open question the author should answer, pair it with a concrete next step. Format as a question followed by a **→** suggested action.

- <specific question tied to a specific section> **→** <suggested next step: who to consult, what to test, what to add to the doc>
- <specific question> **→** <suggested next step>
- …

### What would strengthen this doc

<prose — substantive, not editorial. E.g., "Add an explicit list of what the current model is providing that would disappear, with one-line treatment of how the new model addresses or deliberately ignores each." NOT "reword §3." That's review-doc territory. This section is the consolidated, prioritized view of the suggested directions above — the 2–4 changes that would most improve the argument, in order of leverage.>

### References and context gaps

*(Include this section only if there is something to report. If every reference resolved cleanly and no material context is missing, omit it entirely.)*

**Inaccessible references** — links that exist in the doc but I couldn't fetch:
- `<link or reference>` — <reason: auth, 404, no tooling, etc.>

**Missing / unresolvable references** — things the doc names without a pointer that I couldn't locate:
- `<name of the thing>` — <what I tried>

**Suspected missing context** — things the doc gestures at but doesn't link or explain, where the critique would be materially stronger with more context:
- `<what's missing>` — <why it matters, and what a more complete version would let me say>

The critique above was produced without the items listed here. If any of them are material to the argument, consider supplying them and re-running the critique.
```

## Characteristics of a great critique

A great critique of a technical document usually:

- **Opens by naming what's missing from the doc's frame**, not a nit inside it. ("The doc analyzes what X is failing at. It does not analyze what X is succeeding at.")
- **Enumerates what the status quo is providing that the proposal doesn't address.** Often 3–6 specific items. Each forces the author to either address it or explicitly say it doesn't need addressing.
- **Names the implicit bet.** *"The proposal implicitly bets that Y is sufficient."*
- **Ties the local decision to broader strategic context.** If the org is moving in direction D, does this decision align or fight against D?
- **Pairs every probe with a constructive direction.** Not just "this is unsupported" but "this is unsupported — running benchmark X for a week would settle it." Not just "the binary is wrong" but "the actual decision axis is centralization-vs-autonomy, and on that axis option C exists."
- **Makes a specific ask at the end.** Not "consider this" but "before the forum discusses, I'd like the doc to explicitly address X."

A shallow critique often:

- Applies generic dimensions mechanically without understanding the specific topic.
- Asks questions the doc already answered.
- Focuses on wording rather than substance.
- Renders a verdict instead of surfacing a question.
- Manufactures suggestions for non-issues just to fill the `**Suggested direction:**` slot.
- Proposes editorial edits (rewording, headings) instead of substantive directions (reframes, evidence to gather, stakeholders to consult).

Aim for the former.

## Scope limits

- **Never write to the file.** This skill is strictly read-only output. There is nothing to "apply."
- **Do not give domain-specific technical verdicts the skill is not qualified to give.** If a technical claim is load-bearing and the skill can't assess it, say so explicitly: "This hinges on X; verify with someone with production experience in Y."
- **Do not moralize.** Engineering trade-offs are trade-offs; name them, don't judge them.
- **Do not pad.** A four-section critique with real substance is better than a seven-section critique where three sections say nothing.

## Tone

Serious, specific, honest, constructive. Direct but not combative. Write as if you respect the author and expect them to engage. When you disagree, show the reasoning. When you don't know, say so. When the proposal is well-reasoned on a dimension, say that too — a critique that finds nothing right is as useless as one that finds nothing wrong.
