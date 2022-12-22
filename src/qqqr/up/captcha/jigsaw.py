from os import environ as env
from pathlib import Path
from typing import List, Tuple

import cv2 as cv
import numpy as np

debug = bool(env.get("AIOQZONE_JIGSAW_DEBUG"))

TC_OPERATION_WIDTH = 280


def frombytes(b, dtype="uint8", flags=cv.IMREAD_COLOR) -> np.ndarray:
    return cv.imdecode(np.asarray(bytearray(b), dtype=dtype), flags=flags)


class Piece:
    """Represents the jigsaw piece."""

    def __init__(self, img: np.ndarray, piece_pos: Tuple[slice, slice]) -> None:
        x, y = piece_pos
        piece = img[y, x]
        self.mask = piece[:, :, 3:]
        """alpha channel"""
        self.img = piece[:, :, :3] * (self.mask >= 128)
        """BGR channel masked by :obj:`.mask`"""

    def strip(self):
        """The strip method crops the image and returns exactly the piece w/o any padding.

        Once cropped, use `.bbox` to get bounding box of the piece,
        and use `.padding` to get padding size.
        """
        if not hasattr(self, "bbox"):
            self.crop()

        r = self.img[
            self.bbox[1] : self.bbox[1] + self.bbox[3], self.bbox[0] : self.bbox[0] + self.bbox[2]
        ]
        return r

    def crop(self):
        """
        The crop method crops the image and saves the contour of the jigsaw piece.
        It also saves a bounding box for that contour, and calculates padding to be used in cropping.

        Use `.bbox` to get bounding box of the piece, and `.padding` to get padding size.
        """
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
        self.cont = cont[0]

        self.bbox = cv.boundingRect(self.cont)
        self.padding = (
            *self.bbox[:2],
            self.img.shape[1] - self.bbox[2] - self.bbox[0],
            self.img.shape[0] - self.bbox[3] - self.bbox[1],
        )

    def strip_mask(self):
        """Generate a mask for `cv2.matchTemplate` since the piece is in an irregular shape."""
        r = self.mask[
            self.bbox[1] : self.bbox[1] + self.bbox[3], self.bbox[0] : self.bbox[0] + self.bbox[2]
        ]
        return r * self.strip().astype("bool")

    def imitated(self, a: float = 0.3):
        """This method attempts to generate a piece view like that on the puzzle.
        In order to help `cv2.matchTemplate` to get an accurate result.

        It will dim the original piece and draw its contour with white lines.

        :param a: coeff to be multiplied with the image in order to dim it, default as 0.3
        :return: generated piece image.
        """
        spiece = (self.strip() * a).astype("uint8")
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
    def save(puzzle: bytes, piece: bytes, piece_pos: Tuple[slice, slice], top: int):
        """
        The save function saves the puzzle, piece, piece_pos and top to a yaml file.

        :raises `ImportError`: if PyYaml not installed.
        """

        import yaml

        data_path = Path("./data")
        data_path.mkdir(exist_ok=True)
        ex = len(list(data_path.glob("*.yml")))
        with open(data_path / f"{ex}.yml", "w") as f:
            yaml.safe_dump(
                {"puzzle": puzzle, "piece": piece, "piece_pos": piece_pos, "top": top}, f
            )

    @classmethod
    def load(cls, filename):
        """
        The load function loads a YAML file and use the data to initiate a :class:`Jigsaw`.

        :param filename: Specify the file to be loaded.

        :raises `ImportError`: if PyYaml not installed.
        :return: A :class:`Jigsaw` instance.
        """

        import yaml

        with open(filename) as f:
            return cls(**yaml.safe_load(f))

    @property
    def width(self) -> int:
        """puzzle image width"""
        return self.puzzle.shape[1]

    @property
    def rate(self):
        # TODO: operation width / 680
        return TC_OPERATION_WIDTH / self.width

    @property
    def left(self) -> int:
        """Captcha answer."""
        if not hasattr(self, "_left"):
            self._left = self.solve() - self.piece.padding[0]
        return self._left

    def solve(self) -> int:
        """Solve the captcha using :meth:`cv2.matchTemplate`.

        :return: position with the max confidence. This might be the left of the piece position on the puzzle.
        """
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


def imitate_drag(x1: int, x2: int, y: int) -> Tuple[List[int], List[int]]:
    """
    The imitate_drag function simulates a drag event.

    The function takes one argument, x, which is the number of pixels that the user drags.
    The function returns a list of lists containing three integers: [x_coordinate, y_coordinate, time].
    Each coordinate and time value is randomly generated according to corresponding rules.

    :param x: Specify the number of pixels that the user drags.
    :return: A list of lists, where each sublist contains three elements: the x coordinate, y coordinate and time
    """

    assert 0 < x1 < x2 < 672
    assert 0 < y
    # 244, 1247
    n = np.random.randint(50, 65)
    clean_x = np.linspace(x1, x2, n, dtype=np.int16)
    noise_y = np.random.choice([y - 1, y + 1, y], (n,), replace=True, p=[0.1, 0.1, 0.8])

    nx = np.zeros((n,), dtype=np.int16)
    if n > 50:
        nx[1:-50] = np.random.randint(-3, 3, (n - 51,), dtype=np.int16)
    nx[-50:-20] = np.random.randint(-2, 2, (30,), dtype=np.int16)
    nx[-20:-1] = np.random.randint(-1, 1, (19,), dtype=np.int16)

    noise_x = clean_x + nx
    noise_x.sort()
    return noise_x.tolist(), noise_y.tolist()
