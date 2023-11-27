import io

from PIL import Image as image

__all__ = ["frombytes", "tobytes"]


def frombytes(b: bytes) -> image.Image:
    return image.open(io.BytesIO(b))


def tobytes(img: image.Image, format="png") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format)
    return buf.getvalue()
