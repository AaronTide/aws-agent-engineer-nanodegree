import json


MOCK_WEATHER = {
    "london": {
        "condition": "Light rain in the morning, clearing to partly cloudy by afternoon",
        "temperature_celsius": 11,
        "wind_mph": 12,
        "recommendation": "Bring a light jacket and umbrella for the morning",
    },
    "paris": {
        "condition": "Mostly sunny with light clouds",
        "temperature_celsius": 14,
        "wind_mph": 8,
        "recommendation": "Great day to be outdoors",
    },
    "new york": {
        "condition": "Clear skies, cold",
        "temperature_celsius": 5,
        "wind_mph": 15,
        "recommendation": "Dress warmly, especially in the wind",
    },
}


def lambda_handler(event, context):
    # AgentCore Gateway calls this Lambda with the tool arguments AS the event:
    #   event == {"city": "London", "date": "2026-08-22"}
    # The name of the tool being called is delivered via the Lambda context:
    #   context.client_context.custom["bedrockAgentCoreToolName"]
    # (This replaces the old Bedrock Agents action-group event format, which
    # wrapped parameters in a list and required a messageVersion envelope.)
    tool_name = ""
    if context.client_context and getattr(context.client_context, "custom", None):
        tool_name = context.client_context.custom.get("bedrockAgentCoreToolName", "")
    print(f"Tool invoked: {tool_name} | arguments: {json.dumps(event)}")

    city = str(event.get("city", "")).lower()
    date = str(event.get("date", ""))

    if city not in MOCK_WEATHER:
        result = {"error": f"Unknown city: '{city.title()}'. Supported cities are: London, Paris, New York."}
    else:
        result = dict(MOCK_WEATHER[city])
        result["city"] = city.title()
        result["date"] = date

    # Return the result directly -- the Gateway wraps it as the MCP tool result.
    return result
