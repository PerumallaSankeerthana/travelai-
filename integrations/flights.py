import requests

from backend.core.config import settings


SERP_API_URL = "https://serpapi.com/search.json"


def search_flights(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: str,
    adults: int,
) -> list[dict]:

    if not settings.serp_api_key:
        raise RuntimeError("SERP_API_KEY is not configured")

    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "type": "1",
        "adults": adults,
        "currency": "INR",
        "hl": "en",
        "gl": "in",
        "api_key": settings.serp_api_key,
    }

    response = requests.get(
        SERP_API_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(
            f"SerpApi flight search error: {data['error']}"
        )

    results = (
        data.get("best_flights")
        or data.get("other_flights")
        or []
    )

    flights = []

    for itinerary in results[:5]:

        segments = itinerary.get("flights", [])

        if not segments:
            continue

        first_segment = segments[0]
        last_segment = segments[-1]

        departure_airport = first_segment.get(
            "departure_airport", {}
        )

        arrival_airport = last_segment.get(
            "arrival_airport", {}
        )

        flight_number = first_segment.get(
            "flight_number",
            "unknown"
        )

        result_id = (
            itinerary.get("booking_token")
            or f"{departure_id}-{arrival_id}-"
               f"{outbound_date}-{flight_number}"
        )

        flights.append(
            {
                "result_id": result_id,
                "airline": first_segment.get("airline"),
                "flight_number": flight_number,
                "price": itinerary.get("price"),
                "currency": "INR",
                "departure": {
                    "airport": departure_airport.get("id"),
                    "time": departure_airport.get("time"),
                },
                "arrival": {
                    "airport": arrival_airport.get("id"),
                    "time": arrival_airport.get("time"),
                },
                "duration_minutes": itinerary.get(
                    "total_duration"
                ),
                "stops": max(len(segments) - 1, 0),
                "raw": itinerary,
            }
        )

    return flights