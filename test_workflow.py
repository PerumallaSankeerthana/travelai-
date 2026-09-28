from ai.graph.workflow import build_travel_graph


def main():

    graph = build_travel_graph()

    initial_state = {
        "user_id": 1,
        "trip_id": "test_trip_001",
        "user_message": (
            "Plan a trip from Hyderabad to Goa "
            "from 2026-12-10 to 2026-12-14 "
            "for 2 travelers with a budget of 130000 INR. "
            "I like beaches, local food and nightlife."
        ),
    }

    print("\n========================================")
    print("STARTING TRAVELAI LANGGRAPH")
    print("========================================")

    result = graph.invoke(
        initial_state
    )

    print("\n========================================")
    print("WORKFLOW COMPLETED")
    print("========================================")

    print("\nFINAL STATUS:")
    print(
        result.get("status")
    )

    print("\nBUDGET:")
    print(
        result.get("budget_allocation")
    )

    print("\nITINERARY:")
    print(
        result.get("itinerary")
    )

    print("\nROUTE DATA:")
    print(
        result.get("route_data")
    )


if __name__ == "__main__":
    main()
