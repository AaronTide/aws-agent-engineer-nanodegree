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
