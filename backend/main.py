from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.diagnosis_agent import is_ready
from config import MOCK_MODE
from routes.analysis import router

app = FastAPI(title="Agentic DermaGuard API", version="2.0.0",
              description="Six-agent skin-lesion screening & triage (prototype, not a diagnosis tool).")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)                    # POST /analyze   <- what the frontend calls
app.include_router(router, prefix="/api")     # POST /api/analyze (same handlers)


@app.get("/")
def root():
    return {"service": "Agentic DermaGuard", "agents": 6, "status": "running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok", "model_ready": is_ready(), "mock_mode": MOCK_MODE}
