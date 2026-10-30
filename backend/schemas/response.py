from typing import Dict, List, Optional, Union

from pydantic import BaseModel


class QualityResult(BaseModel):
    agent: str = "image_quality"
    status: str                      # ACCEPTABLE | MARGINAL | POOR
    score: float                     # 0..1
    checks: Dict[str, str]           # blur/brightness/contrast/glare/obstruction -> PASS|WARN|FAIL
    metrics: Dict[str, float]
    reasons: List[str]


class DiagnosisResult(BaseModel):
    agent: str = "diagnosis"
    predicted_class: str
    predicted_name: str
    confidence: float
    probabilities: Dict[str, float]
    top3: List[Dict[str, Union[str, float]]]
    malignant_probability: float
    mock: bool = False


class DecisionResult(BaseModel):
    decision: str                    # AUTO_TRIAGE | REFER | RE_IMAGE
    rule: str
    reasons: List[str]
    quality_influence: str
    diagnosis_influence: str


class AnalyzeResponse(BaseModel):
    success: bool = True
    image_id: str
    quality: QualityResult
    diagnosis: Optional[DiagnosisResult] = None
    decision: DecisionResult
    final_decision: str
    reasons: List[str]
    latency_ms: Dict[str, float]
    disclaimer: str
