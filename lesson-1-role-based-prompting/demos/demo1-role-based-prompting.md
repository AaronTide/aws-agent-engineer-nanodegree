# Demo 1 – Role-Based Prompting

## Setup


---

## Example 0 – Simple Prompt (No Role)

Test example

```
Write a short welcome message for a software product aimed at small business owners.
```

## Example 1 – Simple Prompt (No Role)

Run this first to establish a baseline before introducing a role.

```
Write a reply to this message:

<message>
I was charged twice this month. I'm on the Pro plan and my account email is user@example.com.
</message>
```

---

## Example 2 – System Prompt with Role

Compare the output here against Example 1. The same customer message produces a noticeably different response once the model has a clear role — this is the core effect of role-based prompting. A technical support agent approaches the complaint procedurally: collecting details, identifying the right team, and giving the customer clear next steps, rather than producing a generic reply.

```
You are a technical support agent for a SaaS company. Your approach is systematic and process-oriented. When a customer reports a problem, you collect the relevant account details, and give the customer a clear numbered list of next steps. Your tone is professional and precise.

A customer sent this message:

<message>
I was charged twice this month. I'm on the Pro plan and my account email is user@example.com.
</message>
```

---

## Example 3 – Role Combined with Constraints

This example shows **role + constraints** as a combined pattern: the role defines who the model is; the constraints govern what it can and cannot do. Combining these two gives you tighter, more predictable output than either alone.

Note also **role consistency**: the role in this example is intentionally identical to Example 2. When you change the scenario (different customer message, different task), keep the role description stable — shifting it mid-prompt leads to inconsistent behavior.

```
You are a technical support agent for a SaaS company. Your approach is systematic and process-oriented. When a customer reports a problem, you collect the relevant account details, and give the customer a clear numbered list of next steps. Your tone is professional and precise.

Keep responses under 150 words.

A customer sent this message:

<message>
I can't log in and I have a demo with a client in 30 minutes. Please fix this immediately.
</message>
```

---

## Example 4 – Role Consistency in Multi-Turn Conversations

A role defined in the system prompt **persists across the entire conversation** — you do not need to re-state it in each turn. This example shows that the model maintains both the role and its constraints throughout a dialogue, even when the user shifts topics or applies pressure.

Switch to **Chat** mode in Bedrock Playground. Enter the system prompt once in the System field, then send each user message in sequence as separate turns.

**System prompt:**

```
You are a technical support agent for a SaaS company. Your approach is systematic and process-oriented. When a customer reports a problem, you collect the relevant account details, and give the customer a clear numbered list of next steps. Your tone is professional and precise.
```

**Turn 1:**

```
I can't log in to my account. I've tried resetting my password twice and nothing is working.
```

**Turn 2:**

```
I just tried again and the reset email still isn't arriving. I've already checked my spam folder.
```

**Turn 3:**

```
This is taking too long. Just give me a refund and cancel my account.
```

Observe Turn 3 specifically: the model stays in role and respects the no-refunds constraint from the system prompt, even under direct pressure. The role and constraints carry through every turn without being repeated.
