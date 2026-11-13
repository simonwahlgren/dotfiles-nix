---
name: tone-of-voice
description: "Draft or rewrite text in the user's own voice using their generated style profile. Use when asked to 'use my tone of voice', 'write as me', 'draft a Slack message in my style', or to rewrite text so it sounds like the user. Not for running the analysis; that is analyze-tone-of-voice."
---

# Write in the user's voice

1. Read `~/.agents/tone-of-voice/profile.md`. If the file is missing, say so, point to `/analyze-tone-of-voice`, and stop.
2. Pick the register (channel post, thread reply, DM) and language that match the request. If unclear, choose the closest fit and state it.
3. Take all content and facts from the user's request. The profile governs style only. Do not add facts, greetings, or emoji the request and profile do not support.
4. Write the draft and follow the profile rules and examples.
5. Show the draft only. Never send or schedule a message without explicit confirmation.
