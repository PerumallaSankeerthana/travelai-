from datetime import date

from pydantic import BaseModel, Field, model_validator


class TripCreateRequest(BaseModel):
    destination: str = Field(min_length=1)
    start_date: date
    end_date: date
    travelers: int = Field(gt=0)
    budget: int = Field(gt=0)
    preferences: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError(
                "end_date must be on or after start_date"
            )

        return self


class TripCreateResponse(BaseModel):
    trip_id: str
    status: str
    itinerary: dict | None = None
    flights: list[dict] = Field(default_factory=list)
    hotels: list[dict] = Field(default_factory=list)
    cost_breakdown: dict = Field(default_factory=dict)


class ReplanRequest(BaseModel):
    message: str = Field(min_length=1)
    affected_days: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_days(self):
        if any(day <= 0 for day in self.affected_days):
            raise ValueError(
                "affected_days must contain positive day numbers"
            )

        self.affected_days = sorted(set(self.affected_days))

        return self


class ReplanResponse(BaseModel):
    trip_id: str
    replanned_days: list[int]
    locked_days: list[int]
    updated_itinerary: dict