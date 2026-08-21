#!/usr/bin/env python3
"""
setup.py — one-shot setup for the incident-report feedback loop (starter).

Creates two things:
  1. An IAM execution role the harness runs as
  2. An Amazon Bedrock AgentCore managed harness pinned to Amazon Nova Pro,
     with the incident-report coordinator instructions as its system prompt

Run:
    python setup.py                  # default name: incident_report_agent
    python setup.py --name my_name   # optional custom name

When it finishes it writes harness_arn.txt next to this script, which
chat.py reads. Tear everything down later with cleanup.py.
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

# ------------------------------------------------------------------
# TODO: Write your system prompt here. It is the entire feedback loop.
#
# It must give the model:
#   - A role and goal (incident report coordinator for an SRE team)
#   - A required-fields checklist: severity, affected service, impact,
#     root cause, timeline
#   - A one-question-at-a-time strategy: ask exactly ONE focused
#     follow-up question per turn about a missing field, never fabricate
#     details, and never produce the final report while any field is missing
#   - A completion format: only when all five fields are covered, output
#     a report that starts with the line "FINAL REPORT"
# ------------------------------------------------------------------
SYSTEM_PROMPT = """\
TODO: your instructions here
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
    parser = argparse.ArgumentParser(description="Create the incident-report harness")
    parser.add_argument(
        "--name",
        default="incident_report_agent",
        help="Harness name (letters, digits, underscores only)",
    )
    args = parser.parse_args()
    name = args.name
    # Give the role a fresh name on every run. Recreating a role under a
    # just-deleted name can hand the new harness stale credentials for the
    # old role for several minutes; a unique name sidesteps that entirely.
    # cleanup.py deletes every role that starts with "<name>_role".
    role_name = f"{name}_role_{secrets.token_hex(4)}"

    if "TODO" in SYSTEM_PROMPT:
        sys.exit("Write your system prompt in setup.py (SYSTEM_PROMPT) before running setup.")

    iam = boto3.client("iam", region_name=REGION)
    sts = boto3.client("sts", region_name=REGION)
    control = boto3.client("bedrock-agentcore-control", region_name=REGION)
    account_id = sts.get_caller_identity()["Account"]

    # --- 1. IAM execution role -------------------------------------------
    role_arn = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(TRUST_POLICY),
        Description="Execution role for the Lesson 6 incident-report harness",
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
                # This exercise is about per-session state: the conversation
                # must live in the runtimeSessionId and nowhere else. Disable
                # the harness's managed long-term memory, which would
                # otherwise carry facts from one session into the next and
                # defeat Test 2's fresh-session check.
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
