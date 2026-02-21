# Testing and Evaluation

Once your Bedrock Flow is built, you need to verify that it routes messages correctly and produces reasonable responses. This guide walks you through the full testing workflow: writing test prompts, preparing your flow for programmatic invocation, running the test script, and evaluating the results using Bedrock Evaluations.

## 1. Write Test Prompts

Before you can run any automated tests, you need a set of test prompts that cover each branch of your flow. The goal is to have at least one prompt per category so you can verify that the classifier routes messages to the correct path.

### Steps

1. Copy `flow-tests-template.json` to a new file called `flow-tests.json`:

```bash
cp flow-tests-template.json flow-tests.json
```

2. Open `flow-tests.json` and fill in the `flowInputNode.nodeName` field. This must match the name of the Input node in your flow. To find it, open your flow in the Bedrock console and click on the Input node — the name is displayed at the top of the node panel.

<!-- screenshot: Bedrock Flow editor showing the Input node selected with its name visible -->

3. Add at least one test entry per branch. Each entry has four fields:

| Field | Description |
|-------|-------------|
| `id` | A unique identifier for the test (e.g. `t1_bug_report`). Used in log output to identify which test is running. |
| `category` | The expected classification. This is not used by the flow itself — it is written into the evaluation dataset so you can analyze results by category. |
| `prompt` | The customer message to send to the flow. Write realistic messages that clearly belong to one category. |
| `expected` | A description of what a good response should contain. This becomes the reference response for LLM-as-a-judge evaluation. It does not need to be an exact match — it describes the intent so the evaluator can assess whether the actual response is reasonable. |

Here is an example of a complete test file:

```json
{
  "flowInputNode": {
    "nodeName": "FlowInputNode"
  },
  "tests": [
    {
      "id": "t1_bug_report",
      "category": "BUG_REPORT",
      "prompt": "Your app crashes every time I try to upload a file larger than 10MB on Firefox",
      "expected": "Acknowledges the issue and asks for steps to reproduce or additional details"
    },
    {
      "id": "t2_product_question",
      "category": "PRODUCT_QUESTION",
      "prompt": "What are the pillars of the Well-Architected Framework?",
      "expected": "Lists and describes the pillars of the AWS Well-Architected Framework"
    },
    {
      "id": "t3_other",
      "category": "OTHER",
      "prompt": "I need to update the credit card on file for my account",
      "expected": "Politely explains this cannot be handled automatically and suggests calling the support phone number"
    }
  ]
}
```

## 2. Test Manually in the Console

Before running the full automated test suite, try your flow in the Bedrock console to make sure it works. This is faster than running the script and gives you immediate visual feedback on which path each message takes.

### Steps

1. Open your flow in the Bedrock console.

2. Click **Run** (or use the test panel) and enter a customer message.

<!-- screenshot: Bedrock Flow console test panel with a message entered -->

3. Check that the message is routed to the correct branch. Try one message per category:

- A message describing a software problem (should go to the bug report path).
- A question about the Well-Architected Framework (should go to the Knowledge Base path).
- A request that doesn't fit either category, like a billing change (should go to the default path).

4. Verify the responses make sense: the bug report path should ask for details or confirm a ticket was created, the Knowledge Base path should return information from the PDF, and the default path should suggest calling the support number.

## 3. Create a Flow Alias

To invoke your flow programmatically (from the test script or any application), you need a **flow alias**. An alias is a named pointer to a specific version of your flow. When you call the Bedrock API, you provide both the flow ID and an alias ID — not the flow itself. This is because Bedrock Flows supports versioning: you can publish multiple versions of a flow and use aliases to control which version gets invoked. In production, this lets you deploy updates safely by pointing an alias to a new version without changing the calling code.

For this project, we just need one alias that points to the latest version of the flow.

### Steps

1. Open your flow in the Bedrock console.

2. Make sure you have saved and prepared your flow. If you have made changes since the last save, click **Save** and then **Prepare** to create a new version.

<!-- screenshot: Bedrock Flow editor showing Save and Prepare buttons -->

3. Click on **Aliases** in the flow editor, then click **Create alias**.

<!-- screenshot: Aliases tab with Create alias button -->

4. Give your alias a name (e.g. `latest`) and select the version you want it to point to. Select the most recently prepared version.

5. Click **Create**. Note the **Alias ID** that is generated — you will need it when running the test script.

<!-- screenshot: Alias details page showing the Alias ID -->

6. You also need the **Flow ID**. You can find it on the flow's overview page or in the URL when viewing the flow in the console.

<!-- screenshot: Flow overview page showing the Flow ID -->

## 4. Set Up the Python Environment

The test script (`generate-eval-dataset.py`) uses `boto3` to call the Bedrock API. Before running it, set up a Python virtual environment and install the dependencies.

A virtual environment keeps the project's dependencies isolated from your system Python, so you don't accidentally break other projects or tools on your machine.

### Steps

1. Open a terminal and navigate to the project directory.

2. Create a virtual environment:

```bash
python3 -m venv .venv
```

3. Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

4. Install the dependencies:

```bash
pip install -r requirements.txt
```

5. Verify that `boto3` is installed:

```bash
python -c "import boto3; print(boto3.__version__)"
```

This should print a version number without any errors.

6. Make sure your AWS credentials are configured. The script uses your default AWS credentials (from `~/.aws/credentials` or environment variables). If you have multiple profiles, you can set the `AWS_PROFILE` environment variable:

```bash
export AWS_PROFILE=your-profile-name
```

## 5. Run the Test Script

The `generate-eval-dataset.py` script reads your test prompts, invokes the flow once per prompt, and writes the results to a JSONL file. Each line in the output file contains the original prompt, the flow's actual response, and your reference response — everything that Bedrock Evaluations needs to run an LLM-as-a-judge assessment.

