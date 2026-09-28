from optimization.route_service import (
    optimize_itinerary_routes,
)


def main():

    itinerary = {
        "days": [
            {
                "date": "2026-12-10",
                "day_number": 1,
                "slots": {
                    "morning": [
                        {
                            "activity": "Baga Beach",
                            "location": "Baga Beach, Goa",
                            "est_cost": 500,
                        }
                    ],
                    "afternoon": [
                        {
                            "activity": "Lunch",
                            "location": "Candolim Beach, Goa",
                            "est_cost": 400,
                        }
                    ],
                    "evening": [
                        {
                            "activity": "Sunset",
                            "location": "Anjuna Beach, Goa",
                            "est_cost": 0,
                        }
                    ],
                },
            }
        ]
    }

    result = optimize_itinerary_routes(
        itinerary=itinerary,
        destination="Goa",
    )

    print("\n--- ROUTE SERVICE RESULT ---")

    for day in result["days"]:

        print(
            f"\nDay {day['day_number']}"
        )

        print(
            f"Total distance: "
            f"{day['total_distance_km']} km"
        )

        print(
            f"Total travel time: "
            f"{day['total_travel_minutes']} minutes"
        )

        print("\nTravel segments:")

        for segment in day["travel_segments"]:

            print(
                f"{segment['from']} -> "
                f"{segment['to']} | "
                f"{segment['distance_km']} km | "
                f"{segment['duration_minutes']} min"
            )


if __name__ == "__main__":
    main()
