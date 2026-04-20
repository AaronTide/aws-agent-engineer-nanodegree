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

> **Note – mock data scope:** `WEATHER_DATA` and `ATTRACTIONS_DATA` only contain entries for London. The tool schemas accept any city string, so supporting additional cities requires only adding new entries to those dictionaries — no changes to the tool interface or the Converse loop are needed.

> **Why use a tool instead of relying on the model's knowledge?** The model may already know popular London attractions, but a tool lets you serve *current* information: a newly opened attraction, a venue that is temporarily closed, or a special event happening this weekend. Grounding recommendations in tool results keeps them accurate regardless of what the model was trained on.

---

## Example Prompts

Try these four prompts to exercise different combinations of weather and group type:

| Scenario | Prompt |
|----------|--------|
| Rainy day, family | `I'll be in London on 2026-03-14 with my family. What should we do?` |
| Sunny day, family | `I'll be in London on 2026-03-15 with my kids. What should we do?` |
| Rainy day, adults | `I'm in London on 2026-03-14 for a night out with friends. What do you suggest?` |
| Sunny day, adults | `I'm visiting London on 2026-03-15 with friends. What's fun to do?` |

The model should favour indoor attractions on the rainy day and outdoor ones on the sunny day, and should omit non-family-friendly options when the group includes children.

---

## Sample Session

```
Travel Planner
========================================
Ask me to help plan your visit to a city.

You: I'll be in London on 2026-03-14 with my family. What should we do?
  [tool call] get_weather({'city': 'London', 'date': '2026-03-14'})
  [tool result] {'city': 'London', 'condition': 'Light rain in the morning, clearing to partly cloudy by afternoon', ...}
  [tool call] get_top_attractions({'city': 'London'})
  [tool result] {'city': 'London', 'attractions': [{'name': 'British Museum', ...}, ...]}