from ai.graph.state import TravelState
from integrations.flights import search_flights


def flight_node(state: TravelState) -> dict:
    constraints = state["constraints"]

    flights = search_flights(
        departure_id=constraints["origin"],
        arrival_id=constraints["destination_code"],
        outbound_date=constraints["start_date"],
        return_date=constraints["end_date"],
        adults=constraints["travelers"],
    )

    return {
        "flights": flights
    }