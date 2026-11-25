
from datetime import (
    datetime,
    timedelta,
    timezone,
    date,
    time
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.models import (
    Lead,
    Appointment,
    AppointmentSlot
)

from backend.schemas import (
    AvailabilityRequest,
    BookingRequest
)


IST = timezone(timedelta(hours=5, minutes=30))


def utc_now():
    return datetime.now(
        timezone.utc
    ).replace(tzinfo=None)


def format_slot(slot):

    local_time = slot.start_time.replace(
        tzinfo=timezone.utc
    ).astimezone(IST)

    return {
        "slot_id": slot.id,
        "counsellor": slot.counsellor,
        "date": local_time.strftime("%Y-%m-%d"),
        "time": local_time.strftime("%I:%M %p"),
        "timezone": "Asia/Kolkata",
        "display_time": local_time.strftime(
            "%A, %d %B %Y at %I:%M %p IST"
        )
    }


def check_availability(
    db: Session,
    arguments: dict
):

    data = AvailabilityRequest.model_validate(
        arguments
    )

    booked_slots = db.query(
        Appointment.slot_id
    )

    query = db.query(
        AppointmentSlot
    ).filter(
        AppointmentSlot.start_time > utc_now(),
        ~AppointmentSlot.id.in_(booked_slots)
    )

    if data.date:

        try:
            requested_date = date.fromisoformat(
                data.date
            )

        except ValueError:

            return {
                "success": False,
                "message": "Invalid date format."
            }

        start_local = datetime.combine(
            requested_date,
            time.min,
            tzinfo=IST
        )

        end_local = start_local + timedelta(days=1)

        start_utc = start_local.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

        end_utc = end_local.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

        query = query.filter(
            AppointmentSlot.start_time >= start_utc,
            AppointmentSlot.start_time < end_utc
        )

    slots = query.order_by(
        AppointmentSlot.start_time.asc()
    ).limit(6).all()

    return {
        "success": True,
        "available_slots": [
            format_slot(slot)
            for slot in slots
        ],
        "message": (
            "Available appointments found."
            if slots
            else "No available appointments found."
        )
    }


def book_appointment(
    db: Session,
    call_id: str,
    arguments: dict
):

    data = BookingRequest.model_validate(
        arguments
    )

    if not data.confirmed:

        return {
            "success": False,
            "message": (
                "Customer confirmation is required "
                "before booking."
            )
        }

    if not call_id:

        return {
            "success": False,
            "message": "Missing call ID."
        }

    lead = db.query(Lead).filter(
        Lead.call_id == call_id
    ).first()

    if not lead:

        return {
            "success": False,
            "message": (
                "Collect and save customer "
                "information first."
            )
        }

    if not lead.name or not (
        lead.phone or lead.email
    ):

        return {
            "success": False,
            "message": (
                "Customer name and contact "
                "information are required."
            )
        }

    slot = db.get(
        AppointmentSlot,
        data.slot_id
    )

    if not slot or slot.start_time <= utc_now():

        return {
            "success": False,
            "message": "Invalid or expired slot."
        }

    # Check if the same lead already booked this slot
    existing = db.query(Appointment).filter(
        Appointment.slot_id == slot.id
    ).first()

    if existing:

        if existing.lead_id == lead.id:

            return {
                "success": True,
                "already_booked": True,
                "appointment_id": existing.id,
                "appointment": format_slot(slot)
            }

        return {
            "success": False,
            "message": (
                "This slot is already booked. "
                "Please select another slot."
            )
        }

    appointment = Appointment(
        lead_id=lead.id,
        slot_id=slot.id,
        status="confirmed"
    )

    db.add(appointment)

    try:

        db.commit()
        db.refresh(appointment)

    except IntegrityError:

        db.rollback()

        existing = db.query(Appointment).filter(
            Appointment.slot_id == data.slot_id
        ).first()

        if existing and existing.lead_id == lead.id:

            return {
                "success": True,
                "already_booked": True,
                "appointment_id": existing.id,
                "appointment": format_slot(slot)
            }

        if existing:

            return {
                "success": False,
                "message": (
                    "The slot was just booked "
                    "by another customer."
                )
            }

        raise

    return {
        "success": True,
        "appointment_id": appointment.id,
        "customer": lead.name,
        "appointment": format_slot(slot),
        "message": "Appointment confirmed."
    }
