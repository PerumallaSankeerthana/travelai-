import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.redis import (
    get_trip_state,
    save_trip_state,
)
from models.trip import Trip
from schemas.trip import (
    TripCreateRequest,
    TripCreateResponse,
    ReplanRequest,
    ReplanResponse,
)

from ai.graph.workflow import build_travel_graph
from ai.agents.itinerary_agent import replan_itinerary
from verification.validator import validate_trip_state


router = APIRouter(
    prefix="/api/trips",
    tags=["Trips"],
)

security = HTTPBearer()


# ============================================================
# AUTHENTICATION
# ============================================================

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        return int(user_id)

    except (JWTError, ValueError):

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ============================================================
# CREATE TRIP
# ============================================================

@router.post(
    "",
    response_model=TripCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_trip(
    request: TripCreateRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):

    # --------------------------------------------------------
    # 1. CREATE DATABASE TRIP
    # --------------------------------------------------------

    trip_id = f"trip_{uuid.uuid4().hex[:12]}"

    trip = Trip(
        trip_id=trip_id,
        user_id=user_id,
        destination=request.destination,
        start_date=request.start_date,
        end_date=request.end_date,
        travelers=request.travelers,
        budget=request.budget,
        preferences=json.dumps(
            request.preferences
        ),
        status="created",
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    # --------------------------------------------------------
    # 2. CREATE NATURAL-LANGUAGE REQUEST
    # --------------------------------------------------------

    preferences_text = (
        ", ".join(request.preferences)
        if request.preferences
        else "no specific preferences"
    )

    user_message = (
        f"Plan a trip to {request.destination} "
        f"from {request.start_date} to {request.end_date} "
        f"for {request.travelers} travelers "
        f"with a budget of {request.budget} INR. "
        f"My preferences are: {preferences_text}."
    )

    initial_state = {
        "user_id": user_id,
        "trip_id": trip_id,
        "user_message": user_message,
    }

    # --------------------------------------------------------
    # 3. RUN LANGGRAPH
    # --------------------------------------------------------

    try:

        graph = build_travel_graph()

        result = graph.invoke(
            initial_state
        )

    except Exception as exc:

        trip.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trip planning failed: {str(exc)}",
        )

    # --------------------------------------------------------
    # 4. SAVE WORKFLOW STATE TO REDIS
    # --------------------------------------------------------

    try:

        save_trip_state(
            trip_id=trip_id,
            state=result,
        )

    except Exception as exc:

        trip.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save trip state: {str(exc)}",
        )

    # --------------------------------------------------------
    # 5. UPDATE DATABASE STATUS
    # --------------------------------------------------------

    workflow_status = result.get(
        "status",
        "completed",
    )

    trip.status = workflow_status

    db.commit()

    # --------------------------------------------------------
    # 6. BUILD RESPONSE
    # --------------------------------------------------------

    itinerary = result.get(
        "itinerary",
        {},
    )

    flights = result.get(
        "flights",
        [],
    )

    hotels = result.get(
        "hotels",
        [],
    )

    cost_breakdown = result.get(
        "cost_breakdown",
        result.get(
            "budget_allocation",
            {},
        ),
    )

    return TripCreateResponse(
        trip_id=trip_id,
        status=workflow_status,
        itinerary=itinerary,
        flights=flights,
        hotels=hotels,
        cost_breakdown=cost_breakdown,
    )


# ============================================================
# REPLAN TRIP
# ============================================================

