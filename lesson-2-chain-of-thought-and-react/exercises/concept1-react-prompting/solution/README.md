# Exercise Solution – Restaurant Recommendation Agent

## Overview

This folder contains the complete, runnable solution: a filled-in `setup_agent.py` (instruction prompt + tool schemas), plus the same `invoke_agent.py` and `cleanup.py` as the starter. The Lambdas and the CloudFormation template are shared with the starter folder.

## What you build

An **AgentCore managed harness** (Amazon Nova Pro) whose tools are the three provided Lambdas, exposed through one **AgentCore Gateway** with three targets: `cuisines` → `get_cuisines`, `restaurants` → `search_restaurants`, `availability` → `get_availability`.

## Setup

From this `solution/` folder, deploy the shared CloudFormation template (Lambdas + all roles), then create the agent:

```bash
aws cloudformation deploy \
  --template-file ../starter/template.yaml \
  --stack-name restaurant-agent \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

python setup_agent.py
```

`setup_agent.py` creates the gateway, its three Lambda targets, and the harness, then waits (2–3 minutes) for `READY` — no "prepare" step exists or is needed. A retry message during setup is normal (fresh IAM roles take a few seconds to propagate).

## Agent Instruction

The instruction that forces tool-grounded behavior (this is `SYSTEM_PROMPT` in `setup_agent.py`):

```
You are a helpful restaurant recommendation assistant for a single city — the
one the user is in — so never ask for their location.

Always ground every answer in tool results. When the user asks for a
restaurant recommendation:
1. First call get_cuisines to discover which cuisine types exist.
2. Then call search_restaurants to find matching restaurants.
3. Before recommending a restaurant, call get_availability to confirm it has
   a table tonight. If it is not available, check the next best option from
   the search results.

Never invent, guess, or embellish restaurants, ratings, or availability —
mention only restaurants the tools returned, with the ratings the tools
reported. If no matching restaurant is available, say so honestly instead of
making something up.
```

Why it works:

- The **numbered order** makes the ReAct loop explicit, so the model reliably calls all three tools instead of jumping straight to an answer.
- The **grounding clause** ("mention only restaurants the tools returned") is what stops the model from inventing plausible-sounding restaurants.
- The **fallback rule** handles the built-in trap: `Osteria Romana` (r2) has no availability, so an agent that checks it first must fall back to `Trattoria Bella` (r1) — using tool data, not imagination.

## Tool wiring

One gateway target per Lambda (target names use only letters and digits, tool names only letters, digits, and underscores — the model sees tools namespaced as `<targetName>___<toolName>`, and dashes break tool calling):

| Target | Tool | Parameters |
|--------|------|------------|
| `cuisines` | `get_cuisines` — returns the list of cuisine types available | none |
| `restaurants` | `search_restaurants` — searches for restaurants; returns all if no cuisine given | `cuisine` (string, optional) |
| `availability` | `get_availability` — checks whether a restaurant has availability tonight | `restaurant_id` (string, **required**) |

The exact JSON Schemas are in `TOOL_TARGETS` in `setup_agent.py`.

## Test

```bash
python invoke_agent.py "Find me an Italian restaurant for tonight."
```

Expected agent behavior:

1. The agent calls `get_cuisines` to discover the available cuisine types
2. The agent calls `search_restaurants` with `cuisine=Italian` and receives `Trattoria Bella` (r1) and `Osteria Romana` (r2)
3. The agent calls `get_availability` with `restaurant_id=r1` — `Trattoria Bella` has availability
4. The agent recommends `Trattoria Bella`, citing the rating the tool returned (4.6)
5. If the agent tries `Osteria Romana` (r2) first, it finds no availability and falls back to `Trattoria Bella`

Expected output shape (abridged — Nova streams its reasoning in `<thinking>`
tags between the tool calls; that is the ReAct "Thought" step, live):

```
<thinking> To find an Italian restaurant for tonight, I first need to check the available cuisines ... </thinking>
[tool call] cuisines___get_cuisines({})
<thinking> Italian cuisine is available. Now I will search for Italian restaurants. </thinking>
[tool call] restaurants___search_restaurants({"cuisine":"Italian"})
<thinking> ... I will first check the availability of Trattoria Bella. </thinking>
[tool call] availability___get_availability({"restaurant_id":"r1"})
<thinking> Trattoria Bella has availability for tonight. ... </thinking> Trattoria Bella is an Italian restaurant with a rating of 4.6, and it has availability for tonight.

--- tool calls observed: get_availability, get_cuisines, search_restaurants
--- All three tools were used before the recommendation: the answer is tool-grounded.
```

To continue the conversation, re-run with `--session <id>` (the id is printed
on the first run). On follow-up turns the agent may reuse tool results from
earlier in the session instead of re-calling every tool — that is the
harness's session state at work, so the three-tool verdict applies to the
first turn of a fresh session (the script says so when you use `--session`).

You can double-check that the calls landed in CloudWatch Logs (`/aws/lambda/restaurant-agent-*`): each Lambda prints the tool name it received (from `context.client_context`) and the event (the tool arguments).

## Cleanup

When you are done, delete everything — the harness, the gateway and its targets, and the CloudFormation stack:

```bash
python cleanup.py
```

To iterate on the instruction only, use `python cleanup.py --keep-stack`, edit `SYSTEM_PROMPT`, and run `python setup_agent.py` again. Let cleanup finish before re-running setup: it also waits for the harness's managed session memory to delete (a minute or two) — recreating the agent under the same name too early fails with "Memory ... already exists".

## Hints

- The model is pinned to `us.amazon.nova-pro-v1:0` with `temperature 0.0` and `topK 1` — this makes Nova's tool calling deterministic; leave those settings alone.
- The Lambdas receive the **tool arguments as the event** (e.g. `{"cuisine": "Italian"}`) and the tool name via `context.client_context` — not the old Bedrock Agents action-group envelope. Whatever they return is passed back to the agent as the tool result.
- The gateway invokes the Lambdas with the **gateway role** from the stack (`restaurant-agent-gateway-role`); no resource-based Lambda permission is involved.
