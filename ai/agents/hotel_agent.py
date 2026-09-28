from ai.graph.state import TravelState
from integrations.serp import search_hotels


def hotel_node(state: TravelState) -> dict:
    constraints = state["constraints"]

    hotels = search_hotels(
        destination=constraints["destination"],
        check_in=constraints["start_date"],
        check_out=constraints["end_date"],
        adults=constraints["travelers"],
    )

    return {
        "hotels": hotels
    }