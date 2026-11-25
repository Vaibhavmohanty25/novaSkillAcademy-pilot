
from datetime import datetime, timedelta, timezone

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base

from backend.models import (
    Lead,
    AppointmentSlot,
    Appointment
)

from backend.booking import (
    book_appointment,
    check_availability
)


# ==========================================
# TEST DATABASE
# ==========================================

@pytest.fixture
def db():

    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)

    session = Session()

    try:
        yield session

    finally:
        session.close()
        engine.dispose()


# ==========================================
# SAMPLE TEST DATA
# ==========================================

@pytest.fixture
def sample_data(db):

    lead_one = Lead(
        call_id="test-call-one",
        name="Rahul Sharma",
        email="rahul@example.com"
    )

    lead_two = Lead(
        call_id="test-call-two",
        name="Priya Singh",
        email="priya@example.com"
    )

    slot = AppointmentSlot(
        counsellor="Admissions Counsellor",
        start_time=(
            datetime.now(timezone.utc)
            + timedelta(days=1)
        ).replace(tzinfo=None)
    )

    db.add_all([
        lead_one,
        lead_two,
        slot
    ])

    db.commit()

    return {
        "lead_one": lead_one,
        "lead_two": lead_two,
        "slot": slot
    }


# ==========================================
# TEST 1: SUCCESSFUL BOOKING
# ==========================================

def test_successful_booking(db, sample_data):

    result = book_appointment(
        db=db,
        call_id="test-call-one",
        arguments={
            "slot_id": sample_data["slot"].id,
            "confirmed": True
        }
    )

    assert result["success"] is True

    assert db.query(Appointment).count() == 1


# ==========================================
# TEST 2: PREVENT DOUBLE BOOKING
# ==========================================

def test_prevent_double_booking(db, sample_data):

    args = {
        "slot_id": sample_data["slot"].id,
        "confirmed": True
    }

    first = book_appointment(
        db,
        "test-call-one",
        args
    )

    second = book_appointment(
        db,
        "test-call-two",
        args
    )

    assert first["success"] is True

    assert second["success"] is False

    assert db.query(Appointment).count() == 1


# ==========================================
# TEST 3: DUPLICATE REQUEST HANDLING
# ==========================================

def test_duplicate_request(db, sample_data):

    args = {
        "slot_id": sample_data["slot"].id,
        "confirmed": True
    }

    first = book_appointment(
        db,
        "test-call-one",
        args
    )

    retry = book_appointment(
        db,
        "test-call-one",
        args
    )

    assert first["success"] is True

    assert retry["success"] is True

    assert retry["already_booked"] is True

    assert db.query(Appointment).count() == 1


# ==========================================
# TEST 4: BOOKING WITHOUT CONFIRMATION
# ==========================================

def test_booking_without_confirmation(
    db,
    sample_data
):

    result = book_appointment(
        db,
        "test-call-one",
        {
            "slot_id": sample_data["slot"].id,
            "confirmed": False
        }
    )

    assert result["success"] is False

    assert db.query(Appointment).count() == 0


# ==========================================
# TEST 5: INVALID APPOINTMENT SLOT
# ==========================================

def test_invalid_slot(db, sample_data):

    result = book_appointment(
        db,
        "test-call-one",
        {
            "slot_id": "invalid-slot-id",
            "confirmed": True
        }
    )

    assert result["success"] is False

    assert db.query(Appointment).count() == 0


# ==========================================
# TEST 6: AVAILABILITY CHECKING
# ==========================================

def test_check_availability(db, sample_data):

    result = check_availability(
        db,
        {}
    )

    assert result["success"] is True

    assert len(result["available_slots"]) == 1

    assert (
        result["available_slots"][0]["slot_id"]
        == sample_data["slot"].id
    )


# ==========================================
# TEST 7: BOOKED SLOT REMOVED FROM AVAILABILITY
# ==========================================

def test_booked_slot_unavailable(db, sample_data):

    booking = book_appointment(
        db,
        "test-call-one",
        {
            "slot_id": sample_data["slot"].id,
            "confirmed": True
        }
    )

    assert booking["success"] is True

    result = check_availability(db, {})

    assert result["available_slots"] == []


# ==========================================
# TEST 8: EXPIRED APPOINTMENT SLOT
# ==========================================

def test_expired_slot(db, sample_data):

    slot = sample_data["slot"]

    slot.start_time = (
        datetime.now(timezone.utc)
        - timedelta(days=1)
    ).replace(tzinfo=None)

    db.commit()

    result = book_appointment(
        db,
        "test-call-one",
        {
            "slot_id": slot.id,
            "confirmed": True
        }
    )

    assert result["success"] is False

    assert db.query(Appointment).count() == 0
