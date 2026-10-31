from collections import OrderedDict
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from agents.diagnosis_agent import ModelNotLoadedError, predict_lesion
from agents.quality_agent import check_image_quality
from config import MAX_UPLOAD_MB
from services.orchestrator import analyze, to_py
from utils.image_processing import InvalidImageError, to_bgr

router = APIRouter(tags=["analysis"])

_STORE: "OrderedDict[str, dict]" = OrderedDict()   # in-memory, last 500 results
_ALLOWED = {"image/jpeg", "image/png", "image/jpg", "image/webp", "application/octet-stream"}


async def _read_image(upload: Optional[UploadFile]):
    if upload is None:
        raise HTTPException(422, "Send the image as multipart field 'image' (or 'file')")
    if upload.content_type not in _ALLOWED:
        raise HTTPException(415, f"Unsupported file type: {upload.content_type}")
    data = await upload.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File larger than {MAX_UPLOAD_MB} MB")
    try:
        return to_bgr(data)
    except InvalidImageError:
        raise HTTPException(400, "Uploaded file is not a readable image")


@router.post("/analyze")
async def analyze_endpoint(image: Optional[UploadFile] = File(None), file: Optional[UploadFile] = File(None),
                           age: Optional[str] = Form(None), gender: Optional[str] = Form(None),
                           sex: Optional[str] = Form(None), location: Optional[str] = Form(None)):
    """Frontend contract: multipart 'image' (+ optional age, gender, location). Returns all six agent reports."""
    img = await _read_image(image or file)
    ctx = {"age": age, "gender": gender or sex, "location": location}
    try:
        result = await run_in_threadpool(analyze, img, None, ctx)
    except ModelNotLoadedError as e:
        raise HTTPException(503, str(e))
    _STORE[result["image_id"]] = result
    while len(_STORE) > 500:
        _STORE.popitem(last=False)
    return result


@router.post("/quality")
async def quality_only(image: Optional[UploadFile] = File(None), file: Optional[UploadFile] = File(None)):
    return to_py(await run_in_threadpool(check_image_quality, await _read_image(image or file)))


@router.post("/diagnose")
async def diagnose_only(image: Optional[UploadFile] = File(None), file: Optional[UploadFile] = File(None)):
    img = await _read_image(image or file)
    try:
        return to_py(await run_in_threadpool(predict_lesion, img))
    except ModelNotLoadedError as e:
        raise HTTPException(503, str(e))


@router.get("/results/{image_id}")
def get_result(image_id: str):
    if image_id not in _STORE:
        raise HTTPException(404, "Result not found")
    return _STORE[image_id]
