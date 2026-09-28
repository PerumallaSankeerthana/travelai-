from __future__ import annotations

import re
from datetime import date
from typing import Any


# ============================================================
# BASIC HELPERS
# ============================================================

def _number(value: Any) -> float | None:
    """
    Convert values such as:

        5300
        "5300"
        "₹5,300"
        "₹21,201"
        "21,201"

    into numbers.
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text:
        return None

    # Remove currency symbols, commas and other characters.
    cleaned = re.sub(r"[^\d.]", "", text)

    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def _integer(value: Any) -> int:
    number = _number(value)

    if number is None:
        return 0

    return max(0, int(round(number)))


def _calculate_nights(start_date: str, end_date: str) -> int:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    nights = (end - start).days

    return max(0, nights)


# ============================================================
# HOTEL PRICE
# ============================================================

def _hotel_total(hotel: dict[str, Any], nights: int) -> int | None:
    """
    Prefer the provider's actual total stay price.

    Example:
        total_rate.extracted_lowest = 21201

    If unavailable, fall back to nightly price * nights.
    """

    raw = hotel.get("raw") or {}

    total_rate = raw.get("total_rate") or {}

    total = (
        total_rate.get("extracted_lowest")
        or total_rate.get("lowest")
    )

    total_number = _number(total)

    if total_number is not None:
        return _integer(total_number)

    # Fallback to nightly rate.
    nightly = hotel.get("price_per_night")

    if nightly is None:
        rate_per_night = raw.get("rate_per_night") or {}

        nightly = (
            rate_per_night.get("extracted_lowest")
            or rate_per_night.get("lowest")
        )

    nightly_number = _number(nightly)

    if nightly_number is None:
        return None

    if nights <= 0:
        return 0

    return _integer(nightly_number * nights)


# ============================================================
# FLIGHT PREPARATION
# ============================================================

def _prepare_flights(flights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Remove flights without usable prices and sort cheapest first.
    """

    prepared = []

    for flight in flights:
        price = _number(flight.get("price"))

        if price is None:
            continue

        if price < 0:
            continue

        item = dict(flight)
        item["_price"] = _integer(price)

        prepared.append(item)

    prepared.sort(
        key=lambda flight: (
            flight["_price"],
            flight.get("stops", 999),
            flight.get("duration_minutes", 999999),
        )
    )

    return prepared


# ============================================================
# HOTEL PREPARATION
# ============================================================

def _prepare_hotels(
    hotels: list[dict[str, Any]],
    nights: int,
) -> list[dict[str, Any]]:
    """
    Remove hotels without usable prices and calculate
    total stay price.
    """

    prepared = []

    for hotel in hotels:
        total = _hotel_total(hotel, nights)

        if total is None:
            continue

        if total < 0:
            continue

        item = dict(hotel)
        item["_total_price"] = total

        prepared.append(item)

    prepared.sort(
        key=lambda hotel: (
            hotel["_total_price"],
            -(float(hotel.get("rating") or 0)),
        )
    )

    return prepared


# ============================================================
# FLIGHT SELECTION
# ============================================================

