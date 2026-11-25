
from pydantic import BaseModel, Field
from typing import Optional, Literal



class LeadUpdate(BaseModel):

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    course: Optional[
        Literal[
            "AI and Machine Learning",
            "Data Science",
            "Full Stack Development",
            "Python Programming",
            "Cloud Computing"
        ]
    ] = None

    education: Optional[str] = None

    budget: Optional[int] = Field(
        default=None,
        ge=0
    )

    timeline: Optional[
        Literal[
            "immediate",
            "within_30_days",
            "within_90_days",
            "later",
            "unknown"
        ]
    ] = None

    interest: Optional[
        Literal["high", "medium", "low"]
    ] = None




class BookingRequest(BaseModel):

    slot_id: str = Field(min_length=1)

    confirmed: bool = False



class KnowledgeQuery(BaseModel):

    query: str = Field(min_length=1, max_length=1000)


class CallAnalysis(BaseModel):

    summary: str

    sentiment: Literal[
        "positive",
        "neutral",
        "negative",
        "unknown"
    ]

    next_action: str


class AvailabilityRequest(BaseModel):

    date: Optional[str] = Field(
        default=None,
        description="Date in YYYY-MM-DD format"
    )


class EscalationRequest(BaseModel):

    reason: str = Field(
        min_length=3,
        max_length=1000
    )


class PostCallInsights(BaseModel):

    summary: str

    sentiment: Literal[
        "positive",
        "neutral",
        "negative",
        "unknown"
    ]

    objections: list[str] = Field(
        default_factory=list
    )

    next_action: str

class PostCallInsights(BaseModel):

    summary: str

    sentiment: Literal[
        "positive",
        "neutral",
        "negative",
        "unknown"
    ] = "unknown"

    objections: list[str] = Field(
        default_factory=list
    )

    next_action: Optional[str] = None

