
from sqlalchemy.orm import Session

from backend.models import Lead
from backend.schemas import LeadUpdate, KnowledgeQuery
from backend.qualification import calculate_lead_score
from backend.rag import knowledge_engine
from backend.booking import (
    check_availability,
    book_appointment
)

from backend.models import Escalation
from backend.schemas import EscalationRequest

def search_knowledge(arguments: dict):

    data = KnowledgeQuery.model_validate(arguments)

    return knowledge_engine.search(data.query)


def update_lead(
    db: Session,
    call_id: str,
    arguments: dict
):

    if not call_id:
        raise ValueError("Missing call ID")

    data = LeadUpdate.model_validate(arguments)

    updates = data.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    updates = {
        key: value.strip()
        if isinstance(value, str) else value
        for key, value in updates.items()
    }

    updates = {
        key: value
        for key, value in updates.items()
        if value != ""
    }

    if not updates:
        raise ValueError("No lead information provided")

    # Find an existing lead for this conversation
    lead = db.query(Lead).filter(
        Lead.call_id == call_id
    ).first()

    # Create a lead if one does not exist
    if lead is None:

        lead = Lead(call_id=call_id)

        db.add(lead)

    # Update only the newly supplied information
    for key, value in updates.items():
        setattr(lead, key, value)

    # Calculate qualification score
    qualification = calculate_lead_score(lead)

    lead.score = qualification["score"]
    lead.status = qualification["status"]

    # Persist the lead
    db.commit()
    db.refresh(lead)

    return {
        "success": True,
        "lead_id": lead.id,
        "name": lead.name,
        "course": lead.course,
        "budget": lead.budget,
        "score": lead.score,
        "status": lead.status,
        "breakdown": qualification["breakdown"]
    }



def execute_tool(
    name: str,
    arguments: dict,
    call_id: str,
    db: Session
):

    if name == "search_knowledge":

        return search_knowledge(arguments)

    elif name == "update_lead":

        return update_lead(
            db=db,
            call_id=call_id,
            arguments=arguments
        )

    elif name == "check_availability":

        return check_availability(
            db=db,
            arguments=arguments
        )

    elif name == "book_appointment":

        return book_appointment(
            db=db,
            call_id=call_id,
            arguments=arguments
        )

    elif name == "escalate_to_human":

        return escalate_to_human(
            db=db,
            call_id=call_id,
            arguments=arguments
        )

    raise ValueError(
        f"Unknown tool: {name}"
    )



def escalate_to_human(
    db: Session,
    call_id: str,
    arguments: dict
):

    if not call_id:
        raise ValueError("Missing call ID")

    data = EscalationRequest.model_validate(
        arguments
    )

    lead = db.query(Lead).filter(
        Lead.call_id == call_id
    ).first()

    existing = db.query(Escalation).filter(
        Escalation.call_id == call_id
    ).first()

    if existing:

        existing.reason = data.reason

        if lead:
            existing.lead_id = lead.id

        db.commit()

        return {
            "success": True,
            "escalation_id": existing.id,
            "status": existing.status
        }

    escalation = Escalation(
        call_id=call_id,
        lead_id=lead.id if lead else None,
        reason=data.reason,
        status="pending"
    )

    db.add(escalation)
    db.commit()
    db.refresh(escalation)

    return {
        "success": True,
        "escalation_id": escalation.id,
        "status": "pending",
        "message": (
            "Human assistance request created."
        )
    }

