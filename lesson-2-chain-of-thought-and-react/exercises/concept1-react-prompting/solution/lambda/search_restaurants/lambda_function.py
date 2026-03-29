import json


MOCK_RESTAURANTS = {
    "italian": [
        {"name": "Trattoria Bella", "cuisine": "Italian", "price_range": "moderate", "rating": 4.6, "address": "142 Pike St, Seattle, WA"},
        {"name": "Osteria Romana", "cuisine": "Italian", "price_range": "moderate", "rating": 4.4, "address": "88 Capitol Hill Ave, Seattle, WA"},
        {"name": "Pasta Express", "cuisine": "Italian", "price_range": "budget", "rating": 4.1, "address": "210 2nd Ave, Seattle, WA"},
    ],
    "japanese": [
        {"name": "Sakura Garden", "cuisine": "Japanese", "price_range": "moderate", "rating": 4.7, "address": "55 Westlake Ave, Seattle, WA"},
    ],
}


def lambda_handler(event, context):
    parameters = {p["name"]: p["value"] for p in event.get("parameters", [])}
    cuisine = parameters.get("cuisine", "").lower()

    if cuisine:
        restaurants = MOCK_RESTAURANTS.get(cuisine, [])
        if not restaurants:
            restaurants = [{"message": f"No {cuisine.title()} restaurants found."}]
    else:
        restaurants = [r for items in MOCK_RESTAURANTS.values() for r in items]

    result = {
        "cuisine": cuisine.title() if cuisine else "All",
        "restaurants": restaurants,
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
