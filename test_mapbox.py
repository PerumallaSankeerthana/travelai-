from integrations.mapbox import get_route_matrix


def main():

    # Goa example coordinates.
    #
    # IMPORTANT:
    # (longitude, latitude)

    locations = [
        ("Baga Beach", (73.7537, 15.5557)),
        ("Anjuna Beach", (73.7449, 15.5736)),
        ("Vagator Beach", (73.7276, 15.5970)),
        ("Candolim Beach", (73.7177, 15.5172)),
    ]

    coordinates = [
        coordinate
        for _, coordinate in locations
    ]

    print("\n--- MAPBOX ROUTE MATRIX TEST ---")

    result = get_route_matrix(
        coordinates
    )

    distances = result["distances"]
    durations = result["durations"]

    print("\nDISTANCES (meters):")

    for row in distances:
        print(row)

    print("\nDURATIONS (seconds):")

    for row in durations:
        print(row)

    print("\n--- HUMAN READABLE ---")

    for i, (name_a, _) in enumerate(locations):

        for j, (name_b, _) in enumerate(locations):

            if i == j:
                continue

            distance_km = (
                distances[i][j] / 1000
            )

            duration_minutes = (
                durations[i][j] / 60
            )

            print(
                f"{name_a} → {name_b}: "
                f"{distance_km:.2f} km, "
                f"{duration_minutes:.1f} min"
            )


if __name__ == "__main__":
    main()