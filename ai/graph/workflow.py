from langgraph.graph import END, START, StateGraph

from ai.agents.constraint_agent import extract_constraints
from ai.agents.flight_agent import flight_node
from ai.agents.hotel_agent import hotel_node
from ai.agents.weather_agent import weather_node
from ai.agents.itinerary_agent import itinerary_node
from backend.core.database import SessionLocal
from ai.rag.retriever import retrieve_memories
from verification.validator import validate_trip_state

from ai.graph.state import TravelState

from optimization.budget_allocator import allocate_budget
from optimization.route_service import optimize_itinerary_routes


# ============================================================
# 1. CONSTRAINT AGENT
# ============================================================

def constraint_node(state: TravelState) -> dict:
    """
    Extract structured travel constraints from the user's
    natural-language request.
    """

    constraints = extract_constraints(
        state["user_message"]
    )

    return {
        "constraints": constraints,
        "status": "constraints_extracted",
    }

def rag_node(state: TravelState) -> dict:
    """
    Retrieve relevant user memories from PostgreSQL + pgvector.
    """

    user_id = state.get("user_id")

    if not user_id:
        print("\n--- RAG ---")
        print("No user_id available. Skipping memory retrieval.")
        return {
            "user_memory": [],
            "status": "memory_skipped",
        }

    query = state.get("user_message", "")

    db = SessionLocal()

    try:
        memories = retrieve_memories(
            db=db,
            user_id=user_id,
            query=query,
            limit=5,
        )

        print("\n--- RAG MEMORY ---")

        if not memories:
            print("No previous travel memories found.")
        else:
            for memory in memories:
                print(
                    f"  Memory: {memory['memory']} "
                    f"| distance: {memory['distance']:.4f}"
                )

        return {
            "user_memory": memories,
            "status": "memory_retrieved",
        }

    finally:
        db.close()
# ============================================================
# 2. JOIN NODE
# ============================================================

def join_node(state: TravelState) -> dict:
    """
    Synchronization point.

    Flight, hotel and weather agents run independently after
    constraint extraction.

    LangGraph waits for all incoming branches before
    continuing to the budget allocator.
    """

    return {
        "status": "data_collected",
    }


# ============================================================
# 3. SMART BUDGET ALLOCATION
# ============================================================

def budget_allocation_node(state: TravelState) -> dict:
    """
    Allocate the total trip budget using deterministic rules.

    Priority:

        1. Flight
        2. Hotel
        3. Food
        4. Activities
        5. Buffer

    Flight and hotel are mandatory.

    If the budget is insufficient, the workflow stops
    before itinerary generation.
    """

    constraints = state["constraints"]

    flights = state.get(
        "flights",
        []
    )

    hotels = state.get(
        "hotels",
        []
    )

    allocation = allocate_budget(
        total_budget=constraints["budget"],
        travelers=constraints["travelers"],
        start_date=constraints["start_date"],
        end_date=constraints["end_date"],
        preferences=constraints.get(
            "preferences",
            []
        ),
        flights=flights,
        hotels=hotels,
    )

    print(
        "\n--- SMART BUDGET ALLOCATION ---"
    )

    print(
        allocation
    )

    # --------------------------------------------------------
    # BUDGET FAILURE
    # --------------------------------------------------------

    if allocation.get(
        "status"
    ) == "budget_insufficient":

        print(
            "\n--- BUDGET INSUFFICIENT ---"
        )

        print(
            allocation.get(
                "reason",
                "unknown_reason"
            )
        )

        print(
            allocation.get(
                "message",
                "The trip cannot be planned within the given budget."
            )
        )

        return {
            "budget_allocation": allocation,
            "status": "budget_insufficient",
        }

    # --------------------------------------------------------
    # BUDGET SUCCESS
    # --------------------------------------------------------

    return {
        "budget_allocation": allocation,
        "status": "budget_allocated",
    }


# ============================================================
# 4. ROUTE OPTIMIZATION
# ============================================================

def route_optimization_node(
    state: TravelState,
) -> dict:
    """
    Calculate travel routes after itinerary generation.

    The route service:
        - resolves activity locations
        - gets real road distances/times from Mapbox
        - calculates travel segments
        - preserves Morning/Afternoon/Evening semantics
    """

    itinerary = state.get(
        "itinerary"
    )

    if not itinerary:
        raise RuntimeError(
            "Cannot optimize route because itinerary is missing."
        )

    route_data = optimize_itinerary_routes(
        itinerary=itinerary,
        destination=state["constraints"]["destination"],
    )

    print(
        "\n--- ROUTE OPTIMIZATION ---"
    )

    for day in route_data.get(
        "days",
        []
    ):

        print(
            f"Day {day.get('day_number')}: "
            f"{day.get('total_distance_km')} km, "
            f"{day.get('total_travel_minutes')} minutes"
        )

        for segment in day.get(
            "travel_segments",
            []
        ):

            print(
                f"  {segment['from']} -> "
                f"{segment['to']} | "
                f"{segment['distance_km']} km | "
                f"{segment['duration_minutes']} min"
            )

    return {
        "route_data": route_data,
        "status": "route_optimized",
    }


