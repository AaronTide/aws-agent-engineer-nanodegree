import json


MOCK_AVAILABILITY = {
    "trattoria bella": {"available": True},
    "osteria romana": {"available": False},
    "pasta express": {"available": True},
    "sakura garden": {"available": True},
}


def lambda_handler(event, context):
    parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}
    restaurant_name = parameters.get("restaurant_name", "")
    date = parameters.get("date", "")

    availability = MOCK_AVAILABILITY.get(restaurant_name.lower(), {"available": True})

    result = {
        "restaurant_name": restaurant_name,
        "date": date,
        "available": availability["available"],
        "message": (
            f"{restaurant_name} is available on {date}."
            if availability["available"]
            else f"{restaurant_name} is fully booked on {date}."
        ),
    }

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event["actionGroup"],
            "function": event["function"],
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(result)
                    }
                }
            },
        },
    }
