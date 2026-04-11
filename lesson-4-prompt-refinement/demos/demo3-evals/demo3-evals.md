# Demo 3 – Evals

## Eval JSONL Format

Each line written to `eval_responses.jsonl` follows this schema:

```json
{
  "prompt": "<customer question>",
  "referenceResponse": "<ideal answer used for scoring>",
  "modelResponses": [
    {
      "response": "<model output>",
      "modelIdentifier": "<label for this run>"
    }
  ]
}
```

---

## Eval Job Configuration

| Field | Value |
|-------|-------|
| Evaluation method | Automatic |
| Inference | BYOI – use my own responses |
| Metrics | ROUGE, BERTScore, METEOR |

---

## Metrics

| Metric | What it measures |
|--------|-----------------|
| ROUGE-L | Key phrase overlap with the reference response |
| BERTScore | Semantic similarity to the reference response |
| METEOR | Word-level precision and recall with synonym matching |
