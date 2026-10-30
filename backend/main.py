from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.diagnosis_agent import is_ready
from config import MOCK_MODE
from routes.analysis import router

app = FastAPI(title="Agentic DermaGuard API", version="1.0.0",
              description="Multi-agent skin-lesion screening & triage (prototype, not a diagnosis tool).")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/")
def root():
    return {"service": "Agentic DermaGuard", "status": "running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok", "model_ready": is_ready(), "mock_mode": MOCK_MODE}
