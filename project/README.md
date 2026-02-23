# Customer Support Chatbot with Amazon Bedrock Flows

In this project you will build a customer support chatbot using Amazon Bedrock Flows. The chatbot will need to handle one of the following types of messages:

- **Bug reports** - if a customer reports a bug the application need to collect additional information and create a ticket for the reported bug.
- **Product questions** - the application should respond to a question using its Knowledge Base.
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
| `create-bug-report.py` | Lambda function that stores bug reports in DynamoDB. Deploy this as an Agent tool. |
| `generate-eval-dataset.py` | Script that runs your flow against a test suite and produces a JSONL file for Bedrock Evaluations. |
| `flow-tests-template.json` | Template for your test suite. Copy this and fill in your own test cases. |

## Project Instructions

### Step 1: Create a Bug Report Tool

When a customer reports a bug, the chatbot needs to persist it somewhere so the engineering team can follow up. In this project we use a DynamoDB table as a simple ticket store, and a Lambda function as the tool that Bedrock Agents can call to create a new ticket.

Follow the detailed walkthrough in [Tool Setup](docs/tool-setup.md). This guide covers creating the table, deploying the Lambda, configuring IAM permissions, and testing the function in isolation.

### Step 2: Set Up a Knowledge Base

Product questions need to be answered from internal documentation, as generic LLM models won't have product specific information. Bedrock Knowledge Bases can be used to handle this by indexing documents and retrieving relevant passages at query time.

For this project, use the [AWS Well-Architected Framework PDF](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) as product's internal documentation. This is a well-known document that is commonly used in Knowledge Base demos, and it gives you realistic content to test against without needing to prepare custom documentation.

To test your application you will ask it questions related to the Well-Architected Framework.

Follow these steps:

1. **Create a new S3 bucket in your account.** Create a new S3 bucket to store the knowledge base files.

2. **Upload the PDF to S3.** Download the Well-Architected Framework whitepaper PDF and upload it to the S3 bucket created in step 1.

3. **Create the Knowledge Base.** In the Bedrock console, go to Knowledge Bases and create a new one. Select the S3 bucket from step 1 as the data source. Choose a default chunking strategy and an embedding model (e.g. Amazon Titan Embeddings). Bedrock will create the vector index for you.

4. **Sync the data source.** After creating the Knowledge Base, run a sync so that the PDF is indexed and ready for retrieval. You can test it directly in the console by asking a question like "What are the pillars of the Well-Architected Framework?" and verifying that relevant passages are returned.

### Step 3: Build the Bedrock Flow

Now that you have the bug report tool and the Knowledge Base ready, create a Bedrock Flow that ties everything together.

The flow should accept a customer message and classify it into one of the known categories. Based on the classification, it should route the message to the appropriate handler.

The flow should handle three paths:

- **Bug reports.** The customer may not provide all the details upfront. Use an agent to collect the missing information (description, steps to reproduce, environment) before creating a ticket.

- **Product questions.** Use the Knowledge Base from Step 2 to retrieve relevant passages, then summarize them into a helpful customer-facing response. The raw retrieval results might not be suitable to show directly — they need to be synthesized. If the Knowledge Base doesn't have relevant content, the customer should still get a useful response rather than silence.

- **Everything else.** Any request that doesn't fit the known categories (billing changes, account updates, etc.) can't be handled automatically. The customer should be politely directed to a human support channel.

Every execution path in a Bedrock Flow must terminate at its own Output node.

#### Some suggestions

Here are some things to keep in mind when working on your application:

* Condition nodes in Bedrock Flows use exact string matching, so the classification output needs to be predictable.
* You can use an agent node to collect more information if initial request is unclear or incomplete.
* A single Output node can't receive connections from multiple branches. You need a separate Output node for each path.
* Knowledge Base retrieval results are raw document chunks, not polished answers. You'll likely need a Prompt node after the KB node to synthesize them into a customer-friendly response.
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
* [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html) - RAG for product questions
* [Amazon Bedrock Evaluations](https://docs.aws.amazon.com/bedrock/latest/userguide/evaluation.html) - LLM-as-a-judge evaluation
* [AWS Lambda](https://aws.amazon.com/lambda/) - Bug report tool runtime
* [Amazon DynamoDB](https://aws.amazon.com/dynamodb/) - Bug report storage

## License

[License](../LICENSE.md)
