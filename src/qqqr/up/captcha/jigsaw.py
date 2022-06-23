from pathlib import Path
from random import choices, randint
from typing import List, Tuple

import cv2 as cv
import numpy as np

debug = False

TC_OPERATION_WIDTH = 279


def frombytes(b, dtype="uint8", flags=cv.IMREAD_COLOR) -> np.ndarray:
    return cv.imdecode(np.asarray(bytearray(b), dtype=dtype), flags=flags)


class Piece:
    def __init__(self, img: np.ndarray, piece_pos: Tuple[slice, slice]) -> None:
        x, y = piece_pos
        piece = img[y, x]
        self.mask = piece[:, :, 3:]
        self.img = piece[:, :, :3] * (self.mask >= 128)

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
    def __init__(
        self, puzzle: bytes, piece: bytes, piece_pos: Tuple[slice, slice], top: int
    ) -> None:
        self.top = top
        self.puzzle = frombytes(puzzle)
        self.piece = Piece(frombytes(piece, flags=cv.IMREAD_UNCHANGED), piece_pos)

    @staticmethod
    def save(puzzle, piece, top):
        import yaml

        data_path = Path("./data")
        data_path.mkdir(exist_ok=True)
        ex = len(list(data_path.glob("*.yml")))
        with open(data_path / f"{ex}.yml", "w") as f:
            yaml.safe_dump({"puzzle": puzzle, "piece": piece, "top": top}, f)

    @classmethod
    def load(cls, filename):
        import yaml

        with open(filename) as f:
            return cls(**yaml.safe_load(f))

    @property
    def width(self) -> int:
        return self.puzzle.shape[1]

    @property
    def rate(self):
        # TODO: operation width / 680
        return TC_OPERATION_WIDTH / 680

    @property
    def left(self) -> int:
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
            debug_out = Path("data/debug")
            debug_out.mkdir(exist_ok=True, parents=True)
            cv.imwrite((debug_out / "match.png").as_posix(), np.tile(r * 255, (200, 1)))  # type: ignore
            cv.imwrite((debug_out / "spiece.png").as_posix(), spiece)

            cont = [
                [[x + left - self.piece.padding[0], y + self.top]] for (x, y), in self.piece.cont
            ]
            cont = np.array(cont, dtype="int")
            d = cv.drawContours(self.puzzle, [cont], 0, (0, 0, 255), 2)
            cv.imwrite((debug_out / "contour.png").as_posix(), d)

        return left


def imitate_drag(x: int) -> List[List[int]]:
    assert x < 300
    # 244, 1247
    t = randint(1200, 1300)
    n = randint(50, 65)
    X = lambda i: randint(1, max(2, i // 10)) if i < n - 15 else randint(6, 12)
    Y = lambda: choices([-1, 1, 0], cum_weights=[0.1, 0.2, 1], k=1)[0]
    T = lambda: randint(*choices(((65, 280), (6, 10)), cum_weights=(0.05, 1), k=1)[0])
    xs = ts = 0
    drag = []
    for i in range(n):
        xi, ti = X(i), T()
        drag.append([xi, Y(), ti])
        xs += xi
        ts += ti
    drag.append([max(1, x - xs), Y(), max(1, t - ts)])
    drag.reverse()
    return drag