def _select_cheapest_flight(
    flights: list[dict[str, Any]],
    total_budget: int,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Flight is mandatory.

    Always select the cheapest valid flight if it fits.

    If even the cheapest flight exceeds the entire budget,
    return a clear failure reason.
    """

    if not flights:
        return None, "no_valid_flight_results"

    cheapest = flights[0]

    if cheapest["_price"] > total_budget:
        return None, "cheapest_flight_exceeds_total_budget"

    return cheapest, None


# ============================================================
# HOTEL SELECTION
# ============================================================

def _select_cheapest_hotel(
    hotels: list[dict[str, Any]],
    remaining_budget: int,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Hotel is mandatory.

    Select the cheapest hotel that fits the remaining budget.
    """

    if not hotels:
        return None, "no_valid_hotel_results"

    for hotel in hotels:
        if hotel["_total_price"] <= remaining_budget:
            return hotel, None

    return None, "no_hotel_fits_after_flight"


# ============================================================
# FOOD ALLOCATION
# ============================================================

def _minimum_food_budget(
    travelers: int,
    nights: int,
) -> int:
    """
    Conservative minimum food allowance.

    This is intentionally modest because activities should
    receive whatever budget remains after mandatory costs.

    We use:
        ₹300 per traveler per day
    """

    days = max(1, nights + 1)

    return travelers * days * 300


# ============================================================
# ACTIVITY ALLOCATION
# ============================================================

def _activity_weight(preferences: list[str]) -> float:
    """
    Determine how much importance activities receive based
    on user preferences.

    This does NOT spend money by itself.
    It only influences distribution of leftover money.
    """

    if not preferences:
        return 1.0

    text = " ".join(
        str(preference).lower()
        for preference in preferences
    )

    activity_keywords = [
        "beach",
        "beaches",
        "nightlife",
        "adventure",
        "water sports",
        "sightseeing",
        "tour",
        "museum",
        "food",
        "local food",
    ]

    matches = sum(
        1
        for keyword in activity_keywords
        if keyword in text
    )

    return 1.0 + min(matches * 0.15, 0.75)


# ============================================================
# MAIN ALLOCATOR
# ============================================================

def allocate_budget(
    total_budget: int,
    travelers: int,
    start_date: str,
    end_date: str,
    preferences: list[str],
    flights: list[dict[str, Any]],
    hotels: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Smart budget allocator.

    Priority:

        1. Flight
        2. Hotel
        3. Food
        4. Activities
        5. Buffer

    Mandatory costs are never sacrificed for optional costs.

    The function never allows allocated_total to exceed
    total_budget.
    """

    total_budget = _integer(total_budget)
    travelers = max(1, _integer(travelers))

    nights = _calculate_nights(
        start_date,
        end_date,
    )

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    if total_budget <= 0:
        return {
            "status": "budget_insufficient",
            "reason": "invalid_budget",
            "message": "Total budget must be greater than zero.",
            "total_budget": total_budget,
        }

    if nights <= 0:
        return {
            "status": "budget_insufficient",
            "reason": "invalid_trip_dates",
            "message": "Trip must contain at least one hotel night.",
            "total_budget": total_budget,
        }

    # --------------------------------------------------------
    # PREPARE PROVIDER DATA
    # --------------------------------------------------------

    prepared_flights = _prepare_flights(flights)

    prepared_hotels = _prepare_hotels(
        hotels,
        nights,
    )

    # --------------------------------------------------------
    # STEP 1 — MANDATORY FLIGHT
    # --------------------------------------------------------

    selected_flight, flight_error = _select_cheapest_flight(
        prepared_flights,
        total_budget,
    )

    if selected_flight is None:

        cheapest_price = None

        if prepared_flights:
            cheapest_price = prepared_flights[0]["_price"]

        return {
            "status": "budget_insufficient",
            "reason": flight_error,
            "message": (
                "No flight can be selected within the total "
                "trip budget."
            ),
            "total_budget": total_budget,
            "travelers": travelers,
            "nights": nights,
            "selected_flight": None,
            "selected_hotel": None,
            "cheapest_flight_price": cheapest_price,
            "allocation": {
                "flights": 0,
                "hotel": 0,
                "food": 0,
                "activities": 0,
                "buffer": 0,
            },
            "allocated_total": 0,
            "remaining_budget": total_budget,
            "preferences": preferences,
        }

    flight_cost = selected_flight["_price"]

    # --------------------------------------------------------
    # STEP 2 — REMAINING AFTER FLIGHT
    # --------------------------------------------------------

    remaining_after_flight = (
        total_budget - flight_cost
    )

    # --------------------------------------------------------
    # STEP 3 — MANDATORY HOTEL
    # --------------------------------------------------------

    selected_hotel, hotel_error = _select_cheapest_hotel(
        prepared_hotels,
        remaining_after_flight,
    )

    if selected_hotel is None:

        cheapest_hotel_price = None

        if prepared_hotels:
            cheapest_hotel_price = (
                prepared_hotels[0]["_total_price"]
            )

        return {
            "status": "budget_insufficient",
            "reason": hotel_error,
            "message": (
                "The cheapest available hotel cannot fit "
                "after selecting the mandatory flight."
            ),
            "total_budget": total_budget,
            "travelers": travelers,
            "nights": nights,
            "selected_flight": selected_flight,
            "selected_hotel": None,
            "cheapest_hotel_price": cheapest_hotel_price,
            "allocation": {
                "flights": flight_cost,
                "hotel": 0,
                "food": 0,
                "activities": 0,
                "buffer": 0,
            },
            "allocated_total": flight_cost,
            "remaining_budget": remaining_after_flight,
            "preferences": preferences,
        }

    hotel_cost = selected_hotel["_total_price"]

    # --------------------------------------------------------
    # STEP 4 — REMAINING AFTER MANDATORY COSTS
    # --------------------------------------------------------

    remaining_after_mandatory = (
        total_budget
        - flight_cost
        - hotel_cost
    )

    # --------------------------------------------------------
    # STEP 5 — FOOD
    # --------------------------------------------------------

    minimum_food = _minimum_food_budget(
        travelers,
        nights,
    )

    # Food is required, but if budget is extremely tight,
    # activities will be sacrificed first.
    food_budget = min(
        minimum_food,
        remaining_after_mandatory,
    )

    remaining_after_food = (
        remaining_after_mandatory
        - food_budget
    )

    # --------------------------------------------------------
    # STEP 6 — ACTIVITIES
    # --------------------------------------------------------

    activity_weight = _activity_weight(
        preferences
    )

    # We use all remaining money for activities initially.
    # Buffer is created only from genuinely unused money.
    activity_budget = int(
        remaining_after_food * activity_weight
    )

    activity_budget = min(
        activity_budget,
        remaining_after_food,
    )

    # --------------------------------------------------------
    # STEP 7 — BUFFER
    # --------------------------------------------------------

    buffer_budget = (
        remaining_after_food
        - activity_budget
    )

    # --------------------------------------------------------
    # FINAL SAFETY CALCULATION
    # --------------------------------------------------------

    allocated_total = (
        flight_cost
        + hotel_cost
        + food_budget
        + activity_budget
        + buffer_budget
    )

    # This should mathematically equal total_budget.
    # But enforce the invariant anyway.

    if allocated_total > total_budget:

        overflow = allocated_total - total_budget

        # Remove overflow from buffer first.
        reduction = min(
            overflow,
            buffer_budget,
        )

        buffer_budget -= reduction
        overflow -= reduction

        # Then activities.
        if overflow > 0:

            reduction = min(
                overflow,
                activity_budget,
            )

            activity_budget -= reduction
            overflow -= reduction

        # Finally food, only if absolutely necessary.
        if overflow > 0:

            reduction = min(
                overflow,
                food_budget,
            )

            food_budget -= reduction
            overflow -= reduction

        allocated_total = (
            flight_cost
            + hotel_cost
            + food_budget
            + activity_budget
            + buffer_budget
        )

    # --------------------------------------------------------
    # FINAL REMAINING
    # --------------------------------------------------------

    remaining_budget = max(
        0,
        total_budget - allocated_total,
    )

    # --------------------------------------------------------
    # REMOVE INTERNAL FIELDS FROM PROVIDER OBJECTS
    # --------------------------------------------------------

    clean_flight = dict(selected_flight)
    clean_flight.pop("_price", None)

    clean_hotel = dict(selected_hotel)
    clean_hotel.pop("_total_price", None)

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    result = {
        "status": "allocated",
        "total_budget": total_budget,
        "travelers": travelers,
        "nights": nights,

        "selected_flight": clean_flight,
        "selected_hotel": clean_hotel,

        "allocation": {
            "flights": flight_cost,
            "hotel": hotel_cost,
            "food": food_budget,
            "activities": activity_budget,
            "buffer": buffer_budget,
        },

        "allocated_total": allocated_total,

        "remaining_budget": remaining_budget,

        "preferences": preferences,

        "planning_rules": {
            "flight_required": True,
            "hotel_required": True,
            "food_required": True,
            "activities_flexible": True,
            "buffer_optional": True,
        },
    }

    # --------------------------------------------------------
    # HARD INVARIANTS
    # --------------------------------------------------------

    if result["allocated_total"] > total_budget:
        raise RuntimeError(
            "Budget allocator invariant violated: "
            "allocated_total exceeds total_budget."
        )

    if result["selected_flight"] is None:
        raise RuntimeError(
            "Budget allocator invariant violated: "
            "successful allocation has no flight."
        )

    if result["selected_hotel"] is None:
        raise RuntimeError(
            "Budget allocator invariant violated: "
            "successful allocation has no hotel."
        )

    return result