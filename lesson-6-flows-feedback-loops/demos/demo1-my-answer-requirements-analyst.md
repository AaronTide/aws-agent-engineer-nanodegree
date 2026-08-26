# Requirements Analyst Agent 

## Overview

This demo builds a requirements analyst that refuses to write a spec until it has all the facts. When a user submits a vague tool request, the analyst asks focused follow-up questions — one at a time — and only produces the final specification once every category on its checklist is covered.
 
Has:

1. **A prompt** — role + goal, a required-fields checklist, and a one-question-at-a-time strategy
2. **A session** — the harness is stateful by default; reusing the same `runtimeSessionId` continues the conversation


---

## The Core Architecture:

```
You (chat.py) ──── invoke_harness ────▶  AgentCore managed harness
      ▲                                     "requirements_analyst"
      │                                      (Amazon Nova Pro)
      └───────── streamed reply ─────────────────┘

        same runtimeSessionId every turn  =  one continuous conversation
```



## Setup

1) Agent Harness requires the latest version of boto3:
      
        pip install -U boto3 botocore
      
2) Configure AWS credentials for us-east-1:

        aws configure 
        

        aws configure set aws_sesion_token "your token"

3) In this folder, run:

        python setup_demo.py


    `setup_demo.py` creates an IAM execution role and the harness (pinned to Amazon Nova Pro, with the harness's long-term memory disabled so every new session starts clean 
    — state lives only in the session id), waits until the harness is `READY` (~2–3 minutes), and writes `harness_arn.txt` for the chat script.


4) Start the chat with:

        python chat.py


## My Conversation With The Agent:

```
You: I want a workflow automation that deals with speed to lead

Agent: What is the purpose of the workflow automation for speed to lead?

You: I want to reply to interested inbound leads fast - whether they be contacting me through my website form or by email. Also, I need the replies to be fully personalised according to my brand voice and my FAQs                   

Agent: What are the specific capabilities required for the workflow automation to handle emails and personalize replies according to your brand voice and FAQs?

You: It should be able to receive lead enquiries from a website form and/or email, give a welcoming reply back that addresses the lead's question,update my CRM and inform my team of the lead enquiry.                                                                                                                                                                                                                                                                                   

Agent: How will the team know that the workflow automation is working correctly?

You: There should be error nodes to notify the team if something goes wrong, also, the lead's website form submissions and emails are stored on the company workspace so we can check if we were not notified of a lead

Agent: REQUIREMENTS COMPLETE
- Purpose: Handle emails and personalize replies according to the user's brand voice and FAQs, receive inputs from a website form and/or email, give a welcoming reply back that addresses the lead's question, update the CRM, and notify the team about the inbound lead.
- Key features: Receive inputs from a website form and/or email, give a welcoming reply back that addresses the lead's question, update the CRM, notify the team about the inbound lead, and include error nodes to notify the team if something goes wrong.
- Success criteria: The workflow automation is working correctly if there are error nodes to notify the team if something goes wrong, and the lead's website form submissions and emails are stored on the company workspace so the team can check if they were not notified of a lead.

```

  

      
      
