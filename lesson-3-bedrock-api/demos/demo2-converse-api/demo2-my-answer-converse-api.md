# Setup

Configure the AWS CLI auth first

    aws configure
    
 -> provide the authentications then:
    
    aws configure set aws_session_token "your token"


    cd demo2-converse-api


# Simple Travel Chat

    python simple_travel_chat.py


**Travel Assistant**: 
Hello! I can help you plan your next trip. Where are you thinking of going?



**You**:
hawaii plss



**Travel Assistant**: 
Absolutely, Hawaii is a dream destination! Here’s a quick guide to help you explore:

**Best Time to Visit:**
- April to June or September to November for pleasant weather and fewer crowds.

**Top Islands to Visit:**
1. **Oahu:** Visit Honolulu, Waikiki Beach, and hike Diamond Head.
2. **Maui:** Explore the Road to Hana, snorkeling at Molokini Crater, and the beautiful beaches.
3. **Hawaii (Big Island):** See volcanoes at Hawaii Volcanoes National Park and relax on white sand beaches.
4. **Kauai:** Known as the Garden Isle, explore the Na Pali Coast and Waimea Canyon.

**Must-Try Activities:**
- **Snorkeling/Diving:** Check out Hanauma Bay on Oahu.
- **Surfing:** Learn to surf at Waikiki or other famous spots.
- **Whale Watching:** Best from December to April.
- **Luau:** Experience a traditional Hawaiian feast and show.

**Sample Itinerary (7 Days):**
- **Day 1-2:** Oahu - Explore Honolulu and Waikiki.
- **Day 3-4:** Maui - Road to Hana and snorkeling.
- **Day 5-6:** Big Island - Volcanoes National Park and beaches.
- **Day 7:** Kauai - Na Pali Coast and Waimea Canyon.

Ready to dive into the paradise of Hawaii? 🌺🏝️



# Restaurant Booking Assistant


## Prompt (Todo-1):

You are a restaurant recommendation agent for a user who is located in Paris. You have the following tools:

a) get_cuisines 

Returns the list of cuisine types available. Takes no parameters. 

b) search_restaurants

Searches for restaurants based on the parameter cuisine. Returns all restaurants if no cuisine is specified

c) get_availability

Checks whether a specific restaurant has availability for tonight. Takes a parameter restaurant_id 

Always use the tools before making suggestions to the user. Do NOT invent restaurants/ratings/availability results or add them from memory. You must only rely on the tool results. 
Always confirm availability before recommending the restaurant and try the next best option if the restaurant is not available.

## Tool Wiring:

    TOOL_TARGETS = [
    {
        "target_name": "cuisines",
        "lambda_output_key": "GetCuisinesFunctionArn",
        "tools": [
            {
                "name": "get_cuisines",
                "description": "Returns the list of cuisine types available",  # TODO (see README table)
                "inputSchema": {"type": "object",
                "properties": {


                }},
            }
        ],
    },
    {
        "target_name": "restaurants",
        "lambda_output_key": "SearchRestaurantsFunctionArn",
        "tools": [
            {
                "name": "search_restaurants",
                "description": "Searches for restaurants based on the type of cuisine served",  # TODO (see README table)
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cuisine": {
            "type": "string",
            "description": "The type of cuisine to search for, such as Italian, Mexican, or Japanese. If not specified, all restaurants are returned."
    }
                        # TODO: add the optional "cuisine" string parameter
                        # with a good description (see README table).
                    },
                },
            }
        ],
    },
    {
        "target_name": "availability",
        "lambda_output_key": "GetAvailabilityFunctionArn",
        "tools": [
            {
                "name": "get_availability",
                "description": "checks if a specific restaurant is available now",  # TODO (see README table)
                "inputSchema": {
                    "type": "object",
                    "properties": {


                        "restaurant_id": {
                        "type": "string",
                        "description": "The unique ID of the restaurant to check availability for."
                    }
                        # TODO: add the required "restaurant_id" string
                        # parameter (see README table)...
                    },
                    "required": ["restaurant_id"]
                    # TODO: ...and mark it required:
                    # "required": ["restaurant_id"],
                },
            }
        ],
    },
]


## Chat responses with trace:

     python restaurant_booking_assistant


**Assistant**: Hi! I can help you find a restaurant for tonight.
           What cuisine are you in the mood for?

**You**: Italian food is my all-time fave 



  [tool call] get_cuisines({})
  
  [tool result] {'cuisines': ['American', 'French', 'Indian', 'Italian', 'Japanese', 'Mexican']}
  
  [tool call] search_restaurants({'cuisines': ['Italian']})
  
  
  [tool result] {'restaurants': [{'id': 'r1', 'name': 'Pasta Roma', 'cuisine': 'Italian', 'rating': 4.5}, {'id': 'r7', 'name': 'Trattoria Bella', 'cuisine': 'Italian', 'rating': 4.4}]}
  
  
  [tool call] get_availability({'restaurant_id': 'r1'})
  
  [tool result] {'restaurant_id': 'r1', 'available': True}
  
  [tool call] get_availability({'restaurant_id': 'r7'})
  
  [tool result] {'restaurant_id': 'r7', 'available': True}

**Travel Assistant**: 
 < .thinking >
 Both Pasta Roma and Trattoria Bella have availability for tonight. I will recommend Pasta Roma as it has a slightly higher rating.</thinking 
 

I recommend booking at Pasta Roma, an Italian restaurant, for tonight. It has a 4.5 rating and is available for your preferred time. Enjoy your meal!



**You**: I've already been there, give me some other restaurant



  [tool call] get_availability({'restaurant_id': 'r7'})
  
  [tool result] {'restaurant_id': 'r7', 'available': True}
  

**Travel Assistant**: <.thinking>
Trattoria Bella also has availability for tonight. I will recommend it as an alternative to Pasta Roma.</thinking>


Since you've already been to Pasta Roma, I recommend booking at Trattoria Bella, another Italian restaurant, for tonight. It has a 4.4 rating and is available for your preferred time. Enjoy your meal!

  
