from __future__ import annotations

import math
from typing import Any

import requests

from backend.core.config import settings


GEOCODING_URL = "https://api.mapbox.com/search/geocode/v6/forward"
SEARCHBOX_URL = "https://api.mapbox.com/search/searchbox/v1/forward"
MATRIX_URL = "https://api.mapbox.com/directions-matrix/v1/mapbox/driving"

# Maximum allowed distance between a resolved activity location
# and the main trip destination.
#
# This prevents Mapbox from returning a completely unrelated
# location in another city/state/country.
MAX_DISTANCE_FROM_DESTINATION_KM = 100.0


# ============================================================
# BASIC HELPERS
# ============================================================

def _token() -> str:
    token = settings.mapbox_access_token

    if not token:
        raise RuntimeError(
            "MAPBOX_ACCESS_TOKEN is not configured."
        )

    return token


def _normalize(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(
        value.lower()
        .replace(",", " ")
        .replace("(", " ")
        .replace(")", " ")
        .split()
    )


def _coordinates(
    feature: dict[str, Any],
) -> tuple[float, float]:

    coords = (
        feature
        .get("geometry", {})
        .get("coordinates")
    )

    if not coords or len(coords) < 2:
        raise RuntimeError(
            "Mapbox result has no valid coordinates."
        )

    return float(coords[0]), float(coords[1])


def _distance_km(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
) -> float:

    radius = 6371.0

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1)
        * math.cos(p2)
        * math.sin(dl / 2) ** 2
    )

    return 2 * radius * math.asin(
        math.sqrt(a)
    )


# ============================================================
# DESTINATION DISTANCE GUARD
# ============================================================

def is_near_destination(
    longitude: float,
    latitude: float,
    destination_coordinates: tuple[float, float] | None,
    max_km: float = MAX_DISTANCE_FROM_DESTINATION_KM,
) -> bool:
    """
    Return True only when the resolved location is reasonably
    close to the trip destination.

    If destination coordinates are unavailable, fail closed.
    We do NOT trust an unverified Mapbox coordinate.
    """

    if not destination_coordinates:
        return False

    distance = _distance_km(
        destination_coordinates[0],
        destination_coordinates[1],
        longitude,
        latitude,
    )

    return distance <= max_km


def _filter_near_destination(
    features: list[dict[str, Any]],
    destination_coordinates: tuple[float, float] | None,
    location: str,
) -> list[dict[str, Any]]:
    """
    Remove Mapbox results that are too far away from the
    destination.

    Example:
        Trip destination = Hyderabad

        Mapbox result = Maharashtra

        Result is rejected instead of being sent to the
        route optimizer.
    """

    if not destination_coordinates:
        print(
            f"WARNING: No destination coordinates available "
            f"while resolving '{location}'. "
            f"Rejecting Mapbox results."
        )
        return []

    kept: list[dict[str, Any]] = []

    for feature in features:

        try:
            longitude, latitude = _coordinates(feature)
        except Exception:
            continue

        distance = _distance_km(
            destination_coordinates[0],
            destination_coordinates[1],
            longitude,
            latitude,
        )

        if distance <= MAX_DISTANCE_FROM_DESTINATION_KM:

            kept.append(feature)

        else:

            properties = feature.get(
                "properties",
                {},
            )

            name = (
                properties.get("name")
                or properties.get("name_preferred")
                or "unknown"
            )

            print(
                f"Rejected Mapbox result for '{location}': "
                f"'{name}' is {distance:.0f} km from destination "
                f"(max "
                f"{MAX_DISTANCE_FROM_DESTINATION_KM:.0f} km)."
            )

    return kept


# ============================================================
# DESTINATION GEOCODING
# ============================================================

