"""Image loading helpers shared by both agents. Accepts a path, raw bytes or a numpy BGR array."""
from pathlib import Path
from typing import Union

import cv2
import numpy as np
from PIL import Image

ImageInput = Union[str, Path, bytes, np.ndarray]


class InvalidImageError(ValueError):
    pass


def to_bgr(image: ImageInput) -> np.ndarray:
    if isinstance(image, np.ndarray):
        arr = image
    elif isinstance(image, (bytes, bytearray)):
        arr = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
    else:
        arr = cv2.imread(str(image), cv2.IMREAD_COLOR)
    if arr is None or arr.size == 0:
        raise InvalidImageError("Could not decode image")
    if arr.ndim == 2:
        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
    return arr


def to_pil(image: ImageInput) -> Image.Image:
    bgr = to_bgr(image)
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
