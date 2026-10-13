"""
FastAPI REST API Server for Mascc Febrile Neutropenia Score.
"""
from typing import Dict, Any, List, Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, StrictBool
from mascc_score import calculate_metrics
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Mascc Febrile Neutropenia Score API",
    description="Validated MASCC calculator and separate legacy component-audit demo.",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


class MASCCRequest(BaseModel):
    """Seven required criteria of the validated MASCC index."""
    burden: Literal["none_mild", "moderate", "severe"]
    no_hypotension: StrictBool
    no_copd: StrictBool
    favorable_malignancy: StrictBool
    no_dehydration: StrictBool
    outpatient_onset: StrictBool
    age_under_60: StrictBool


@app.post("/api/score")
def api_score(payload: MASCCRequest):
    return calculate_metrics(**payload.model_dump())


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "mascc-febrile-neutropenia-score", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
