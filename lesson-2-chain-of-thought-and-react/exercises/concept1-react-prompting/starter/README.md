# Exercise – Restaurant Recommendation Agent

## Overview

In this exercise you will build a restaurant recommendation agent using Amazon Bedrock Agents. The Lambda functions that back the agent's tools are provided and ready to deploy. Your task is to deploy the infrastructure, create the agent, and wire everything together.

---

## Step 1 – Deploy the Lambda Functions

A CloudFormation template is provided in this folder. It creates two Lambda functions and grants Bedrock permission to invoke them.

**AWS Console:**

1. Open the [CloudFormation console](https://console.aws.amazon.com/cloudformation)
2. Click **Create stack** → **With new resources (standard)**
3. Select **Upload a template file** and choose `template.yaml` from this folder
4. Enter a stack name, for example `restaurant-agent`
5. Click **Next** through the remaining steps, check **I acknowledge that AWS CloudFormation might create IAM resources with custom names**, then click **Submit**
6. Wait for the stack status to reach `CREATE_COMPLETE`
7. Open the **Outputs** tab and copy the two Lambda ARNs — you will need them when creating the action group

**AWS CLI:**

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

In your agent, create an action group named `restaurant-tools` with two functions:

### `search_restaurants`

Searches for restaurants matching the user's preferences.

| Parameter | Type   | Description           |
|-----------|--------|-----------------------|
| `city`    | string | The city to search in |
| `cuisine` | string | The cuisine type      |

Connect this function to the `search-restaurants` Lambda (ARN from the CloudFormation outputs).

### `get_availability`

Checks table availability at a specific restaurant.

| Parameter         | Type   | Description                   |
|-------------------|--------|-------------------------------|
| `restaurant_name` | string | The name of the restaurant    |
| `date`            | string | The date in YYYY-MM-DD format |

Connect this function to the `get-availability` Lambda (ARN from the CloudFormation outputs).

---

## Step 4 – Test the Agent

Use this prompt:

```
Find me a moderately priced Italian restaurant in Seattle for tonight.
```

Observe how the agent calls tools in sequence before producing a final recommendation.

---

## Deliverable

- Your agent instruction prompt
- A screenshot or copy of the chat history showing the agent using both tools
