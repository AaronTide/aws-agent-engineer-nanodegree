import boto3
import json

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

# ---------------------------------------------------------------------------
# Sample meeting notes
# ---------------------------------------------------------------------------
MEETING_NOTES = """\
Meeting – Q3 Product Review
Date: Thursday afternoon
Attendees: Sarah (PM), Jake (Eng Lead), Priya (Design), Tom (QA)

Started about 10 minutes late. Sarah opened by saying the search feature is running
roughly two weeks behind schedule because the ranking algorithm keeps failing QA.
Tom confirmed three test cases are still red.

Jake said the core indexing work is done and the delay is entirely on ranking.
He proposed cutting the fuzzy-match feature from v1 and shipping exact-match only
to hit the release date. Sarah agreed; fuzzy-match moves to the backlog.

Priya raised a concern: the empty-state illustration hasn't been reviewed yet.
Sarah asked Priya to share it in Slack by Friday EOD for async feedback.

Budget question came up: Jake mentioned the new search infrastructure will add
roughly $200/month to the AWS bill. Sarah said she'd confirm with Finance
whether that fits Q3 budget before the next sprint.

Wrap-up: next sync same time next week.
"""


# ---------------------------------------------------------------------------
# Streaming variant
# ---------------------------------------------------------------------------
def summarize_notes_stream(notes: str) -> None:
    prompt = (
        "Summarize the following meeting notes into:\n"
        "1. Key decisions made\n"
        "2. Action items with owners\n\n"
        f"Meeting notes:\n{notes}"
    )

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.0,
        "messages": [{"role": "user", "content": prompt}],
    }

    response = bedrock.invoke_model_with_response_stream(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )

    for event in response["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        if chunk["type"] == "content_block_delta":
            print(chunk["delta"].get("text", ""), end="", flush=True)

    print()  # final newline


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== InvokeModelWithResponseStream ===\n")
    summarize_notes_stream(MEETING_NOTES)
