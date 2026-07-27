from app.modules.market_context.schemas import (
    AvailabilityStatus as ContextAvailabilityStatus,
)
from app.modules.market_context.schemas import (
    AvailableValue as ContextAvailableValue,
)
from app.modules.market_context.schemas import MarketContextResponse
from app.schemas.metadata import (
    AlignmentMetadata,
    AvailabilityStatus,
    AvailableValue,
    PartialDataStatus,
)


def test_canonical_availability_states_are_stable() -> None:
    assert [item.value for item in AvailabilityStatus] == [
        "available",
        "unavailable",
        "not_applicable",
        "planned_phase8",
    ]
    assert [item.value for item in PartialDataStatus] == [
        "complete",
        "partial",
        "unavailable",
    ]


def test_phase7_reexports_the_canonical_availability_contract() -> None:
    assert ContextAvailabilityStatus is AvailabilityStatus
    assert ContextAvailableValue is AvailableValue


def test_available_value_preserves_original_fields_and_adds_optional_alignment() -> None:
    legacy = AvailableValue[str](
        status=AvailabilityStatus.UNAVAILABLE,
        reason="Not supplied.",
    )
    aligned = AvailableValue[str](
        status=AvailabilityStatus.AVAILABLE,
        value="POSITIVE",
        reason="Calculated.",
        alignment=AlignmentMetadata(
            actual_overlap_count=20,
            aligned_start_timestamp=None,
            aligned_end_timestamp=None,
            requested_lookback=20,
            minimum_required=15,
            alignment_sufficient=True,
        ),
    )
    assert legacy.model_dump()["alignment"] is None
    assert aligned.alignment is not None
    assert aligned.alignment.actual_overlap_count == 20
    assert "partial_data_status" in MarketContextResponse.model_fields
