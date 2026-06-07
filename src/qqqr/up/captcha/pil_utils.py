"""PIL image conversion utilities.

Provides :func:`frombytes` and :func:`tobytes` for converting between
PIL Image objects and raw bytes.
"""

import io

from PIL import Image as image

__all__ = ["frombytes", "tobytes"]


def frombytes(b: bytes) -> image.Image:
    """Convert raw bytes to a PIL Image."""
    return image.open(io.BytesIO(b))


def tobytes(img: image.Image, format="png") -> bytes:
    """Convert a PIL Image to bytes in the given format."""
    buf = io.BytesIO()
    img.save(buf, format)
    return buf.getvalue()
