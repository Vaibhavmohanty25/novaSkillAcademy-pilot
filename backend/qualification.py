
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

with open(
    ROOT / "knowledge_base" / "courses.json",
    encoding="utf-8"
) as file:
    documents = json.load(file)


COURSE_FEES = {
    doc["title"].strip().lower(): doc["fee"]
    for doc in documents
    if doc["category"] == "course"
}


def calculate_lead_score(lead):

    breakdown = {
        "interest": 0,
        "budget": 0,
        "timeline": 0,
        "contact": 0
    }

    # 1. Customer interest
    interest = (lead.interest or "").lower()

    breakdown["interest"] = {
        "high": 30,
        "medium": 15,
        "low": 0
    }.get(interest, 0)

    # 2. Budget compatibility
    course = (lead.course or "").strip().lower()
    fee = COURSE_FEES.get(course)

    if lead.budget is not None and fee:

        if lead.budget >= fee:
            breakdown["budget"] = 30

        elif lead.budget >= fee * 0.7:
            breakdown["budget"] = 15

    # 3. Enrollment timeline
    timeline = (lead.timeline or "").lower()

    breakdown["timeline"] = {
        "immediate": 25,
        "within_30_days": 25,
        "within_90_days": 10,
        "later": 5,
        "unknown": 0
    }.get(timeline, 0)

    # 4. Contact information
    if lead.phone or lead.email:
        breakdown["contact"] = 15

    score = sum(breakdown.values())

    # Don't classify incomplete leads prematurely
    if (
        not lead.course
        or not lead.interest
        or lead.budget is None
        or not lead.timeline
        or lead.timeline == "unknown"
    ):
        status = "qualifying"

    elif score >= 75:
        status = "hot"

    elif score >= 45:
        status = "warm"

    else:
        status = "cold"

    return {
        "score": score,
        "status": status,
        "breakdown": breakdown
    }
