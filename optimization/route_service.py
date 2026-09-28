# optimization/route_service.py

from __future__ import annotations

from typing import Any

from integrations.mapbox import (
    geocode_location,
    search_poi,
    get_route_matrix,
    is_near_destination,
    MAX_DISTANCE_FROM_DESTINATION_KM,
)

from optimization.route_optimizer import (
    optimize_activity_order,
)


SLOTS = [
    "morning",
    "afternoon",
    "evening",
]


# ============================================================
# RESOLVE ACTIVITY LOCATION
# ============================================================

def _resolve_activity_location(
    activity: dict[str, Any],
    destination: str,
    destination_coordinates: tuple[float, float] | None,
) -> dict[str, Any] | None:

    location = activity.get("location")

    if not location:
        return None

    def _accept_if_near_destination(
        longitude: float,
        latitude: float,
        source: str,
    ) -> dict[str, Any] | None:

        if not is_near_destination(
            longitude=longitude,
            latitude=latitude,
            destination_coordinates=destination_coordinates,
        ):
            print(
                f"WARNING: Rejecting {source} location "
                f"'{location}' because it is outside the "
                f"{MAX_DISTANCE_FROM_DESTINATION_KM:.0f} km "
                f"destination radius."
            )
            return None

        resolved = dict(activity)

        resolved["_longitude"] = longitude
        resolved["_latitude"] = latitude

        return resolved

    # --------------------------------------------------------
    # First attempt: POI search
    # --------------------------------------------------------

    try:

        longitude, latitude = search_poi(
            location=location,
            destination=destination,
            destination_coordinates=destination_coordinates,
            activity=activity.get("activity"),
        )

        resolved = _accept_if_near_destination(
            longitude,
            latitude,
            "POI",
        )

        if resolved is not None:
            return resolved

    except Exception as exc:

        print(
            f"WARNING: Could not resolve "
            f"'{location}' through POI search: {exc}"
        )

    # --------------------------------------------------------
    # Second attempt: normal geocoding
    # --------------------------------------------------------

    try:

        longitude, latitude = geocode_location(
            location=location,
            destination=destination,
            destination_coordinates=destination_coordinates,
        )

        resolved = _accept_if_near_destination(
            longitude,
            latitude,
            "geocoded",
        )

        if resolved is not None:
            return resolved

    except Exception as fallback_exc:

        print(
            f"WARNING: Skipping unresolved "
            f"location '{location}': "
            f"{fallback_exc}"
        )

    return None


# ============================================================
# COLLECT ACTIVITIES
# ============================================================

def _collect_day_activities(
    day: dict[str, Any],
    destination: str,
    destination_coordinates: tuple[float, float] | None,
) -> list[dict[str, Any]]:

    activities = []

    for slot in SLOTS:

        slot_activities = (
            day.get("slots", {})
            .get(slot, [])
        )

        # Support alternate itinerary format.
        if not slot_activities:
            slot_activities = day.get(
                slot,
                []
            )

        for activity in slot_activities:

            resolved = _resolve_activity_location(
                activity=activity,
                destination=destination,
                destination_coordinates=destination_coordinates,
            )

            if resolved is None:
                continue

            resolved["_slot"] = slot

            activities.append(resolved)

    return activities


# ============================================================
# BUILD MAPBOX DISTANCE MATRIX
# ============================================================

def _build_distance_matrix(
    activities: list[dict[str, Any]],
) -> list[list[float]]:

    if not activities:
        return []

    coordinates = [
        (
            activity["_longitude"],
            activity["_latitude"],
        )
        for activity in activities
    ]

    try:

        matrix_data = get_route_matrix(
            coordinates
        )

        distances = matrix_data.get(
            "distances",
            []
        )

        size = len(activities)

        matrix = []

        for i in range(size):

            row = []

            for j in range(size):

                try:
                    value = distances[i][j]

                    if value is None:
                        value = 10**9

                    row.append(
                        float(value)
                    )

                except (
                    IndexError,
                    TypeError,
                    ValueError,
                ):

                    row.append(
                        float(10**9)
                    )

            matrix.append(row)

        return matrix

    except Exception as exc:

        print(
            f"WARNING: Could not build "
            f"Mapbox distance matrix: {exc}"
        )

        size = len(activities)

        return [
            [
                0.0 if i == j else 10**9
                for j in range(size)
            ]
            for i in range(size)
        ]


# ============================================================
# OR-TOOLS ROUTE ORDERING
# ============================================================

def _optimize_with_or_tools(
    activities: list[dict[str, Any]],
    distance_matrix: list[list[float]],
) -> list[dict[str, Any]]:

    if len(activities) <= 1:
        return activities

    try:

        optimized = optimize_activity_order(
            activities=activities,
            distance_matrix=distance_matrix,
        )

        if optimized:

            print(
                "\nOR-TOOLS ROUTE ORDER:"
            )

            for index, activity in enumerate(
                optimized,
                start=1,
            ):

                print(
                    f"  {index}. "
                    f"{activity.get('location')} "
                    f"[{activity.get('_slot')}]"
                )

            return optimized

    except Exception as exc:

        print(
            f"WARNING: OR-Tools optimization "
            f"failed: {exc}"
        )

    return activities


