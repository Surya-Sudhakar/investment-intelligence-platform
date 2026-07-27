from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class AvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"
    PLANNED_PHASE8 = "planned_phase8"


class PartialDataStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class AlignmentMetadata(BaseModel):
    actual_overlap_count: int
    aligned_start_timestamp: datetime | None = None
    aligned_end_timestamp: datetime | None = None
    requested_lookback: int
    minimum_required: int
    alignment_sufficient: bool


class AvailableValue[T](BaseModel):
    status: AvailabilityStatus
    value: T | None = None
    reason: str
    alignment: AlignmentMetadata | None = None
