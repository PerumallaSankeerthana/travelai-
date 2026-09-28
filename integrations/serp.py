import requests

from backend.core.config import settings


SERP_API_URL = "https://serpapi.com/search.json"


def search_hotels(
    destination: str,
    check_in: str,
    check_out: str,
    adults: int,
) -> list[dict]:

    if not settings.serp_api_key:
        raise RuntimeError("SERP_API_KEY is not configured")

    params = {
        "engine": "google_hotels",
        "q": destination,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "adults": adults,
        "currency": "INR",
        "api_key": settings.serp_api_key,
    }

    response = requests.get(
        SERP_API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    hotels = []

    for hotel in data.get("properties", [])[:5]:
        hotels.append(
            {
                "result_id": hotel.get("property_token"),
                "name": hotel.get("name"),
                "price_per_night": hotel.get("rate_per_night", {}).get(
                    "lowest"
                ),
                "rating": hotel.get("overall_rating"),
                "location": hotel.get("gps_coordinates"),
                "raw": hotel,
            }
        )

    return hotels
