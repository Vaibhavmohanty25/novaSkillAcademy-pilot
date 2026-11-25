
import json
import logging
import secrets

from fastapi import (
    APIRouter,
    Request,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from starlette.concurrency import run_in_threadpool

from backend.config import settings
from backend.database import get_db
from backend.models import Call, Lead, CallInsight
from backend.tools import execute_tool
from backend.analysis import extract_call_analysis


router = APIRouter(prefix="/api/vapi")

logger = logging.getLogger(__name__)


def process_event(message: dict, db: Session):

    event_type = message.get("type")

    call_id = (
        message.get("call") or {}
    ).get("id")

    logger.info(
        "Vapi event: %s | Call: %s",
        event_type,
        call_id
    )

    # =====================================
    # TOOL CALL EXECUTION
    # =====================================

    if event_type == "tool-calls":

        results = []

        for tool in message.get("toolCallList", []):

            tool_call_id = tool.get("id")

            function = tool.get("function") or {}

            name = function.get("name")

            arguments = function.get("arguments") or {}

            try:

                if isinstance(arguments, str):
                    arguments = json.loads(arguments)

                if not isinstance(arguments, dict):
                    raise ValueError(
                        "Invalid tool arguments"
                    )

                result = execute_tool(
                    name=name,
                    arguments=arguments,
                    call_id=call_id,
                    db=db
                )

                logger.info(
                    "Tool executed: %s",
                    name
                )

                results.append({
                    "toolCallId": tool_call_id,
                    "result": json.dumps(
                        result,
                        ensure_ascii=False
                    )
                })

            except Exception:

                db.rollback()

                logger.exception(
                    "Tool execution failed: %s",
                    name
                )

                results.append({
                    "toolCallId": tool_call_id,
                    "error": (
                        "Unable to complete the "
                        "requested operation."
                    )
                })

        return {"results": results}

    # =====================================
    # END-OF-CALL REPORT
    # =====================================

    if event_type == "end-of-call-report":

        if not call_id:

            raise HTTPException(
                status_code=400,
                detail="Missing call ID"
            )

        artifact = message.get("artifact") or {}

        analysis = extract_call_analysis(message)

        lead = db.query(Lead).filter(
            Lead.call_id == call_id
        ).first()

        record = db.get(Call, call_id)

        if record is None:

            record = Call(
                id=call_id,
                status="completed"
            )

            db.add(record)

        if lead:
            record.lead_id = lead.id

        transcript = (
            artifact.get("transcript")
            or message.get("transcript")
        )

        if transcript:
            record.transcript = transcript

        if analysis.get("summary"):
            record.summary = analysis["summary"]

        sentiment = analysis.get(
            "sentiment",
            "unknown"
        )

        if sentiment != "unknown" or not record.sentiment:
            record.sentiment = sentiment

        if message.get("cost") is not None:
            record.cost = message["cost"]

        if message.get("endedReason"):
            record.ended_reason = message["endedReason"]

        try:

            db.flush()

            insight = db.get(CallInsight, call_id)

            if insight is None:

                insight = CallInsight(
                    call_id=call_id
                )

                db.add(insight)

            if analysis.get("next_action"):

                insight.next_action = analysis[
                    "next_action"
                ]

            if (
                analysis.get("objections")
                or not insight.objections
            ):

                insight.objections = json.dumps(
                    analysis.get("objections", []),
                    ensure_ascii=False
                )

            db.commit()

            logger.info(
                "Call report saved: %s",
                call_id
            )

        except IntegrityError:

            db.rollback()

            logger.exception(
                "Database integrity error while "
                "saving call report: %s",
                call_id
            )

            raise

        except Exception:

            db.rollback()

            logger.exception(
                "Failed to save call report: %s",
                call_id
            )

            raise

        return {"status": "saved"}

    # =====================================
    # OTHER VAPI EVENTS
    # =====================================

    return {
        "status": "received",
        "event": event_type
    }


# =====================================
# AUTHENTICATED WEBHOOK ENDPOINT
# =====================================

@router.post("/webhook")
async def vapi_webhook(
    request: Request,
    db: Session = Depends(get_db)
):

    expected = settings.vapi_webhook_secret

    received = request.headers.get(
        "X-Vapi-Secret", ""
    )

    authorization = request.headers.get(
        "Authorization", ""
    )

    valid = bool(expected) and (
        secrets.compare_digest(
            received,
            expected
        )
        or secrets.compare_digest(
            authorization,
            f"Bearer {expected}"
        )
    )

    if not valid:

        raise HTTPException(
            status_code=401,
            detail="Invalid webhook credentials"
        )

    try:

        payload = await request.json()

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload"
        )

    if not isinstance(payload, dict):

        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload"
        )

    message = payload.get("message")

    if not isinstance(message, dict):

        raise HTTPException(
            status_code=400,
            detail="Invalid message payload"
        )

    return await run_in_threadpool(
        process_event,
        message,
        db
    )
