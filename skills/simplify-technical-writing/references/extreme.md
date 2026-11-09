# Extreme mode

Use only for an explicit request such as `/simplify-technical-writing extreme <path>`. Treat the rest of the argument as the path, including spaces. Infer the source from the conversation when clear; otherwise ask for it.

Produce a deliberately lossy summary for readers seeking feedback on a proposal's problem and solution shape. Aim for one readable page, not a hard word limit. Default mode's important-meaning preservation gives way to selective summarization here, but never invent a claim or leave a false impression.

## Structure and content

Read the source and any specified template. Honor the template's required headers, style, and order. Without a template, infer a useful structure from the document's purpose; ask only if the missing template would materially affect correctness.

Preserve the source title and identity metadata verbatim: YAML frontmatter, or the short label/value and byline lines under the title before body prose. Keep required headers even when their bodies shrink to one sentence. Mark a required section absent from the source with `*(not addressed in the source)*`; do not invent its content. If plain language changes a term used in the preserved title or headers, connect the terms once in the body.

Within that structure, retain:

- The problem, why it matters, and the proposed solution shape.
- The decision or ask, including its deadline when stated.
- Caveats, non-goals, and material risks that shape the reader's understanding.
- One illustrative example if the source has one, trimmed without changing what it demonstrates.
- Brief signposts for unresolved questions, related decisions, and sources of truth. Fit these into the specified template when necessary.

For retained claims and figures, keep qualifications needed to interpret them, including snapshot dates and whether they are measured, estimated, or proposed.

Drop implementation detail, extensive scope lists, appendices, repetition, meeting notes, and incidental numbers or attributions unless they make the central argument. Collapse required detail-heavy sections such as Alternatives and Risks instead of dropping them. Preserve numbers that are themselves the argument. Do not turn a non-goal into a goal, a firm decision into uncertainty, or an unverified benefit into a fact.

## Readability

Use short prose paragraphs for the problem and proposal, and lists for parallel risks or alternatives. Each surviving item must make sense without the source. Explain what a risk could cause and its stated mitigation, or what an alternative is and why the source rejects it. Do not invent a mitigation or rejection reason that the source lacks. For example:

> Workload Identity Federation, the new keyless GCP authentication, could break deployments or grant excessive access if configured incorrectly. The proposal mitigates this with validation in each environment and a security review before the bulk migration.

If explaining every item would exceed a useful page, select the most important ones and briefly indicate the omissions. Prefer clear sentences over cryptic fragments. Without a template, a useful shape is the original title and metadata followed by Problem, Proposal, material scope caveats, and Decision when relevant. Adapt it rather than forcing empty sections.

## Verify and deliver

Compare the summary with the source: required structure and identity remain intact; the example stays faithful; surviving lines are understandable; and omissions do not misrepresent the problem, proposal, decision, or material caveats. Label the result as a summary so readers know it omits detail.

Leave the original untouched. When writing is authorized, save to a sibling `<stem>.tldr.md`, for example `design.md` becomes `design.tldr.md`, and report its path. If that sibling already exists, check whether replacement is within the authorized scope. For review-only work or when approval is required, show the complete draft first. Honor existing authorization without repeated confirmation.
