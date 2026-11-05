---
name: simplify-doc
description: "Simplify maintained repository documentation, code comments, and docstrings while preserving task-relevant facts and contracts. Use for READMEs, runbooks, reference docs, or prose accompanying authorized code changes. Decision documents and proposals belong to simplify-technical-writing."
---

# Simplify repository documentation and comments

Make the writing shorter, clearer, and easier to use. Preserve the facts and constraints readers need to act correctly. Leave clear, concise text unchanged.

Use `simplify-technical-writing` for ADRs, RFCs, solution designs, proposals, and plan prose, even when stored in a repository. Its explicit extreme mode creates a separate lossy summary. The `pr` skill owns PR authoring.

## Scope and authorization

Accept paths, selected passages, a diff, or a scope from the conversation. `/simplify-doc <path>` selects a writing pass. Paths may contain spaces.

Infer an obvious target from the current task. Ask only when missing scope, audience, or intent would materially change the work. Stay within the requested files or changed areas; reading related context does not authorize editing it. Skip generated, vendor, instruction, and memory files unless requested or required by the agreed scope. Do not turn a writing pass into a repository-wide cleanup or external posting.

Follow existing session authorization and applicable approval rules. If edits are authorized, complete them and verify the result. If the request is review-only or approval is still required, present a concise, concrete proposal and wait. Do not require another approval merely because this skill was invoked.

## Establish the meaning

Read the target passages and enough surrounding material to understand their purpose. For comments and docstrings, inspect the relevant code and callers or tests where needed. Check referenced documentation or tool consumers when a proposed change depends on them. Keep investigation proportional to the scope.

Distinguish verified behavior from assumptions. Code can clarify an explanation, but documentation may be the sole record of externally managed state, operational decisions, or constraints. Absence from code is not evidence that such information is obsolete. Flag contradictions, stale claims, or uncertain cuts separately rather than silently changing facts during simplification.

Preserve the facts and constraints the reader needs to act correctly:

- Requirements, public contracts, decisions, assumptions, scope, and necessary rationale.
- Exact identifiers, commands, values, units, conditions, negation, uncertainty, and requirement strength where they carry meaning.
- Non-obvious invariants, security rationale, failure and recovery behavior, rollout order, and conditions for removing temporary measures. Merged and applied are different states.
- Caveats, warnings, examples, and coverage boundaries that prevent mistakes or support a decision.

Keep important specifics explicit or clearly linked. Do not retain every historical datum or named entity solely because it appears in the source. Remove detail only when it is irrelevant to the reader's task or verified safe to remove; keep and flag it when uncertain.

## Simplify in this order

1. Remove repetition, obvious narration, and optional template filler before compressing sentences. Preserve required template structure. Long file headers often duplicate a README; prefer an existing canonical explanation and a useful local pointer over another copy or a new companion document.
2. Give each fact or decision one authoritative explanation where practical. Keep local safety reminders when readers need them at the point of action. Do not move clutter into new documents just to shorten the target.
3. Lead with the outcome or action. Separate usage from implementation reference, put prerequisites before steps, and place exceptions beside the rules they qualify. Use headings, lists, or tables only when they help readers find or compare information.
4. Use consistent terms, active voice, and plain, complete sentences. Retain necessary technical terms and the author's voice. Avoid telegraphic prose, forced summaries, reduction targets, bullet quotas, and fixed vocabulary or sentence limits.

## Maintained documentation

Revise the affected explanation to describe verified current behavior instead of appending change history. Preserve actionable migration constraints and distinguish merged changes from changes applied to the relevant environment. Keep instructions separate from implementation reference, with prerequisites and failure or recovery steps where readers need them.

Remove investigation logs, raw verification histories, speculative future work, and descriptions of unchanged behavior when they do not help the reader's task. Preserve relevant evidence and history in archival or investigation material encountered in scope; do not silently modernize it. A task to edit a decision record belongs to `simplify-technical-writing`.

## Comments, docstrings, and new code

Separate human prose from syntax and machine-readable content before editing. Comments can affect tooling: consumers may scan raw text or filenames. Preserve shebangs, linter and type directives, generator markers, licenses, and tool-consumed references. Docstrings may define contracts, contain doctests, or supply runtime metadata. Check the relevant consumer when changing such content; a parser alone may not catch a broken text scan.

Preserve executable code, meaningful examples, and commands. Do not change executable logic to make prose easier to simplify. Apply this guidance to prose accompanying new or changed code only within the authorized task scope.

Remove comments that merely narrate clear code. Keep or add comments for otherwise missing intent, constraints, contracts, security rationale, or likely mistakes. Preserve task-critical warnings even when nearby code seems self-explanatory, and retain temporary-workaround removal conditions. Prefer an existing canonical explanation with a short local reminder when readers need it at the point of action; do not create companion documentation just to relocate comments.

## Verify and report

Compare the rewrite with the original for changed meaning, especially conditions, negation, uncertainty, and requirement strength. Check links and anchors affected by moves or heading changes. For edited comments or docstrings, use proportionate parser, lint, doctest, or consumer checks where useful. Do not execute documentation examples or infrastructure commands merely because they appear in the text.

Report the result, checks performed, and unresolved factual questions briefly. For a proposal, show the affected passages or a concise diff with enough rationale to assess material changes. Group repeated edits instead of listing every wording swap. Use a full rewrite only when that is easier to review. No mandatory moves table or unchanged-content inventory is needed.
