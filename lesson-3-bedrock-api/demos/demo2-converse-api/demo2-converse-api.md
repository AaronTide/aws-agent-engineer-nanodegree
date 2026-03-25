# Demo 2 – Using the Converse API

## Client Setup

```python
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
```

---

## System Prompt

```python
SYSTEM_PROMPT = """\
You are a helpful travel planning assistant. Your job is to help the user find a restaurant to book for tonight.
Ask the user about their cuisine preference and which area of the city they prefer.
Use the available tools to look up options and check availability before making a recommendation.
Base your recommendation on tool results only — do not invent restaurant names or availability.
..."""
```

**Expected:** The model asks for preferences before calling any tools. It does not suggest restaurant names until after `search_restaurants` and `get_availability` have been called.

---

## Tool Schemas

```python
{
    "toolSpec": {
        "name": "search_restaurants",
        "description": "Searches for restaurants matching one or more cuisine types and city areas.",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "cuisines": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of cuisine types to filter by.",
                    },
                    "areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of city areas to filter by.",
                    },
                },
                "required": ["cuisines", "areas"],
            }
        },
    }
}
```

Tools with no required inputs still need a valid schema: `"properties": {}, "required": []`.

---

## Converse Loop

```python
while True:  # outer loop: one iteration per user message
    messages.append(user_message)

    while True:  # inner loop: one iteration per model call
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
            break

        elif stop_reason == "tool_use":
            # Execute all requested tools, append results, loop again
            messages.append(tool_results_message)
```

---

## Test Conversation

Run with:
```bash
python travel_assistant.py
```

Try:
```
You: I'm in Seattle
You: Japanese, somewhere on the East Side
```

**Expected:** `[tool call]` and `[tool result]` lines appear as the model calls `search_restaurants`, then `get_availability`. Sakura Garden (`r2`) has no availability, so the model finds an alternative and recommends a restaurant that is actually available in the mock data.

---

## Bonus Test

```
You: French food in the Waterfront area
```

**Expected:** Le Bistro (`r5`) has no availability. The model either suggests an alternative French restaurant or explains that none are available in that area.
