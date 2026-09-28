from ai.graph.state import TravelState
from integrations.weather import get_weather


def weather_node(state: TravelState) -> dict:
    constraints = state["constraints"]

    weather = get_weather(
        city=constraints["destination"],
        start_date=constraints["start_date"],
        end_date=constraints["end_date"],
    )

    return {
        "weather": weather
    }
