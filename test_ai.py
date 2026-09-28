from ai.graph.workflow import build_travel_graph


message = (
    "I want to travel from Hyderabad to Goa "
    "from December 10 to December 14, 2026, "
    "for 2 people. "
    "My budget is 30000 INR. "
    "I like beaches, local food and nightlife."
)


print("\n--- LANGGRAPH TRAVELAI TEST ---")


graph = build_travel_graph()


result = graph.invoke(
    {
        "user_message": message
    }
)


print("\n--- FINAL STATUS ---")
print(result.get("status"))


print("\n--- CONSTRAINTS ---")
print(result.get("constraints"))


print("\n--- FLIGHTS ---")

for flight in result.get("flights", []):

    print({
        "airline": flight.get("airline"),
        "flight_number": flight.get("flight_number"),
        "price": flight.get("price"),
        "stops": flight.get("stops"),
    })


print("\n--- HOTELS ---")

for hotel in result.get("hotels", []):

    print({
        "name": hotel.get("name"),
        "price_per_night": hotel.get("price_per_night"),
        "rating": hotel.get("rating"),
    })
print("\n--- RAW ITINERARY ---")
print(result.get("itinerary"))

print("\n--- ITINERARY DAYS ---")

itinerary = result.get("itinerary", {})

for day in itinerary.get("days", []):

    print(f"\nDay {day.get('day_number')} - {day.get('date')}")

    print("Weather:")
    print(day.get("weather"))

    print("Morning:")
    print(day.get("slots", {}).get("morning"))

    print("Afternoon:")
    print(day.get("slots", {}).get("afternoon"))

    print("Evening:")
    print(day.get("slots", {}).get("evening"))