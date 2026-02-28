# Testing and Evaluation

Once your Bedrock Flow is built, you need to verify that it routes messages correctly and produces reasonable responses. This guide walks you through the full testing workflow: writing test prompts, preparing your flow for programmatic invocation, running the test script, and evaluating the results using Bedrock Evaluations.

Bedrock Evaluations can't run a Bedrock Flow application, so instead we would have to invoke Bedrock Flow application, store its responses into a JSON file, and then upload this file to Bedrock Evaluations.

### Automated Testing and Evaluation

This project already includes a script that can run your application on a set of prompts. To use it, you need to:

* Create test prompts
* Run the testing script
* Evaluate the output of your application using Bedrock Evaluations

## 1. Write Test Prompts

Before you can run any automated tests, you need a set of test prompts that cover each branch of your flow. The goal is to have at least one prompt per category so you can verify that the classifier routes messages to the correct path.

### Steps

1. Copy `flow-tests-template.json` to a new file called `flow-tests.json`:

```bash
cp flow-tests-template.json flow-tests.json
```

2. Open `flow-tests.json` and fill in the `flowInputNode.nodeName` field. This must match the name of the Input node in your flow. To find it, open your flow in the Bedrock console and click on the Input node — the name is displayed at the top of the node panel.

<!-- screenshot: Bedrock Flow editor showing the Input node selected with its name visible -->

3. Add prompts you want to test your application on. Each entry has four fields:

| Field | Description |
|-------|-------------|
| `id` | A unique identifier for the test (e.g. `t1_bug_report`). Used in log output to identify which test is running. |
| `category` | The expected classification. This is not used by the flow itself — it is written into the evaluation dataset so you can analyze results by category. |
| `prompt` | The customer message to send to the flow. Write realistic messages that clearly belong to one category. |
| `expected` | A description of what a good response should contain. This becomes the reference response for LLM-as-a-judge evaluation. It does not need to be an exact match — it describes the intent so the evaluator can assess whether the actual response is reasonable. |

## 2. Create a Flow Alias

To invoke your flow programmatically (from the test script or any application), you need a **flow alias**. An alias is a named pointer to a specific version of your flow. When you call the Bedrock API, you provide both the flow ID and an alias ID — not the flow itself. This is because Bedrock Flows supports versioning: you can publish multiple versions of a flow and use aliases to control which version gets invoked. In production, this lets you deploy updates safely by pointing an alias to a new version without changing the calling code.

For this project, we just need one alias that points to the latest version of the flow.

### Steps

1. Open your flow in the Bedrock console.

2. Make sure you have saved and prepared your flow. If you have made changes since the last save, click **Save** first.

<!-- screenshot: Bedrock Flow editor showing Save and Prepare buttons -->

3. Click on **Aliases** in the flow editor, then click **Create alias**.

<!-- screenshot: Aliases tab with Create alias button -->

4. Give your alias a name (e.g. `v1`) and select **Prepare and create a new version and associate it to this alias.**.

5. Click **Create alias**.

6. In the **Aliases** tab copy the **Alias ID** that was generated — you will need it when running the test script.

<!-- screenshot: Aliases table -->

6. You also need the **Flow ID**. You can find it on the flow's overview page or in the URL when viewing the flow in the console.

<!-- screenshot: Flow overview page showing the Flow ID -->

## 3. Set Up the Python Environment

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

## 4. Run the Test Script

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


Trace output shows which nodes were executed and in what order, which is useful for debugging when a message is routed to the wrong branch.

When the script finishes, check the output file:

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

## 5. Run Bedrock Evaluations

Now that you have a JSONL dataset with your flow's responses alongside reference responses, you can use Bedrock Evaluations to assess quality automatically. Bedrock Evaluations supports an **LLM-as-a-judge** method: an evaluator LLM reads each of the flow's response, the reference response, and then scores how well the flow answered.

We use the **Bring Your Own Inference (BYOI)** approach because our responses come from a file we supply. The JSONL file we generated in the previous step is the BYOI dataset — it already contains the flow's responses, so Bedrock Evaluations doesn't need to invoke anything. It only needs to judge the quality.

