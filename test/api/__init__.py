import cv2 as cv
import numpy as np


def frombytes(b: bytes, dtype="uint8", flags=cv.IMREAD_COLOR) -> np.ndarray:
    return cv.imdecode(np.frombuffer(b, dtype=dtype), flags=flags)


def showqr(png: bytes):
    try:
        cv.destroyAllWindows()
        cv.imshow("Scan and login", frombytes(png))
        cv.waitKey()
    except:
        from pathlib import Path

        Path("tmp").mkdir(exist_ok=True)
        with open("tmp/r.png", "wb") as f:
            f.write(png)
        print("Open tmp/r.png and scan")