### Steps

1. Run the script with your flow ID and alias ID:

```bash
python generate-eval-dataset.py \
  --tests-json flow-tests.json \
  --flow-id <your-flow-id> \
  --flow-alias-id <your-flow-alias-id>
```

Replace `<your-flow-id>` and `<your-flow-alias-id>` with the values you noted in section 3.

2. The script prints progress to the terminal as it runs. For each test, you will see the raw events from the flow and a summary line:

```
t1_bug_report: wrote eval line (category=BUG_REPORT)
t2_product_question: wrote eval line (category=PRODUCT_QUESTION)
t3_other: wrote eval line (category=OTHER)

Wrote 3 JSONL lines to output_eval_dataset.jsonl (3 flow calls succeeded).
```

3. If you want more detail about how the flow processed each message, add the `--enable-trace` flag:

```bash
python generate-eval-dataset.py \
  --tests-json flow-tests.json \
  --flow-id <your-flow-id> \
  --flow-alias-id <your-flow-alias-id> \
  --enable-trace
```

Trace output shows which nodes were executed and in what order, which is useful for debugging when a message is routed to the wrong branch.

4. When the script finishes, check the output file:

```bash
cat output_eval_dataset.jsonl
```

Each line is a JSON object with this structure:

```json
{
  "prompt": "Your app crashes every time I try to upload a file...",
  "referenceResponse": "Acknowledges the issue and asks for steps to reproduce...",
  "category": "BUG_REPORT",
  "modelResponses": [
    {
      "response": "I'm sorry to hear about the crash. Could you tell me...",
      "modelIdentifier": "my-flow-app"
    }
  ]
}
```

If any flow call failed, the `response` field will contain an error message prefixed with `[FLOW_ERROR]`. Check the terminal output for details on what went wrong.

## 6. Run Bedrock Evaluations

Now that you have a JSONL dataset with your flow's responses alongside reference responses, you can use Bedrock Evaluations to assess quality automatically. Bedrock Evaluations supports an **LLM-as-a-judge** method: an evaluator model reads each prompt, the flow's response, and the reference response, then scores how well the flow answered.

We use the **Bring Your Own Inference (BYOI)** approach because our responses come from a Bedrock Flow, not from a single model invocation. The JSONL file we generated in the previous step is the BYOI dataset — it already contains the flow's responses, so Bedrock Evaluations doesn't need to invoke anything. It only needs to judge the quality.

### Create an S3 Bucket for the Evaluation

Bedrock Evaluations reads input datasets from S3 and writes results to S3. You need an S3 bucket (or a prefix in an existing bucket) for this.

1. Open the **S3** console and click **Create bucket**.

<!-- screenshot: S3 console → Create bucket button -->

2. Give the bucket a name (e.g. `my-flow-eval-data`). S3 bucket names must be globally unique, so you may need to add your account ID or a random suffix.

3. Select the same AWS region where your Bedrock Flow is deployed.

4. Leave the other settings at their defaults and click **Create bucket**.

<!-- screenshot: S3 bucket creation form -->

### Upload the Dataset

1. Open the bucket you just created.

2. Click **Upload** and select the `output_eval_dataset.jsonl` file from your project directory.

<!-- screenshot: S3 upload page with the JSONL file selected -->

3. Click **Upload**. Note the S3 URI of the uploaded file (e.g. `s3://my-flow-eval-data/output_eval_dataset.jsonl`) — you will need it when creating the evaluation job.

<!-- screenshot: S3 showing the uploaded file with its URI -->

### Create the Evaluation Job

1. In the Bedrock console, navigate to **Evaluations** in the left sidebar.

<!-- screenshot: Bedrock console sidebar showing Evaluations -->

2. Click **Create evaluation job**.

3. Give the job a name (e.g. `flow-eval-run-1`).

4. Under evaluation type, select **LLM-as-a-judge**.

5. Select the evaluator model. This is the model that will judge the quality of your flow's responses. Choose a capable model (e.g. Claude or Amazon Nova).

<!-- screenshot: Evaluation job creation form with LLM-as-a-judge selected -->

6. Under **Inference source**, select **Bring your own inference (BYOI)**.

7. For the input dataset, provide the S3 URI of the JSONL file you uploaded (e.g. `s3://my-flow-eval-data/output_eval_dataset.jsonl`).

8. For the output location, provide an S3 path where Bedrock should write the evaluation results (e.g. `s3://my-flow-eval-data/results/`).

<!-- screenshot: Evaluation job form with BYOI selected and S3 paths filled in -->

9. Click **Create** to start the evaluation job. The job may take a few minutes to complete depending on the size of your dataset.

<!-- screenshot: Evaluation jobs list showing the job in progress -->

### Review the Results

1. Once the job completes, click on it to see the results.

2. The results page shows overall scores and per-record breakdowns. The evaluator model scores each response based on how well it matches the intent described in the reference response.

<!-- screenshot: Evaluation results page showing scores -->

3. Look for patterns in the scores:
   - Are all three branches producing reasonable responses?
   - Are any prompts being misrouted (e.g. a bug report getting the "call support" response)?
   - Are Knowledge Base answers relevant, or is the KB returning unrelated passages?

4. If scores are low for a particular category, go back to your flow and iterate on the prompts. Common fixes include making the classifier prompt more specific, improving the Knowledge Base aggregation prompt, or adding more detail to the agent instructions.

## Next Steps

If you want to expand your test suite, add more test entries to `flow-tests.json` and re-run the script. Edge cases are particularly valuable — try ambiguous messages that could fall into multiple categories, very short messages, or messages in unusual formats. Then re-run the evaluation to see if your changes improved the scores.
