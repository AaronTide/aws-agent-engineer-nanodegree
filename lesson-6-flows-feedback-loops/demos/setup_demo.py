#!/usr/bin/env python3
"""
setup_demo.py — one-shot setup for the Demo 1 requirements analyst.

Creates two things:
  1. An IAM execution role the harness runs as
  2. An Amazon Bedrock AgentCore managed harness pinned to Amazon Nova Pro,
     with the requirements-analyst instructions as its system prompt

Run:
    python setup_demo.py                  # default name: requirements_analyst
    python setup_demo.py --name my_name   # optional custom name

When it finishes it writes harness_arn.txt next to this script, which
chat.py reads. Tear everything down later with cleanup_demo.py.
"""
import argparse
import json
import pathlib
import secrets
import sys
import time

import boto3

REGION = "us-east-1"

# Always pin the model. Do not rely on the harness default model.
MODEL_ID = "us.amazon.nova-pro-v1:0"

# The whole feedback loop lives in this prompt: a role and goal, a
# required-fields checklist, and a one-question-at-a-time strategy.
SYSTEM_PROMPT = """\
You are a requirements analyst for an internal tools team. Your job is to \
collect enough information to write a precise requirements specification.

A specification is complete only when you have specific answers for all \
three of these categories:
- Purpose: what the tool does and why it is needed
- Key features: the specific capabilities required
- Success criteria: how the team will know it is working correctly

On every turn:
1. Compare everything the user has told you so far against the three \
categories. Any concrete answer the user has given counts as covered — \
including qualitative or behavioral ones. Never ask the user to confirm, \
refine, quantify, or make measurable something they have already told you.
2. If a category has not been addressed at all, or is too vague to write a \
sentence about, ask about the most important gap — phrased as ONE single, \
short question. Never ask two questions in a turn, not even two phrasings \
of the same question, and never re-ask about a category you already have \
an answer for.
3. Do not fabricate or assume any details. The specification may only \
contain details the user actually gave — never add capabilities or \
specifics they did not mention. Do not produce the specification while \
any category is still missing.
4. If all three categories are covered — even in the user's very first \
message — do not ask anything; immediately respond with the specification.

Only when you have specific answers for all three categories, respond with \
exactly this format — plain text, no XML tags or wrappers — and nothing else:

REQUIREMENTS COMPLETE
- Purpose: [what the tool does and why it is needed]
- Key features: [the specific capabilities required]
- Success criteria: [how the team will know it is working correctly]
"""

# The harness assumes this role when it runs.
TRUST_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ],
}


