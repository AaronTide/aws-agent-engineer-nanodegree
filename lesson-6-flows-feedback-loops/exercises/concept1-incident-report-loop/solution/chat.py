#!/usr/bin/env python3
"""
chat.py — multi-turn chat with an AgentCore managed harness.

The entire feedback loop is one idea: keep the SAME runtimeSessionId on
every call. The harness is stateful by default, so each invoke_harness
call that reuses the session id continues the same conversation — no
agent node, no "User input" toggle, no prepare step.

Usage:
    python chat.py                 # reads harness_arn.txt written by setup
    python chat.py --arn <arn>     # or pass the harness ARN directly

Type a message and press Enter. Type "quit" (or press Ctrl-D) to exit.
"""
import argparse
import pathlib
import sys
import uuid

import boto3
import botocore.exceptions

REGION = "us-east-1"


class ThinkingFilter:
    """Hides <thinking>...</thinking> spans in streamed text.

    Amazon Nova often streams its private reasoning first, wrapped in
    <thinking> tags. Only the reply meant for the user should reach the
    screen, so this tiny state machine drops those spans as the text
    deltas arrive.
    """

    OPEN, CLOSE = "<thinking>", "</thinking>"

    def __init__(self):
        self.buffer = ""
        self.hiding = False
        self.printed_anything = False

    def feed(self, chunk):
        """Add a streamed chunk; return the part that is safe to print."""
        self.buffer += chunk
        visible = ""
        while True:
            if self.hiding:
                end = self.buffer.find(self.CLOSE)
                if end == -1:
                    # Keep only a tail that could still complete the tag.
                    self.buffer = self.buffer[-(len(self.CLOSE) - 1):]
                    break
                self.buffer = self.buffer[end + len(self.CLOSE):]
                self.hiding = False
            else:
                start = self.buffer.find(self.OPEN)
                if start == -1:
                    # Emit everything except a tail that could be the
                    # beginning of a tag split across two chunks.
                    keep = len(self.OPEN) - 1
                    if len(self.buffer) > keep:
                        visible += self.buffer[:-keep]
                        self.buffer = self.buffer[-keep:]
                    break
                visible += self.buffer[:start]
                self.buffer = self.buffer[start + len(self.OPEN):]
                self.hiding = True
        if not self.printed_anything:
            visible = visible.lstrip()
        if visible:
            self.printed_anything = True
        return visible

    def flush(self):
        """Return whatever remains once the stream has ended."""
        leftover = "" if self.hiding else self.buffer
        self.buffer, self.hiding = "", False
        if not self.printed_anything:
            leftover = leftover.lstrip()
        return leftover


def read_arn(args):
    """Harness ARN comes from --arn, or from harness_arn.txt written by setup."""
    if args.arn:
        return args.arn
    arn_file = pathlib.Path(__file__).with_name("harness_arn.txt")
    if arn_file.exists():
        return arn_file.read_text().strip()
    sys.exit("No harness ARN found. Run the setup script first, or pass --arn <harness-arn>.")


def main():
    parser = argparse.ArgumentParser(description="Chat with an AgentCore managed harness")
    parser.add_argument("--arn", help="Harness ARN (overrides harness_arn.txt)")
    args = parser.parse_args()
    harness_arn = read_arn(args)

    # ONE session id for the whole conversation. Reusing it is what makes
    # this a feedback loop. It must be at least 33 characters long — a
    # prefix plus a UUID comfortably clears that bar.
    session_id = f"lesson6-{uuid.uuid4()}"

    runtime = boto3.client("bedrock-agentcore", region_name=REGION)

    print(f"Session: {session_id}")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            user_text = input("You: ").strip()
        except EOFError:
            break
        if not user_text or user_text.lower() in ("quit", "exit"):
            break
        if not sys.stdin.isatty():
            # Input is being piped in — echo it so the transcript still
            # reads like a conversation.
            print(user_text)

        response = runtime.invoke_harness(
            harnessArn=harness_arn,
            runtimeSessionId=session_id,  # SAME id every turn = same conversation
            messages=[{"role": "user", "content": [{"text": user_text}]}],
        )

        # The response is a stream of events; print the text deltas as they
        # arrive, hiding the model's <thinking> reasoning spans. Error
        # events (throttling, a transient credential hiccup) are raised by
        # boto3 as exceptions while iterating — print them and keep the
        # session alive so the turn can simply be retried.
        print("\nAgent: ", end="", flush=True)
        thinking_filter = ThinkingFilter()
        try:
            for event in response["stream"]:
                delta = event.get("contentBlockDelta", {}).get("delta", {})
                if "text" in delta:
                    print(thinking_filter.feed(delta["text"]), end="", flush=True)
            print(thinking_filter.flush(), end="", flush=True)
        except botocore.exceptions.EventStreamError as err:
            print(f"\n[stream error — retry this message] {err}", flush=True)
        print("\n")


if __name__ == "__main__":
    main()
