# Project Rubric: Customer Support Chatbot with Amazon Bedrock Flows

### 2. Build a Bedrock Flow with Classification and Routing

| Criteria | Submission Requirements | Reviewer Tip |
|----------|------------------------|--------------|
| Build a Bedrock Flow that classifies customer messages and routes them across distinct paths | - The flow contains an Input node connected to a Prompt node that classifies the customer message <br> - The classifier Prompt node instructs the model to return only one of the defined category labels with no additional text <br> - The flow contains a Condition node that routes execution based on the classifier output <br> - The Condition node expressions use exact string matching that aligns with the labels defined in the classifier prompt <br> - At least three distinct paths exist in the flow, each terminating at a separate Output node | - **Pass if:** messages of different types route to different branches and each path ends at its own Output node <br> - **Fail if:** fewer than three paths are present <br> - **Pass with comment if:** the flow uses structured output to generate a routing decision |

---

### 2. Implement the Bug Report Path Using an Agent and Lambda Tool

| Criteria | Submission Requirements | Reviewer Tip |
|----------|------------------------|--------------|
| Implement the bug report path using a Bedrock Agent configured with a Lambda-backed tool to collect information and create tickets | - The bug report path includes at least one Agent node <br> - The Agent node is configured with an action group that calls the `create-bug-report` Lambda function <br> - The agent collects bug description, steps to reproduce, and environment information from the customer <br> - A record is created in the `BugReports` DynamoDB table when a bug report message is processed through the flow | - **Pass if:** a bug report message sent through the flow results in a new item in the `BugReports` table <br> - **Fail if:** the Agent node is not connected to the Lambda tool, or no DynamoDB record is created <br> - **Pass with comment if:** the agent works but does not attempt to collect steps to reproduce or environment — note that these fields improve ticket quality <br> |

---

### 3. Implement Platform Question and Other Request Paths Using Prompt Nodes

| Criteria | Submission Requirements | Reviewer Tip |
|----------|------------------------|--------------|
| Implement paths for platform questions and other customer requests using Prompt nodes with embedded instructions | - The platform question path includes a Prompt node with the FAQ document content embedded in the prompt template <br> - The FAQ prompt produces a relevant answer when the question is covered by the FAQ <br> - The FAQ prompt directs the user to a support phone number when the question is not covered by the FAQ <br> - A separate path exists for other customer support requests that directs the user to a support phone number | - **Pass if:** a platform question returns an answer drawn from the FAQ content, an off-FAQ question returns a phone redirect, and an other-request message returns a phone redirect <br> - **Fail if:** the FAQ path is missing, the prompt template contains no FAQ content, or the other-requests path is absent <br> - **Pass with comment if:** the embedded FAQ is minimal — note that a more complete document improves response quality <br> - **Praise if:** the student uses a knowledge base instead of embedding FAQ into a prompt |

---

### 4. Test and Evaluate the Flow Using Automated Tooling and Bedrock Evaluations

| Criteria | Submission Requirements | Reviewer Tip |
|----------|------------------------|--------------|
| Test the flow using an automated test suite and evaluate response quality using Bedrock Evaluations with LLM-as-a-judge | - `flow-tests.json` contains at least one test entry for the bug report path, at least one for the platform question path, and at least one for the other requests path <br> - Each test entry contains an `id`, `prompt`, and `expected` field <br> - The `generate-eval-dataset.py` script is run against the flow and produces a JSONL output file <br> - The JSONL file is uploaded to S3 and a Bedrock Evaluation job is created <br> - The student provides at least one written observation about the evaluation results | - **Pass if:** the test file covers all three paths, a JSONL file is produced, and an evaluation job exists in the AWS account <br> - **Fail if:** the test file covers fewer than three paths, the JSONL file is not produced, or no evaluation job was created, the result correctness score is close to 0 <br> - **Pass with comment if:** scores are uniformly low — encourage the student to review reference responses and iterate on prompts <br> - **Praise if:** the student added edge-case prompts such as ambiguous messages or prompt injection attempts |

---

## Suggestions To Make Your Project Stand Out

1. Add a guardrail to the flow that blocks harmful content and prompt injection attempts before any model processes the message.
2. Add edge-case test prompts to `flow-tests.json`: ambiguous messages that could belong to multiple categories, very short messages with minimal context, and prompt injection attempts.
3. Replace the embedded FAQ with a Bedrock Knowledge Base backed by a vector index so the flow can handle a larger document without embedding it in every prompt.
4. Use structured output to ensure that the classifier node only produces valid values
