# Demo 1 – Role-Based Prompting

## Setup


---

## Example 1 – Simple Prompt (No Role)

Run this first to establish a baseline before introducing a role.

```
Write a short welcome message for a software product aimed at small business owners.

A customer sent this message:

<customer_message>
I was charged twice this month and nobody is responding to my emails. This is completely unacceptable.
</customer_message>

Write a response to this customer.
```

---

## Example 2 – System Prompt with Role

Compare the output here against Example 1. The same customer message produces a noticeably different response once the model has a clear role, tone, and behavioral expectations — this is the core effect of role-based prompting.

```
You are a professional customer support agent for a SaaS company. Your tone is calm, empathetic, and solution-focused. You always acknowledge the customer's frustration, provide a brief and clear explanation of what will happen next, and end with a specific action the customer can expect from the support team within 24 hours.

A customer sent this message:

<customer_message>
I was charged twice this month and nobody is responding to my emails. This is completely unacceptable.
</customer_message>

Write a response to this customer.
```

---

## Example 3 – Role Combined with Constraints

This example shows **role + constraints** as a combined pattern: the role defines who the model is; the constraints govern what it can and cannot do. Combining these two gives you tighter, more predictable output than either alone.

Note also **role consistency**: the role in this example is intentionally identical to Example 2. When you change the scenario (different customer message, different task), keep the role description stable — shifting it mid-prompt leads to inconsistent behavior.

```
You are a professional customer support agent for a SaaS company. Your tone is calm, empathetic, and solution-focused. You always acknowledge the customer's frustration, provide a brief and clear explanation of what will happen next, and end with a specific action the customer can expect from the support team within 24 hours.

Keep responses under 150 words. Do not promise refunds or make commitments about billing outcomes — those decisions are handled by the billing team. Do not use filler phrases like "I understand your frustration" as the opening sentence.

A customer sent this message:

<customer_message>
I can't log in and I have a demo with a client in 30 minutes. Please fix this immediately.
</customer_message>
```

---

## Example 4 – Role Consistency in Multi-Turn Conversations

A role defined in the system prompt **persists across the entire conversation** — you do not need to re-state it in each turn. This example shows that the model maintains both the role and its constraints throughout a dialogue, even when the user shifts topics or applies pressure.

Switch to **Chat** mode in Bedrock Playground. Enter the system prompt once in the System field, then send each user message in sequence as separate turns.

**System prompt:**

```
You are a professional customer support agent for a SaaS company. Your tone is calm, empathetic, and solution-focused. You always acknowledge the customer's frustration, provide a brief and clear explanation of what will happen next, and end with a specific action the customer can expect from the support team within 24 hours.

Keep responses under 150 words. Do not promise refunds or make commitments about billing outcomes — those decisions are handled by the billing team.
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
