# Exercise Solution – Travel Planner

## System Prompt

The key design choice: the system prompt explicitly forbids answering from memory and requires tool use before any recommendation. Without this constraint, the model may skip tool calls when it already "knows" about a city.

```
You are a helpful travel planning assistant. Help users plan their visits to cities.

You must NOT answer travel planning questions from memory. Always use the available tools
to gather current weather information and top attractions before making any recommendations.

Base your recommendations on tool results only.
```

---

## Tool Schemas

Two tools are defined. Both require `city`; `get_weather` additionally requires `date`.

```python
TOOLS = [
    {
        "toolSpec": {
            "name": "get_weather",
            "description": "Returns current weather conditions and forecast for a given city and date.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "The city to get weather for."},
                        "date": {"type": "string", "description": "The date in YYYY-MM-DD format."},
                    },
                    "required": ["city", "date"],
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
                        "city": {"type": "string", "description": "The city to get attractions for."},
                    },
                    "required": ["city"],
                }
            },
        }
    },
]
```

---

## Tool Implementations

Both functions use `.lower()` on the city so lookups are case-insensitive, and return sensible fallbacks when data is missing.

```python
def get_weather(city: str, date: str) -> dict:
    key = (city.lower(), date)
    return WEATHER_DATA.get(
        key,
        {"city": city, "date": date, "condition": "No data available"},
    )

def get_top_attractions(city: str) -> dict:
    return ATTRACTIONS_DATA.get(
        city.lower(),
        {"city": city, "attractions": []},
    )
```

---

## Converse Loop

The model typically calls both tools in sequence before producing its final answer. The inner `while True` loop keeps running until `stop_reason == "end_turn"`, at which point we print the response and break.

```python
if stop_reason == "end_turn":
    for block in output_message["content"]:
        if "text" in block:
            print(f"\nAssistant: {block['text']}\n")
    break

elif stop_reason == "tool_use":
    tool_results = []
    for block in output_message["content"]:
        if "toolUse" in block:
            tool_name = block["toolUse"]["name"]
            tool_input = block["toolUse"]["input"]
            tool_use_id = block["toolUse"]["toolUseId"]

            print(f"  [tool call] {tool_name}({tool_input})")
            result = execute_tool(tool_name, tool_input)
            print(f"  [tool result] {result}")

            tool_results.append({
                "toolResult": {
                    "toolUseId": tool_use_id,
                    "content": [{"json": result}],
                }
            })
    messages.append({"role": "user", "content": tool_results})
```

---

## Sample Session

```
Travel Planner
========================================
Ask me to help plan your visit to a city.

You: I'll be in London this Saturday with my family. What should we do?
  [tool call] get_weather({'city': 'London', 'date': '2026-03-14'})
  [tool result] {'city': 'London', 'condition': 'Light rain in the morning, clearing to partly cloudy by afternoon', ...}
  [tool call] get_top_attractions({'city': 'London'})
  [tool result] {'city': 'London', 'attractions': [{'name': 'British Museum', ...}, ...]}