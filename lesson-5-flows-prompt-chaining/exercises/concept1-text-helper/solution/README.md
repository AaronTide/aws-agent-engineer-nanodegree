# Exercise Solution – Text Helper Flow

## Flow Structure

```
Flow Input (user_message)
    │
    ▼
[DecideOperation]  →  "summarize" or "rewrite"
    │
    ▼
[RouteByOperation]
    ├── operation == "summarize"  →  [Summarizer]
    └── else                      →  [Rewriter]
                                          │
                                          ▼
                                     Flow Output
```

---

## Node 1: DecideOperation

**Prompt template:**
```
You are an operation classifier for a text editing tool. Your only job is to read the user's message and decide which operation they want: summarize or rewrite.

Output exactly one word: either "summarize" or "rewrite". No explanation, no punctuation, no extra text.

Use "summarize" for requests about condensing, shortening, giving the main points, or producing a summary.
Use "rewrite" for requests about improving clarity, readability, simplifying language, or rephrasing.
If the request is ambiguous or unclear, output "rewrite".

User message:
{{user_message}}

Which operation should be applied: summarize or rewrite?
```

**Input variable:** `user_message` (String)

---

## Condition Node: RouteByOperation

- **Condition 1:** `operation == "summarize"` → Summarizer
- **Default (else):** → Rewriter

Wire: `DecideOperation` model output → condition input `operation`

---

## Node 2A: Summarizer

**Prompt template:**
```
You are a precise summarization assistant. The user's message contains their request followed by the text they want summarized. Extract the text and produce two things:

1. A 5-bullet summary — each bullet captures one distinct main point from the text. Keep each bullet under 20 words.
2. A TL;DR — one sentence (under 25 words) that captures the single most important takeaway.

Format your output exactly like this:
**Summary:**
- [bullet 1]
- [bullet 2]
- [bullet 3]
- [bullet 4]
- [bullet 5]

**TL;DR:** [one sentence]

Do not add bullets about topics not present in the text. Do not editorialize.

User message:
{{user_message}}
```

**Input variable:** `user_message` (String)

---

## Node 2B: Rewriter

**Prompt template:**
```
You are a clarity editor. The user's message contains their request followed by the text they want rewritten. Extract the text and rewrite it to be easier to read while preserving the original meaning exactly.

Rules:
- Do not add information that is not in the original
- Do not remove any meaningful content
- Use shorter sentences where possible
- Replace jargon or overly complex phrasing with plain language
- Keep the same general structure and paragraph breaks as the original
- Do not add a preamble — output the rewritten text directly

User message:
{{user_message}}
```

**Input variable:** `user_message` (String)

---

## Connection Map

| From | To | Mapping |
|------|----|---------|
| Flow input | DecideOperation | `user_message` → `user_message` |
| DecideOperation (model output) | RouteByOperation | response → `operation` |
| Flow input | Summarizer | `user_message` → `user_message` |
| Flow input | Rewriter | `user_message` → `user_message` |
| Summarizer (model output) | Flow output | response → output |
| Rewriter (model output) | Flow output | response → output |

---

## Expected Outputs

### Test Case 1 – Summarize

`DecideOperation` should output `summarize`.

`Summarizer` output (example):

```
**Summary:**
- Remote work has pushed companies toward hybrid models splitting time between home and office
- Collaboration, onboarding, and maintaining culture are harder in distributed settings
- Geography is no longer a barrier to hiring — companies can recruit talent anywhere
- Managing distributed teams requires new skills from managers
- Asynchronous communication and outcome-based reviews are essential in distributed work

**TL;DR:** Remote work has expanded talent pools and forced companies to adopt new management practices to keep distributed teams cohesive.
```

### Test Case 2 – Rewrite

`DecideOperation` should output `rewrite`.

`Rewriter` output (example):

```
Using asynchronous communication in distributed teams has shown real benefits for collaboration, even when team members work in different time zones. The main challenge is keeping everyone aligned without the ability to meet in real time.
```

---

## Why These Prompts Work

**DecideOperation:** The classifier prompt is strict about output format ("exactly one word") and provides a clear default for ambiguous cases. This prevents the condition node from receiving unexpected values like `"summarize it"` or `"I would choose summarize"` that would break the routing logic.

**Summarizer and Rewriter:** Both nodes receive the full `user_message` and are instructed to extract the text themselves. This keeps the flow simple — one input variable flows through every node, and no node needs to split or transform the input before passing it downstream.
