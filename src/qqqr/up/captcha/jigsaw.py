import os

import cv2 as cv
import numpy as np

debug = False

TC_OPERATION_WIDTH = 279


def frombytes(b, dtype="uint8", flags=cv.IMREAD_COLOR) -> np.ndarray:
    return cv.imdecode(np.asarray(bytearray(b), dtype=dtype), flags=flags)


class Piece:
    def __init__(self, img: np.ndarray) -> None:
        self.mask = img[:, :, 3:]
        self.img = img[:, :, :3] * (self.mask == 255)

    def strip(self):
        if not hasattr(self, "bbox"):
            cont, (hier,) = cv.findContours(
                cv.cvtColor(self.img, cv.COLOR_BGR2GRAY), cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE
            )
            center = (int(self.img.shape[0] // 2), int(self.img.shape[1] // 2))
            cond = [
                cv.pointPolygonTest(i, center, False) == 1
                and cv.pointPolygonTest(i, (0, 0), False) == -1
                for i in cont
            ]
            cont = [i for i, c in zip(cont, cond) if c]
            if len(cont) == 2:
                hier = [i for i, c in zip(hier, cond) if c]
                cont = [i for i, c in zip(cont, hier) if c[2] == -1]
            assert len(cont) == 1
            self.setContour(cont[0])

        r = self.img[
            self.bbox[1] : self.bbox[1] + self.bbox[3], self.bbox[0] : self.bbox[0] + self.bbox[2]
        ]
        return r

    def setContour(self, cont: list):
        self.cont = cont
        self.bbox = cv.boundingRect(cont)
        self.padding = (
            *self.bbox[:2],
            self.img.shape[1] - self.bbox[2] - self.bbox[0],
            self.img.shape[0] - self.bbox[3] - self.bbox[1],
        )

    def strip_mask(self):
        r = self.mask[
            self.bbox[1] : self.bbox[1] + self.bbox[3], self.bbox[0] : self.bbox[0] + self.bbox[2]
        ]
        return r * self.strip().astype("bool")

    def imitated(self):
        spiece = (self.strip() * 0.3).astype("uint8")
        cont = np.array(
            [[[x - self.bbox[0], y - self.bbox[1]]] for (x, y), in self.cont], dtype="int"
        )
        return cv.drawContours(spiece, [cont], 0, (255, 255, 255), 1)


class Jigsaw:
    def __init__(self, origin: bytes, puzzle: bytes, piece: bytes, top: int) -> None:
        self.top = top
        self.ans = frombytes(origin)
        self.puzzle = frombytes(puzzle)
        self.piece = Piece(frombytes(piece, flags=cv.IMREAD_UNCHANGED))

    @staticmethod
    def save(ans, puzzle, piece, top):
        import yaml

        os.makedirs("data", exist_ok=True)
        ex = len([i for i in os.listdir("data") if i.endswith(".yml")])
        with open(f"data/{ex}.yml", "w") as f:
            yaml.safe_dump({"origin": ans, "puzzle": puzzle, "piece": piece, "top": top}, f)

    @classmethod
    def load(cls, filename):
        import yaml

        with open(filename) as f:
            return cls(**yaml.safe_load(f))

    @property
    def width(self) -> int:
        return self.ans.shape[1]

    @property
    def rate(self):
        # TODO: operation width / 680
        return TC_OPERATION_WIDTH / 680

    @property
    def left(self):
        if not hasattr(self, "_left"):
            self._left = self.solve() - self.piece.padding[0]
        return self._left

    def solve(self) -> int:
        spiece = self.piece.imitated()
        top = self.top + self.piece.padding[1]

        r = cv.matchTemplate(
            self.puzzle[top : top + self.piece.bbox[3]],
            spiece,
            cv.TM_CCOEFF_NORMED,
            mask=self.piece.strip_mask(),
        )
        left = int(np.argmax(r))

        if debug:
            cv.imshow("match", np.tile(r, (200, 1)))
            cv.imshow("spiece", spiece)

            cont = [
                [[x + left - self.piece.padding[0], y + self.top]] for (x, y), in self.piece.cont
            ]
            cont = np.array(cont, dtype="int")
            d = cv.drawContours(self.puzzle, [cont], 0, (0, 0, 255), 2)
            cv.imshow("contour", d)
            cv.waitKey()

        return left
