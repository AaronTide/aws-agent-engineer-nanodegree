# Exercise Solution – Restaurant Recommendation Agent

## Agent Instruction

```
You are a helpful restaurant recommendation assistant. When a user asks for a restaurant recommendation, always use the available tools to search for matching options and check availability before making a suggestion. Base your recommendation on the tool results, not on assumptions. If the first restaurant has no availability, check the next best option before responding.
```

---

## Action Group

Action group name: `restaurant-tools`

### `get_cuisines`

Returns the list of cuisine types available. Takes no parameters.

### `search_restaurants`

| Parameter | Type   | Required | Description                                                              |
|-----------|--------|----------|--------------------------------------------------------------------------|
| `cuisine` | string | No       | The cuisine type (e.g. Italian, Japanese). If omitted, all are returned. |

### `get_availability`

| Parameter       | Type   | Required | Description                     |
|-----------------|--------|----------|---------------------------------|
| `restaurant_id` | string | Yes      | The unique ID of the restaurant |

---

## Test Prompt

```
Find me an Italian restaurant for tonight.
```

---

## Expected Agent Behavior

1. The agent calls `get_cuisines` to discover available cuisine types
2. The agent calls `search_restaurants` with `cuisine=Italian` and receives `Trattoria Bella` (r1) and `Osteria Romana` (r2)
3. The agent calls `get_availability` with `restaurant_id=r1` — `Trattoria Bella` has availability
4. The agent presents `Trattoria Bella` as the recommendation
5. If the agent tries `Osteria Romana` (r2) first, it will find no availability and fall back to `Trattoria Bella`

---

## Cleanup

When you are done with the exercise, delete the CloudFormation stack to avoid ongoing charges:

```bash
aws cloudformation delete-stack --stack-name restaurant-agent --region us-east-1
```

You can also delete the Bedrock Agent from the Amazon Bedrock console.
