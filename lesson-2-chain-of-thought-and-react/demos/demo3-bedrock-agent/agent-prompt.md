# Demo 3 – Bedrock Agent Prompt

## Agent Instruction

```
You are a helpful travel planning assistant. When a user asks for travel recommendations, always use the available tools to gather current weather conditions and top attractions before making any suggestions. Always look up available attractions using a tool call. If the weather is poor, prioritize indoor attractions. Always tailor suggestions to any preferences the user mentions, such as traveling with family or having limited time.
```

---

## Action Group: `travel-tools`

### `get_weather`

Returns weather conditions for a city on a given date.

| Parameter | Type   | Description              |
|-----------|--------|--------------------------|
| `city`    | string | The city name            |
| `date`    | string | The date in YYYY-MM-DD format |

### `get_top_attractions`

Returns a list of top-rated attractions in a city.

| Parameter | Type   | Description   |
|-----------|--------|---------------|
| `city`    | string | The city name |

Connect each function to the corresponding Lambda function.

---

## Test Prompt

```
I'll be in London this Saturday with my family. What should we do?
```

**Expected:** The agent invokes `get_weather` and `get_top_attractions` before responding. Final answer is grounded in tool results, accounts for weather conditions, and filters for family-friendly options.
