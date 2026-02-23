# Tool Setup: DynamoDB Table and Lambda Function

When a customer reports a bug, the chatbot needs to persist it somewhere so the engineering team can track and follow up on it. A simple way to do this is to store each bug report as a record in a database. In this project we use DynamoDB as our database of choice, but we could have used any other datastore.

The Bedrock Agent itself cannot write to DynamoDB directly. Agents interact with external systems through *tools* — functions that the agent can invoke during a conversation. AWS Lambda is the standard way to implement these tools: you write a  function, and the agent calls it with structured parameters. The Lambda function then does the actual work (in our case, writing to DynamoDB).

This guide walks you through creating both resources and connecting them.

## Deploy with CloudFormation

All three resources — the DynamoDB table, the Lambda function, and the IAM role — are defined together in `cloudformation.yaml` at the root of the project. CloudFormation provisions them in the right order and wires them together automatically.

### What the template creates

| Resource | Name | Purpose |
|---|---|---|
| DynamoDB table | `BugReports` | Stores one item per bug report, keyed by `ticketId` |
| IAM role | `create-bug-report-role` | Grants the Lambda function permission to write logs and call `PutItem` on the table |
| Lambda function | `create-bug-report` | Receives a bug report from the Bedrock Agent and writes it to DynamoDB |

The IAM role follows the principle of least privilege: it grants only `dynamodb:PutItem` on the `BugReports` table — nothing more.

### Steps

Run the following command from the project root to create the stack:

```bash
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name bug-report-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --profile bedrock-user
```

The `--capabilities CAPABILITY_NAMED_IAM` flag is required because the template creates a named IAM role. CloudFormation asks you to acknowledge this explicitly as a safety check.

Wait for the command to print `Successfully created/updated stack - bug-report-stack`. The three resources are now live.

### Understanding the Lambda code

The Lambda handler is defined in `create_bug_report.py` and embedded in the template. Here is what it does:

- **Validates the request.** It checks that the incoming event has `messageVersion: "1.0"` and `function: "create_bug_report"`. This is the format that Bedrock Agents use when calling a tool. If the event doesn't match, the function returns an error.

- **Extracts parameters.** The agent sends parameters as a list of `{name, value}` objects. The function extracts `description`, `stepsToReproduce`, and `environment` from this list.

- **Generates a ticket ID.** Each bug report gets a unique UUID so it can be referenced later.

- **Writes to DynamoDB.** The function stores the ticket with a status of `OPEN` and a creation timestamp.

- **Returns a response.** The function returns the ticket ID and status (`OPEN`) in the format that Bedrock Agents expect. The agent then uses this information to confirm the ticket with the customer.

## Test the Lambda Function

At this stage you should have a Lambda function that should be able to create new tickets. In theory now it can be used by your agent, but to make sure that everything was set up correctly, you can test this function in isolation. We can call our function from the AWS console and check if it works correctly and if it can create new tickets in DynamodDB.

### Steps

To test a function we need to create a test event, and call our function with it.

1. In the Lambda console, open the `create-bug-report` function and go to the **Test** tab.

2. Create a new test event with the following JSON:

```json
{
    "messageVersion": "1.0",
    "function": "create_bug_report",
    "actionGroup": "bug-report-actions",
    "sessionId": "test-session-001",
    "agent": {
        "id": "test-agent",
        "alias": "test-alias"
    },
    "parameters": [
        {
            "name": "description",
            "value": "The checkout page crashes when I click the Pay button"
        },
        {
            "name": "stepsToReproduce",
            "value": "1. Add an item to the cart. 2. Go to checkout. 3. Click Pay."
        },
        {
            "name": "environment",
            "value": "Chrome 120 on macOS Sonoma"
        }
    ]
}
```

This event matches the format that Bedrock Agents use when calling a tool. The `messageVersion`, `function`, and `parameters` fields are what the Lambda handler expects, including the `sessionId` and `agent` fields that agent passes as metadata.

<!-- screenshot: Lambda Test tab with the test event JSON -->

3. To call the function and pass the test event click **Test**. You should see a successful response like:

```json
{
    "messageVersion": "1.0",
    "response": {
        "actionGroup": "bug-report-actions",
        "function": "create_bug_report",
        "functionResponse": {
            "responseBody": {
                "TEXT": {
                    "body": "{\"ticketId\": \"...\", \"status\": \"OPEN\"}"
                }
            }
        }
    }
}
```

<!-- screenshot: Lambda test execution result showing a successful response -->

4. To confirm the record was actually written, go to the **DynamoDB** console, open the `BugReports` table, and click **Explore table items**. You should see one item with the ticket ID from the response.

<!-- screenshot: DynamoDB table items view showing the newly created bug report -->

## Common failures

If the test fails with an `AccessDeniedException`, go back to step 3 above and check that the IAM policy is attached to the correct execution role.

If it fails with a `ResourceNotFoundException`, check that the DynamoDB table name is exactly `BugReports`.

## Next Steps

Now that the Lambda function can create bug reports in DynamoDB, the next step is to connect it to a Bedrock Agent. Go back to the main [README](../README.md) and continue with the agent setup in Step 1.
