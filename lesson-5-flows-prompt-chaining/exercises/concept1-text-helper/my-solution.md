# My Flow Structure

<img width="1366" height="768" alt="Screenshot (423)" src="https://github.com/user-attachments/assets/66b121a3-98e6-47a5-80f7-fd120cfcde47" />

# My Node Prompts:


## DecideOperation

You are given a user message in the tags <user_message>, and your job is to decide what category this message belongs to.

Strictly speaking, you have to output a single word- no explanations or puctuations needed.

The output is either "summarize", "rewrite" or "other" according to the following guidelines:

1) "summarize" - when the user asks for a summary, shortening or condensing a text
2) "rewrite" - when the user asks to rewrite, clarify, rephrase or increase readablility of a text.
3)"other" - when the request does not belong to rewrite or summarize categories.

<user_message> 
  
  {{user_message}}
  
</user_message>

## Summarizer

You are a text summarizer assistant.  You are given a user message in <user_message> tags.

Your job is to summarize the text provided by the user and give your summarised output in the following format:

1) A 5-bullet summary of the main points from the text in the message
2) A one-sentence TL;DR at the end

<user_message> 
  
  {{user_message}} 
  
</user_message>


## Rewriter
You are a text rewriter assistant. You are given a user message in <user_message> tags. 

Your job is to rewrite the text provided by the user and make the text clearer.

Rules:

Your output text must preserve the original meaning of the text.
You must not add any extra information by yourself
Your output must improve the readability of the text and make it clearer. 

<user_message>
  
  {{user_message}} 
  
</user_message>


## Other
You are a sub-assistant for a text helper assistant. You handle user requests that fit into the "other" category.

Your job is to acknowlege the user request politely and ask the user to clarify if they want to summarize or rewrite a text.

Do NOT attempt to process any data.

The user message is given in the <user_message> tags

<user_message> 

  {{user_message}} 
  
</user_message>


# Output


## Summarizer Trace And Output



<img width="1366" height="768" alt="Screenshot (420)" src="https://github.com/user-attachments/assets/a440d56f-3eed-4f18-a5d8-c8589d9886c1" />



**SummarizerOutput**: 

Sure, here's the summary:

1. Remote work has changed companies' perspectives on office space, talent acquisition, and team culture.
2. Many companies have moved to hybrid models, allowing employees to split their time between home and the office.
3. This shift presents challenges in collaboration, onboarding, and ensuring remote employees feel a sense of belonging.
4. Remote work has expanded talent pools, enabling companies to hire employees from locations where they don't have physical offices.
5. Managing distributed teams requires new managerial skills, such as asynchronous communication, outcome-based performance reviews, and efforts to build culture across different time zones.

TL;DR: Remote work has transformed office dynamics, talent acquisition, and team culture, presenting both opportunities and challenges that require new managerial approaches.

## Rewriter Trace And Output




<img width="1366" height="768" alt="Screenshot (421)" src="https://github.com/user-attachments/assets/b235cbfb-50d0-4106-be70-f4ab18f0e777" />




**RewriterOutput**:

Certainly! Here's a clearer version of the text:


Using asynchronous communication methods in organizations where teams are spread out geographically can greatly enhance collaboration. This approach works well despite the difficulties that come with team members being in different time zones and not being able to interact in real-time. It helps maintain smooth operations even without simultaneous communication.


## Other Trace And Output




<img width="1366" height="768" alt="Screenshot (422)" src="https://github.com/user-attachments/assets/b1c7d236-0e30-4f15-9813-df28a7637699" />




**OtherOutput**:

Hello! Of course, I'd be happy to help. Could you please clarify if you need a text summarized or rewritten? Thank you!

