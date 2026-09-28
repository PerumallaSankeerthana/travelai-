from ai.agents.constraint_agent import extract_constraints
from ai.agents.flight_agent import flight_node
from ai.agents.hotel_agent import hotel_node
from ai.agents.weather_agent import weather_node


message = (
    "I want to travel from Hyderabad to Goa "
    "from December 10 to December 14, 2026, "
    "for 2 people. My budget is 30000 INR. "
    "I like beaches, local food and nightlife."
)


print("\n--- CONSTRAINT AGENT ---")

constraints = extract_constraints(message)

print(constraints)


state = {
    "user_message": message,
    "constraints": constraints,
}


print("\n--- FLIGHT AGENT ---")

flight_result = flight_node(state)

for flight in flight_result["flights"]:
    print({
        "result_id": flight["result_id"],
        "airline": flight["airline"],
        "flight_number": flight["flight_number"],
        "price": flight["price"],
        "stops": flight["stops"],
    })


print("\n--- HOTEL AGENT ---")

hotel_result = hotel_node(state)

for hotel in hotel_result["hotels"]:
    print({
        "result_id": hotel["result_id"],
        "name": hotel["name"],
        "price_per_night": hotel["price_per_night"],
        "rating": hotel["rating"],
    })


print("\n--- WEATHER AGENT ---")

weather_result = weather_node(state)

for weather in weather_result["weather"][:5]:
    print(weather)