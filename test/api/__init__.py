import io

from PIL import Image as image


def showqr(png: bytes):
    buf = io.BytesIO(png)
    image.open(buf).show()
