import io
import typing as t

import numpy as np
from PIL import Image as image

if t.TYPE_CHECKING:
    mat_u1 = np.ndarray[t.Any, np.dtype[np.uint8]]
    mat_i2 = np.ndarray[t.Any, np.dtype[np.int16]]
    mat_i4 = np.ndarray[t.Any, np.dtype[np.int32]]
else:
    mat_u1 = mat_i2 = mat_i4 = np.ndarray

__all__ = ["mat_u1", "mat_i2", "mat_i4", "frombytes", "tobytes"]


def frombytes(b: bytes, dtype=np.uint8) -> mat_u1:
    buf = io.BytesIO(b)
    return np.asarray(image.open(buf), dtype=dtype)


def tobytes(img: mat_u1, format="png") -> bytes:
    buf = io.BytesIO()
    image.fromarray(img).save(buf, format)
    return buf.getvalue()
