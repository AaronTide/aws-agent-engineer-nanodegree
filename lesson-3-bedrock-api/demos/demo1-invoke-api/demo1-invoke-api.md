# Demo 1 – Using the InvokeModel API

## Client Setup

```python
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
```

---

## InvokeModel Request

```python
body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 512,
    "temperature": 0.0,
    "messages": [{"role": "user", "content": prompt}],
}

response = bedrock.invoke_model(
    modelId=MODEL_ID,
    body=json.dumps(body),
    contentType="application/json",
    accept="application/json",
)

result = json.loads(response["body"].read())
print(result["content"][0]["text"])
```

**Expected:** A structured summary of the meeting notes — decisions and action items extracted from unstructured text. Output is deterministic at `temperature: 0.0`.

Run with:
```bash
python meeting_summarizer.py
```

---

## Parameter Variations

| Parameter | Original | Try | Expected effect |
|-----------|----------|-----|-----------------|
| `temperature` | `0.0` | `0.7` | More varied phrasing on repeated runs |
| `max_tokens` | `512` | `128` | Shorter, punchier summary |
| `max_tokens` | `512` | `1024` | More detailed breakdown |

---

## Streaming Request

```python
response = bedrock.invoke_model_with_response_stream(
    modelId=MODEL_ID,
    body=json.dumps(body),
    contentType="application/json",
    accept="application/json",
)

for event in response["body"]:
    chunk = json.loads(event["chunk"]["bytes"])
    if chunk["type"] == "content_block_delta":
        print(chunk["delta"].get("text", ""), end="", flush=True)
```

**Expected:** Tokens print to the terminal in real time as they are generated, rather than appearing all at once after the full response is ready.

Run with:
```bash
python meeting_summarizer_stream.py
```
