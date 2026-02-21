# Tool Setup: DynamoDB Table and Lambda Function

When a customer reports a bug, the chatbot needs to persist it somewhere so the engineering team can track and follow up on it. A simple way to do this is to store each bug report as a record in a database. In this project we use DynamoDB as our database of choice, but we could have used any other datastore.

The Bedrock Agent itself cannot write to DynamoDB directly. Agents interact with external systems through *tools* — functions that the agent can invoke during a conversation. AWS Lambda is the standard way to implement these tools: you write a  function, and the agent calls it with structured parameters. The Lambda function then does the actual work (in our case, writing to DynamoDB).

This guide walks you through creating both resources and connecting them.

## 1. Create the DynamoDB Table

We first need create a DynamoDB table, which is similar to a table in a relational database. Our DynamoDB table will store one item per bug report.

DynamoDB requires to define a column with unique values that uniquely identify each row. This special column is called a partition column or a parition field. In our case it will be a column called `ticketId`

### Steps

Here is what you need to do to create a new DynamoDB table.

1. Open the **DynamoDB** console and click **Create table**.

<!-- screenshot: DynamoDB console → Create table button -->

2. Set the table name to `BugReports`.

3. Set the partition key to `ticketId` with type **String**.

<!-- screenshot: Table creation form with name and partition key filled in -->

4. Leave the rest of the settings at their defaults. On-demand capacity mode is fine for this project since we won't be generating high traffic.

5. Click **Create table** and wait for the status to change to **Active**.

<!-- screenshot: Table list showing BugReports with Active status -->

That's all we need for the table. We don't need to define any other attributes upfront because DynamoDB is schema-flexible — the Lambda function will write additional fields (description, steps to reproduce, environment, status) and DynamoDB will accept them without any schema changes. The only mandatory field in our case is `ticketId`.

## 2. Create the Lambda Function

We now need do define a Lambda function that the Bedrock Agent will call to create a new ticket. When the agent decides it has enough information to file a bug report, it invokes this function with three parameters: a description of the bug, the steps to reproduce it, and the environment (browser, OS, etc.). The function generates a ticket ID, writes the record to DynamoDB, and returns the ticket ID to the agent so it can share it with the customer.

The code for this function is provided in `create-bug-report.py`.

### Steps

Here is how to define a Lambda function.

1. Open the **Lambda** console and click **Create function**.

<!-- screenshot: Lambda console → Create function button -->

2. Select **Author from scratch**.

3. Set the function name to `create-bug-report`.

4. Set the runtime to **Python 3.9** (or any later Python 3.x version).

5. Leave the other settings at their defaults and click **Create function**.

<!-- screenshot: Create function form with name and runtime filled in -->

6. In the **Code** tab we can write the implementation of our function. Just remove the default code, and replace it with the content of the `create-bug-report.py`

<!-- screenshot: Lambda code editor with the create-bug-report.py code pasted in -->

7. Click **Deploy** to save the function.

We can now call our function to create new tickets!

### Understanding the Code

Before moving on, it's worth understanding what the Lambda handler does:

- **Validates the request.** It checks that the incoming event has `messageVersion: "1.0"` and `function: "create_bug_report"`. This is the format that Bedrock Agents use when calling a tool. If the event doesn't match, the function returns an error.

- **Extracts parameters.** The agent sends parameters as a list of `{name, value}` objects. The function extracts `description`, `stepsToReproduce`, and `environment` from this list.

- **Generates a ticket ID.** Each bug report gets a unique UUID so it can be referenced later.

- **Writes to DynamoDB.** The function stores the ticket along with metadata like the session ID and agent ID, which are useful for tracing and debugging.

- **Returns a response.** The function returns the ticket ID and status (`OPEN`) in the format that Bedrock Agents expect. The agent then uses this information to confirm the ticket with the customer.

## 3. Grant Lambda Permission to Write to DynamoDB

By default, a new Lambda function only has permission to write logs to CloudWatch. It cannot access DynamoDB or any other AWS service. If you try to invoke the function now, it will fail with an `AccessDeniedException` when it tries to call `table.put_item()`.

AWS uses IAM (Identity and Access Management) to control what each service and function can do. To control what our function can do we need to update a so-called *IAM role* associated with our Lambda function.

To allow our Lambda to write to DynamoDB we need to add a policy to this role that allows writing to the `BugReports` table.

### Steps

Here is what you need to do to allow this Lambda function to write to the `BugReports` table.

1. In the Lambda console, open the `create-bug-report` function and go to the **Configuration** tab.

2. Click **Permissions** in the left sidebar. You will see the function's execution role name.

<!-- screenshot: Lambda Configuration → Permissions showing the execution role -->

3. Click the role name to open it in the IAM console.

4. Click **Add permissions** → **Attach policies** → **Create inline policy**.

<!-- screenshot: IAM role page → Add permissions dropdown -->

5. Switch to the **JSON** editor and paste the following policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "dynamodb:PutItem",
            "Resource": "arn:aws:dynamodb:*:*:table/BugReports"
        }
    ]
}
```

This policy grants the minimum permission needed: only `PutItem` (write a single record) and only on the `BugReports` table. Following the principle of least privilege, we don't grant broader permissions like `dynamodb:*` or access to all tables.

<!-- screenshot: IAM policy editor with the JSON policy -->

6. Click **Next**, give the policy a name (e.g. `BugReportsWriteAccess`), and click **Create policy**.

7. Go back to the Lambda function's **Permissions** tab and verify the new policy appears under the execution role.

<!-- screenshot: Lambda Permissions tab showing the role with the new policy attached -->

## 4. Test the Lambda Function

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
