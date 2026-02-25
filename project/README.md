# Customer Support Chatbot with Amazon Bedrock Flows

In this project you will build a customer support chatbot using Amazon Bedrock Flows. The chatbot will need to handle one of the following types of messages:

- **Bug reports** - if a customer reports a bug the application need to collect additional information and create a ticket for the reported bug.
- **Platform questions** - the application should answer common questions about orders, shipping, returns, and payments using an embedded FAQ.
- **Other requests** - politely redirected to a human support phone line.

## Getting Started

### Dependencies

- An AWS account with Amazon Bedrock access enabled.
- AWS CLI configured with appropriate credentials.
- Python 3.9+ with `boto3` installed.
- Access to an Amazon Bedrock model (the solution uses Amazon Nova models, but you can use any supported model).

### Project Files

| File | Description |
|------|-------------|
| `docs/tool-setup.md` | Step-by-step guide for creating the DynamoDB table, Lambda function, and IAM permissions. |
| `docs/testing.md` | Step-by-step guide for automated testing, creating a flow alias, and running Bedrock Evaluations. |
| `solution/` | Reference solution with the complete flow definition, test prompts, and a diagram. |
| `create_bug_report.py` | Lambda function that stores bug reports in DynamoDB. Deploy this as an Agent tool. |
| `generate-eval-dataset.py` | Script that runs your flow against a test suite and produces a JSONL file for Bedrock Evaluations. |
| `flow-tests-template.json` | Template for your test suite. Copy this and fill in your own test cases. |

## Project Instructions

### Step 1: Create a Bug Report Tool

When a customer reports a bug, the chatbot needs to persist it somewhere so the engineering team can follow up. In this project we use a DynamoDB table as a simple ticket store, and a Lambda function as the tool that Bedrock Agents can call to create a new ticket.

Follow the detailed walkthrough in [Tool Setup](docs/tool-setup.md). This guide covers creating the table, deploying the Lambda, configuring IAM permissions, and testing the function in isolation.

### Step 2: Handle Platform Questions

Platform questions (orders, shipping, returns, payments) need to be answered from your product's documentation. The simplest approach is to embed the document directly in the prompt — the model reads it at inference time and answers from it.

In this project, the flow includes a `FaqQuestion` prompt node that embeds a short FAQ document inline. You can replace the FAQ content with your own documentation.

> **Note:** Embedding documents in the prompt works well for short, stable content like a FAQ. For large documents, embedding the full text in every prompt becomes expensive and hits context limits. The standard solution is **Retrieval-Augmented Generation (RAG)**, which retrieves only the relevant passages at query time using a vector index. RAG with Amazon Bedrock Knowledge Bases is covered in a later course.

### Step 3: Build the Bedrock Flow

Now that you have the bug report tool ready, create a Bedrock Flow that ties everything together.

The flow should accept a customer message and classify it into one of the known categories. Based on the classification, it should route the message to the appropriate handler.

The flow should handle three paths:

- **Bug reports.** The customer may not provide all the details upfront. Use an agent to collect the missing information (description, steps to reproduce, environment) before creating a ticket.

- **Platform questions.** Use a Prompt node with an embedded FAQ to answer common questions about orders, shipping, returns, and payments. If the FAQ doesn't cover the question, the customer should still get a useful response rather than silence.

- **Everything else.** Any request that doesn't fit the known categories (billing changes, account updates, etc.) can't be handled automatically. The customer should be politely directed to a human support channel.

Every execution path in a Bedrock Flow must terminate at its own Output node.

#### Some suggestions

Here are some things to keep in mind when working on your application:

* Condition nodes in Bedrock Flows use exact string matching, so the classification output needs to be predictable.
* You can use an agent node to collect more information if initial request is unclear or incomplete.
* A single Output node can't receive connections from multiple branches. You need a separate Output node for each path.
* For platform questions, embed your FAQ directly in the prompt. Keep it concise — large documents inflate token costs and can hit context limits.
* Don't forget to deploy resources: deploy Lambda function, prepare agents
* Implement your solution step by step
* Agents can prompt users for additional information
* Use us-east-1

## Testing

### Write Test Prompts

Copy `flow-tests-template.json` to `flow-tests.json` and fill in your own test cases. You should create at least one test per branch (bug report, product question, and other). The template shows the required fields for each test entry.

Set `flowInputNode.nodeName` to the name of the Input node in your flow.

### Test Manually in the Console

Before running the full test suite, try your flow in the Bedrock console. Enter a customer message and verify that it is routed to the correct branch. Use one message per category to confirm the classifier works. Think about other use-cases you might need to test.

### Automated Testing and Evaluation

Once the flow handles all three branches correctly in the console, follow the detailed walkthrough in [Testing and Evaluation](docs/testing.md) to run automated tests and evaluate your flow.

## Built With

* [Amazon Bedrock Flows](https://docs.aws.amazon.com/bedrock/latest/userguide/flows.html) - Orchestration of the LLM application
* [Amazon Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html) - Tool use for bug report creation
* [Amazon Bedrock Evaluations](https://docs.aws.amazon.com/bedrock/latest/userguide/evaluation.html) - LLM-as-a-judge evaluation
* [AWS Lambda](https://aws.amazon.com/lambda/) - Bug report tool runtime
* [Amazon DynamoDB](https://aws.amazon.com/dynamodb/) - Bug report storage

## License

[License](../LICENSE.md)
