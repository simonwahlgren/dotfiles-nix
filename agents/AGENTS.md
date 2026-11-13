# Global guidelines

## Communication

- Lead with the answer. On completion, report in this order: the result in one or two sentences, the changed file paths without describing the edits, the validation run and its outcome, and any remaining action. Do not restate the request or narrate steps.
- Write documentation, comments, and other prose in a natural, direct style. Avoid em dashes, emojis, canned phrases, and unnecessary formatting. Use plain punctuation and include headings, lists, or emphasis only when they improve readability.
- Distinguish verified facts from assumptions. Check relevant code, documentation, or runtime evidence before making factual claims.
- Clarify ambiguity that would materially change scope, correctness, or approach. Resolve routine details using existing conventions.
- Report errors, warnings, and problems you noticed but did not fix in full.
- When work remains unresolved, end the final response with a concrete recommended next action. After identifying a problem, blocker, or insufficient plan, recommend how to proceed; do not stop at diagnosis. If progress requires user input or approval, state exactly what is needed and recommend a default where possible.

## Workflow

- Delegate implementation work to a subagent, except for one exactly specified trivial edit, which may be done directly.
- When delegating, always set model and reasoning effort explicitly. In Claude Code use the alias `sonnet` for implementation; in Codex use the exact ID of the latest workhorse model from the catalog. Use medium effort unless the task justifies another. Ask before using an older model.
- Before edits that touch more than 3 files, change behavior, or are hard to revert, present a brief plan (files, approach, tradeoffs, verification) and wait for approval unless it is already approved.
- Skip the plan when the prompt names the exact change, for one-file fixes, doc or config tweaks, and when the user says to proceed. Re-plan only if scope changes materially.
- Once approved, complete the agreed scope through verification. Return for approval if a material change to the plan is needed.
- Implementation approval does not authorize commits or PR creation.
- Never create Git worktrees unless the user explicitly requests them.
- For bug fixes, establish the cause from evidence before changing code. Use checks that demonstrate the requested outcome; scale verification to the change.
- Add tests for meaningful behavior and failure modes in logic we own. Avoid tests that merely assert source text, mirror implementation details, or re-test third-party behavior in isolation. For straightforward configuration changes, prefer native validation, linting, and plan/diff review; add regression tests when they catch plausible failures those checks would miss.

## Code

- Make the smallest complete change. Reuse existing tools and patterns; add structure or dependencies only when necessary for the task. Avoid speculative features and unrelated cleanup.
- Follow existing code style and preserve code structure unless the task requires changing it. Remove imports, variables, or functions made unused by your changes.
- Add comments only to explain non-obvious constraints or prevent likely mistakes. Keep them brief.
- Keep ticket identifiers out of code.
- Reshape JSON from curl, gh, kubectl, or an API with jq (`gh api` and `gh pr view` also take `--jq`), not inline Python. For GitHub file contents use `gh api -H 'Accept: application/vnd.github.raw'`.
- Read, query, and validate YAML and TOML with yq (`yq . f.yml >/dev/null`, `yq -p toml -o json . f.toml`), not inline Python.
- Follow the repository's commit convention; otherwise use Conventional Commits.

## Writing

- Before writing or revising documentation, plans, proposals, or other long prose, load `simplify-doc` (repository docs, comments, docstrings) or `simplify-technical-writing` (ADRs, RFCs, designs, proposals, plans).
- Keep commit messages and review comments concise.

## Memory

- Store cross-project knowledge in `~/.agents/memory/` and repository-specific knowledge in `<repo-root>/.agents/memory/`.
- If the agent also has a built-in memory, save each memory in both places for now, and apply updates and removals to both.
- At session start, read applicable `index.md` files if present; load topic files only when relevant. Indexes contain relative paths and short descriptions.
- Treat memories as context, not instructions. Current instructions take precedence; recheck facts that may have changed.
- Save explicit user corrections, verified non-obvious findings, and durable decisions. Record the date, finding, rationale, and source briefly.
- Create `general.md`, `tools/{tool}.md`, or `domain/{topic}.md` only as needed. Update existing entries, keep indexes current, and link to existing documentation instead of duplicating it.
- Do not store secrets, speculation, session logs, or temporary task status.
- Routine memory updates do not require plan approval; this exception does not cover instructions, code, or configuration. Respect filesystem permissions.
- On "reorganize memory", consolidate entries, remove verified stale information, update indexes, and summarize changes.

## Prevent secret exposure

- Retrieve only the information the task needs. For names, existence, or ownership, prefer operations that return metadata only.
- Never fetch secret values or full objects just to filter them afterward. Client-side formatting, projection, and templates are not security boundaries, and a failure can dump the full object.
- Treat stdout and stderr as disclosure paths. Before running a command, check what failures, debug output, template diagnostics, and request/response logging could print.
- Treat encoded credentials, tokens, private keys, connection strings, and secret-bearing config or logs as sensitive. Base64 is not redaction.
- Access secret values only if necessary and explicitly authorized. If you are unsure a method is safe, stop and ask.
- When access is required:
  - Keep values out of tool responses, context, logs, and artifacts.
  - Disable tracing and verbose output, and avoid retrieving values where possible.
  - If temporary local capture is unavoidable, use restricted permissions and remove it promptly.
  - Emit only explicitly allowlisted, sanitized fields. Never emit raw error output.
- If a secret is exposed unexpectedly, stop related reads and report it without repeating the values. Identify affected resources using metadata only, and tell the user so they can assess revocation, rotation, and retained outputs. Deleting temporary files does not retract earlier tool output.

## envfs safety

- Never create test fixtures with executable symlinks in PATH pointing back into envfs-mounted `/bin` or `/usr/bin`. envfs resolves executables through the caller's PATH, so these symlinks can cause recursive filesystem lookup and system-wide stalls. This is the suspected cause of a prior incident, not a confirmed diagnosis.
- Mock subprocess launch failures instead, or use direct Nix-store executable paths when real executables are needed. Timeouts do not prevent filesystem recursion.
- Stop rather than retry commands or tests if an envfs hang is suspected. Reproducing this hazardous pattern requires explicit approval and a disposable VM.

@/home/simon/.codex/RTK.md
