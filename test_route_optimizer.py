from integrations.mapbox import get_route_matrix
from optimization.route_optimizer import optimize_route


def main():

    locations = [
        {
            "name": "Baga Beach",
            "latitude": 15.5557,
            "longitude": 73.7537,
        },
        {
            "name": "Anjuna Beach",
            "latitude": 15.5736,
            "longitude": 73.7449,
        },
        {
            "name": "Vagator Beach",
            "latitude": 15.5970,
            "longitude": 73.7276,
        },
        {
            "name": "Candolim Beach",
            "latitude": 15.5172,
            "longitude": 73.7177,
        },
    ]

    coordinates = [
        (
            location["longitude"],
            location["latitude"],
        )
        for location in locations
    ]

    # --------------------------------------------------------
    # MAPBOX
    # --------------------------------------------------------

    matrix = get_route_matrix(
        coordinates
    )

    # --------------------------------------------------------
    # OR-TOOLS
    # --------------------------------------------------------

    result = optimize_route(
        locations=locations,
        durations=matrix["durations"],
    )

    print("\n--- OPTIMIZED ROUTE ---")

    for index, location in enumerate(
        result["ordered_locations"],
        start=1,
    ):
        print(
            f"{index}. {location['name']}"
        )

    print(
        "\nTotal travel time:",
        result["total_duration_minutes"],
        "minutes",
    )


if __name__ == "__main__":
    main()