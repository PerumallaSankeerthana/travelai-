from integrations.flights import search_flights


results = search_flights(
    departure_id="HYD",
    arrival_id="GOI",
    outbound_date="2026-12-10",
    return_date="2026-12-14",
    adults=2,
)

print("\n--- LIVE GOOGLE FLIGHTS ---")

for flight in results:
    print(
        {
            "result_id": flight["result_id"],
            "airline": flight["airline"],
            "flight_number": flight["flight_number"],
            "price": flight["price"],
            "currency": flight["currency"],
            "departure": flight["departure"],
            "arrival": flight["arrival"],
            "duration_minutes": flight["duration_minutes"],
            "stops": flight["stops"],
        }
    )