# ============================================================
# CALCULATE FINAL ROUTE
# ============================================================

def _calculate_consecutive_travel(
    activities: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    float,
    float,
]:

    if len(activities) < 2:

        return (
            [],
            0.0,
            0.0,
        )

    coordinates = [
        (
            activity["_longitude"],
            activity["_latitude"],
        )
        for activity in activities
    ]

    try:

        matrix = get_route_matrix(
            coordinates
        )

    except Exception as exc:

        print(
            f"WARNING: Final Mapbox route "
            f"calculation failed: {exc}"
        )

        return (
            [],
            0.0,
            0.0,
        )

    distances = matrix.get(
        "distances",
        []
    )

    durations = matrix.get(
        "durations",
        []
    )

    segments = []

    total_distance_km = 0.0
    total_travel_minutes = 0.0

    for index in range(
        len(activities) - 1
    ):

        from_activity = activities[index]
        to_activity = activities[index + 1]

        try:

            distance_meters = distances[
                index
            ][
                index + 1
            ]

        except (
            IndexError,
            TypeError,
        ):

            distance_meters = None

        try:

            duration_seconds = durations[
                index
            ][
                index + 1
            ]

        except (
            IndexError,
            TypeError,
        ):

            duration_seconds = None

        if (
            distance_meters is None
            or duration_seconds is None
        ):

            print(
                "WARNING: Mapbox could not "
                "calculate route: "
                f"{from_activity.get('location')} "
                "-> "
                f"{to_activity.get('location')}"
            )

            continue

        try:

            distance_km = (
                float(distance_meters)
                / 1000.0
            )

            duration_minutes = (
                float(duration_seconds)
                / 60.0
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        segments.append(
            {
                "from": from_activity.get(
                    "location"
                ),
                "to": to_activity.get(
                    "location"
                ),
                "distance_km": round(
                    distance_km,
                    2,
                ),
                "duration_minutes": round(
                    duration_minutes,
                    1,
                ),
            }
        )

        total_distance_km += distance_km
        total_travel_minutes += (
            duration_minutes
        )

    return (
        segments,
        round(
            total_distance_km,
            2,
        ),
        round(
            total_travel_minutes,
            1,
        ),
    )


# ============================================================
# OPTIMIZE ONE DAY
# ============================================================

def optimize_day_route(
    day: dict[str, Any],
    destination: str,
    destination_coordinates: tuple[float, float] | None,
) -> dict[str, Any]:

    activities = _collect_day_activities(
        day=day,
        destination=destination,
        destination_coordinates=destination_coordinates,
    )

    if not activities:

        return {
            "day_number": day.get(
                "day_number"
            ),
            "date": day.get(
                "date"
            ),
            "activities": [],
            "travel_segments": [],
            "total_distance_km": 0.0,
            "total_travel_minutes": 0.0,
        }

    # --------------------------------------------------------
    # Build Mapbox matrix.
    # --------------------------------------------------------

    distance_matrix = (
        _build_distance_matrix(
            activities
        )
    )

    # --------------------------------------------------------
    # OR-Tools optimization.
    #
    # It optimizes activities within the same time slot.
    # Morning/afternoon/evening ordering is preserved.
    # --------------------------------------------------------

    optimized_activities = (
        _optimize_with_or_tools(
            activities=activities,
            distance_matrix=distance_matrix,
        )
    )

    # --------------------------------------------------------
    # Calculate actual final route using Mapbox.
    # --------------------------------------------------------

    (
        travel_segments,
        total_distance_km,
        total_travel_minutes,
    ) = _calculate_consecutive_travel(
        optimized_activities
    )

    return {
        "day_number": day.get(
            "day_number"
        ),
        "date": day.get(
            "date"
        ),
        "activities": optimized_activities,
        "travel_segments": travel_segments,
        "total_distance_km": total_distance_km,
        "total_travel_minutes": total_travel_minutes,
    }


# ============================================================
# COMPLETE ITINERARY
# ============================================================

def optimize_itinerary_routes(
    itinerary: dict[str, Any],
    destination: str,
) -> dict[str, Any]:

    if not itinerary:

        raise RuntimeError(
            "Cannot optimize an empty itinerary."
        )

    destination_coordinates = None

    try:

        destination_coordinates = (
            geocode_location(
                location=destination,
                destination=destination,
            )
        )

    except Exception as exc:

        print(
            f"WARNING: Could not geocode "
            f"destination '{destination}': "
            f"{exc}"
        )

    days = itinerary.get(
        "days",
        []
    )

    optimized_days = []

    for day in days:

        optimized_day = (
            optimize_day_route(
                day=day,
                destination=destination,
                destination_coordinates=destination_coordinates,
            )
        )

        optimized_days.append(
            optimized_day
        )

    return {
        "days": optimized_days
    }