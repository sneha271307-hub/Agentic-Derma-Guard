"""Agent 2 - Diagnosis Agent (EfficientNet-B0, 7-class HAM10000 classifier).

Contract:  predict_lesion(image) -> dict (see schemas.response.DiagnosisResult)
Checkpoint (saved by scripts/train_diagnosis.py): {"state_dict", "classes", "img_size"}
If no checkpoint exists the agent raises ModelNotLoadedError, unless DERMAGUARD_MOCK=1
(deterministic fake output, for integration testing ONLY - never for the real submission).
"""
import hashlib
import threading

import numpy as np

from config import CLASS_NAMES, CLASSES, HIGH_RISK_CLASSES, IMG_SIZE, MOCK_MODE, MODEL_PATH
from utils.image_processing import to_bgr, to_pil


class ModelNotLoadedError(RuntimeError):
    pass


_lock = threading.Lock()
_state = {"model": None, "classes": CLASSES, "size": IMG_SIZE, "tf": None, "device": None}


def build_model(num_classes: int = len(CLASSES), pretrained: bool = False):
    import torch.nn as nn
    from torchvision import models
    weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
    m = models.efficientnet_b0(weights=weights)
    m.classifier[1] = nn.Linear(m.classifier[1].in_features, num_classes)
    return m


def _load():
    if _state["model"] is not None:
        return
    with _lock:
        if _state["model"] is not None:
            return
        if not MODEL_PATH.exists():
            raise ModelNotLoadedError(f"Model weights not found at {MODEL_PATH}")
        import torch
        from torchvision import transforms
        ckpt = torch.load(MODEL_PATH, map_location="cpu")
        classes = ckpt.get("classes", CLASSES)
        size = ckpt.get("img_size", IMG_SIZE)
        model = build_model(len(classes))
        model.load_state_dict(ckpt["state_dict"])
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device).eval()
        _state.update(model=model, classes=classes, size=size, device=device,
                      tf=transforms.Compose([
                          transforms.Resize((size, size)),
                          transforms.ToTensor(),
                          transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
                      ]))


def is_ready() -> bool:
    return _state["model"] is not None or MOCK_MODE or MODEL_PATH.exists()


def _mock_probs(image) -> np.ndarray:
    seed = int(hashlib.md5(to_bgr(image).tobytes()).hexdigest()[:8], 16)
    p = np.random.RandomState(seed).dirichlet(np.ones(len(CLASSES)) * 0.6)
    return p


def _real_probs(image) -> np.ndarray:
    import torch
    _load()
    x = _state["tf"](to_pil(image)).unsqueeze(0).to(_state["device"])
    with torch.no_grad():
        return torch.softmax(_state["model"](x), dim=1)[0].cpu().numpy()


def predict_probs_batch(images) -> np.ndarray:
    """Batch inference helper for evaluation scripts (list of images -> [N, C] probs)."""
    import torch
    _load()
    x = torch.stack([_state["tf"](to_pil(i)) for i in images]).to(_state["device"])
    with torch.no_grad():
        return torch.softmax(_state["model"](x), dim=1).cpu().numpy()


def result_from_probs(probs: np.ndarray, mock: bool = False) -> dict:
    classes = _state["classes"] if not mock else CLASSES
    order = np.argsort(probs)[::-1]
    top = classes[int(order[0])]
    prob_map = {c: round(float(p), 4) for c, p in zip(classes, probs)}
    return {
        "agent": "diagnosis",
        "predicted_class": top,
        "predicted_name": CLASS_NAMES.get(top, top),
        "confidence": round(float(probs[order[0]]), 4),
        "probabilities": prob_map,
        "top3": [{"class": classes[int(i)], "probability": round(float(probs[i]), 4)} for i in order[:3]],
        "malignant_probability": round(float(sum(prob_map[c] for c in HIGH_RISK_CLASSES if c in prob_map)), 4),
        "mock": mock,
    }


def predict_lesion(image) -> dict:
    if not MODEL_PATH.exists() and MOCK_MODE:
        return result_from_probs(_mock_probs(image), mock=True)
    return result_from_probs(_real_probs(image))
