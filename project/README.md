# Customer Support Chatbot with Amazon Bedrock Flows

In this project you will build a customer support chatbot using Amazon Bedrock Flows. The chatbot will need to handle one of the following types of messages:

- **Bug reports** - Collected by an agent and stored in a DynamoDB table via a Lambda tool.
- **Product questions** - Answered using a Knowledge Base with your product documentation.
- **Other requests** - Politely redirected to a human support phone line.

## Getting Started

### Dependencies

- An AWS account with Amazon Bedrock access enabled.
- AWS CLI configured with appropriate credentials.
- Python 3.9+ with `boto3` installed.
- Access to an Amazon Bedrock model (the solution uses Amazon Nova Premier, but you can use any supported model).

### Project Files

| File | Description |
|------|-------------|
| `create-bug-report.py` | Lambda function that stores bug reports in DynamoDB. Deploy this as an Agent tool. |
| `generate-eval-dataset.py` | Script that runs your flow against a test suite and produces a JSONL file for Bedrock Evaluations. |
| `flow-tests-template.json` | Template for your test suite. Copy this and fill in your own test cases. |
| `solution/` | Reference solution with the complete flow definition, test prompts, and a diagram. |

## Project Instructions

### Step 1: Create a Bug Report Tool

When a customer reports a bug, the chatbot needs to persist it somewhere so the engineering team can follow up. In this project we use a DynamoDB table as a simple ticket store, and a Lambda function as the tool that Bedrock Agents can call to create a new ticket.

The provided `create-bug-report.py` is the Lambda handler. It receives structured bug report parameters (description, steps to reproduce, environment), generates a unique ticket ID, and writes the record to DynamoDB.

Follow these steps to deploy it:

1. **Create the DynamoDB table.** In the DynamoDB console, create a table named `BugReports`. Set the partition key to `ticketId` (String). The default on-demand capacity settings are fine for this project.

2. **Create the Lambda function.** In the Lambda console, create a new function with a Python 3.9+ runtime. Copy the contents of `create-bug-report.py` into the function code. Under the function's execution role, add a policy that allows `dynamodb:PutItem` on the `BugReports` table.

3. **Create a Bedrock Agent for bug data collection.** In the Bedrock console, create a new agent. This agent's job is to talk to the customer and collect the details needed for a bug report: a description of the problem, steps to reproduce it, and the environment (browser, OS, etc.). Write the agent's instructions so that it asks the customer for any missing information before proceeding.

4. **Create a Bedrock Agent for bug report creation.** Create a second agent and attach the Lambda function from step 2 as an action group tool. Define a function called `create_bug_report` with three string parameters: `description`, `stepsToReproduce`, and `environment`. This agent receives the structured data from the first agent and calls the tool to persist the bug report.

We use two separate agents because each has a distinct responsibility. The first agent focuses on conversation and information gathering, while the second focuses on formatting the data and calling the tool. This separation keeps each agent's prompt simple and makes the overall pipeline easier to debug.

### Step 2: Set Up a Knowledge Base

Product questions (e.g. "What is a Well-Architected Framework?") need to be answered from your documentation. Bedrock Knowledge Bases handle this by indexing documents and retrieving relevant passages at query time.

For this project, use the [AWS Well-Architected Framework PDF](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) as your data source. This is a well-known document that is commonly used in Knowledge Base demos, and it gives you realistic content to test against without needing to prepare custom documentation.

Follow these steps:

1. **Upload the PDF to S3.** Download the Well-Architected Framework whitepaper PDF and upload it to an S3 bucket in your account.

2. **Create the Knowledge Base.** In the Bedrock console, go to Knowledge Bases and create a new one. Select the S3 bucket from step 1 as the data source. Choose a default chunking strategy and an embedding model (e.g. Amazon Titan Embeddings). Bedrock will create the vector index for you.

3. **Sync the data source.** After creating the Knowledge Base, run a sync so that the PDF is indexed and ready for retrieval. You can test it directly in the console by asking a question like "What are the pillars of the Well-Architected Framework?" and verifying that relevant passages are returned.

### Step 3: Build the Bedrock Flow

Now that you have the bug report tool and the Knowledge Base ready, create a Bedrock Flow that ties everything together. The flow receives a customer message, classifies it, and routes it to the appropriate path.

Open the Bedrock Flows console and build the flow step by step:

1. **Add the Input node.** Every flow starts with an Input node. This is where the customer message enters the flow as a string.

