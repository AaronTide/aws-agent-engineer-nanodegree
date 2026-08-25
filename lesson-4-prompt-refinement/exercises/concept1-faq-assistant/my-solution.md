# FAQ Assistant (My Solution)


## Step -1: My Prompt in the Bedrock Console 

  Open Bedrock Console Prompt Management, put in my prompt:


    You are a helpful Product FAQ Assistant for a SaaS Team.
     A Product FAQ is given to you that covers many frequently asked questions. 
    You help customers get accurate answers from the Product FAQ. Always be polite and respectful. 

    The customer’s question is: {{customer_question}}

    The FAQ is {{faq}}

    Your answers should be concise (within 1-3 lines) and to-the-point. 
    Your answers must ALWAYS be grounded in the product FAQ, do not try to invent any answer by yourself. 

    If the question asked is not covered in the FAQ, apologise and let the user know that you cannot answer this questions as the answer is not available in the FAQ.


## Step-2: My Demo Questions 

 Open faq_assistant.py and fill in EVAL_QUESTIONS with my demo questions. 

 I've added 6 entries with 4 answerable questions from the FAQ and 2 no answerable from the FAQ:

    {
    "prompt": "What are your pricing tiers",
    "referenceResponse": "Individual plan is $29 per month, team plan is $99 per month for upto 10 users, for enterprise plans, please contact our sales team for custom pricing
    ",
    }


    {
    "prompt": "Can I use it for free",
    "referenceResponse": "Yes, we offer a 14-day free trial for all plans, no credit card required",
    }


    {
    "prompt": "What is your products annual revenue?",
    "referenceResponse": "Sorry, I cannot answer this question as this is not provided in the FAQ",
    }

    
    {
    "prompt": "Can I get a special student discount?",
    "referenceResponse": "Sorry, I cannot answer this question as this is not provided in the FAQ",
    }

    
    {
    "prompt": "I am facing bugs in the product. Who can I contact?",
    "referenceResponse": "Sorry for the bugs. We provide email support for all plans and live chat support for Team and Enterprise plans",
    }

  
    {
    "prompt": "Will this product integrate with my team’s tools?",
    "referenceResponse": "Our product support integrations with Google Workspace and Slack. Other platforms are not currently supported.",
    }


  
## Step 3 – Configure and Run the Script

Fill in this constant at the top of `faq_assistant.py`:

```python
PROMPT_VERSION_ARN = "<paste your prompt version ARN>"
```

Then run:

```bash
python faq_assistant.py
```

The script will call the assistant for each question and write results to `eval_responses.jsonl`.

## Assistant's responses in terminal:

```bash
  Running FAQ Assistant Eval

============================================================
Question:  What are your pricing tiers
Expected:  Individual plan is $29 per month, team plan is $99 per month for upto 10 users, for enterprise plans, please contact our sales team for custom pricing
Response:  Here are our pricing tiers: Individual plan (29/month),Teamplan(99/month for up to 10 users), and Enterprise (contact sales for custom pricing).
------------------------------------------------------------
Question:  Can I use it for free
Expected:  Yes, we offer a 14-day free trial for all plans, no credit card required
Response:  You can try all plans for free with a 14-day free trial, no credit card required.
------------------------------------------------------------
Question:  What is your products annual revenue?
Expected:  Sorry, I cannot answer this question as this is not provided in the FAQ
Response:  I'm sorry, but the annual revenue of our product is not disclosed in the provided FAQ. If you have any other questions about our pricing, features, or support, feel free to ask!
------------------------------------------------------------
Question:  Can I get a special student discount?
Expected:  Sorry, I cannot answer this question as this is not provided in the FAQ
Response:  I'm sorry, but the FAQ does not mention any special student discounts.
------------------------------------------------------------
Question:  I am facing bugs in the product. Who can I contact?
Expected:  Sorry for the bugs. We provide email support for all plans and live chat support for Team and Enterprise plans
Response:  For bug-related issues, please contact email support for all plans or live chat support for Team and Enterprise plans.
------------------------------------------------------------
Question:  Will this product integrate with my team’s tools?
Expected:  Our product support integrations with Google Workspace and Slack. Other platforms are not currently supported.
Response:  Currently, the product integrates only with Slack and Google Workspace. If you need integration with other tools, please contact our sales team for more information.
------------------------------------------------------------

Wrote 6 records to eval_responses.jsonl

```


## Step 4 – Upload Results to S3

Deploy the provided CloudFormation template to create an S3 bucket with a unique name:

```bash
aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name faq-assistant-eval \
  --region us-east-1
```

Then retrieve the bucket name and upload the results:

```bash
BUCKET=$(aws cloudformation describe-stacks --stack-name faq-assistant-eval \
  --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
  --region us-east-1 \
  --output text)

aws s3 cp eval_responses.jsonl s3://$BUCKET/eval_responses.jsonl
```

## Step 5 – Run a Bedrock Model Evaluation Job

1. Open **Amazon Bedrock console** → **Evaluations** → **Create** → **Automatic: LLM as a judge**
2. Select **Amazon Nova Pro** as an evaluator model
3. In **Inference source** select **Bring your own inference responses**. Set **Source name** to `faq-assistant`
4. In **Metrics** select **Correctness**, unselect all other metrics
5. In **Datasets**  → **Prompt dataset**, point to the file you uploaded:

   ```
   s3://<your-bucket-name>/eval_responses.jsonl
   ```
   
6. Set an S3 output location to any folder in the same S3 bucket, e.g. `s3://<your-bucket-name>/lesson-4/results/`


## My Evaluation Results:





   