def execution_policy(account_id):
    """Standard AgentCore harness execution policy for this course."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "InvokeModels",
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/*",
                    f"arn:aws:bedrock:{REGION}:{account_id}:*",
                    f"arn:aws:bedrock:*:{account_id}:inference-profile/*",
                ],
            },
            {
                "Sid": "ServiceTokens",
                "Effect": "Allow",
                "Action": ["ecr-public:GetAuthorizationToken", "sts:GetServiceBearerToken"],
                "Resource": "*",
            },
            {
                "Sid": "Tracing",
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets",
                ],
                "Resource": "*",
            },
            {
                "Sid": "HarnessLogs",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams",
                    "logs:PutLogEvents",
                ],
                "Resource": [
                    f"arn:aws:logs:{REGION}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*",
                    f"arn:aws:logs:{REGION}:{account_id}:log-group:*",
                ],
            },
            {
                "Sid": "LogPolicy",
                "Effect": "Allow",
                "Action": "logs:PutResourcePolicy",
                "Resource": "*",
            },
            {
                "Sid": "Metrics",
                "Effect": "Allow",
                "Action": "cloudwatch:PutMetricData",
                "Resource": "*",
                "Condition": {"StringEquals": {"cloudwatch:namespace": "bedrock-agentcore"}},
            },
            {
                "Sid": "WorkloadIdentity",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId",
                ],
                "Resource": f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:workload-identity-directory/default*",
            },
            {
                "Sid": "SessionMemory",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:CreateEvent",
                    "bedrock-agentcore:GetEvent",
                    "bedrock-agentcore:ListEvents",
                    "bedrock-agentcore:DeleteEvent",
                    "bedrock-agentcore:RetrieveMemoryRecords",
                ],
                "Resource": f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:memory/*",
            },
            {
                "Sid": "CodeInterpreter",
                "Effect": "Allow",
                "Action": [
                    "bedrock-agentcore:StartCodeInterpreterSession",
                    "bedrock-agentcore:InvokeCodeInterpreter",
                    "bedrock-agentcore:GetCodeInterpreterSession",
                    "bedrock-agentcore:StopCodeInterpreterSession",
                ],
                "Resource": f"arn:aws:bedrock-agentcore:{REGION}:aws:code-interpreter/*",
            },
            {
                "Sid": "Gateways",
                "Effect": "Allow",
                "Action": "bedrock-agentcore:InvokeGateway",
                "Resource": f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:gateway/*",
            },
            {
                "Sid": "Marketplace",
                "Effect": "Allow",
                "Action": ["aws-marketplace:ViewSubscriptions", "aws-marketplace:Subscribe"],
                "Resource": "*",
            },
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Create the demo harness")
    parser.add_argument(
        "--name",
        default="requirements_analyst",
        help="Harness name (letters, digits, underscores only)",
    )
    args = parser.parse_args()
    name = args.name
    # Give the role a fresh name on every run. Recreating a role under a
    # just-deleted name can hand the new harness stale credentials for the
    # old role for several minutes; a unique name sidesteps that entirely.
    # cleanup_demo.py deletes every role that starts with "<name>_role".
    role_name = f"{name}_role_{secrets.token_hex(4)}"

    iam = boto3.client("iam", region_name=REGION)
    sts = boto3.client("sts", region_name=REGION)
    control = boto3.client("bedrock-agentcore-control", region_name=REGION)
    account_id = sts.get_caller_identity()["Account"]

    # --- 1. IAM execution role -------------------------------------------
    role_arn = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(TRUST_POLICY),
        Description="Execution role for the Lesson 6 demo harness",
    )["Role"]["Arn"]
    print(f"Created IAM role {role_name}")
    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="harness_execution_policy",
        PolicyDocument=json.dumps(execution_policy(account_id)),
    )

    # --- 2. The harness ---------------------------------------------------
    # A brand-new role can take a few seconds to propagate, so retry.
    for attempt in range(3):
        try:
            harness = control.create_harness(
                harnessName=name,
                executionRoleArn=role_arn,
                model={"bedrockModelConfig": {"modelId": MODEL_ID, "temperature": 0.0}},
                systemPrompt=[{"text": SYSTEM_PROMPT}],
                # This lesson is about per-session state: the conversation
                # must live in the runtimeSessionId and nowhere else. Disable
                # the harness's managed long-term memory, which would
                # otherwise carry facts from one session into the next and
                # defeat the fresh-session tests.
                memory={"disabled": {}},
            )["harness"]
            break
        except Exception as err:  # noqa: BLE001 — retry only for propagation delay
            if attempt == 2:
                raise
            print(f"Waiting for the new role to propagate ({type(err).__name__}) — retrying in 10s")
            time.sleep(10)

    harness_id = harness["harnessId"]
    harness_arn = harness["arn"]
    print(f"Created harness {name} ({harness_id}) — waiting for READY (~2–3 minutes)")

    # --- 3. Wait until it is ready to chat --------------------------------
    deadline = time.time() + 360
    while time.time() < deadline:
        status = control.get_harness(harnessId=harness_id)["harness"]["status"]
        if status == "READY":
            break
        if status.endswith("FAILED"):
            sys.exit(f"Harness entered status {status} — check the console and retry.")
        time.sleep(10)
    else:
        sys.exit("Timed out waiting for the harness to become READY.")

    arn_file = pathlib.Path(__file__).with_name("harness_arn.txt")
    arn_file.write_text(harness_arn + "\n")
    print(f"Harness is READY.\n  ARN: {harness_arn}\n  (saved to {arn_file.name})")
    print("Start chatting with:  python chat.py")


if __name__ == "__main__":
    main()
