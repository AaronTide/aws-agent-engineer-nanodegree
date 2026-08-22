# Demo 3 – Travel Assistant on the AgentCore Managed Harness

## Overview

In Demos 1 and 2 you wrote chain-of-thought and ReAct prompts by hand. This demo shows the production version of the same idea: an agent on the **Amazon Bedrock AgentCore managed harness** that *acts* on its reasoning by calling real tools — a weather lookup and an attractions lookup — before it answers.

The prompt lesson is one sentence in the agent instruction: **"always use the available tools."** Without it, the model will cheerfully invent London's weather. With it, every recommendation is grounded in tool results. Watch for that grounding as the response streams.

> **What changed from Bedrock Agents?**
> Bedrock Agents Classic closed to new customers on July 30, 2026, so this course uses the AgentCore managed harness instead. Three practical differences:
> - **No Prepare step.** You create the harness once; when its status is `READY`, it stays ready. Change the instruction and it takes effect — no rebuild.
> - **Tools live on an AgentCore Gateway,** not in action groups. The Gateway exposes your Lambdas as MCP tools; any agent you attach the Gateway to can use them.
> - **Traces come from the response stream.** `chat.py` prints each tool call — name, arguments, result — as it happens, replacing the console's "Show trace" panel. Deeper traces are in CloudWatch.
>
> (Bedrock Flows, Prompt Management, Guardrails, and Evaluations are unaffected — you'll keep using them later in the course.)

## What you build

- **Two Lambda functions** (`lambda/get_weather`, `lambda/get_top_attractions`) returning mock data for London, Paris, and New York
- **An AgentCore Gateway** with one Lambda target per tool, so the model sees two MCP tools: `weather___get_weather` and `attractions___get_top_attractions`
- **A managed harness** — the agent itself: Amazon Nova Pro plus the travel-assistant instruction
- **A chat client** (`chat.py`) that streams the answer and prints tool calls live

```
you ──> chat.py ──> AgentCore harness (Nova Pro + instruction)
                        │  tool calls (MCP)
                        ▼
                  AgentCore Gateway ──> Lambda: get_weather
                                   └──> Lambda: get_top_attractions
```

## Setup

Prerequisites: AWS credentials configured for **us-east-1**, Python 3.10+, and `boto3` (`pip install boto3` — any recent version with the AgentCore APIs).

Run the one-shot setup from this folder:

```bash
python setup.py
```

It creates the IAM roles, both Lambdas, the Gateway with its two targets, and the harness (the harness takes ~2–3 minutes to reach `READY`), then writes `demo_config.json` for the other scripts. Everything is created with plain boto3 calls — the same API style you've used all course — so you can read `setup.py` top to bottom and see exactly what gets created and why.

Sharing an account? Use `python setup.py --prefix yourname` to avoid name collisions (then clean up with the same folder's `cleanup.py`, which reads the prefix from `demo_config.json`).

## Steps

1. **Read the agent instruction** at the top of `setup.py` (`SYSTEM_PROMPT`). Note the three behavioral rules: always use tools, prefer indoor when weather is poor, tailor to stated preferences. (When it creates the harness, `setup.py` also appends today's date to the instruction — models have no clock, so without it "this Saturday" makes the model invent a date.)
2. **Skim a Lambda handler** (`lambda/get_weather/lambda_function.py`). With a Gateway, the event *is* the tool arguments — `{"city": "London", "date": "..."}` — and the tool name arrives via `context.client_context.custom["bedrockAgentCoreToolName"]`. Compare this with the old action-group envelope if you've seen it: much simpler.
3. **Run `python setup.py`** and wait for `READY`.
4. **Chat:** `python chat.py` starts an interactive session (one harness session across turns, so follow-ups keep context). Or pass a message as an argument for a single turn.

## Test

```bash
python chat.py "I'll be in London this Saturday with my family. What should we do?"
```

**Expected:** the response streams in ReAct order — you literally watch the loop run:

1. A `<thinking>` passage: Nova narrates its plan (gather weather and attractions first) before acting. This is the chain of thought from Demos 1–2, now driving real actions.
2. Both tool calls, with the arguments the model chose (the stamped date is what lets it work out which date "this Saturday" is), e.g.

   ```
   -> tool call: weather___get_weather({"date":"2026-08-22","city":"London"})
   -> tool call: attractions___get_top_attractions({"city":"London"})
   ```
3. Each tool's result as it comes back through the Gateway:

   ```
   <- result (weather___get_weather): {"condition":"Light rain in the morning, ...
   <- result (attractions___get_top_attractions): {"city":"London","attractions":[...
   ```
4. The final answer, grounded in those results: it mentions the morning rain, leads with indoor options (British Museum, Natural History Museum), and filters for family-friendly choices.

Add `--debug` to dump every raw stream event — useful for seeing exactly how tool use, tool results, and text interleave (tool results arrive as a separate `user`-role message in the stream, mirroring how the Converse API represents them).

## Cleanup

```bash
python cleanup.py
```

Deletes the harness, Gateway targets, Gateway, Lambdas, and IAM roles it created (in that order), then removes `demo_config.json`.

## Hints

- **Tool names are namespaced.** The model sees `<targetName>___<toolName>`; target names may only contain letters, digits, and underscores — a dash in a target name breaks Nova's tool calling.
- **See what the Gateway actually sends:** open CloudWatch → Log groups → `/aws/lambda/demo3-get-weather`. The handler logs the tool name and raw event on every call.
- **Only the model is pinned on purpose.** `setup.py` pins `us.amazon.nova-pro-v1:0` because the harness's default model requires a Marketplace subscription that classroom accounts don't have.
- **Session IDs must be ≥ 33 characters** — `chat.py` generates a UUID-based one and reuses it for the whole conversation, which is what makes multi-turn context work.
- **Experiment with the prompt lesson:** remove "always use the available tools" from `SYSTEM_PROMPT`, run `cleanup.py` then `setup.py` again, and ask the same question. The answer will sound plausible — and be completely ungrounded. That contrast is the point of this demo.
- Harness docs: [managed harness](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html) · [get started](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-get-started.html) · [gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html)
