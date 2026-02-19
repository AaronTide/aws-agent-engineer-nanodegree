import json
import uuid
import boto3

table = boto3.resource("dynamodb").Table("BugReports")

REQUIRED_FIELDS = ("description", "stepsToReproduce", "environment")

def lambda_handler(event, _):
    print("EVENT:", json.dumps(event, indent=2, default=str))

    if event.get("messageVersion") != "1.0" or event.get("function") != "create_bug_report":
        return _resp(event, {"error": "unsupported"})

    params = event.get("parameters") or []
    body = {
        p.get("name"): p.get("value")
        for p in params
        if isinstance(p, dict) and p.get("name") is not None
    }

    description = (body.get("description") or "").strip()
    steps = (body.get("stepsToReproduce") or "").strip()
    environment = (body.get("environment") or "").strip()

    ALLOW_EMPTY_FIELDS = True
    if not ALLOW_EMPTY_FIELDS:
        if not description:
            return _resp(event, {"error": "missing", "field": "description"})
        if not steps:
            return _resp(event, {"error": "missing", "field": "stepsToReproduce"})
        if not environment:
            return _resp(event, {"error": "missing", "field": "environment"})

    ticket_id = str(uuid.uuid4())
    item = {
        "ticketId": ticket_id,
        "description": description,
        "stepsToReproduce": steps,
        "environment": environment,
        "status": "OPEN",
        # Helpful for tracing/debugging
        "sessionId": event.get("sessionId"),
        "agentId": (event.get("agent") or {}).get("id"),
        "agentAlias": (event.get("agent") or {}).get("alias"),
    }

    table.put_item(Item=item)

    return _resp(event, {"ticketId": ticket_id, "status": "OPEN"})


import json

def _resp(event, obj):
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup"),
            "function": event.get("function"),
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(obj)
                    }
                }
            },
        },
    }