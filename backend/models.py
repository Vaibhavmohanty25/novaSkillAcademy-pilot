
import uuid

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Text,
    DateTime, ForeignKey, Float
)

from backend.database import Base


def generate_id():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class Lead(Base):

    __tablename__ = "leads"

    id = Column(String, primary_key=True,
                default=generate_id)

    call_id = Column(String, unique=True, index=True)

    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)

    course = Column(String, nullable=True)
    education = Column(String, nullable=True)

    budget = Column(Integer, nullable=True)
    timeline = Column(String, nullable=True)
    interest = Column(String, nullable=True)

    score = Column(Integer, default=0)
    status = Column(String, default="qualifying")

    created_at = Column(DateTime, default=utc_now)


class AppointmentSlot(Base):

    __tablename__ = "appointment_slots"

    id = Column(String, primary_key=True,
                default=generate_id)

    counsellor = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)


class Appointment(Base):

    __tablename__ = "appointments"

    id = Column(String, primary_key=True,
                default=generate_id)

    lead_id = Column(
        String,
        ForeignKey("leads.id"),
        nullable=False
    )

    slot_id = Column(
        String,
        ForeignKey("appointment_slots.id"),
        nullable=False,
        unique=True
    )

    status = Column(String, default="confirmed")
    created_at = Column(DateTime, default=utc_now)


class Call(Base):

    __tablename__ = "calls"

    id = Column(String, primary_key=True)

    lead_id = Column(
        String,
        ForeignKey("leads.id"),
        nullable=True
    )

    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    sentiment = Column(String, nullable=True)

    ended_reason = Column(String, nullable=True)
    cost = Column(Float, nullable=True)

    status = Column(String, default="completed")

    created_at = Column(DateTime, default=utc_now)



class Escalation(Base):

    __tablename__ = "escalations"

    id = Column(
        String,
        primary_key=True,
        default=generate_id
    )

    call_id = Column(
        String,
        nullable=False,
        unique=True
    )

    lead_id = Column(
        String,
        ForeignKey("leads.id"),
        nullable=True
    )

    reason = Column(Text, nullable=False)
    status = Column(String, default="pending")

    created_at = Column(
        DateTime,
        default=utc_now
    )


class CallInsight(Base):

    __tablename__ = "call_insights"

    call_id = Column(
        String,
        ForeignKey("calls.id"),
        primary_key=True
    )

    next_action = Column(Text, nullable=True)
    objections = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=utc_now
    )

