import boto3

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

# TODO (Task 1): Create the Bedrock Runtime client
# bedrock = boto3.client(...)

MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

# TODO (Task 2): Write the system prompt.
# The assistant should:
# - Help users plan visits to cities
# - NOT answer from memory — always use tools first
# - Base recommendations only on tool results
SYSTEM_PROMPT = """\
...\
"""

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------
WEATHER_DATA = {
    ("london", "2026-03-14"): {
        "city": "London",
        "date": "2026-03-14",
        "condition": "Light rain in the morning, clearing to partly cloudy by afternoon",
        "temperature_celsius": 11,
        "wind_mph": 12,
        "recommendation": "Bring a light jacket and umbrella for the morning",
    }
}

ATTRACTIONS_DATA = {
    "london": {
        "city": "London",
        "attractions": [
            {"name": "British Museum",        "type": "indoor",          "family_friendly": True, "avg_visit_hours": 2.0},
            {"name": "Tower of London",       "type": "outdoor/indoor",  "family_friendly": True, "avg_visit_hours": 2.5},
            {"name": "Natural History Museum","type": "indoor",          "family_friendly": True, "avg_visit_hours": 2.0},
            {"name": "Hyde Park",             "type": "outdoor",         "family_friendly": True, "avg_visit_hours": 1.5},
            {"name": "Covent Garden",         "type": "outdoor/indoor",  "family_friendly": True, "avg_visit_hours": 1.0},
        ],
    }
}

# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "toolSpec": {
            "name": "get_weather",
            "description": "Returns current weather conditions and forecast for a given city and date.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        # TODO (Task 3a): Define the two input properties — city and date
                        # "city": { "type": "string", "description": "..." },
                        # "date": { "type": "string", "description": "..." },
                    },
                    "required": [
                        # TODO (Task 3a): List the required fields
                    ],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "get_top_attractions",
            "description": "Returns a list of top-rated attractions in a given city.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        # TODO (Task 3b): Define the one input property — city
                        # "city": { "type": "string", "description": "..." },
                    },
                    "required": [
                        # TODO (Task 3b): List the required fields
                    ],
                }
            },
        }
    },
]

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------
def get_weather(city: str, date: str) -> dict:
    # TODO (Task 4a): Look up (city.lower(), date) in WEATHER_DATA.
    # Return the matching dict, or {"city": city, "date": date, "condition": "No data available"} if not found.
    pass


def get_top_attractions(city: str) -> dict:
    # TODO (Task 4b): Look up city.lower() in ATTRACTIONS_DATA.
    # Return the matching dict, or {"city": city, "attractions": []} if not found.
    pass


def execute_tool(name: str, tool_input: dict) -> dict:
    if name == "get_weather":
        return get_weather(tool_input["city"], tool_input["date"])
    elif name == "get_top_attractions":
        return get_top_attractions(tool_input["city"])
    return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Converse loop
# ---------------------------------------------------------------------------
def run_chat() -> None:
    messages = []

    print("Travel Planner")
    print("=" * 40)
    print("Ask me to help plan your visit to a city.\n")

    try:
        user_input = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not user_input:
        print("No input provided.")
        return

    messages.append({"role": "user", "content": [{"text": user_input}]})

    while True:
        response = bedrock.converse(
            modelId=MODEL_ID,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig={"tools": TOOLS},
        )

        stop_reason = response["stopReason"]
        output_message = response["output"]["message"]
        messages.append(output_message)

        if stop_reason == "end_turn":
            for block in output_message["content"]:
                if "text" in block:
                    print(f"\nAssistant: {block['text']}\n")
            break

        elif stop_reason == "tool_use":
            # TODO (Task 5): Handle tool calls.
            # 1. Create an empty tool_results list
            # 2. Loop through output_message["content"]
            # 3. For each block with a "toolUse" key:
            #    a. Extract tool_name, tool_input, and tool_use_id
            #    b. Print: f"  [tool call] {tool_name}({tool_input})"
            #    c. Call execute_tool(tool_name, tool_input) and store the result
            #    d. Print: f"  [tool result] {result}"
            #    e. Append a toolResult entry to tool_results
            # 4. Append a user message containing tool_results to messages
            pass


if __name__ == "__main__":
    run_chat()
