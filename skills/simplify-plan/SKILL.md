---
name: simplify-plan
description: Simplify an existing design plan, implementation plan, or mixed solution plan at its current level of detail by preserving required outcomes and constraints while removing, reusing, merging, deferring, or simplifying unnecessary architectural and implementation concepts. Use for a final KISS/YAGNI pass when a viable plan seems overengineered, too abstract, too decomposed, excessively future-proofed, or larger than its current requirements justify. Not for initial brainstorming, requirements gathering, prose-only editing, or comprehensive architecture, correctness, security, or code review; architectural and implementation choices in the plan remain in scope for complexity reduction.
---

# Simplify a solution plan

Reduce the solution itself, not merely the plan's wording. A plan is an intermediate proposal and may describe high-level design, low-level implementation, or both. Preserve required behavior, correctness, hard constraints, and justified rollout safety while minimizing total system complexity at the level represented by the plan.

Prefer removing a planned concept over improving its design. Evaluate each concept in this order:

1. Remove it.
2. Reuse an existing mechanism.
3. Merge it with another concept.
4. Defer it until demonstrated need.
5. Simplify it.
6. Improve or generalize it only when a current requirement demands that.

Apply DRY only when it lowers total complexity. Small duplication is often cheaper than a premature abstraction.

## Run in an isolated worker

Run the simplification pass in exactly one fresh worker by default.

If the first line of the worker's task is `SIMPLIFY_PLAN_WORKER`, do not delegate again. Continue with the rest of this skill directly.

Otherwise:

1. Build a curated context packet containing only:
   - the exact plan text or path
   - authoritative requirements and their source text or paths
   - hard constraints and their source text or paths
   - verified architecture or code facts needed to judge the plan, with sources
   - known unknowns that may affect simplification
2. Exclude previous simplification suggestions, expected conclusions, and planning discussion unless it establishes an authoritative requirement or hard constraint. Prefer raw artifacts and source paths over summaries.
3. Use the host's delegation mechanism to start one separate agent or session with no inherited conversation. Require read-only analysis and prohibit further delegation. Ensure it can load this skill by name or path.
4. Give the worker this task:

```text
SIMPLIFY_PLAN_WORKER

Read and apply the simplify-plan skill directly. Do not delegate or edit files.

Plan:
<exact text or path>

Authoritative requirements:
<source text or paths>

Hard constraints:
<source text or paths>

Verified relevant facts:
<facts with sources>

Known unknowns:
<unknowns>
```

Wait for the worker, then check its recommendations against the authoritative context. Reject unsupported removals, restore missed constraints, and present the reconciled assessment and revised plan. Do not rerun the full simplification pass in the parent context.

If the host cannot create a worker without inherited conversation, stop and report that isolated execution is unavailable. Run in the current context only after the user explicitly approves that fallback.

## Establish the authority boundary

Read the complete plan and any provided problem statement, requirements, constraints, architecture context, compatibility needs, and rollout requirements.

Treat requirements and hard constraints as authoritative. Treat planned design and implementation choices as proposals. Do not preserve a choice merely because the plan presents it as decided.

Before simplifying, identify:

- required outcomes
- correctness, security, integrity, compatibility, availability, regulatory, and known scale constraints
- rollout, migration, observability, and rollback needs required for safe operation
- explicitly required extension points or imminent use cases

Do not invent missing requirements. State any uncertainty that materially affects a recommendation. Verify claims about existing code or mechanisms from available evidence before recommending reuse.

## Match the plan's altitude

Identify the level of each planned concept instead of forcing the whole document into one mode:

- **Design:** entities, services, ownership and system boundaries, datastores, deployment units, dependencies, communication paths, protocols, events, and data flows.
- **Implementation:** modules, files, classes, interfaces, functions, configuration, state, branches, pseudocode, migrations, rollout steps, and tasks.
- **Mixed:** design decisions and their downstream implementation details.

Preserve the appropriate altitude. Do not invent code, files, or tasks for a design-only plan. Do not discard required implementation detail from an implementation plan. For a mixed plan, simplify the design first, then simplify its downstream implementation against that design.

## Run the simplification pass

Inventory every significant planned concept at both applicable levels:

