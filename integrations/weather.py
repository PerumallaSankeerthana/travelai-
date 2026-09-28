import requests
from datetime import datetime
from collections import defaultdict

from backend.core.config import settings


WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_weather(
    city: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:

    if not settings.openweather_api_key:
        raise RuntimeError(
            "OPENWEATHER_API_KEY is not configured"
        )

    params = {
        "q": city,
        "appid": settings.openweather_api_key,
        "units": "metric",
    }

    response = requests.get(
        WEATHER_API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    daily = defaultdict(list)

    for item in data.get("list", []):
        datetime_text = item.get("dt_txt")

        if not datetime_text:
            continue

        date = datetime_text.split(" ")[0]

        # If trip dates were supplied, only keep relevant dates.
        if start_date and date < start_date:
            continue

        if end_date and date > end_date:
            continue

        daily[date].append(item)

    weather = []

    for date in sorted(daily.keys()):
        entries = daily[date]

        temperatures = [
            item.get("main", {}).get("temp")
            for item in entries
            if item.get("main", {}).get("temp") is not None
        ]

        conditions = [
            item.get("weather", [{}])[0].get("description")
            for item in entries
            if item.get("weather", [{}])[0].get("description")
        ]

        humidities = [
            item.get("main", {}).get("humidity")
            for item in entries
            if item.get("main", {}).get("humidity") is not None
        ]

        wind_speeds = [
            item.get("wind", {}).get("speed")
            for item in entries
            if item.get("wind", {}).get("speed") is not None
        ]

        weather.append(
            {
                "date": date,
                "temp_c": round(sum(temperatures) / len(temperatures), 1)
                if temperatures
                else None,
                "condition": conditions[0] if conditions else None,
                "humidity": round(sum(humidities) / len(humidities), 1)
                if humidities
                else None,
                "wind_speed": round(sum(wind_speeds) / len(wind_speeds), 1)
                if wind_speeds
                else None,
            }
        )

    return weather
