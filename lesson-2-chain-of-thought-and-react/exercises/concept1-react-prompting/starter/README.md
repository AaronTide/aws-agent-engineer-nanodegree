# Exercise – Restaurant Recommendation Agent

## Overview

In this exercise you will build a restaurant recommendation agent using Amazon Bedrock Agents. The Lambda functions that back the agent's tools are provided and ready to deploy. Your task is to deploy the infrastructure, create the agent, and wire everything together.

---

## Step 1 – Deploy the Lambda Functions

A CloudFormation template is provided in this folder to create functions for your agent. It creates three Lambda functions and grants Bedrock permission to invoke them:

- **get-cuisines** – returns the list of cuisine types available
- **search-restaurants** – returns restaurants, optionally filtered by cuisine
- **get-availability** – checks whether a specific restaurant has availability tonight

You would need to run the following command

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name restaurant-agent \
  --capabilities CAPABILITY_NAMED_IAM
```

---

## Step 2 – Create the Bedrock Agent

1. Open the [Amazon Bedrock console](https://console.aws.amazon.com/bedrock) and navigate to **Agents**
2. Click **Create agent**
3. Write an agent instruction that:
   - Describes it as a restaurant recommendation assistant
   - Tells it to always use tools before making suggestions
   - Tells it to base its recommendation on tool results, not assumptions

---

## Step 3 – Create the Action Group

In your agent, create an action group named `restaurant-tools` with three functions:

### `get_cuisines`

Returns the list of cuisine types available. Takes no parameters.

Connect this function to the `get-cuisines` Lambda (ARN from the CloudFormation outputs).

### `search_restaurants`

Searches for restaurants. Returns all restaurants if no cuisine is specified.

| Parameter | Type   | Required | Description                                                              |
|-----------|--------|----------|--------------------------------------------------------------------------|
| `cuisine` | string | No       | The cuisine type (e.g. Italian, Japanese). If omitted, all are returned. |

Connect this function to the `search-restaurants` Lambda (ARN from the CloudFormation outputs).

### `get_availability`

Checks whether a specific restaurant has availability for tonight.

| Parameter         | Type   | Required | Description                         |
|-------------------|--------|----------|-------------------------------------|
| `restaurant_id`   | string | Yes      | The unique ID of the restaurant     |

Connect this function to the `get-availability` Lambda (ARN from the CloudFormation outputs).

---

## Step 4 – Test the Agent

Use this prompt:

```
Find me an Italian restaurant for tonight.
```

Observe how the agent calls tools in sequence before producing a final recommendation.

---

## Deliverable

- Your agent instruction prompt
- A screenshot or copy of the chat history showing the agent using the tools