- **Design:** entity, service, responsibility, ownership boundary, system or deployment boundary, datastore, external dependency, communication path, protocol, event, queue, data flow, and consistency or availability mechanism.
- **Implementation:** component, layer, module, file, class, interface, function, dependency, configuration option, state, branch, pseudocode construct, migration step, rollout mechanism, and task.

For each one, ask:

- Which current requirement requires it?
- What breaks if it is removed?
- Can an existing system, service, or mechanism own the responsibility?
- Can it merge with an existing or planned concept?
- Can a boundary, entity, datastore, deployment unit, or communication path disappear?
- Can direct interaction replace events, queues, adapters, or orchestration?
- Can convention replace configuration?
- Can concrete behavior replace a generic abstraction?
- Can synchronous behavior replace asynchronous coordination?
- Can derived or ephemeral data replace persistent state?
- Can the main design change eliminate special cases?
- Does simplifying a design choice eliminate downstream implementation machinery?
- Can standard or existing functionality avoid a dependency?
- Can the work wait for a concrete second use case?

Actively detect:

- single-implementation interfaces, factories, plugin systems, repositories, and service layers
- entities, services, boundaries, or datastores separated without independently required responsibilities
- communication paths and coordination mechanisms without a concrete distribution or decoupling need
- flexibility justified only by hypothetical future use
- excessive splitting across files, modules, handlers, events, queues, tables, or configuration objects
- duplicated state, caches without demonstrated need, status machines, synchronization, and bookkeeping fields
- indirection chains whose boundaries lack distinct requirements
- special cases caused by an unnecessarily narrow core representation or flow
- migration or rollout machinery disproportionate to the actual risk
- optional or speculative scope mixed into required work

Recommend evidence-supported changes directly. Avoid weak phrasing such as “consider” or “might.”

## Derive the minimal core

Independently answer:

> If solving this problem from scratch today, with the known requirements, what is the smallest solution at the plan's current level of detail that solves it correctly?

For a design plan, derive the minimum viable design. For an implementation plan, derive the minimum concrete implementation. For a mixed plan, derive the minimum design first, then the minimum implementation needed for it.

Compare this minimal core with the proposed plan. Prefer the minimal solution unless a concrete constraint justifies each added piece. Use this comparison to challenge the overall design, not only simplify its parts locally.

## Preserve justified complexity

Keep complexity directly required for correctness, data integrity, security, backwards compatibility, availability, known scale, regulation, safe migration, rollback, required observability, explicit extension points, or known imminent use cases.

Do not:

- change product requirements to ease implementation
- turn concrete constraints into assumptions
- remove necessary error handling or safety controls
- replace clear code with clever code
- introduce one abstraction while claiming to remove another
- optimize primarily for lines or files
- silently discard a constraint

If simplification requires changing a requirement or accepted constraint, separate that proposal from the simplification assessment.

## Produce the assessment

Start with a concise assessment using these exact categories. Omit an empty category only when saying `None` would add no useful signal.

### Remove

For each item, state what disappears, why it is unnecessary, and which apparent justification does not establish a current requirement.

### Simplify / Merge

For each item, state the concrete replacement: what remains, what combines or becomes direct, and why it still satisfies the requirements.

### Defer

For each item, state why it is unnecessary now and the concrete future condition that would justify adding it.

### Keep

Briefly name complexity that may look removable but is justified, and cite the requirement or constraint that requires it.

Distinguish verified facts from assumptions. If the original plan is already minimal, say so rather than manufacturing changes.

## Write the revised plan

After the assessment, provide a `## Revised Plan` that is standalone and actionable at the appropriate level. The reader must not need to apply recommendations mentally or consult the original plan to understand the solution.

Use the simplest structure that communicates the work. Prefer:

- fewer design concepts, steps, and moving parts
- direct, concrete design or implementation
- existing mechanisms and dependencies
- validation criteria tied to required behavior and risks
- tests when the plan includes implementation work
- migration, rollout, observability, and rollback steps only when justified
- explicit deferral of nonessential work

Preserve every authoritative requirement and constraint in substance. Do not retain the original plan's sections, ordering, or terminology when a simpler presentation is clearer. Do not invent implementation detail for a design plan or erase required detail from an implementation plan. For a mixed plan, present simplified design decisions before their downstream implementation work.

Keep the plan sufficient for its next step; do not make it imitate a final implementation or system.

Return the assessment and revised plan in chat by default. Modify a plan file only when the user explicitly asks.
