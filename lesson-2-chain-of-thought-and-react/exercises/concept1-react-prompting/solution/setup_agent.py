#!/usr/bin/env python3
"""Create the restaurant recommendation agent on Amazon Bedrock AgentCore.

This script wires together everything the CloudFormation stack deployed:

    1. Creates an AgentCore Gateway (the agent's toolbox, speaking MCP).
    2. Adds one gateway target per tool Lambda, with the tool's schema.
    3. Creates an AgentCore managed harness (the agent itself) with your
       instruction prompt. No "prepare" step is needed — once the harness
       reaches READY you can invoke it immediately.

Usage:
    python setup_agent.py [--stack-name restaurant-agent]

It reads the Lambda ARNs and role ARNs from the CloudFormation stack outputs,
and writes agent_config.json next to this script for invoke_agent.py /
cleanup.py to use.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"

# Pin the model. Do NOT rely on the harness default model — it is not
# available in the lab AWS accounts. temperature 0.0 + topK 1 make Nova's
# tool calling deterministic and reliable.
MODEL_ID = "us.amazon.nova-pro-v1:0"

# ---------------------------------------------------------------------------
# The agent instruction (system prompt). This is the heart of the exercise:
# it must force tool-grounded answers — the agent may only talk about
# restaurants the tools returned, and must verify availability before
# recommending.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
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
"""

# ---------------------------------------------------------------------------
# Tool wiring: one gateway target per Lambda. Target names may use ONLY
# letters and digits; tool names ONLY letters, digits, and underscores.
# Never use a dash in either: the model sees tools namespaced as
# "<targetName>___<toolName>", and a dash in that string breaks tool calling.
# ---------------------------------------------------------------------------
TOOL_TARGETS = [
    {
        "target_name": "cuisines",
        "lambda_output_key": "GetCuisinesFunctionArn",
        "tools": [
            {
                "name": "get_cuisines",
                "description": "Returns the list of cuisine types available.",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ],
    },
    {
        "target_name": "restaurants",
        "lambda_output_key": "SearchRestaurantsFunctionArn",
        "tools": [
            {
                "name": "search_restaurants",
                "description": (
                    "Searches for restaurants. Returns all restaurants if "
                    "no cuisine is specified."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cuisine": {
                            "type": "string",
                            "description": (
                                "The cuisine type (e.g. Italian, Japanese). "
                                "If omitted, all restaurants are returned."
                            ),
                        }
                    },
                },
            }
        ],
    },
    {
        "target_name": "availability",
        "lambda_output_key": "GetAvailabilityFunctionArn",
        "tools": [
            {
                "name": "get_availability",
                "description": (
                    "Checks whether a specific restaurant has availability "
                    "for tonight."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "string",
                            "description": "The unique ID of the restaurant, e.g. r1.",
                        }
                    },
                    "required": ["restaurant_id"],
                },
            }
        ],
    },
]

CONFIG_PATH = Path(__file__).parent / "agent_config.json"


def check_inputs():
    """Fail fast on the two classic mistakes: no prompt, dashed names."""
    if not SYSTEM_PROMPT.strip():
        sys.exit("SYSTEM_PROMPT is empty — write your agent instruction first "
                 "(see the README).")
    for target in TOOL_TARGETS:
        if not re.fullmatch(r"[A-Za-z0-9]+", target["target_name"]):
            sys.exit(f"Invalid target name '{target['target_name']}': gateway "
                     "target names may only contain letters and digits — the "
                     "API rejects underscores, and a dash breaks tool calling.")
        for tool in target["tools"]:
            if not re.fullmatch(r"[A-Za-z0-9_]+", tool["name"]):
                sys.exit(f"Invalid tool name '{tool['name']}': tool names may "
                         "only contain letters, digits, and underscores — "
                         "no dashes.")
            if not tool["description"].strip():
                sys.exit(f"Tool '{tool['name']}' has an empty description — "
                         "the model relies on it to pick the right tool.")


def stack_outputs(stack_name):
    """Read the CloudFormation outputs (Lambda ARNs + role ARNs)."""
    cfn = boto3.client("cloudformation", region_name=REGION)
    try:
        stack = cfn.describe_stacks(StackName=stack_name)["Stacks"][0]
    except ClientError:
        sys.exit(f"Could not read stack '{stack_name}'. Deploy it first "
                 "(see the README) or pass --stack-name.")
    return {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}


