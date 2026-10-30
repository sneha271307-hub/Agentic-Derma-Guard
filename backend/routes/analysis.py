from collections import OrderedDict

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from agents.diagnosis_agent import ModelNotLoadedError, predict_lesion
from agents.quality_agent import check_image_quality
from config import MAX_UPLOAD_MB
from schemas.response import AnalyzeResponse, DiagnosisResult, QualityResult
from services.orchestrator import analyze
from utils.image_processing import InvalidImageError, to_bgr

router = APIRouter(prefix="/api", tags=["analysis"])

_STORE: "OrderedDict[str, dict]" = OrderedDict()   # in-memory, last 500 results
_ALLOWED = {"image/jpeg", "image/png", "image/jpg", "image/webp", "application/octet-stream"}


async def _read_image(file: UploadFile):
    if file.content_type not in _ALLOWED:
        raise HTTPException(415, f"Unsupported file type: {file.content_type}")
    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File larger than {MAX_UPLOAD_MB} MB")
    try:
        return to_bgr(data)
    except InvalidImageError:
        raise HTTPException(400, "Uploaded file is not a readable image")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(file: UploadFile = File(...)):
    img = await _read_image(file)
    try:
        result = await run_in_threadpool(analyze, img)
    except ModelNotLoadedError as e:
        raise HTTPException(503, str(e))
    _STORE[result["image_id"]] = result
    while len(_STORE) > 500:
        _STORE.popitem(last=False)
    return result


@router.post("/quality", response_model=QualityResult)
async def quality_only(file: UploadFile = File(...)):
    img = await _read_image(file)
    return await run_in_threadpool(check_image_quality, img)


@router.post("/diagnose", response_model=DiagnosisResult)
async def diagnose_only(file: UploadFile = File(...)):
    img = await _read_image(file)
    try:
        return await run_in_threadpool(predict_lesion, img)
    except ModelNotLoadedError as e:
        raise HTTPException(503, str(e))


@router.get("/results/{image_id}", response_model=AnalyzeResponse)
def get_result(image_id: str):
    if image_id not in _STORE:
        raise HTTPException(404, "Result not found")
    return _STORE[image_id]
