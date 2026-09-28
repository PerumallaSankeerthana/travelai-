from integrations.mapbox import geocode_location


def main():
    locations = [
        "Baga Beach, Goa",
        "Anjuna Beach, Goa",
        "Vagator Beach, Goa",
        "Candolim Beach, Goa",
    ]

    for location in locations:
        coordinates = geocode_location(location)

        print(
            f"{location} -> "
            f"longitude={coordinates[0]}, "
            f"latitude={coordinates[1]}"
        )


if __name__ == "__main__":
    main()
