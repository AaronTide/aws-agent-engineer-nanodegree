# Exercise – Technical Documentation Assistant

## Overview

Your engineering team writes fast, messy implementation notes during feature development. Those notes are hard for other developers to understand later. Your task is to build a Bedrock Playground prompt that turns informal notes into polished internal documentation. The assistant should behave like an experienced technical writer who understands software systems and writes clearly for engineers.

---

## Task 1 – Write an Initial Role-Based Prompt

Set a system prompt in Bedrock Playground that:

- Assigns the model a clear role as a technical documentation specialist
- Specifies the audience as internal software engineers
- Describes the expected output format (structured sections, clear language)

Test it with the sample notes in Task 2 before refining.

---

## Task 2 – Test with Sample Engineering Notes

Use the rough notes below as your user message. Paste them as-is — do not clean them up.

```
<engineering_notes>
auth flow changes - pushed to staging 3/10

old way: session token stored in cookie, validated on every req via middleware
new way: JWT issued at login, includes user_id + role + exp timestamp. middleware now just verifies signature + checks exp, no db lookup on each req

why: db was getting hammered on high-traffic endpoints, latency was bad. this cuts ~40% of auth-related db queries

edge cases we handled:
- token refresh: silent refresh at 5 min before exp using refresh token in httpOnly cookie
- logout: we add token to blocklist in redis, TTL matches token exp
- role changes: if admin revokes role mid-session, old token still valid until exp. known tradeoff, acceptable for now

not done yet: need to write migration guide for services still using old session middleware. also need to update the API gateway config to pass Authorization header correctly
</engineering_notes>
```

Observe where the output is unclear, too verbose, or missing structure. Take notes — you will use them in Task 3.

---

## Task 3 – Refine Your Prompt

Based on what you observed, update the system prompt to address at least two of the following:

- Output structure (headings, sections, bullet lists)
- Level of detail (technical depth vs. plain language)
- What to do with incomplete items (the "not done yet" notes)
- Tone (neutral/formal vs. conversational)

Run the same notes through the refined prompt and compare the outputs.

---

## Task 4 – Experiment

Try at least one of the following and note what changes:

- Swap to a different model and run the same prompt
- Adjust Temperature (try 0 vs. 0.7) and observe variation
- Change the audience in your role (e.g., "for a non-technical product manager") and compare the result

---

## Deliverable

Submit:
1. Your final system prompt
2. The model and any parameter settings you used
3. The documentation output generated from the engineering notes above