# ============================================================
# 5. BUDGET DECISION
# ============================================================

def budget_decision_node(
    state: TravelState,
) -> str:
    """
    Decide whether the workflow can continue to
    itinerary generation.
    """

    status = state.get(
        "status"
    )

    if status == "budget_insufficient":
        return "budget_failed"

    if status == "budget_allocated":
        return "budget_success"

    return "budget_failed"


# ============================================================
# 6. VERIFICATION
# ============================================================

def verification_node(
    state: TravelState,
) -> dict:
    """
    Deterministic rule-based verification.

    No LLM call is made here.

    Checks:
        - constraints
        - dates
        - travelers
        - budget
        - flight availability
        - hotel availability
        - budget allocation
        - itinerary structure
        - activity costs
        - weather structure
        - route optimization output
    """

    errors = validate_trip_state(
        state
    )

    # --------------------------------------------------------
    # VERIFICATION FAILED
    # --------------------------------------------------------

    if errors:

        print(
            "\n--- VERIFICATION FAILED ---"
        )

        for error in errors:
            print(
                f"  ❌ {error}"
            )

        return {
            "verification_errors": errors,
            "verification_passed": False,
            "status": "verification_failed",
        }

    # --------------------------------------------------------
    # VERIFICATION PASSED
    # --------------------------------------------------------

    print(
        "\n--- VERIFICATION PASSED ---"
    )

    print(
        "  ✓ Budget valid"
    )

    print(
        "  ✓ Dates valid"
    )

    print(
        "  ✓ Itinerary structure valid"
    )

    print(
        "  ✓ Activity costs valid"
    )

    print(
        "  ✓ Weather structure valid"
    )

    print(
        "  ✓ Route data valid"
    )

    return {
        "verification_errors": [],
        "verification_passed": True,
        "status": "verified",
    }


# ============================================================
# 7. VERIFICATION DECISION
# ============================================================

def verification_decision_node(
    state: TravelState,
) -> str:
    """
    Decide whether verification passed or failed.
    """

    if state.get(
        "verification_passed"
    ):
        return "verification_success"

    return "verification_failed"


# ============================================================
# 8. BUILD LANGGRAPH WORKFLOW
# ============================================================

def build_travel_graph():

    graph = StateGraph(
        TravelState
    )

    # ========================================================
    # NODES
    # ========================================================

    graph.add_node(
        "constraint_agent",
        constraint_node,
    )
    graph.add_node("rag", rag_node)

    graph.add_node(
        "flight_agent",
        flight_node,
    )

    graph.add_node(
        "hotel_agent",
        hotel_node,
    )

    graph.add_node(
        "weather_agent",
        weather_node,
    )

    graph.add_node(
        "join_results",
        join_node,
    )

    graph.add_node(
        "budget_allocator",
        budget_allocation_node,
    )

    graph.add_node(
        "itinerary_agent",
        itinerary_node,
    )

    graph.add_node(
        "route_optimizer",
        route_optimization_node,
    )

    graph.add_node(
        "verification",
        verification_node,
    )

    # ========================================================
    # START
    # ========================================================

    graph.add_edge(
        START,
        "constraint_agent",
    )

    # ========================================================
    # CONSTRAINT → PARALLEL AGENTS
    # ========================================================

    graph.add_edge("constraint_agent", "rag")

    graph.add_edge("rag", "flight_agent")
    graph.add_edge("rag", "hotel_agent")
    graph.add_edge("rag", "weather_agent")

    # ========================================================
    # PARALLEL AGENTS → JOIN
    # ========================================================

    graph.add_edge(
        "flight_agent",
        "join_results",
    )

    graph.add_edge(
        "hotel_agent",
        "join_results",
    )

    graph.add_edge(
        "weather_agent",
        "join_results",
    )

    # ========================================================
    # JOIN → BUDGET
    # ========================================================

    graph.add_edge(
        "join_results",
        "budget_allocator",
    )

    # ========================================================
    # BUDGET → CONDITIONAL ROUTING
    # ========================================================

    graph.add_conditional_edges(
        "budget_allocator",
        budget_decision_node,
        {
            "budget_success": "itinerary_agent",
            "budget_failed": END,
        },
    )

    # ========================================================
    # ITINERARY → ROUTE OPTIMIZER
    # ========================================================

    graph.add_edge(
        "itinerary_agent",
        "route_optimizer",
    )

    # ========================================================
    # ROUTE OPTIMIZER → VERIFICATION
    # ========================================================

    graph.add_edge(
        "route_optimizer",
        "verification",
    )

    # ========================================================
    # VERIFICATION → FINAL DECISION
    # ========================================================

    graph.add_conditional_edges(
        "verification",
        verification_decision_node,
        {
            "verification_success": END,
            "verification_failed": END,
        },
    )

    # ========================================================
    # COMPILE
    # ========================================================

    return graph.compile()