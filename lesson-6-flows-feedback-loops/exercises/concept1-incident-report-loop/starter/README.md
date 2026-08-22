# Exercise – Incident Report Feedback Loop

## Overview

An SRE submits a terse incident report after a production issue — often just one line. Your task is to build a feedback loop that reviews the report, asks targeted follow-up questions about what is missing, and produces a finalized report only once every required detail has been collected.

You will build this on the Amazon Bedrock AgentCore managed harness. The harness is stateful by default: reusing the same `runtimeSessionId` continues the conversation. That means the entire feedback loop is just **a system prompt + a session** — no agent node, no "User input" toggle, no prepare step.

The prompt is the whole exercise. The infrastructure is one script.

---

## What You Will Build

```
Engineer (chat.py) ── invoke_harness ──▶  AgentCore managed harness
        ▲                                   "incident_report_agent"
        │                                    (Amazon Nova Pro)
        └────────── streamed reply ───────────────┘

          same runtimeSessionId every turn  =  one continuous conversation
```

A complete incident report must cover **all five** of these required fields:

- **Severity** — P1 / P2 / P3 / P4
- **Affected service** — which service, component, or region was impacted
- **Impact** — who or what was affected, and to what extent
- **Root cause** — what caused the incident (a labeled hypothesis is fine)
- **Timeline** — when it started, was detected, and was resolved

---

## Setup

This folder gives you three scripts:

| File | What it does |
|------|--------------|
| `setup.py` | Creates the IAM execution role and the harness. **Contains the `SYSTEM_PROMPT` you must write.** |
| `chat.py` | Provided multi-turn chat client — generates one session id and reuses it every turn (it also hides the `<thinking>…</thinking>` reasoning spans Amazon Nova streams before its replies) |
| `cleanup.py` | Deletes the harness and role when you are done |

You need AWS credentials configured for `us-east-1` and `boto3` installed.

---

## Steps

### Step 1 – Write the system prompt

Open `setup.py` and replace the `TODO` in `SYSTEM_PROMPT` with instructions that make the model:

1. Act as an **incident report coordinator for an SRE team** (role + goal)
2. Check every submission against the **five required fields** listed above (checklist)
3. Ask **exactly one** focused follow-up question per turn about a missing field — never several at once, never about a field it already has (one-question-at-a-time strategy)
4. **Never fabricate** or assume details, and **never produce the final report while any field is missing**
5. Once all five fields are covered, output a structured report that starts with the line `FINAL REPORT` (completion format)

### Step 2 – Create the harness

```bash
python setup.py
```

Wait for `READY` (~2–3 minutes). The script saves the harness ARN to `harness_arn.txt` for the chat client. (The script also disables the harness's long-term memory, so every new session starts clean — conversation state lives only in the session id.)

### Step 3 – Chat

```bash
python chat.py
```

`chat.py` generates one `runtimeSessionId` at startup and sends it with every `invoke_harness` call — that single reused id is what turns separate API calls into one conversation.

---

## Test

### Test 1 – Terse report (the main event)

Start a chat and submit this exact report:

```
API latency spiked at 14:00 UTC
```

Answer each follow-up question naturally (make up plausible details). Verify that the harness:

- asks **one** question per turn, not a bundle
- works through the missing fields without re-asking what you already told it
- never emits `FINAL REPORT` until all five fields have answers
- emits a structured `FINAL REPORT` once they do

### Test 2 – Complete report on turn one

Start a **new** chat session (rerun `chat.py`) and paste a report that already covers all five fields — severity, affected service, impact, root cause, timeline. Verify the harness outputs `FINAL REPORT` immediately, with no follow-up questions.

---

## Cleanup

```bash
python cleanup.py
```

Deletes the harness, the IAM role, and `harness_arn.txt`.

---

## Hints

- Make the five fields an explicit bulleted checklist in the prompt — a named list turns "is this report good enough?" into a field-by-field check the model can actually perform.
- Spell out the per-turn procedure ("On every turn: 1. compare … 2. ask exactly ONE question … 3. never produce the report while …"). Models follow numbered procedures far more reliably than adjectives like "thorough".
- Give the completion output an exact format anchored on the literal line `FINAL REPORT`. That marker is both the model's permission to stop asking and your test's success signal.
- If the model bundles several questions into one turn, tighten the wording: "exactly ONE question" and "Never ask more than one question per turn" are stronger than "one at a time".
- If it produces a report with invented values, add an explicit prohibition: "Do not fabricate or assume any details."
- If it keeps asking the engineer to confirm or refine details they already gave (especially in Test 2), add: "Treat a field as covered as soon as the engineer has given a concrete answer for it — do not ask them to confirm, refine, or quantify it further."
