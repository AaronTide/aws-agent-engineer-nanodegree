"""One-shot setup for Demo 3: travel assistant on the Amazon Bedrock AgentCore
managed harness, with tools served by an AgentCore Gateway.

Creates, in order:
  1. Three IAM roles (Lambda execution, Gateway invocation, harness execution)
  2. Two Lambda functions from the lambda/ folder (get_weather, get_top_attractions)
  3. An AgentCore Gateway with one Lambda target per tool
  4. An AgentCore managed harness (the agent) pinned to Amazon Nova Pro

Everything is created with plain boto3 calls so the whole stack is visible in
this one script. When it finishes it writes demo_config.json, which chat.py
and cleanup.py read.

Usage:
    python setup.py                   # default resource prefix "demo3"
    python setup.py --prefix myname   # custom prefix (shared accounts)
"""

import argparse
import io
import json
import re
import sys
import time
import zipfile
from datetime import date
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
# Pin the model: the harness default model is not available in classroom
# accounts, so we always name the model explicitly.
MODEL_ID = "us.amazon.nova-pro-v1:0"

# The agent instruction -- the same prompt lesson as ever: "always use the
# available tools" is what makes the model gather facts before answering.
SYSTEM_PROMPT = (
    "You are a helpful travel planning assistant. When a user asks for travel "
    "recommendations, always use the available tools to gather current weather "
    "conditions and top attractions before making any suggestions. Always look "
    "up available attractions using a tool call. If the weather is poor, "
    "prioritize indoor attractions. Always tailor suggestions to any "
    "preferences the user mentions, such as traveling with family or having "
    "limited time."
)

HERE = Path(__file__).resolve().parent


def wait_for(desc, fn, ok, fail=lambda s: False, delay=10, attempts=30):
    """Poll fn() until ok(status) is true. Prints progress dots."""
    for _ in range(attempts):
        status = fn()
        if ok(status):
            print(f" {desc}: {status}")
            return status
        if fail(status):
            raise RuntimeError(f"{desc} entered failed state: {status}")
        print(".", end="", flush=True)
        time.sleep(delay)
    raise RuntimeError(f"Timed out waiting for {desc}")


