Configure the AWS CLI auth first

  aws configure
 -> provide the authentications
  aws configure set aws_session_token "your token"


  cd demo2-converse-api

## Simple Travel Chat

python simple_travel_chat.py


Travel Assistant: Hello! I can help you plan your next trip. Where are you thinking of going?

You: hawaii plss

Travel Assistant: Absolutely, Hawaii is a dream destination! Here’s a quick guide to help you explore:

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


## Restaurant Booking Assistant

 python restaurant_booking_assistant


Assistant: Hi! I can help you find a restaurant for tonight.
           What cuisine are you in the mood for?

You: Italian food is my all-time fave 
  [tool call] get_cuisines({})
  [tool result] {'cuisines': ['American', 'French', 'Indian', 'Italian', 'Japanese', 'Mexican']}
  [tool call] search_restaurants({'cuisines': ['Italian']})
  [tool result] {'restaurants': [{'id': 'r1', 'name': 'Pasta Roma', 'cuisine': 'Italian', 'rating': 4.5}, {'id': 'r7', 'name': 'Trattoria Bella', 'cuisine': 'Italian', 'rating': 4.4}]}
  [tool call] get_availability({'restaurant_id': 'r1'})
  [tool result] {'restaurant_id': 'r1', 'available': True}
  [tool call] get_availability({'restaurant_id': 'r7'})
  [tool result] {'restaurant_id': 'r7', 'available': True}

Travel Assistant: <thinking>Both Pasta Roma and Trattoria Bella have availability for tonight. I will recommend Pasta Roma as it has a slightly higher rating.</thinking>

I recommend booking at Pasta Roma, an Italian restaurant, for tonight. It has a 4.5 rating and is available for your preferred time. Enjoy your meal!

You: I've already been there, give me some other restaurant
  [tool call] get_availability({'restaurant_id': 'r7'})
  [tool result] {'restaurant_id': 'r7', 'available': True}

Travel Assistant: <thinking>Trattoria Bella also has availability for tonight. I will recommend it as an alternative to Pasta Roma.</thinking>

Since you've already been to Pasta Roma, I recommend booking at Trattoria Bella, another Italian restaurant, for tonight. It has a 4.4 rating and is available for your preferred time. Enjoy your meal!

  
