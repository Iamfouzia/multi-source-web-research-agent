from dotenv import load_dotenv

load_dotenv()

import json
import logging
import os
import queue
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from research_agent.agent import ResearchAgent
from research_agent.config import load_settings
from research_agent.models import ResearchAnswer

logger = logging.getLogger("research_api")
logging.basicConfig(level=logging.INFO)

FRONTEND_DIR = Path(__file__).parent / "frontend"
GENERIC_ERROR = "The research run failed on the server. Check the server logs for details."


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    top_n: int = Field(8, ge=1, le=15, description="Number of ranked sources to use")

    @field_validator("question")
    @classmethod
    def _strip_question(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Question must be at least 3 characters.")
        return value


class Reference(BaseModel):
    title: str
    url: str


class ResearchResponse(BaseModel):
    question: str
    answer: str
    key_claims: list[str]
    references: list[Reference]
    conflicts: list[str]
    uncertainties: list[str]
    provider_failures: list[str]


def to_payload(result: ResearchAnswer) -> dict:
    return {
        "question": result.question,
        "answer": result.answer,
        "key_claims": list(result.key_claims),
        "references": [{"title": r.title, "url": r.url} for r in result.references],
        "conflicts": list(result.conflicts),
        "uncertainties": list(result.uncertainties),
        "provider_failures": list(result.provider_failures),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = ResearchAgent(load_settings())
    logger.info("ResearchAgent ready")
    yield


app = FastAPI(title="Multi-Source Web Research Agent", version="1.0.0", lifespan=lifespan)

_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
def research(req: ResearchRequest) -> dict:
    try:
        result = app.state.agent.run(req.question, top_n=req.top_n)
    except Exception:
        logger.exception("Research run failed")
        raise HTTPException(status_code=500, detail=GENERIC_ERROR)
    return to_payload(result)


@app.post("/research/stream")
def research_stream(req: ResearchRequest) -> StreamingResponse:
    events: "queue.Queue[Optional[dict]]" = queue.Queue()

    def on_stage(stage: str, detail: Optional[str]) -> None:
        events.put({"type": "stage", "stage": stage, "detail": detail})

    def worker() -> None:
        try:
            result = app.state.agent.run(req.question, top_n=req.top_n, on_stage=on_stage)
            events.put({"type": "result", "data": to_payload(result)})
        except Exception:
            logger.exception("Research run failed")
            events.put({"type": "error", "message": GENERIC_ERROR})
        finally:
            events.put(None)

    threading.Thread(target=worker, daemon=True).start()

    def event_stream():
        while True:
            item = events.get()
            if item is None:
                break
            yield json.dumps(item) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)