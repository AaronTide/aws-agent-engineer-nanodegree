# Solution: Customer Support Chatbot

This folder contains a complete, working solution for the customer support chatbot project. It is intended as a reference for reviewers.

## Files

| File | Description |
|------|-------------|
| `flow-definition.json` | The full Bedrock Flow exported as JSON. |
| `flow-tests.json` | Test suite with one prompt per branch. |
| `final-flow.png` | Visual diagram of the flow in the Bedrock console. |

## Flow Architecture

![Final Flow](final-flow.png)

The flow has three paths that fan out from a shared classification step. Below is a walkthrough of every node, why it exists, and how the paths connect.

### Input and Classification

**FlowInputNode** (Input) receives the raw customer message as a string.

**InputPrompt** (Prompt) classifies the message into one of two known categories. The prompt is intentionally constrained:

```
Classify an input customer message as one of the following:
* BUG_REPORT
* PRODUCT_QUESTION
Customer message:
```{{customer_message}}```
Return just one word.
```

The instruction "Return just one word" is important. The Condition node downstream performs an exact string match (`conditionInput == "BUG_REPORT"`), so the classifier must return a single, predictable token. Allowing free-form output would make the condition unreliable.

Only two explicit categories are listed. Any message that does not fit either one will produce a response that matches neither condition, causing it to fall through to the `default` branch. This avoids maintaining an ever-growing list of categories and keeps the classifier focused.

**InputClassifier** (Condition) routes execution based on the classification:

| Condition | Expression | Target path |
|-----------|-----------|-------------|
| `is_bug` | `conditionInput == "BUG_REPORT"` | Bug report agents |
| `is_product_question` | `conditionInput == "PRODUCT_QUESTION"` | Knowledge Base |
| `default` | *(none - catches everything else)* | Other requests prompt |

### Path 1: Bug Reports

This path chains two Agent nodes:

**BugDataCollector** (Agent) receives the original customer message directly from FlowInputNode (not from the classifier output). This ensures the agent sees the full user message, not just the classification label. The agent's job is to converse with the user to collect structured bug details: what happened, steps to reproduce, and the environment.

**BugReportCreator** (Agent) receives the output of BugDataCollector. It takes the collected details and calls the `create-bug-report` Lambda tool to store a formal bug report in DynamoDB. The response includes the generated ticket ID.

Two separate agents are used instead of one because each has a distinct responsibility. BugDataCollector focuses on information gathering, while BugReportCreator focuses on formatting and persisting the report. This separation makes each agent's prompt simpler and more reliable.

### Path 2: Product Questions

This path combines retrieval with summarization:

**KnowledgeBaseNode** (KnowledgeBase) takes the original customer message from FlowInputNode and queries the Knowledge Base. It returns raw retrieval results as an array of matched document chunks.

**AggregateKnowledgeBase** (Prompt) receives two inputs: the original customer message (from FlowInputNode) and the retrieval results (from KnowledgeBaseNode). Its prompt instructs the model to:

- Summarize the Knowledge Base results into a helpful response if they answer the question.
- Suggest calling the support phone number if the results are not relevant.

This two-step design (retrieve then summarize) is used instead of a single RetrieveAndGenerate call because the Prompt node gives full control over how results are presented to the user. The fallback instruction ("suggest to call +12345678") ensures the chatbot never leaves the customer without a next step, even when the Knowledge Base has no relevant content.

### Path 3: Other Requests

**OtherRequests** (Prompt) handles everything that is not a bug report or a product question (e.g. billing changes, account updates). The prompt directs the model to politely explain that the request cannot be handled automatically and to suggest calling the support phone number. The instruction "Do not write anything else. Your output will be sent to a user directly" prevents the model from adding meta-commentary.

This path exists as a catch-all so the chatbot always responds, rather than failing silently on unrecognized requests.

### Output Nodes

Each path has its own Output node (`BugReportOutputNode`, `KnowledgeBaseOutputNode`, `OtherRequestsOutputNode`). Separate outputs are used because Bedrock Flows requires each execution path to terminate at an Output node, and a single output node cannot receive connections from multiple upstream branches.

## Test Suite

`flow-tests.json` contains three test cases, one per branch. Each test targets a specific routing path to verify the classifier and downstream nodes work correctly.

### t1_bug_report_branch (BUG_REPORT)

**Prompt:** "There is an issue with your website. It loads too slowly. Up to 20 seconds long. I am using Safari"

This prompt describes a clear software defect and includes environment details (Safari). It should be classified as `BUG_REPORT` and routed to the BugDataCollector agent. The expected response acknowledges the issue and asks for reproduction steps, confirming the agent is gathering structured data before creating a ticket.

### t2_product_question_branch (PRODUCT_QUESTION)

**Prompt:** "What is a Well-Architected Framework?"

A factual question about an AWS product. It should be classified as `PRODUCT_QUESTION` and routed to the Knowledge Base path. The expected response summarizes what the Well-Architected Framework is, based on content retrieved from the Knowledge Base.

### t3_default_other_branch (OTHER)

**Prompt:** "Can you change the billing address on my last invoice and resend it to accounting?"

A billing/account request that does not fit either known category. The classifier should return something other than `BUG_REPORT` or `PRODUCT_QUESTION`, causing it to fall through to the `default` condition. The expected response politely directs the customer to call the support phone number.

### About the `expected` field

The `expected` field provides a reference response for LLM-as-a-judge evaluation. It does not need to be an exact match; it describes the intent so the evaluator model can assess whether the actual response is reasonable.

## Model Choice

All Prompt nodes in this solution use **Amazon Nova Premier** (`us.amazon.nova-premier-v1:0`). This model was chosen because it handles both structured classification (returning a single token) and free-form generation (summarizing KB results, writing polite redirects) well. You can substitute any Bedrock-supported model.