def retry_create(desc, fn, attempts=4, delay=10):
    """IAM roles take a few seconds to propagate; retry creates that use them."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if attempt < attempts and code in (
                "ValidationException",
                "InvalidParameterValueException",
                "AccessDeniedException",
            ):
                print(f"  {desc}: waiting for IAM to propagate (attempt {attempt})...")
                time.sleep(delay)
                continue
            raise


def zip_lambda(src_dir: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(src_dir / "lambda_function.py", "lambda_function.py")
    return buf.getvalue()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="demo3", help="prefix for all AWS resource names")
    args = parser.parse_args()
    prefix = args.prefix

    iam = boto3.client("iam", region_name=REGION)
    lam = boto3.client("lambda", region_name=REGION)
    acc = boto3.client("bedrock-agentcore-control", region_name=REGION)
    account_id = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]

    # ------------------------------------------------------------------ 1. IAM
    print("Step 1/4 - IAM roles")

    def create_role(name, service, inline_policy=None, managed=None):
        trust = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": service},
                "Action": "sts:AssumeRole",
            }],
        }
        try:
            arn = iam.create_role(
                RoleName=name, AssumeRolePolicyDocument=json.dumps(trust)
            )["Role"]["Arn"]
            print(f"  created role {name}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "EntityAlreadyExists":
                raise
            arn = iam.get_role(RoleName=name)["Role"]["Arn"]
            print(f"  role {name} already exists, reusing")
        if inline_policy:
            iam.put_role_policy(
                RoleName=name, PolicyName=f"{name}-policy",
                PolicyDocument=json.dumps(inline_policy),
            )
        if managed:
            iam.attach_role_policy(RoleName=name, PolicyArn=managed)
        return arn

    # Role the Lambda functions run as (only needs to write its own logs).
    lambda_role_arn = create_role(
        f"{prefix}-lambda-role", "lambda.amazonaws.com",
        managed="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    # Role the Gateway assumes to invoke your Lambdas. NOTE: with AgentCore the
    # GATEWAY's role needs lambda:InvokeFunction -- there is no resource-based
    # Lambda permission for a service principal like there was with Bedrock
    # Agents action groups.
    gateway_role_arn = create_role(
        f"{prefix}-gateway-role", "bedrock-agentcore.amazonaws.com",
        inline_policy={
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": "lambda:InvokeFunction",
                "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:{prefix}-*",
            }],
        },
    )

    # Role the harness (the agent runtime) assumes: call the model, write logs
    # and metrics, and invoke the Gateway.
    harness_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "InvokeModel",
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/*",
                    f"arn:aws:bedrock:{REGION}:{account_id}:*",
                    f"arn:aws:bedrock:*:{account_id}:inference-profile/*",
                ],
            },
            {
                "Sid": "InvokeGateway",
                "Effect": "Allow",
                "Action": "bedrock-agentcore:InvokeGateway",
                "Resource": f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:gateway/*",
            },
            {
                "Sid": "Logs",
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup", "logs:CreateLogStream",
                    "logs:DescribeLogGroups", "logs:DescribeLogStreams",
                    "logs:PutLogEvents",
                ],
                "Resource": f"arn:aws:logs:{REGION}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*",
            },
            {"Sid": "LogsPolicy", "Effect": "Allow",
             "Action": "logs:PutResourcePolicy", "Resource": "*"},
            {
                "Sid": "Metrics",
                "Effect": "Allow",
                "Action": "cloudwatch:PutMetricData",
                "Resource": "*",
                "Condition": {"StringEquals": {"cloudwatch:namespace": "bedrock-agentcore"}},
            },
            {"Sid": "Tracing", "Effect": "Allow",
             "Action": ["xray:PutTraceSegments", "xray:PutTelemetryRecords",
                        "xray:GetSamplingRules", "xray:GetSamplingTargets"],
             "Resource": "*"},
            {"Sid": "Auth", "Effect": "Allow",
             "Action": ["ecr-public:GetAuthorizationToken", "sts:GetServiceBearerToken"],
             "Resource": "*"},
            {
                "Sid": "WorkloadIdentity",
                "Effect": "Allow",
                "Action": "bedrock-agentcore:GetWorkloadAccessToken*",
                "Resource": f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:workload-identity-directory/default*",
            },
            {
                "Sid": "Memory",
                "Effect": "Allow",
                "Action": ["bedrock-agentcore:CreateEvent", "bedrock-agentcore:GetEvent",
                           "bedrock-agentcore:ListEvents", "bedrock-agentcore:DeleteEvent",
                           "bedrock-agentcore:RetrieveMemoryRecords"],
                "Resource": f"arn:aws:bedrock-agentcore:{REGION}:{account_id}:memory/*",
            },
            {
                "Sid": "CodeInterpreter",
                "Effect": "Allow",
                "Action": ["bedrock-agentcore:StartCodeInterpreterSession",
                           "bedrock-agentcore:InvokeCodeInterpreter",
                           "bedrock-agentcore:StopCodeInterpreterSession",
                           "bedrock-agentcore:GetCodeInterpreterSession",
                           "bedrock-agentcore:ListCodeInterpreterSessions"],
                "Resource": f"arn:aws:bedrock-agentcore:{REGION}:aws:code-interpreter/*",
            },
            {"Sid": "Marketplace", "Effect": "Allow",
             "Action": ["aws-marketplace:ViewSubscriptions", "aws-marketplace:Subscribe"],
             "Resource": "*"},
        ],
    }
    harness_role_arn = create_role(
        f"{prefix}-harness-role", "bedrock-agentcore.amazonaws.com",
        inline_policy=harness_policy,
    )

    # -------------------------------------------------------------- 2. Lambdas
    print("Step 2/4 - Lambda functions")
    function_arns = {}
    for tool in ("get_weather", "get_top_attractions"):
        fn_name = f"{prefix}-{tool.replace('_', '-')}"
        code = zip_lambda(HERE / "lambda" / tool)
        try:
            arn = retry_create(fn_name, lambda: lam.create_function(
                FunctionName=fn_name,
                Runtime="python3.12",
                Role=lambda_role_arn,
                Handler="lambda_function.lambda_handler",
                Code={"ZipFile": code},
                Timeout=15,
            ))["FunctionArn"]
            print(f"  created function {fn_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceConflictException":
                raise
            lam.update_function_code(FunctionName=fn_name, ZipFile=code)
            arn = lam.get_function(FunctionName=fn_name)["Configuration"]["FunctionArn"]
            print(f"  function {fn_name} already exists, updated its code")
        function_arns[tool] = arn

    # -------------------------------------------------------------- 3. Gateway
    print("Step 3/4 - AgentCore Gateway + Lambda targets")
    gw = retry_create("gateway", lambda: acc.create_gateway(
        name=f"{prefix}-gateway",
        roleArn=gateway_role_arn,
        protocolType="MCP",
        authorizerType="AWS_IAM",
    ))
    gateway_id = gw["gatewayId"]
    gateway_arn = gw["gatewayArn"]
    wait_for("gateway", lambda: acc.get_gateway(gatewayIdentifier=gateway_id)["status"],
             ok=lambda s: s == "READY", fail=lambda s: s == "FAILED", delay=5)

    # One target per Lambda. IMPORTANT: target names may only contain letters,
    # digits, and underscores (no dashes) -- the MCP tool name that the model
    # sees is "<targetName>___<toolName>".
    targets = {
        "weather": {
            "lambdaArn": function_arns["get_weather"],
            "tools": [{
                "name": "get_weather",
                "description": "Get the weather forecast for a city on a given date.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "The city name"},
                        "date": {"type": "string", "description": "The date in YYYY-MM-DD format"},
                    },
                    "required": ["city", "date"],
                },
            }],
        },
        "attractions": {
            "lambdaArn": function_arns["get_top_attractions"],
            "tools": [{
                "name": "get_top_attractions",
                "description": "Get the top tourist attractions for a city.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "The city name"},
                    },
                    "required": ["city"],
                },
            }],
        },
    }
    for target_name, cfg in targets.items():
        retry_create(f"target {target_name}", lambda cfg=cfg, n=target_name: acc.create_gateway_target(
            gatewayIdentifier=gateway_id,
            name=n,
            targetConfiguration={"mcp": {"lambda": {
                "lambdaArn": cfg["lambdaArn"],
                "toolSchema": {"inlinePayload": cfg["tools"]},
            }}},
            credentialProviderConfigurations=[{"credentialProviderType": "GATEWAY_IAM_ROLE"}],
        ))
        print(f"  created gateway target {target_name}")

    # -------------------------------------------------------------- 4. Harness
    print("Step 4/4 - AgentCore managed harness (takes ~2-3 minutes)")
    harness_name = re.sub(r"[^A-Za-z0-9_]", "_", f"{prefix}_travel_assistant")
    # Models have no clock. Stamp today's date into the instruction so a
    # relative date like "this Saturday" resolves to a real calendar date in
    # the tool calls instead of a guess.
    date_line = date.today().strftime(" Today's date is %A, %Y-%m-%d.")
    harness = retry_create("harness", lambda: acc.create_harness(
        harnessName=harness_name,
        executionRoleArn=harness_role_arn,
        model={"bedrockModelConfig": {
            "modelId": MODEL_ID,
            # Deterministic tool calling with Nova:
            "temperature": 0.0,
            "additionalParams": {"additionalModelRequestFields": {"inferenceConfig": {"topK": 1}}},
        }},
        # systemPrompt is a LIST of content blocks:
        systemPrompt=[{"text": SYSTEM_PROMPT + date_line}],
    ))["harness"]  # the response nests everything under "harness"
    harness_id = harness["harnessId"]
    harness_arn = harness["arn"]

    def harness_status():
        h = acc.get_harness(harnessId=harness_id)["harness"]
        if h["status"] == "CREATE_FAILED":
            raise RuntimeError(
                f"harness CREATE_FAILED: {h.get('failureReason', 'no reason given')}"
            )
        return h["status"]

    wait_for("harness", harness_status, ok=lambda s: s == "READY", delay=10)

    # ------------------------------------------------------------------ Config
    config = {
        "region": REGION,
        "prefix": prefix,
        "modelId": MODEL_ID,
        "gatewayId": gateway_id,
        "gatewayArn": gateway_arn,
        "harnessId": harness_id,
        "harnessArn": harness_arn,
        "harnessName": harness_name,
        "functionArns": function_arns,
    }
    (HERE / "demo_config.json").write_text(json.dumps(config, indent=2))
    print("\nSetup complete. Wrote demo_config.json")
    print("Try it:  python chat.py \"I'll be in London this Saturday with my family. What should we do?\"")


if __name__ == "__main__":
    sys.exit(main())