2. **Add a classification Prompt node.** Connect it to the Input node. Write a prompt that classifies the customer message as `BUG_REPORT` or `PRODUCT_QUESTION`. Instruct the model to return just one word. This is important because the Condition node downstream uses exact string matching, so the classifier must output a single, predictable token. Only list two categories explicitly; anything that doesn't match will fall through to the default branch, so you don't need to maintain a growing list of category names.

3. **Add a Condition node.** Connect it to the classification Prompt node. Define two conditions:
   - `is_bug`: `conditionInput == "BUG_REPORT"`
   - `is_product_question`: `conditionInput == "PRODUCT_QUESTION"`

   Any input that matches neither condition will follow the `default` branch.

4. **Wire up the bug report path.** Add an Agent node for the BugDataCollector agent from Step 1 and connect the `is_bug` condition to it. Feed the original customer message (from the Input node) into the agent, not the classification output. Then add a second Agent node for the BugReportCreator agent and connect it after the first. Finally, add an Output node at the end of this chain.

5. **Wire up the product question path.** Add a Knowledge Base node and connect the `is_product_question` condition to it. Feed the original customer message as the retrieval query. Then add a Prompt node that receives both the original customer message and the Knowledge Base retrieval results. Write a prompt that summarizes the retrieved passages into a helpful answer, or suggests calling a support phone number if the results don't address the question. Add an Output node at the end.

6. **Wire up the default path.** Add a Prompt node and connect the `default` condition to it. Write a prompt that politely tells the customer their request can't be handled automatically and suggests calling a support phone number. Add an Output node at the end.

Each path needs its own Output node because Bedrock Flows requires every execution path to terminate at an Output node.

## Testing

### Write Test Prompts

Copy `flow-tests-template.json` to `flow-tests.json` and fill in your own test cases. You should create at least one test per branch (bug report, product question, and other). The template shows the required fields for each test entry.

Set `flowInputNode.nodeName` to the name of the Input node in your flow.

### Test Manually in the Console

Before running the full test suite, try your flow in the Bedrock console. Enter a customer message and verify that it is routed to the correct branch. Use one message per category to confirm the classifier works:

- A message describing a software problem (should go to the bug report path).
- A question about the Well-Architected Framework (should go to the Knowledge Base path).
- A request that doesn't fit either category, like a billing change (should go to the default path).

### Generate an Evaluation Dataset

Once your flow handles all three branches correctly, use `generate-eval-dataset.py` to invoke it with every test prompt and produce a JSONL dataset for Bedrock Evaluations:

```bash
python generate-eval-dataset.py \
  --tests-json flow-tests.json \
  --flow-id <your-flow-id> \
  --flow-alias-id <your-flow-alias-id>
```

This writes `output_eval_dataset.jsonl`, where each line contains the original prompt, your flow's response, and the reference response from your test file.

Add the `--enable-trace` flag to print trace events for each invocation, which is useful for debugging routing issues:

```bash
python generate-eval-dataset.py \
  --tests-json flow-tests.json \
  --flow-id <your-flow-id> \
  --flow-alias-id <your-flow-alias-id> \
  --enable-trace
```

### Run Bedrock Evaluations

Finally, use the generated dataset to run an LLM-as-a-judge evaluation in Bedrock:

1. **Upload the dataset to S3.** Upload `output_eval_dataset.jsonl` to an S3 bucket.
2. **Create an evaluation job.** In the Bedrock console, go to Evaluations and create a new job. Select the **LLM-as-a-judge** method and point it to the JSONL file you uploaded. The evaluator model will compare each flow response against the reference response and score it.
3. **Review results.** Check the evaluation results to assess how well your flow handles each category of request. Look for cases where the flow misrouted a message or produced an unhelpful response, and iterate on your prompts or flow design accordingly.

## Built With

* [Amazon Bedrock Flows](https://docs.aws.amazon.com/bedrock/latest/userguide/flows.html) - Orchestration of the LLM application
* [Amazon Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html) - Tool use for bug report creation
* [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html) - RAG for product questions
* [Amazon Bedrock Evaluations](https://docs.aws.amazon.com/bedrock/latest/userguide/evaluation.html) - LLM-as-a-judge evaluation
* [AWS Lambda](https://aws.amazon.com/lambda/) - Bug report tool runtime
* [Amazon DynamoDB](https://aws.amazon.com/dynamodb/) - Bug report storage

## License

[License](../LICENSE.md)
