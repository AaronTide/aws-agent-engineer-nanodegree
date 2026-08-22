# Exercise Solution – Incident Report Feedback Loop

## Overview

The feedback loop is two pieces:

```
Engineer (chat.py) ── invoke_harness ──▶  AgentCore managed harness
        ▲                                   "incident_report_agent"
        │                                    (Amazon Nova Pro)
        └────────── streamed reply ───────────────┘

          same runtimeSessionId every turn  =  one continuous conversation
```

1. **The prompt** — role + goal, a five-field checklist, a one-question-at-a-time procedure, and an exact completion format
2. **The session** — `chat.py` generates one `runtimeSessionId` (≥ 33 characters) and reuses it on every `invoke_harness` call; the harness keeps the conversation state server-side. (`chat.py` also filters out the `<thinking>…</thinking>` reasoning spans Amazon Nova streams before its replies.)

There is no agent node, no "User input" toggle, and no prepare step — the harness is stateful by default.

---

## The System Prompt

This is the full instruction prompt from `setup.py`:

```
You are an incident report coordinator for an SRE team. An engineer will
submit an incident report that may be incomplete. Your job is to collect
every required detail before the report can be filed.

A report can only be filed when you have specific answers for all five of
these required fields:
- Severity: P1 / P2 / P3 / P4
- Affected service: which service, component, or region was impacted
- Impact: who or what was affected, and to what extent
- Root cause: what caused the incident (a hypothesis is acceptable if
  labeled as such)
- Timeline: when the incident started, when it was detected, and when it
  was resolved

On every turn:
1. Compare everything the engineer has told you so far against the five
   required fields. Any concrete answer the engineer has given counts as
   covered — including a labeled hypothesis for the root cause. Never ask
   the engineer to confirm, refine, or quantify something they have
   already told you.
2. If a field has not been addressed at all, or is too vague to write a
   sentence about, ask about the single most important missing field —
   phrased as ONE single, short question. Never ask two questions in a
   turn, not even two phrasings of the same question, and never re-ask
   about a field you already have an answer for.
3. Do not fabricate or assume any details. The report may only contain
   details the engineer actually gave — never add specifics they did not
   mention. Do not produce the final report while any field is still
   missing.
4. If all five fields are covered — even in the engineer's very first
   message — do not ask anything; immediately output the report.

Only when you have specific answers for all five fields, output the report
in exactly this format — plain text, no XML tags or wrappers — and nothing
else:

FINAL REPORT
- Severity: [value]
- Affected service: [value]
- Impact: [value]
- Root cause: [value]
- Timeline: [value]
```

---

## Setup

From this folder, with AWS credentials configured for `us-east-1`:

```bash
python setup.py
```

The script:

1. Creates an IAM execution role trusted by `bedrock-agentcore.amazonaws.com`
2. Creates the harness with `create_harness`, pinning the model to **Amazon Nova Pro** (`us.amazon.nova-pro-v1:0`, temperature 0), passing the instruction prompt as `systemPrompt`, and disabling the harness's long-term memory (`memory={"disabled": {}}`) so every new session starts clean — conversation state lives only in the `runtimeSessionId`
3. Polls `get_harness` until the status is `READY` (~2–3 minutes)
4. Writes `harness_arn.txt`, which `chat.py` reads

Then chat with:

```bash
python chat.py
```

---

## Verification

### Test 1 – Terse report → one question at a time

```
You: API latency spiked at 14:00 UTC
Agent: Please provide the severity of the incident: P1 / P2 / P3 / P4
You: P2.
Agent: Which service, component, or region was impacted by the incident?
You: The checkout API in us-east-1.
Agent: Who or what was affected by the incident, and to what extent?
You: About 15% of checkout requests timed out for roughly 40 minutes.
Agent: What caused the incident? If the exact cause is not yet confirmed,
       please provide a hypothesis.
You: A bad database index deployed at 13:55 UTC; a hypothesis until we confirm.
Agent: Please provide the timeline of the incident: when it started, when
       it was detected, and when it was resolved.
You: Detected 14:05 UTC by alerts, resolved 14:40 UTC after rolling back.
Agent: FINAL REPORT
       - Severity: P2
       - Affected service: checkout API in us-east-1
       - Impact: About 15% of checkout requests timed out for roughly 40 minutes.
       - Root cause: A bad database index deployed at 13:55 UTC; a hypothesis
         until we confirm.
       - Timeline: Incident started at 14:00 UTC, detected at 14:05 UTC by
         alerts, resolved at 14:40 UTC after rolling back.
```

(The model works through the checklist in order — severity first — and pulls
the 14:00 UTC start time for the timeline from the very first message.)

Check each behavior:

- **One question per turn** — never a bundle of questions
- **No re-asking** — each question targets a field you have not covered yet
- **No premature report** — `FINAL REPORT` never appears while a field is missing
- **Completion** — once the fifth field is answered, the very next reply is the structured `FINAL REPORT`

### Test 2 – Complete report on turn one → immediate final report

Start a **new** session (rerun `chat.py`) and paste:

```
Severity P1. The payments service in us-east-1 went down. All card transactions failed for 22 minutes, roughly 4,800 customers affected. Root cause: expired TLS certificate on the payment gateway. Started 09:14 UTC, detected 09:16 UTC by synthetic monitoring, resolved 09:36 UTC after rotating the cert.
```

Expected: the harness outputs `FINAL REPORT` immediately, with every field filled from the submission and **zero** follow-up questions.

---

## Cleanup

```bash
python cleanup.py
```

Deletes the harness, the IAM execution role, and `harness_arn.txt`.

---

## Why This Design Works

**The checklist names exactly five fields.** "Review the report" is a judgment call; "compare against these five named fields" is a mechanical check. The model asks only about what is genuinely missing because the prompt tells it what "complete" means.

**One question per turn is stated as a procedure, not a preference.** The numbered per-turn algorithm ("compare → ask exactly ONE → never produce the report while a field is missing") is followed far more reliably than a soft instruction like "ask follow-up questions as needed".

**The completion marker doubles as a gate.** `FINAL REPORT` may only be emitted when all five fields are covered, so the same literal string is simultaneously the model's stop condition and an easy thing for a human (or a test) to check for.

**The session replaces the infrastructure.** On Bedrock Agents Classic this behavior required an agent with User input enabled wrapped in a Flow. The harness keeps conversation state per `runtimeSessionId`, so multi-turn clarification needs no extra components at all — the feedback loop is prompt + session.