### Upload the Dataset

You first need to upload the JSONL dataset to the S3 bucket that was created by the CloudFormation stack earlier in this project.

**Find the bucket name.** Run the following command to retrieve it from the stack outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name bug-report-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`EvalDatasetBucketName`].OutputValue' \
  --output text \
  --region us-east-1 \
  --profile bedrock-user
```

Alternatively, open the S3 console and look for a bucket whose name starts with `udacity-agentic-engineer-c1-eval-`.

**Upload the file:**

```bash
aws s3 cp output_eval_dataset.jsonl s3://<your-bucket-name>/output_eval_dataset.jsonl \
  --region us-east-1 \
  --profile bedrock-user
```

Note the full S3 URI (e.g. `s3://udacity-agentic-engineer-c1-eval-123456789012/output_eval_dataset.jsonl`) — you will need it when creating the evaluation job.

### Create the Evaluation Job

Before running this command you need the ARN of the IAM role and the name of the S3 bucket created by the CloudFormation stack. Both are printed as stack outputs when you run `aws cloudformation deploy`. You can also find them in the AWS console: open **CloudFormation** → **Stacks** → **bug-report-stack** → **Outputs** tab. Look for `BedrockEvalRoleArn` and `EvalDatasetBucketName`.

Run the following command to create an LLM-as-a-judge evaluation job using your uploaded dataset:

```bash
aws bedrock create-evaluation-job \
  --job-name flow-eval-run-1 \
  --role-arn <BedrockEvalRoleArn> \
  --evaluation-config '{
    "automated": {
      "datasetMetricConfigs": [{
        "taskType": "General",
        "dataset": {
          "name": "flow-eval-dataset",
          "datasetLocation": {
            "s3Uri": "s3://<EvalDatasetBucketName>/output_eval_dataset.jsonl"
          }
        },
        "metricNames": ["Builtin.Correctness"]
      }],
      "evaluatorModelConfig": {
        "bedrockEvaluatorModels": [{
          "modelIdentifier": "amazon.nova-pro-v1:0"
        }]
      }
    }
  }' \
  --inference-config '{
    "models": [{
      "precomputedInferenceSource": {
        "inferenceSourceIdentifier": "my-flow-app"
      }
    }]
  }' \
  --output-data-config '{"s3Uri": "s3://<EvalDatasetBucketName>/results/"}' \
  --region us-east-1 \
  --profile bedrock-user
```

Replace `<BedrockEvalRoleArn>` and `<EvalDatasetBucketName>` with the values from the CloudFormation stack outputs.

The job may take a few minutes to complete. To check its status:

```bash
aws bedrock list-evaluation-jobs \
  --region us-east-1 \
  --profile bedrock-user \
  --query 'jobSummaries[?jobName==`flow-eval-run-1`].[jobName,status]' \
  --output table
```

To view the results in the console, go to [Amazon Bedrock](https://console.aws.amazon.com/bedrock) → **Evaluations** in the left sidebar → click on your job once it shows status **Completed**.

<!-- screenshot: Evaluation jobs list showing the job completed -->

### Review the Results

1. Once the job completes, click on it to see the results.

2. The results page shows overall scores and per-record breakdowns. The evaluator model scores each response based on how well it matches the intent described in the reference response.

<!-- screenshot: Evaluation results page showing scores -->

3. Look for patterns in the scores:
   - Are all three branches producing reasonable responses?
   - Are any prompts being misrouted (e.g. a bug report getting the "call support" response)?
   - Are FAQ answers relevant, or is the model missing the point of the question?

4. If scores are low for a particular category, go back to your flow and iterate on the prompts. Common fixes include making the classifier prompt more specific, improving the Knowledge Base aggregation prompt, or adding more detail to the agent instructions.

## Next Steps

If you want to expand your test suite, add more test entries to `flow-tests.json` and re-run the script. Edge cases are particularly valuable — try ambiguous messages that could fall into multiple categories, very short messages, or messages in unusual formats. Then re-run the evaluation to see if your changes improved the scores.
