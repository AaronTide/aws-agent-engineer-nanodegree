#!/usr/bin/env python3
"""
cleanup.py — deletes everything setup.py created:
the harness, its IAM execution role, and the local harness_arn.txt.

Run:
    python cleanup.py                  # default name: incident_report_agent
    python cleanup.py --name my_name   # if you used a custom name
"""
import argparse
import pathlib
import time

import boto3

REGION = "us-east-1"


def find_harness_id(control, name):
    token = None
    while True:
        kwargs = {"nextToken": token} if token else {}
        page = control.list_harnesses(**kwargs)
        for summary in page.get("harnesses", []):
            if summary["harnessName"] == name:
                return summary["harnessId"]
        token = page.get("nextToken")
        if not token:
            return None


def main():
    parser = argparse.ArgumentParser(description="Delete the incident-report harness and role")
    parser.add_argument("--name", default="incident_report_agent")
    args = parser.parse_args()
    name = args.name

    control = boto3.client("bedrock-agentcore-control", region_name=REGION)
    iam = boto3.client("iam", region_name=REGION)

    # --- Harness ----------------------------------------------------------
    harness_id = find_harness_id(control, name)
    if harness_id:
        control.delete_harness(harnessId=harness_id)
        print(f"Deleting harness {name} ({harness_id}) ...")
        deadline = time.time() + 180
        while time.time() < deadline:
            try:
                control.get_harness(harnessId=harness_id)
            except Exception:  # noqa: BLE001 — gone (ResourceNotFound)
                print("Harness deleted.")
                break
            time.sleep(5)
        else:
            print("Harness deletion is still finishing server-side — it will complete on its own.")
    else:
        print(f"No harness named {name} found — nothing to delete.")

    # --- IAM role(s) ------------------------------------------------------
    # setup.py gives the role a unique suffix each run, so delete every
    # role that belongs to this harness name.
    role_prefix = f"{name}_role"
    role_names, marker = [], None
    while True:
        page = iam.list_roles(**({"Marker": marker} if marker else {}))
        role_names += [r["RoleName"] for r in page["Roles"] if r["RoleName"].startswith(role_prefix)]
        if not page.get("IsTruncated"):
            break
        marker = page["Marker"]
    for role_name in role_names:
        for policy_name in iam.list_role_policies(RoleName=role_name)["PolicyNames"]:
            iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
        iam.delete_role(RoleName=role_name)
        print(f"Deleted IAM role {role_name}.")
    if not role_names:
        print(f"No IAM role starting with {role_prefix} found — nothing to delete.")

    # --- Local state ------------------------------------------------------
    arn_file = pathlib.Path(__file__).with_name("harness_arn.txt")
    if arn_file.exists():
        arn_file.unlink()
        print("Removed harness_arn.txt.")

    print("Cleanup complete.")


if __name__ == "__main__":
    main()
