"""Chat with the Demo 3 travel assistant (AgentCore managed harness).

Streams the agent's answer token by token and prints every tool call as it
happens -- which tool, with which arguments, and what came back. This is the
AgentCore equivalent of the old Bedrock Agents "Show trace" panel.

Usage:
    python chat.py "I'll be in London this Saturday with my family. What should we do?"
    python chat.py            # interactive: keeps one session across turns
    python chat.py --debug "..."   # also dump every raw stream event
"""

import argparse
import json
import sys
import uuid
from pathlib import Path

import boto3

HERE = Path(__file__).resolve().parent

BOLD = "\033[1m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def load_config():
    path = HERE / "demo_config.json"
    if not path.exists():
        sys.exit("demo_config.json not found -- run `python setup.py` first.")
    return json.loads(path.read_text())


def send(rt, config, session_id, text, debug=False):
    """Send one user message and stream the response, printing tool activity."""
    response = rt.invoke_harness(
        harnessArn=config["harnessArn"],
        runtimeSessionId=session_id,
        messages=[{"role": "user", "content": [{"text": text}]}],
        # Attach the Gateway: its tools (weather, attractions) become available
        # to the model for this invocation.
        tools=[{
            "type": "agentcore_gateway",
            "name": "gateway",
            "config": {"agentCoreGateway": {"gatewayArn": config["gatewayArn"]}},
        }],
    )

    tool_name = None
    tool_input_parts = None
    names_by_id = {}     # toolUseId -> tool name, so results can be labeled
    result_name = None   # which tool the current toolResult block belongs to
    printed_text = False

    for event in response["stream"]:
        if debug:
            print(f"\n{YELLOW}[event]{RESET} {json.dumps(event, default=str)}")

        if "contentBlockStart" in event:
            start = event["contentBlockStart"].get("start", {})
            if "toolUse" in start:
                # The model decided to call a tool. The start event carries the
                # tool name and a toolUseId; the arguments stream in as deltas.
                tool_name = start["toolUse"].get("name", "?")
                names_by_id[start["toolUse"].get("toolUseId")] = tool_name
                tool_input_parts = []
            elif "toolResult" in start:
                # The harness ran the tool through the Gateway. The start event
                # has only the toolUseId and status; the result body follows as
                # deltas, so remember which tool it belongs to.
                tr = start["toolResult"]
                result_name = names_by_id.get(tr.get("toolUseId"), "?")

        elif "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            if "text" in delta:
                # Normal assistant text -- stream it as it arrives.
                print(delta["text"], end="", flush=True)
                printed_text = True
            elif "toolUse" in delta:
                if tool_input_parts is None:
                    tool_input_parts = []
                tool_input_parts.append(delta["toolUse"].get("input", ""))
            elif "toolResult" in delta:
                # delta["toolResult"] is the list of result content blocks,
                # e.g. [{"text": "{\"condition\": ...}"}].
                content = delta["toolResult"]
                if isinstance(content, dict):  # tolerate a wrapped form too
                    content = content.get("content", [content])
                for block in content if isinstance(content, list) else [content]:
                    body = block.get("text", block) if isinstance(block, dict) else block
                    print(f"{CYAN}   <- result ({result_name}): {body}{RESET}")

        elif "contentBlockStop" in event:
            if tool_name is not None and tool_input_parts is not None:
                args = "".join(tool_input_parts) or "{}"
                print(f"\n{BOLD}{CYAN}-> tool call: {tool_name}({args}){RESET}")
                tool_name = None
            tool_input_parts = None
            result_name = None

        elif "messageStop" in event:
            reason = event["messageStop"].get("stopReason")
            if debug:
                print(f"\n{YELLOW}[stop: {reason}]{RESET}")
            if reason == "end_turn" and printed_text:
                print()  # final newline after the streamed answer

        elif "metadata" in event and debug:
            print(f"{YELLOW}[metadata] {json.dumps(event['metadata'], default=str)}{RESET}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("message", nargs="?", help="one-shot message (omit for interactive mode)")
    parser.add_argument("--debug", action="store_true", help="print raw stream events")
    args = parser.parse_args()

    config = load_config()
    rt = boto3.client("bedrock-agentcore", region_name=config["region"])

    # Session ids must be at least 33 characters; reusing one keeps the
    # conversation stateful across turns (the harness remembers the history).
    session_id = f"demo3-session-{uuid.uuid4()}"

    if args.message:
        send(rt, config, session_id, args.message, debug=args.debug)
        return

    print("Travel assistant ready. Type a message (Ctrl+C or empty line to quit).")
    while True:
        try:
            text = input(f"\n{BOLD}You:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            break
        send(rt, config, session_id, text, debug=args.debug)


if __name__ == "__main__":
    main()