def create_with_retry(fn, what, attempts=3, delay=10):
    """New IAM roles can take a few seconds to propagate; retry politely."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except ClientError as err:
            if attempt == attempts:
                raise
            code = err.response.get("Error", {}).get("Code", "error")
            print(f"  {what} failed ({code}); retrying in {delay}s — "
                  "new IAM roles can take a moment to propagate...")
            time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stack-name", default="restaurant-agent",
                        help="CloudFormation stack you deployed (default: restaurant-agent)")
    args = parser.parse_args()

    check_inputs()

    outputs = stack_outputs(args.stack_name)
    for key in ("GatewayRoleArn", "HarnessRoleArn"):
        if key not in outputs:
            sys.exit(f"Stack output '{key}' not found — did you deploy the "
                     "template from this exercise?")

    # Two different naming rules apply (both enforced by the API):
    #   - Gateway names allow letters, digits, and dashes — no underscores.
    #   - Harness names allow letters, digits, and underscores — no dashes.
    gateway_name = f"{args.stack_name}-gw"
    harness_name = args.stack_name.replace("-", "_") + "_harness"

    acc = boto3.client("bedrock-agentcore-control", region_name=REGION)

    # -- 1. Gateway (the agent's toolbox) -----------------------------------
    print(f"Creating AgentCore Gateway '{gateway_name}'...")
    gw = create_with_retry(
        lambda: acc.create_gateway(
            name=gateway_name,
            roleArn=outputs["GatewayRoleArn"],
            protocolType="MCP",
            authorizerType="AWS_IAM",
        ),
        "create_gateway",
    )
    gateway_id = gw["gatewayId"]
    gateway_arn = gw["gatewayArn"]

    # Gateway creation is asynchronous — wait for READY before adding targets.
    deadline = time.time() + 5 * 60
    while True:
        status = acc.get_gateway(gatewayIdentifier=gateway_id).get("status")
        if status == "READY":
            break
        if status in ("FAILED", "DELETING"):
            sys.exit(f"Gateway entered status {status} — run cleanup.py and "
                     "try again.")
        if time.time() > deadline:
            sys.exit("Timed out waiting for the gateway to become READY.")
        time.sleep(5)
    print(f"  gateway ready: {gateway_arn}")

    # -- 2. One target per tool Lambda --------------------------------------
    for target in TOOL_TARGETS:
        print(f"Adding gateway target '{target['target_name']}' "
              f"-> {target['lambda_output_key']}...")
        create_with_retry(
            lambda t=target: acc.create_gateway_target(
                gatewayIdentifier=gateway_id,
                name=t["target_name"],
                targetConfiguration={
                    "mcp": {
                        "lambda": {
                            "lambdaArn": outputs[t["lambda_output_key"]],
                            "toolSchema": {"inlinePayload": t["tools"]},
                        }
                    }
                },
                credentialProviderConfigurations=[
                    {"credentialProviderType": "GATEWAY_IAM_ROLE"}
                ],
            ),
            f"create_gateway_target({target['target_name']})",
        )

    # -- 3. Managed harness (the agent itself) ------------------------------
    print(f"Creating AgentCore managed harness '{harness_name}'...")
    harness = create_with_retry(
        lambda: acc.create_harness(
            harnessName=harness_name,
            executionRoleArn=outputs["HarnessRoleArn"],
            model={
                "bedrockModelConfig": {
                    "modelId": MODEL_ID,
                    "temperature": 0.0,
                    "additionalParams": {
                        "additionalModelRequestFields": {
                            "inferenceConfig": {"topK": 1}
                        }
                    },
                }
            },
            systemPrompt=[{"text": SYSTEM_PROMPT}],
        ),
        "create_harness",
    )["harness"]
    harness_id = harness["harnessId"]
    harness_arn = harness["arn"]

    # No "prepare" step exists (or is needed): just wait for READY (~2-3 min).
    print("  waiting for the harness to become READY (usually 2-3 minutes)...")
    deadline = time.time() + 12 * 60
    while True:
        h = acc.get_harness(harnessId=harness_id)["harness"]
        status = h.get("status")
        if status == "READY":
            break
        if status in ("CREATE_FAILED", "FAILED", "DELETING"):
            reason = h.get("failureReason") or "no reason given"
            sys.exit(f"Harness entered status {status}: {reason}\n"
                     "Run 'python cleanup.py --keep-stack', wait for it to "
                     "finish, then run setup_agent.py again.")
        if time.time() > deadline:
            sys.exit("Timed out waiting for the harness to become READY.")
        print(f"    status: {status}")
        time.sleep(15)
    print(f"  harness READY: {harness_arn}")

    # -- 4. Save what invoke_agent.py / cleanup.py need ---------------------
    CONFIG_PATH.write_text(json.dumps({
        "stack_name": args.stack_name,
        "gateway_name": gateway_name,
        "gateway_id": gateway_id,
        "gateway_arn": gateway_arn,
        "harness_name": harness_name,
        "harness_id": harness_id,
        "harness_arn": harness_arn,
    }, indent=2))
    print(f"\nWrote {CONFIG_PATH.name}. Test your agent with:")
    print('  python invoke_agent.py "Find me an Italian restaurant for tonight."')


if __name__ == "__main__":
    main()
