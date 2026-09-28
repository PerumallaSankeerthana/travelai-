from integrations.serp import search_hotels


results = search_hotels(
    destination="Goa",
    check_in="2026-12-10",
    check_out="2026-12-14",
    adults=2,
)

print("\n--- LIVE HOTEL RESULTS ---")

for hotel in results:
    print(
        {
            "result_id": hotel["result_id"],
            "name": hotel["name"],
            "price_per_night": hotel["price_per_night"],
            "rating": hotel["rating"],
        }
    )