from datetime import date, timedelta
from typing import Any


# Maximum reasonable road travel between activities
# within the same destination/day.
MAX_ROUTE_DISTANCE_KM = 250
MAX_ROUTE_DURATION_MINUTES = 360


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_trip_state(state: dict) -> list[str]:
    """
    Deterministic rule-based verification for TravelAI.

    Returns:
        []          -> verification passed
        [errors...] -> verification failed
    """

    errors: list[str] = []

    constraints = state.get("constraints") or {}
    flights = state.get("flights") or []
    hotels = state.get("hotels") or []
    itinerary = state.get("itinerary") or {}
    budget = state.get("budget_allocation") or {}
    route_data = state.get("route_data") or {}

    # ========================================================
    # 1. REQUIRED CONSTRAINTS
    # ========================================================

    required_constraints = [
        "destination",
        "start_date",
        "end_date",
        "travelers",
        "budget",
    ]

    for field in required_constraints:
        if field not in constraints:
            errors.append(
                f"Missing constraint: {field}"
            )

    if errors:
        return errors

    start_date = constraints["start_date"]
    end_date = constraints["end_date"]
    total_budget = constraints["budget"]

    # ========================================================
    # 2. DATE VALIDATION
    # ========================================================

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        if end < start:
            errors.append(
                "End date is before start date."
            )

    except (TypeError, ValueError):
        errors.append(
            "Invalid trip dates. Expected YYYY-MM-DD."
        )

        # Cannot perform date-dependent checks
        start = None
        end = None

    # ========================================================
    # 3. TRAVELER VALIDATION
    # ========================================================

    travelers = constraints["travelers"]

    if not isinstance(travelers, int):
        errors.append(
            "Travelers must be an integer."
        )

    elif travelers <= 0:
        errors.append(
            "Travelers must be greater than zero."
        )

    # ========================================================
    # 4. BUDGET VALIDATION
    # ========================================================

    if not _is_number(total_budget):
        errors.append(
            "Budget must be numeric."
        )

    elif total_budget <= 0:
        errors.append(
            "Budget must be greater than zero."
        )

    # ========================================================
    # 5. FLIGHT VALIDATION
    # ========================================================

    if not flights:
        errors.append(
            "No flight results available."
        )

    # ========================================================
    # 6. HOTEL VALIDATION
    # ========================================================

    if not hotels:
        errors.append(
            "No hotel results available."
        )

    # ========================================================
    # 7. BUDGET ALLOCATION VALIDATION
    # ========================================================

    if budget.get("status") == "budget_insufficient":
        errors.append(
            "Budget allocation reported insufficient budget."
        )

    allocated_total = budget.get(
        "allocated_total"
    )

    if allocated_total is None:

        errors.append(
            "Budget allocation is missing allocated_total."
        )

    elif not _is_number(allocated_total):

        errors.append(
            "allocated_total must be numeric."
        )

    elif allocated_total > total_budget:

        errors.append(
            f"Allocated budget ₹{allocated_total} "
            f"exceeds total budget ₹{total_budget}."
        )

    # ========================================================
    # 8. ITINERARY VALIDATION
    # ========================================================

    days = itinerary.get("days")

    if not isinstance(days, list):

        errors.append(
            "Itinerary days must be a list."
        )

        days = []

    # ========================================================
    # 9. ITINERARY DATE SEQUENCE
    # ========================================================

    if days and start is not None and end is not None:

        expected_days = (
            end - start
        ).days + 1

        if len(days) != expected_days:

            errors.append(
                f"Itinerary has {len(days)} days, "
                f"but trip requires {expected_days} days."
            )

        for index, day_data in enumerate(
            days
        ):

            expected_date = (
                start + timedelta(days=index)
            )

            actual_date = day_data.get(
                "date"
            )

            actual_day_number = day_data.get(
                "day_number"
            )

            if actual_date != expected_date.isoformat():

                errors.append(
                    f"Day {index + 1} has incorrect date: "
                    f"{actual_date}. "
                    f"Expected {expected_date.isoformat()}."
                )

            if actual_day_number != index + 1:

                errors.append(
                    f"Invalid day_number for "
                    f"itinerary day {index + 1}."
                )

    # ========================================================
    # 10. ITINERARY SLOT VALIDATION
    # ========================================================

    activity_total = 0

    required_slots = [
        "morning",
        "afternoon",
        "evening",
    ]

    for index, day_data in enumerate(
        days,
        start=1
    ):

        slots = day_data.get(
            "slots"
        )

        if not isinstance(slots, dict):

            errors.append(
                f"Day {index} is missing slots."
            )

            continue

        for slot in required_slots:

            activities = slots.get(
                slot
            )

            if not isinstance(
                activities,
                list
            ):

                errors.append(
                    f"Day {index} {slot} "
                    f"slot must be a list."
                )

                continue

            for activity in activities:

                if not isinstance(
                    activity,
                    dict
                ):

                    errors.append(
                        f"Day {index} {slot} "
                        f"contains invalid activity."
                    )

                    continue

                if not activity.get(
                    "activity"
                ):

                    errors.append(
                        f"Day {index} {slot} "
                        f"activity is missing a name."
                    )

                location = activity.get(
                    "location"
                )

                if not location:

                    errors.append(
                        f"Day {index} {slot} "
                        f"activity is missing location."
                    )

                cost = activity.get(
                    "est_cost",
                    0
                )

                if not _is_number(cost):

                    errors.append(
                        f"Day {index} {slot} "
                        f"has invalid est_cost."
                    )

                elif cost < 0:

                    errors.append(
                        f"Day {index} {slot} "
                        f"has negative est_cost."
                    )

                else:

                    activity_total += cost

    # ========================================================
    # 11. ACTIVITY BUDGET VALIDATION
    # ========================================================

    allocated_activities = budget.get(
        "allocation",
        {}
    ).get(
        "activities"
    )

    # Also support a direct "activities" field
    if allocated_activities is None:

        allocated_activities = budget.get(
            "activities"
        )

    if (
        allocated_activities is not None
        and _is_number(allocated_activities)
        and activity_total > allocated_activities
    ):

        errors.append(
            f"Activity costs ₹{activity_total} "
            f"exceed allocated activity budget "
            f"₹{allocated_activities}."
        )

    # ========================================================
    # 12. WEATHER VALIDATION
    # ========================================================

    for index, day_data in enumerate(
        days,
        start=1
    ):

        weather = day_data.get(
            "weather"
        )

        if not isinstance(
            weather,
            dict
        ):

            errors.append(
                f"Day {index} has invalid weather data."
            )

            continue

        if "condition" not in weather:

            errors.append(
                f"Day {index} weather "
                f"is missing condition."
            )

        if "temp_c" not in weather:

            errors.append(
                f"Day {index} weather "
                f"is missing temp_c."
            )

    # ========================================================
    # 13. ROUTE DATA VALIDATION
    # ========================================================

    route_days = route_data.get(
        "days"
    )

    if not isinstance(
        route_days,
        list
    ):

        errors.append(
            "Route optimization output "
            "is missing days."
        )

        route_days = []

    if days and route_days:

        # ----------------------------------------------------
        # Number of route days
        # ----------------------------------------------------

        if len(route_days) != len(days):

            errors.append(
                "Route data day count "
                "does not match itinerary."
            )

        # ----------------------------------------------------
        # Validate every route day
        # ----------------------------------------------------

        for route_day in route_days:

            day_number = route_day.get(
                "day_number"
            )

            distance = route_day.get(
                "total_distance_km"
            )

            duration = route_day.get(
                "total_travel_minutes"
            )

            # -----------------------------------------------
            # Distance
            # -----------------------------------------------

            if distance is not None:

                if (
                    not _is_number(distance)
                    or distance < 0
                ):

                    errors.append(
                        f"Invalid route distance "
                        f"on day {day_number}."
                    )

                elif distance > MAX_ROUTE_DISTANCE_KM:

                    errors.append(
                        f"Unrealistic route distance "
                        f"on day {day_number}: "
                        f"{distance} km."
                    )

            # -----------------------------------------------
            # Duration
            # -----------------------------------------------

            if duration is not None:

                if (
                    not _is_number(duration)
                    or duration < 0
                ):

                    errors.append(
                        f"Invalid route duration "
                        f"on day {day_number}."
                    )

                elif duration > MAX_ROUTE_DURATION_MINUTES:

                    errors.append(
                        f"Unrealistic route duration "
                        f"on day {day_number}: "
                        f"{duration} minutes."
                    )

            # -----------------------------------------------
            # Individual travel segments
            # -----------------------------------------------

            segments = route_day.get(
                "travel_segments",
                []
            )

            for segment in segments:

                segment_distance = segment.get(
                    "distance_km"
                )

                segment_duration = segment.get(
                    "duration_minutes"
                )

                segment_from = segment.get(
                    "from",
                    "unknown"
                )

                segment_to = segment.get(
                    "to",
                    "unknown"
                )

                # -------------------------------------------
                # Segment distance
                # -------------------------------------------

                if segment_distance is not None:

                    if (
                        not _is_number(
                            segment_distance
                        )
                        or segment_distance < 0
                    ):

                        errors.append(
                            f"Invalid route segment "
                            f"distance: "
                            f"{segment_from} -> "
                            f"{segment_to}."
                        )

                    elif (
                        segment_distance
                        > MAX_ROUTE_DISTANCE_KM
                    ):

                        errors.append(
                            f"Unrealistic route segment: "
                            f"{segment_from} -> "
                            f"{segment_to} = "
                            f"{segment_distance} km."
                        )

                # -------------------------------------------
                # Segment duration
                # -------------------------------------------

                if segment_duration is not None:

                    if (
                        not _is_number(
                            segment_duration
                        )
                        or segment_duration < 0
                    ):

                        errors.append(
                            f"Invalid route segment "
                            f"duration: "
                            f"{segment_from} -> "
                            f"{segment_to}."
                        )

                    elif (
                        segment_duration
                        > MAX_ROUTE_DURATION_MINUTES
                    ):

                        errors.append(
                            f"Unrealistic route segment "
                            f"duration: "
                            f"{segment_from} -> "
                            f"{segment_to} = "
                            f"{segment_duration} minutes."
                        )

    # ========================================================
    # 14. FINAL RESULT
    # ========================================================

    return errors