@router.post(
    "/{trip_id}/replan",
    response_model=ReplanResponse,
)
def replan_trip(
    trip_id: str,
    request: ReplanRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):

    # --------------------------------------------------------
    # 1. FIND TRIP
    # --------------------------------------------------------

    trip = (
        db.query(Trip)
        .filter(
            Trip.trip_id == trip_id
        )
        .first()
    )

    if trip is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    # --------------------------------------------------------
    # 2. CHECK OWNERSHIP
    # --------------------------------------------------------

    if trip.user_id != user_id:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this trip",
        )

    # --------------------------------------------------------
    # 3. LOAD TRIP STATE FROM REDIS
    # --------------------------------------------------------

    state = get_trip_state(
        trip_id
    )

    if state is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Active trip state was not found in Redis"
            ),
        )

    # --------------------------------------------------------
    # 4. CHECK EXISTING ITINERARY
    # --------------------------------------------------------

    itinerary = state.get(
        "itinerary"
    )

    if not itinerary:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Trip does not contain an existing itinerary"
            ),
        )

    existing_days = itinerary.get(
        "days",
        [],
    )

    if not existing_days:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Trip itinerary contains no days"
            ),
        )

    existing_day_numbers = {
        day.get("day_number")
        for day in existing_days
    }

    # --------------------------------------------------------
    # 5. VALIDATE AFFECTED DAYS
    # --------------------------------------------------------

    affected_days = sorted(
        set(
            request.affected_days
        )
    )

    invalid_days = [
        day
        for day in affected_days
        if day not in existing_day_numbers
    ]

    if invalid_days:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid affected day",
                "invalid_days": invalid_days,
                "available_days": sorted(
                    existing_day_numbers
                ),
            },
        )

    # --------------------------------------------------------
    # 6. DETERMINE LOCKED DAYS
    # --------------------------------------------------------
    #
    # Earlier days remain locked when a later day is replanned.
    #
    # Example:
    #
    # affected_days = [3]
    #
    # Day 1 -> locked
    # Day 2 -> locked
    # Day 3 -> replanned
    # Day 4 -> unchanged
    # Day 5 -> unchanged
    #
    # --------------------------------------------------------

    earliest_affected_day = min(
        affected_days
    )

    locked_days = sorted(
        day
        for day in existing_day_numbers
        if day < earliest_affected_day
    )

    # --------------------------------------------------------
    # 7. RUN PARTIAL REPLANNING
    # --------------------------------------------------------

    try:

        updated_itinerary = replan_itinerary(
            state=state,
            affected_days=affected_days,
            message=request.message,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Replanning failed: {str(exc)}",
        )

    # --------------------------------------------------------
    # 8. UPDATE STATE
    # --------------------------------------------------------

    updated_state = dict(
        state
    )

    updated_state["itinerary"] = (
        updated_itinerary
    )

    updated_state["user_message"] = (
        request.message
    )

    updated_state["status"] = (
        "replanned"
    )

    # --------------------------------------------------------
    # 9. APPLY BACKEND DAY LOCKING
    # --------------------------------------------------------

    for day in updated_state[
        "itinerary"
    ].get(
        "days",
        [],
    ):

        day_number = day.get(
            "day_number"
        )

        day["is_editable"] = (
            day_number not in locked_days
        )

    # --------------------------------------------------------
    # 10. RUN VERIFICATION AS NON-BLOCKING WARNINGS
    # --------------------------------------------------------
    #
    # Verification remains in the system.
    #
    # However, during the current product/demo phase,
    # verification warnings do not block replanning.
    #
    # Route-quality and verification hardening will be
    # handled later.
    #
    # --------------------------------------------------------

    verification_errors = validate_trip_state(
        updated_state
    )

    if verification_errors:

        print(
            "\n--- REPLAN VERIFICATION WARNINGS ---"
        )

        for error in verification_errors:

            print(
                f"⚠️ {error}"
            )

        print(
            "--- REPLAN CONTINUING ---\n"
        )

    updated_state["verification_errors"] = (
        verification_errors
    )

    updated_state["verification_passed"] = (
        not bool(verification_errors)
    )

    updated_state["status"] = (
        "replanned"
    )

    # --------------------------------------------------------
    # 11. SAVE REPLANNED STATE TO REDIS
    # --------------------------------------------------------

    try:

        save_trip_state(
            trip_id=trip_id,
            state=updated_state,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Failed to save replanned state: {str(exc)}"
            ),
        )

    # --------------------------------------------------------
    # 12. UPDATE DATABASE STATUS
    # --------------------------------------------------------

    trip.status = "replanned"

    db.commit()

    # --------------------------------------------------------
    # 13. RETURN REPLAN API CONTRACT
    # --------------------------------------------------------

    return ReplanResponse(
        trip_id=trip_id,
        replanned_days=affected_days,
        locked_days=locked_days,
        updated_itinerary=updated_state[
            "itinerary"
        ],
    )