---
name: ci-triage
description: "Find the root cause of a failing CI, release, or deploy run and propose a fix without changing anything. Use for 'CI fails', 'pipeline failed', 'apply failed', 'release failed', a GitHub Actions run URL, a PR with failing checks, or 'merged, check the run' after a merge. Read-only: does not push fixes or rerun jobs unless asked."
---

# Triage a failing CI run

Work out why a run failed, show the evidence, and propose a fix. This is read-only. Do not push a fix or rerun jobs unless the user asks.

## 1. Find the run

- Run or job URL: take the run id from it (`gh run view <id>`).
- PR with failing checks: `gh pr checks [<number>]`. Use `--json name,bucket,link,workflow` to find the failed checks and their links.
- After a merge ("merged, check the run"): get the merge commit SHA, then `gh run list --commit <sha>`. Follow an unfinished run with `gh run watch <id> --exit-status`.

## 2. Get only the failing logs

For GitHub Actions use `gh run view <id> --log-failed`. For one job use `gh run view --job <job-id> --log-failed`. Filter the output to the failing step and its last 30 to 50 lines, for example with `tail` or `grep -n -i -E 'error|fail|denied'`. Do not put a whole log into context.

Logs can contain secrets. Quote the minimum lines needed, and never echo tokens, environment dumps, or credentials. Redact anything that looks like one.

## 3. Classify

Pick one: test failure, lint or format, build, infrastructure apply, permission or auth, flaky or timeout.

To decide whether the PR's diff caused it, compare the failing files or steps with `gh pr diff` or `git diff <base>...HEAD`. Check whether the same job failed on the base branch (`gh run list --branch <base> --workflow <name>`). A failure that predates the PR is pre-existing.

## 4. Report

- Root cause, in one or two sentences.
- The few log lines that show it.
- Caused by this change or pre-existing, and how you know.
- Proposed fix.

Mark what you verified and what is a hypothesis. If the log was truncated or unavailable, say so.

## Terraform apply failures

Before proposing anything, report which resources failed, which succeeded, and what that means for state: partially applied changes, resources created but not recorded, or a held state lock. Do not suggest `terraform apply`, `force-unlock`, or state edits as a first step. Hand the user the resource list and the options.

## Rerunning

Suggest `gh run rerun <id> --failed` only when the evidence shows the failure is flaky, such as a network timeout or a test that passes on the base branch with no related change. Otherwise propose a code or config fix. To commit and push a fix, use the `commit` and `pr` skills once the user agrees.
