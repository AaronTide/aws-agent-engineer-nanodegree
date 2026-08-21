# Demo 1 – Requirements Clarification with a Multi-Turn Harness Session

## Overview

This demo builds a requirements analyst that refuses to write a spec until it has all the facts. When a user submits a vague tool request, the analyst asks focused follow-up questions — one at a time — and only produces the final specification once every category on its checklist is covered.

On Bedrock Agents Classic this took an agent with **User input** enabled sitting inside a Bedrock Flow. (Agents Classic is closed to new customers as of July 30, 2026, so this course uses the Amazon Bedrock AgentCore managed harness instead. Bedrock Flows, Prompt Management, Guardrails, and Evaluations are unaffected.) On the harness the whole feedback loop collapses into two things:

1. **A prompt** — role + goal, a required-fields checklist, and a one-question-at-a-time strategy
2. **A session** — the harness is stateful by default; reusing the same `runtimeSessionId` continues the conversation

No agent node. No User-input toggle. No prepare step.

---

## What You Build

```
You (chat.py) ──── invoke_harness ────▶  AgentCore managed harness
      ▲                                     "requirements_analyst"
      │                                      (Amazon Nova Pro)
      └───────── streamed reply ─────────────────┘

        same runtimeSessionId every turn  =  one continuous conversation
```

---

## The System Prompt

The feedback loop lives entirely in the harness's system prompt:

```
You are a requirements analyst for an internal tools team. Your job is to
collect enough information to write a precise requirements specification.

A specification is complete only when you have specific answers for all
three of these categories:
- Purpose: what the tool does and why it is needed
- Key features: the specific capabilities required
- Success criteria: how the team will know it is working correctly

On every turn:
1. Compare everything the user has told you so far against the three
   categories. Any concrete answer the user has given counts as covered —
   including qualitative or behavioral ones. Never ask the user to confirm,
   refine, quantify, or make measurable something they have already told you.
2. If a category has not been addressed at all, or is too vague to write a
   sentence about, ask about the most important gap — phrased as ONE single,
   short question. Never ask two questions in a turn, not even two phrasings
   of the same question, and never re-ask about a category you already have
   an answer for.
3. Do not fabricate or assume any details. The specification may only
   contain details the user actually gave — never add capabilities or
   specifics they did not mention. Do not produce the specification while
   any category is still missing.
4. If all three categories are covered — even in the user's very first
   message — do not ask anything; immediately respond with the specification.

Only when you have specific answers for all three categories, respond with
exactly this format — plain text, no XML tags or wrappers — and nothing else:

REQUIREMENTS COMPLETE
- Purpose: [what the tool does and why it is needed]
- Key features: [the specific capabilities required]
- Success criteria: [how the team will know it is working correctly]
```

Three prompt patterns to point out:

- **Role + goal** — "requirements analyst … collect enough information" frames every turn.
- **Required-fields checklist** — three named categories turn "is this enough detail?" into a concrete field-by-field check.
- **One-question-at-a-time strategy** — an explicit per-turn procedure plus a completion marker (`REQUIREMENTS COMPLETE`) the model may only emit when the checklist is satisfied.

Every seemingly redundant sentence in the procedure earns its keep — each one was added because the model misbehaved without it. "Any concrete answer counts as covered" stops the model from asking the user to make an already-given answer more measurable; "phrased as ONE single, short question" stops it from restating the same question twice in a turn; "plain text, no XML tags" stops it from wrapping the final spec in invented markup; "even in the user's very first message" makes a fully-specified request complete immediately instead of triggering a confirmation question.

---

## Setup

From this folder, with AWS credentials configured for `us-east-1`:

```bash
python setup_demo.py
```

The script creates an IAM execution role and the harness (pinned to Amazon Nova Pro, with the harness's long-term memory disabled so every new session starts clean — state lives only in the session id), waits until the harness is `READY` (~2–3 minutes), and writes `harness_arn.txt` for the chat script.

---

## The Chat Script

`chat.py` (in this folder) is the entire multi-turn client. The only load-bearing lines:

```python
session_id = f"lesson6-{uuid.uuid4()}"   # generated ONCE, reused every turn (must be ≥ 33 chars)

response = runtime.invoke_harness(
    harnessArn=harness_arn,
    runtimeSessionId=session_id,          # same id = same conversation
    messages=[{"role": "user", "content": [{"text": user_text}]}],
)
```

Because the harness keeps the conversation state server-side, the client never resends history — each call carries only the new user message.

The rest of the script just prints the streamed reply. One detail: Amazon Nova often streams its private reasoning first, wrapped in `<thinking>…</thinking>` tags, so `chat.py` filters those spans out and shows only the reply meant for the user.

Start it with:

```bash
python chat.py
```

---

## Test Prompts

**Test 1 – Vague request** → expected: one focused follow-up question per turn, over several turns

```
I need a dashboard for the AI agent.
```

**Test 2 – Partially detailed** → expected: questions only about the missing categories

```
We need a tool to track employee onboarding. It should show which steps each new hire has completed.
```

**Test 3 – Already complete** → expected: `REQUIREMENTS COMPLETE` immediately, no follow-up questions

```
Build an internal API status page for our platform engineers. The purpose is to help on-call engineers to quickly troubleshoot incidents. It should poll our 12 microservices every 60 seconds, show uptime percentage and last response time for each, and send a Slack alert when any service is down for more than 2 minutes. Success means on-call engineers stop checking Grafana manually during incidents.
```

---

## Sample Conversation

Run `python chat.py` and start with the vague request; answer the follow-up questions naturally:

```
You: I need a dashboard for the AI agent.
Agent: What is the purpose of the dashboard for the AI agent?
You: It should show the agent's health so the ops team can spot failures
     quickly — today we have no visibility at all.
Agent: What are the key features required for the dashboard to show the
       agent's health?
You: It needs to show request volume, error rate, and average latency per
     hour, pulled from CloudWatch, with a red banner when the error rate
     goes above 5%.
Agent: How will the team know the dashboard is working correctly?
You: Success means the ops team detects agent failures within 5 minutes
     instead of hearing about them from users.
Agent: REQUIREMENTS COMPLETE
       - Purpose: The dashboard shows the AI agent's health to allow the
         ops team to spot failures quickly.
       - Key features: The dashboard displays request volume, error rate,
         and average latency per hour, pulled from CloudWatch. It includes
         a red banner when the error rate exceeds 5%.
       - Success criteria: The ops team detects agent failures within
         5 minutes instead of hearing about them from users.
```

Each turn used the same session id — that reuse *is* the feedback loop.

---

## Cleanup

```bash
python cleanup_demo.py
```

Deletes the harness, the IAM role, and the local `harness_arn.txt`.

---

## Docs

- AgentCore managed harness: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html
- Get started: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-get-started.html
