from backend.rag import knowledge_engine
from backend.schemas import KnowledgeQuery
import logging
import secrets
from fastapi import Header, HTTPException
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import init_db, get_db
from backend.models import Lead, Call, Appointment
from backend.webhook import router as webhook_router


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):

    init_db()

    print("Database initialized successfully")

    try:
        yield
    finally:
        knowledge_engine.close()




app = FastAPI(
    title=settings.app_name,
    description="Autonomous AI Sales Voice Agent",
    version="0.1.0",
    lifespan=lifespan
)

def verify_admin(
    x_admin_key: str = Header(default="")
):
    if not secrets.compare_digest(
        x_admin_key, settings.admin_api_key
    ):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

app.include_router(webhook_router)


@app.get("/")
def root():

    return {
        "service": settings.app_name,
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
def health():

    return {"status": "healthy"}


@app.get(
    "/api/leads",
    dependencies=[Depends(verify_admin)]
)
def get_leads(db: Session = Depends(get_db)):

    return db.query(Lead).all()


@app.get(
    "/api/calls",
    dependencies=[Depends(verify_admin)]
)
def get_calls(db: Session = Depends(get_db)):

    return db.query(Call).all()


@app.get(
    "/api/appointments",
    dependencies=[Depends(verify_admin)]
)
def get_appointments(
    db: Session = Depends(get_db)
):

    return db.query(Appointment).all()

@app.post(
    "/api/knowledge/search",
    dependencies=[Depends(verify_admin)]
)
def search_knowledge(data: KnowledgeQuery):

    return knowledge_engine.search(
        data.query
    )
