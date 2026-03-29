# Exercise Solution – Restaurant Recommendation Agent

## Agent Instruction

```
You are a helpful restaurant recommendation assistant. When a user asks for a restaurant recommendation, always use the available tools to search for matching options and check availability before making a suggestion. Base your recommendation on the tool results, not on assumptions. If the first restaurant has no availability, check the next best option before responding.
```

---

## Action Group

Action group name: `restaurant-tools`

### `search_restaurants`

| Parameter | Type   | Required | Description                                          |
|-----------|--------|----------|------------------------------------------------------|
| `cuisine` | string | No       | The cuisine type (e.g. Italian, Japanese). If omitted, all restaurants are returned. |

### `get_availability`

| Parameter         | Type   | Description                   |
|-------------------|--------|-------------------------------|
| `restaurant_name` | string | The name of the restaurant    |
| `date`            | string | The date in YYYY-MM-DD format |

---

## Test Prompt

```
Find me a moderately priced Italian restaurant for tonight.
```

---

## Expected Agent Behavior

1. The agent calls `search_restaurants` with `cuisine=Italian`
2. The agent picks the top result (`Trattoria Bella`) and calls `get_availability`
3. `Trattoria Bella` has availability — the agent presents it as the recommendation
4. If the agent tries `Osteria Romana` instead, it will find no availability and fall back to the next option
