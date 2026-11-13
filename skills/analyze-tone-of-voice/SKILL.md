---
name: analyze-tone-of-voice
description: "Analyze the user's own Slack messages and build or update their tone-of-voice profile in ~/.agents/tone-of-voice/. Use for /analyze-tone-of-voice or when asked to refresh the profile. The first run samples the last 2 years; later runs analyze only newer messages. To write text in the user's voice, use tone-of-voice instead."
---

# Analyze tone of voice from Slack

Build a style profile from the user's Slack messages only. Data lives in `~/.agents/tone-of-voice/`, outside git, because it quotes private Slack.

- `profile.md`: the only file the `tone-of-voice` skill reads. Maximum about 500 words.
- `evidence.md`: longer observations with rough counts. Read only by this skill. Maximum about 1,500 words.
- `state.json`: `{"watermark": "<ISO timestamp of newest analyzed message>", "last_run": "<date>", "message_count": <cumulative>}`.

Never store raw messages.

## Fetch

1. Use the Slack search tool available in this session. If none exists, stop and say so. In Claude Code, load `mcp__plugin_slack_slack__slack_search_public_and_private` with ToolSearch.
2. Get the user's Slack user ID from the tool description (the logged-in user) or from the Slack profile tools. Do not hardcode an ID.
3. Query with `from:<@USERID>` (verified syntax) plus `after:YYYY-MM-DD` and `before:YYYY-MM-DD`. Search public, private, DM, and group DM channels. Set `include_context` to false, `response_format` to `concise`, `limit` to 20, `sort` to `timestamp`, and `sort_dir` to `asc`. Exclude bots.
4. Slack date filters work by day and exclude the named day. Results show local time; convert to the watermark's timezone before comparing. Drop any message at or before the watermark.
5. If the harness supports subagents, run steps 6 to 8 in subagents and return only distilled observations, counts, and example messages. Otherwise run them here.
6. If `state.json` is missing, sample. For each calendar month of the last 24 months, fetch one page (20 messages) from each third of the month (days 1 to 10, 11 to 20, 21 to end), so the sample is not only the first days.
7. If `state.json` exists, fetch every message after the watermark, oldest first, up to 15 pages. If the cap is hit, set the new watermark to the newest message analyzed so the next run continues from there.
8. Skip messages that are mostly pasted code, logs, links, or automated text when judging style.

## Observe

Note, per register (channel post, thread reply, DM) and per language:

- The real language mix. Do not assume it.
- Sentence and message length, capitalization, punctuation.
- Greetings and sign-offs, emoji and which ones, hedging, humor, typical phrases, formatting habits.
- What the user never does.
- Rough counts for each trait.

## Merge

1. Read `evidence.md` if it exists. Merge the new observations into it and update the counts. Consolidate rather than append, and keep it within its cap.
2. Regenerate `profile.md` from `evidence.md`. Use concrete, checkable rules grouped by register, then by language if more than one appears. Add a few short real example messages per register. Remove other people's names, customer data, and secrets from examples.
3. Write `state.json` last, so a failed run does not advance the watermark. Add the new message count to the cumulative count.

## Report

Report the number of messages analyzed, the date range, and what changed in the profile.
