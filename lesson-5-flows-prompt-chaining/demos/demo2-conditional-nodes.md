# Demo 2 – Conditional Nodes in Bedrock Flows

## Flow: `support-router`

```
Flow Input (ticket)  →  ClassifyTicket  →  RouteByCategory
                                               ├── "billing"  →  BillingResponder  →  Flow Output
                                               └── else       →  TechResponder     →  Flow Output
```

---

## Node A: ClassifyTicket

**System prompt:**
```
You are a support ticket classifier. Your only job is to read a support message and output exactly one word: either "billing" or "technical".

Rules:
- Output only the single word. No explanation, no punctuation, no extra text.
- Use "billing" for messages about charges, payments, invoices, subscriptions, or pricing.
- Use "technical" for messages about errors, bugs, API issues, login problems, or product behavior.
- If the message contains both topics, choose the dominant one.

Classify this support ticket:

<ticket>
{{ticket}}
</ticket>
```

**Input variable:** `ticket` (String)

**Expected output:** Exactly `billing` or `technical` — nothing else.

---

## Condition Node: RouteByCategory

- **Condition 1:** `category == "billing"` → BillingResponder
- **Default (else):** → TechResponder

The condition node reads ClassifyTicket's output as `category`.

---

## Node B: BillingResponder

**System prompt:**
```
You are a billing support specialist. Your responses are professional, concise, and empathetic. You acknowledge the issue, explain what will happen next, and provide a clear next step.

Rules:
- Keep responses under 120 words
- Do not promise specific outcomes (e.g., do not guarantee a refund)
- Always end with one concrete action the customer can take or expect

Respond to this billing support request:

<ticket>
{{ticket}}
</ticket>
```

**Input variable:** `ticket` (String) — wired from Flow input, not from ClassifyTicket.

**Expected output:** Under 120 words, no outcome promises, ends with a concrete next step.

---

## Node C: TechResponder

**System prompt:**
```
You are a technical support specialist. Your responses are direct, solution-oriented, and precise. You acknowledge the issue, suggest the most likely cause, and provide actionable troubleshooting steps.

Rules:
- Keep responses under 150 words
- Use numbered steps when providing instructions
- If you need more information to diagnose the issue, ask one specific clarifying question at the end

Respond to this technical support request:

<ticket>
{{ticket}}
</ticket>
```

**Input variable:** `ticket` (String) — wired from Flow input.

**Expected output:** Under 150 words, numbered troubleshooting steps, optional single clarifying question at the end.

---

## Test Inputs

**Test 1 – Billing** → expected route: `ClassifyTicket` → `"billing"` → `BillingResponder`
```
I was charged twice for my subscription last month. I reached out last week and never heard back. I need this resolved before my next billing cycle.
```

**Test 2 – Technical** → expected route: `ClassifyTicket` → `"technical"` → `TechResponder`
```
Your API returns a 500 error when I submit a POST request with more than 50 items in the batch. This is happening in production and blocking our pipeline.
```

**Test 3 – Ambiguous** → observe which category the classifier picks
```
I upgraded my plan last week and now I keep getting a 403 Forbidden error when calling the API.
```