def geocode_location(
    location: str,
    destination: str | None = None,
    destination_coordinates: tuple[float, float] | None = None,
) -> tuple[float, float]:
    """
    Geocode a broad geographic location.

    Examples:
        Goa
        Hyderabad
        Paris
        Dubai
        London
    """

    token = _token()

    location = location.strip()

    if not location:
        raise RuntimeError(
            "Cannot geocode empty location."
        )

    params = {
        "q": location,
        "access_token": token,
        "limit": 10,
        "autocomplete": "false",
    }

    if destination_coordinates:
        params["proximity"] = (
            f"{destination_coordinates[0]},"
            f"{destination_coordinates[1]}"
        )

    response = requests.get(
        GEOCODING_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    features = data.get(
        "features",
        [],
    )

    if not features:
        raise RuntimeError(
            f"Mapbox could not geocode '{location}'."
        )

    # --------------------------------------------------------
    # SAFETY FILTER
    # --------------------------------------------------------
    #
    # Mapbox can sometimes return a result with a strong
    # textual match but completely wrong coordinates.
    #
    # Example:
    #   "Charminar & Nimrah Cafe"
    #
    # could potentially resolve to a location hundreds of
    # kilometres away.
    #
    # Never allow such a result into the route optimizer.
    # --------------------------------------------------------

    features = _filter_near_destination(
        features,
        destination_coordinates,
        location,
    )

    if not features:
        raise RuntimeError(
            f"No geocoding result for '{location}' within "
            f"{MAX_DISTANCE_FROM_DESTINATION_KM:.0f} km "
            f"of the destination."
        )

    query = _normalize(location)

    best_feature = None
    best_score = float("-inf")

    # Broad geographic types.
    preferred_types = {
        "place": 100,
        "locality": 95,
        "neighborhood": 90,
        "district": 85,
        "region": 70,
        "country": 60,
        "postcode": 50,
        "address": 40,
        "street": 30,
    }

    for feature in features:

        props = feature.get(
            "properties",
            {},
        )

        feature_type = props.get(
            "feature_type",
            "",
        )

        name = _normalize(
            props.get("name")
            or props.get("name_preferred")
        )

        full_address = _normalize(
            props.get("full_address")
            or props.get("place_formatted")
        )

        score = 0

        # Exact name is strongest.
        if name == query:
            score += 1000

        elif query in name:
            score += 500

        elif name and name in query:
            score += 250

        # Exact full address.
        if full_address == query:
            score += 700

        elif query in full_address:
            score += 200

        # Prefer broad geographic feature types.
        score += preferred_types.get(
            feature_type,
            0,
        )

        # Proximity is a secondary signal.
        if destination_coordinates:

            try:

                lon, lat = _coordinates(feature)

                distance = _distance_km(
                    destination_coordinates[0],
                    destination_coordinates[1],
                    lon,
                    lat,
                )

                score += max(
                    0,
                    20 - distance,
                )

            except Exception:
                pass

        if score > best_score:

            best_score = score
            best_feature = feature

    if best_feature is None:
        raise RuntimeError(
            f"Could not select Mapbox result for '{location}'."
        )

    lon, lat = _coordinates(
        best_feature
    )

    # Final safety check.
    if not is_near_destination(
        lon,
        lat,
        destination_coordinates,
    ):
        raise RuntimeError(
            f"Mapbox selected an unsafe location for "
            f"'{location}'. The result is outside the allowed "
            f"{MAX_DISTANCE_FROM_DESTINATION_KM:.0f} km radius."
        )

    print(
        f"Mapbox geocoded: "
        f"{location} -> ({lon}, {lat})"
    )

    return lon, lat


# ============================================================
# POI SEARCH
# ============================================================

def search_poi(
    location: str,
    destination: str,
    destination_coordinates: tuple[float, float] | None = None,
    activity: str | None = None,
) -> tuple[float, float]:
    """
    Search for a real activity/location.

    Uses Mapbox Search Box because Search Box supports POIs.
    """

    token = _token()

    location = location.strip()
    destination = destination.strip()

    if not location:
        raise RuntimeError(
            "Cannot search an empty location."
        )

    # --------------------------------------------------------
    # Query 1: exact location + destination
    # --------------------------------------------------------

    queries = [
        f"{location}, {destination}",
        location,
    ]

    all_features: list[dict[str, Any]] = []

    for query in queries:

        params = {
            "q": query,
            "access_token": token,
            "limit": 10,
            "language": "en",
        }

        if destination_coordinates:
            params["proximity"] = (
                f"{destination_coordinates[0]},"
                f"{destination_coordinates[1]}"
            )

        response = requests.get(
            SEARCHBOX_URL,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        features = data.get(
            "features",
            [],
        )

        all_features.extend(features)

        # Exact POI found — we can stop.
        exact_poi = False

        location_normalized = _normalize(
            location
        )

        for feature in features:

            props = feature.get(
                "properties",
                {},
            )

            feature_type = props.get(
                "feature_type",
                "",
            )

            name = _normalize(
                props.get("name")
            )

            if (
                feature_type == "poi"
                and (
                    name == location_normalized
                    or location_normalized in name
                    or name in location_normalized
                )
            ):
                exact_poi = True
                break

        if exact_poi:
            break

    # --------------------------------------------------------
    # Remove duplicate Mapbox IDs.
    # --------------------------------------------------------

    unique_features: dict[str, dict[str, Any]] = {}

    for feature in all_features:

        props = feature.get(
            "properties",
            {},
        )

        mapbox_id = props.get(
            "mapbox_id"
        )

        if mapbox_id:
            unique_features[mapbox_id] = feature

    features = list(
        unique_features.values()
    )

    # --------------------------------------------------------
    # SAFETY FILTER
    # --------------------------------------------------------

    features = _filter_near_destination(
        features,
        destination_coordinates,
        location,
    )

    # --------------------------------------------------------
    # No Search Box result.
    # --------------------------------------------------------

    if not features:

        print(
            f"No valid Search Box result for "
            f"'{location}' within "
            f"{MAX_DISTANCE_FROM_DESTINATION_KM:.0f} km "
            f"of {destination}. "
            f"Using normal geocoding."
        )

        return geocode_location(
            location=location,
            destination=destination,
            destination_coordinates=destination_coordinates,
        )

    query_normalized = _normalize(
        location
    )

    activity_normalized = _normalize(
        activity or ""
    )

    best_feature = None
    best_score = float("-inf")

    for feature in features:

        props = feature.get(
            "properties",
            {},
        )

        feature_type = props.get(
            "feature_type",
            "",
        )

        name = _normalize(
            props.get("name")
        )

        preferred_name = _normalize(
            props.get("name_preferred")
        )

        full_address = _normalize(
            props.get("full_address")
        )

        place_formatted = _normalize(
            props.get("place_formatted")
        )

        score = 0

        # ====================================================
        # NAME MATCHING
        # ====================================================

        if name == query_normalized:
            score += 2000

        elif preferred_name == query_normalized:
            score += 1800

        elif query_normalized in name:
            score += 1000

        elif query_normalized in preferred_name:
            score += 900

        elif name in query_normalized:
            score += 500

        # ====================================================
        # POI TYPE
        # ====================================================

        if feature_type == "poi":
            score += 500

        # Do NOT automatically trust hotels/vacation rentals
        # when searching for a tourist location.
        if feature_type in {
            "address",
            "street",
            "building",
        }:
            score -= 300

        # ====================================================
        # ADDRESS CONTEXT
        # ====================================================

        if query_normalized in full_address:
            score += 300

        if query_normalized in place_formatted:
            score += 150

        # ====================================================
        # ACTIVITY CONTEXT
        # ====================================================

        activity_words = [
            word
            for word in activity_normalized.split()
            if len(word) >= 4
        ]

        for word in activity_words:

            if word in name:
                score += 20

            if word in full_address:
                score += 10

        # ====================================================
        # PROXIMITY
        # ====================================================

        if destination_coordinates:

            try:

                lon, lat = _coordinates(
                    feature
                )

                distance = _distance_km(
                    destination_coordinates[0],
                    destination_coordinates[1],
                    lon,
                    lat,
                )

                # Small bonus only.
                # Name matching remains much stronger.
                score += max(
                    0,
                    30 - min(
                        distance * 2,
                        30,
                    ),
                )

            except Exception:
                pass

        if score > best_score:

            best_score = score
            best_feature = feature

    # --------------------------------------------------------
    # Selected result
    # --------------------------------------------------------

    if best_feature is None:

        return geocode_location(
            location=location,
            destination=destination,
            destination_coordinates=destination_coordinates,
        )

    props = best_feature.get(
        "properties",
        {},
    )

    feature_type = props.get(
        "feature_type",
        "",
    )

    selected_name = (
        props.get("name")
        or props.get("name_preferred")
        or "unknown"
    )

    lon, lat = _coordinates(
        best_feature
    )

    # --------------------------------------------------------
    # FINAL DESTINATION SAFETY CHECK
    # --------------------------------------------------------

    if not is_near_destination(
        lon,
        lat,
        destination_coordinates,
    ):
        raise RuntimeError(
            f"Selected Mapbox POI '{selected_name}' "
            f"for '{location}' is outside the allowed "
            f"{MAX_DISTANCE_FROM_DESTINATION_KM:.0f} km "
            f"destination radius."
        )

    print(
        f"Mapbox POI search: "
        f"{location}, {destination} "
        f"-> {selected_name} "
        f"({lon}, {lat})"
    )

    # ========================================================
    # STRICT VALIDATION
    # ========================================================

    selected_name_normalized = _normalize(
        selected_name
    )

    meaningful_name_match = (
        selected_name_normalized
        == query_normalized
        or query_normalized
        in selected_name_normalized
        or selected_name_normalized
        in query_normalized
    )

    # A genuine POI with a strong textual match is accepted.
    if (
        feature_type == "poi"
        and meaningful_name_match
    ):
        return lon, lat

    # A broad geographic location can legitimately be a
    # locality/place rather than a POI.
    geographic_types = {
        "place",
        "city",
        "locality",
        "neighborhood",
        "district",
        "region",
    }

    if (
        feature_type in geographic_types
        and meaningful_name_match
    ):
        return lon, lat

    # Otherwise, use Geocoding API rather than accepting
    # an unrelated hotel/address.
    print(
        f"Weak POI match for '{location}'. "
        f"Using Geocoding fallback."
    )

    return geocode_location(
        location=location,
        destination=destination,
        destination_coordinates=destination_coordinates,
    )


# ============================================================
# ROUTE MATRIX
# ============================================================

def get_route_matrix(
    coordinates: list[tuple[float, float]],
) -> dict[str, Any]:
    """
    Calculate road distance and driving time between
    all supplied coordinates.
    """

    token = _token()

    if len(coordinates) < 2:
        return {
            "durations": [],
            "distances": [],
        }

    coordinate_string = ";".join(
        f"{lon},{lat}"
        for lon, lat in coordinates
    )

    url = (
        f"{MATRIX_URL}/"
        f"{coordinate_string}"
    )

    params = {
        "access_token": token,
        "annotations": "duration,distance",
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("code") != "Ok":
        raise RuntimeError(
            f"Mapbox Matrix API failed: {data}"
        )

    return {
        "durations": data.get(
            "durations",
            [],
        ),
        "distances": data.get(
            "distances",
            [],
        ),
    }