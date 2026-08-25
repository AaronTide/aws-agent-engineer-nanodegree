# Set up 

We will set up a new evaluation on AWS console with automatic LLM-as-a-judge, but before that: 

1) Go to aws bedrock console
   
2)   Make sure to add this as your prompt in AWS console prompt management

         You are a customer support agent for ShopFast, an e-commerce retailer.
          Draft a professional reply to the customer email below.

         Structure your reply as:
          1. Apology – acknowledge the specific issue sincerely
          2. Resolution – explain exactly what will happen next
          3. Follow-up – one concrete next step with a timeframe

          Company policy:{{policy}}

         Brand voice: {{brand_voice}}

          Customer email:
          {{customer_email}}

          Write only the reply body. Do not include a subject line.

3) Make sure your generate_responses.py file has your prompt ARN:

       PROMPT_VERSION_ARN = "<VERSION_ARN>"

4) Set up an S3 bucket on aws console to store your evaluations; add your bucket name to generate_responses.py:

       S3_BUCKET   = "<YOUR_S3_BUCKET_NAME>"

5) Configure aws credentials on terminal
   
         aws configure
         aws configure set aws_session_token "your token"

6) Run the script to create the responses and store on s3 bucket as JSONL file:

         python generate_responses.py
   

7) Set up a new evaluation on aws bedrock console with the s3 bucket name. Inference source is shopfast_email_agent

    Should take a few minutes to get the evaluations.

    
 ## My Results:  
 
<img width="1366" height="768" alt="Screenshot (415)" src="https://github.com/user-attachments/assets/02cd45b7-5113-4313-aec0-6e4963b30a85" />
