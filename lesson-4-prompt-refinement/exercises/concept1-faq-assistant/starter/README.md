# Exercise – NovaPlan FAQ Assistant Eval

## Overview

You will build an evaluation pipeline for a Product FAQ Assistant. The assistant helps
customers get accurate answers from a pre-launch FAQ — and should refuse to answer questions
that are not covered or that try to manipulate it.

**Scenario:** NovaPlan, a project management SaaS tool, is preparing for launch. The team
needs to verify that the FAQ assistant answers correctly, stays grounded in the FAQ, and
handles unsafe inputs gracefully before rollout.

---

## What You'll Do

1. Define the assistant's prompt as a Bedrock Prompt Management template
2. Create a guardrail to handle unsafe or manipulative inputs
3. Fill in an eval dataset (question → expected answer) in the script
4. Create an S3 bucket to store the results
5. Run the evaluation script and review the results

---

## Step 1 – Create the Prompt Template in the Bedrock Console

1. Open the **Amazon Bedrock console** → **Prompt Management** → **Create prompt**
2. Select the model: **Claude 3 Haiku**
3. Write a prompt template that:
   - Identifies the assistant as a product assistant for NovaPlan
   - Instructs it to answer **only from the FAQ provided**
   - Instructs it to say when an answer is not available in the FAQ
   - Uses exactly two template variables: `{{faq}}` and `{{customer_question}}`
4. Save the prompt and publish **version 1**
5. Copy the **Prompt version ARN** — you will need it in the script

---

## Step 2 – Create a Guardrail in the Bedrock Console

1. Open **Amazon Bedrock console** → **Guardrails** → **Create guardrail**
2. Add a **Denied Topic** that blocks requests trying to get unauthorized discounts or free subscriptions
3. Enable the **Prompt attacks** content filter at **High** strength
4. Save the guardrail
5. Copy the **Guardrail ID** and note the version (default: `1`)

---

## Step 3 – Fill In the Eval Dataset

Open `faq_assistant.py` and fill in `EVAL_QUESTIONS`. Add at least 7 entries covering:

- **Answerable questions** – questions with clear answers in the FAQ
- **Unanswerable questions** – questions not covered by the FAQ
- **An unsafe input** – a prompt injection or manipulation attempt

Each entry uses this format:

```python
{
    "prompt": "Your question here",
    "referenceResponse": "The ideal answer you expect",
}
```

---

## Step 4 – Create an S3 Bucket

The script uploads the eval results to S3 after writing them locally. Create a bucket to receive the file:

```bash
aws s3 mb s3://<your-bucket-name>
```

Choose a globally unique bucket name, for example `novaplan-eval-<your-name>`.

---

## Step 5 – Configure and Run the Script

Fill in these constants at the top of `faq_assistant.py`:

```python
PROMPT_VERSION_ARN = "<paste your prompt version ARN>"
GUARDRAIL_ID       = "<paste your guardrail ID>"
S3_BUCKET          = "<paste your bucket name>"
```

Then run:

```bash
python faq_assistant.py
```

The script will call the assistant for each question, write results to `eval_responses.jsonl`, and upload the file to your S3 bucket.

---

## Expected Output

```
Running NovaPlan FAQ Assistant Eval
============================================================
Question:  What is the price of the team plan?
Expected:  The team plan is $99 per month for up to 10 users.
Response:  The team plan is priced at $99 per month and supports up to 10 users.
------------------------------------------------------------
...
Wrote 7 records to eval_responses.jsonl
Uploaded eval_responses.jsonl to s3://novaplan-eval-yourname/eval_responses.jsonl
```
