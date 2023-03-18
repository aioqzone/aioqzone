import io

from PIL import Image as image


def showqr(png: bytes):
    image.open(io.BytesIO(png)).show()
