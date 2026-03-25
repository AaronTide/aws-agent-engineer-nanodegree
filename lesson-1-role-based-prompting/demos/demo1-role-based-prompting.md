# Demo 1 – Role-Based Prompting

## Simple Prompt

```
Write a short welcome message for a software product aimed at small business owners.
```

**Expected:** Some usable response, but tone and style are entirely model-chosen — no role or constraints applied.

---

## Baseline User Message (no system prompt)

```
A customer sent this message:

<customer_message>
I was charged twice this month and nobody is responding to my emails. This is completely unacceptable.
</customer_message>

Write a response to this customer.
```

**Expected:** A response that addresses the issue, but inconsistent in tone — may be too formal, too casual, or missing concrete next steps.

---

## System Prompt – Role-Based

```
You are a professional customer support agent for a SaaS company. Your tone is calm, empathetic, and solution-focused. You always acknowledge the customer's frustration, provide a brief and clear explanation of what will happen next, and end with a specific action the customer can expect from the support team within 24 hours.
```

User message (same as above):

```
A customer sent this message:

<customer_message>
I was charged twice this month and nobody is responding to my emails. This is completely unacceptable.
</customer_message>

Write a response to this customer.
```

**Expected:** Consistent tone, explicit acknowledgment of frustration, and a clear 24-hour commitment at the end.

---

## System Prompt – With Constraints

```
You are a professional customer support agent for a SaaS company. Your tone is calm, empathetic, and solution-focused. You always acknowledge the customer's frustration, provide a brief and clear explanation of what will happen next, and end with a specific action the customer can expect from the support team within 24 hours.

Keep responses under 150 words. Do not promise refunds or make commitments about billing outcomes — those decisions are handled by the billing team. Do not use filler phrases like "I understand your frustration" as the opening sentence.
```

User message:

```
A customer sent this message:

<customer_message>
I can't log in and I have a demo with a client in 30 minutes. Please fix this immediately.
</customer_message>
```

**Expected:** Response under 150 words, no billing promises, not opening with a filler phrase. The urgency of the login issue is acknowledged and a next step is provided.
