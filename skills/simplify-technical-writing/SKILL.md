---
name: simplify-technical-writing
description: "Simplify ADRs, RFCs, solution designs, proposals, and plan prose while preserving their substance. Use for clearer expression and structure, not argument critique or solution redesign. Explicit extreme mode creates a separate, deliberately lossy one-page summary."
---

# Simplify technical writing

Make the writing shorter, clearer, and easier to assess. Default mode preserves substantive meaning; it changes expression and structure, not the underlying argument. Leave clear, concise passages unchanged and retain the author's voice.

Use this skill for decision and proposal writing, including an ADR stored in a repository. Use `simplify-doc` for maintained repository documentation and comments. A prose-only plan edit belongs here; `simplify-plan` changes the plan's complexity. The `pr` skill owns PR authoring.

## Scope and authorization

Accept paths, selected passages, or a scope from the conversation. `/simplify-technical-writing <path>` selects default mode. Paths may contain spaces. Only a leading whitespace-delimited `extreme` token selects [Extreme mode](references/extreme.md); read that reference only for an explicit extreme request.

Infer an obvious target from the current task. Ask only when missing scope, audience, or intent would materially change the work. Reading related material to understand the source does not authorize editing it or expanding the assignment.

Follow existing session authorization and applicable approval rules. If edits are authorized, complete them and verify the result. For review-only work or when approval is still required, present a concrete proposal and wait. Do not require another approval merely because this skill was invoked.

## Preserve the argument

Read enough of the document and relevant references to understand each passage in context. Treat the source's substantive claims as the content to preserve. Do not silently correct facts, add evidence or analysis, critique the argument, or redesign the solution. Flag suspected contradictions or factual problems separately.

Preserve in substance:

- Claims and their supporting evidence, assumptions, and qualifications. Keep meaningful figures, dates, units, identifiers, and links with the context needed to interpret them.
- Decisions, recommendations, alternatives, and their stated rejection reasons.
- Material tradeoffs, risks, mitigations, uncertainty, requirements, conditions, and negation. Preserve the strength of words such as must, should, and may.
- Scope, non-goals, dependencies, and relevant historical context.

Distinguish proposed, decided, implemented, and deployed states. Do not turn a proposal into a fact or rewrite a historical ADR to describe today's system. Preserve meaningful identity metadata, status, references, and required template structure.

Remove repetition and incidental detail only when no substantive meaning is lost. Do not keep every name or historical datum mechanically, but retain and flag details whose significance is uncertain. Default mode does not replace evidence, alternatives, or caveats with a selective summary.

## Simplify the expression

Remove repeated explanations, throat-clearing, and optional template filler before shortening sentences. Merge duplicate passages while keeping their distinct qualifications. Give each substantive point a clear home without moving detail into new companion documents merely to shorten the target.

Surface the problem, proposal, decision, or ask where readers need it. Reorder context and prerequisites to make the reasoning easier to follow. Use headings, lists, or tables when they help readers navigate or compare; do not impose a new template or force a summary.

Use consistent terms, active voice, and plain, complete sentences. Retain technical terms needed for precision and explain unfamiliar terms using context already supported by the source. Match the expression to the audience without deleting supporting facts. Avoid telegraphic prose, reduction targets, bullet quotas, fixed vocabulary, and sentence limits.

## Verify and report

Compare the rewrite with the source for lost claims, evidence, rejection reasons, or qualifications. Check especially conditions, negation, uncertainty, status, and requirement strength. Check affected links, anchors, and template requirements.

Report the result, validation, and unresolved factual questions briefly. For a proposal, show the affected passages or a concise diff with enough rationale to assess material changes. Group repeated edits; show a full rewrite when that is easier to review. Do not require a moves table, numbered edit inventory, or list of unchanged content.
