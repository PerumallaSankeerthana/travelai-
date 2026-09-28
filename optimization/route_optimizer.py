# optimization/route_optimizer.py

from __future__ import annotations

from typing import Any

from ortools.constraint_solver import (
    pywrapcp,
    routing_enums_pb2,
)


def optimize_activity_order(
    activities: list[dict[str, Any]],
    distance_matrix: list[list[float]],
) -> list[dict[str, Any]]:
    """
    Reorders activities using OR-Tools to minimize
    the total travel distance.

    Slot order is preserved:
        morning -> afternoon -> evening

    OR-Tools is only used when there are 3+ activities.
    """

    if len(activities) <= 1:
        return activities

    if len(distance_matrix) != len(activities):
        return activities

    # --------------------------------------------------------
    # IMPORTANT:
    # For our current itinerary, activities are already grouped
    # by morning -> afternoon -> evening.
    #
    # We optimize only when multiple activities exist in the
    # same slot. This prevents OR-Tools from moving an evening
    # activity into the morning.
    # --------------------------------------------------------

    optimized = []

    slot_order = [
        "morning",
        "afternoon",
        "evening",
    ]

    for slot in slot_order:

        slot_activities = [
            activity
            for activity in activities
            if activity.get("_slot") == slot
        ]

        if len(slot_activities) <= 1:
            optimized.extend(slot_activities)
            continue

        # Map original activity index.
        indices = [
            activities.index(activity)
            for activity in slot_activities
        ]

        if len(indices) <= 1:
            optimized.extend(slot_activities)
            continue

        sub_matrix = [
            [
                float(distance_matrix[i][j])
                for j in indices
            ]
            for i in indices
        ]

        ordered_indices = _solve_tsp(
            sub_matrix
        )

        for local_index in ordered_indices:
            optimized.append(
                slot_activities[local_index]
            )

    return optimized


def _solve_tsp(
    distance_matrix: list[list[float]],
) -> list[int]:
    """
    Solve a small travelling-salesperson problem
    using OR-Tools.
    """

    size = len(distance_matrix)

    if size <= 1:
        return list(range(size))

    manager = pywrapcp.RoutingIndexManager(
        size,
        1,
        0,
    )

    routing = pywrapcp.RoutingModel(
        manager
    )

    def distance_callback(
        from_index: int,
        to_index: int,
    ) -> int:

        from_node = manager.IndexToNode(
            from_index
        )

        to_node = manager.IndexToNode(
            to_index
        )

        distance = distance_matrix[
            from_node
        ][to_node]

        if distance is None:
            return 10**9

        return int(
            max(0, distance)
        )

    transit_callback_index = (
        routing.RegisterTransitCallback(
            distance_callback
        )
    )

    routing.SetArcCostEvaluatorOfAllVehicles(
        transit_callback_index
    )

    search_parameters = (
        pywrapcp.DefaultRoutingSearchParameters()
    )

    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )

    search_parameters.time_limit.seconds = 2

    solution = routing.SolveWithParameters(
        search_parameters
    )

    if solution is None:
        return list(range(size))

    ordered = []

    index = routing.Start(0)

    while not routing.IsEnd(index):

        node = manager.IndexToNode(index)

        ordered.append(node)

        index = solution.Value(
            routing.NextVar(index)
        )

    return ordered