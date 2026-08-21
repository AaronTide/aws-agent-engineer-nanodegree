"""Delete every AWS resource Demo 3 created: harness, gateway targets, gateway,
Lambda functions, and IAM roles. Reads demo_config.json (written by setup.py).

Usage:
    python cleanup.py
"""

import json
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

HERE = Path(__file__).resolve().parent


def ignore_missing(fn, *codes):
    try:
        fn()
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in codes + ("ResourceNotFoundException", "NoSuchEntity", "NotFoundException"):
            return False
        raise


def main():
    path = HERE / "demo_config.json"
    if not path.exists():
        sys.exit("demo_config.json not found -- nothing to clean up (or run from the demo folder).")
    config = json.loads(path.read_text())
    region, prefix = config["region"], config["prefix"]

    iam = boto3.client("iam", region_name=region)
    lam = boto3.client("lambda", region_name=region)
    acc = boto3.client("bedrock-agentcore-control", region_name=region)

    # 1. Harness (delete first: it references the gateway). The harness owns a
    # managed memory named after it; delete that too, and wait until both are
    # gone -- otherwise an immediate re-run of setup.py fails because the new
    # harness's memory name collides with the old one still deleting.
    print("Deleting harness (takes a minute or two)...")
    if ignore_missing(lambda: acc.delete_harness(
            harnessId=config["harnessId"], deleteManagedMemory=True)):
        for _ in range(40):
            try:
                acc.get_harness(harnessId=config["harnessId"])
                time.sleep(5)
            except ClientError:
                break
    # Each memory lists the harness that manages it in managedByResourceArn,
    # so we can wait for exactly ours to disappear.
    for _ in range(40):
        try:
            memories = acc.list_memories().get("memories", [])
        except ClientError:
            break
        if not any(m.get("managedByResourceArn") == config["harnessArn"] for m in memories):
            break
        time.sleep(5)
    print("  done")

    # 2. Gateway targets, then the gateway itself.
    print("Deleting gateway targets and gateway...")
    try:
        targets = acc.list_gateway_targets(gatewayIdentifier=config["gatewayId"]).get("items", [])
    except ClientError:
        targets = []
    for t in targets:
        ignore_missing(lambda t=t: acc.delete_gateway_target(
            gatewayIdentifier=config["gatewayId"], targetId=t["targetId"]))
    for _ in range(12):  # wait until targets are gone; gateway delete fails otherwise
        try:
            if not acc.list_gateway_targets(gatewayIdentifier=config["gatewayId"]).get("items"):
                break
            time.sleep(5)
        except ClientError:
            break
    ignore_missing(lambda: acc.delete_gateway(gatewayIdentifier=config["gatewayId"]))
    print("  done")

    # 3. Lambda functions.
    print("Deleting Lambda functions...")
    for arn in config["functionArns"].values():
        ignore_missing(lambda arn=arn: lam.delete_function(FunctionName=arn))
    print("  done")

    # 4. IAM roles (inline policies and managed attachments must go first).
    print("Deleting IAM roles...")
    for role in (f"{prefix}-lambda-role", f"{prefix}-gateway-role", f"{prefix}-harness-role"):
        try:
            for p in iam.list_role_policies(RoleName=role)["PolicyNames"]:
                iam.delete_role_policy(RoleName=role, PolicyName=p)
            for p in iam.list_attached_role_policies(RoleName=role)["AttachedPolicies"]:
                iam.detach_role_policy(RoleName=role, PolicyArn=p["PolicyArn"])
            iam.delete_role(RoleName=role)
            print(f"  deleted {role}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchEntity":
                raise
            print(f"  {role} already gone")

    path.unlink()
    print("Cleanup complete.")


if __name__ == "__main__":
    main()
