from os import environ as env
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

import cv2 as cv
import numpy as np

if TYPE_CHECKING:
    mat_u1 = np.ndarray[Any, np.dtype[np.uint8]]
    mat_i4 = np.ndarray[Any, np.dtype[np.int32]]
else:
    mat_u1 = mat_i4 = np.ndarray

debug = bool(env.get("AIOQZONE_JIGSAW_DEBUG"))


def frombytes(b: bytes, dtype="uint8", flags=cv.IMREAD_UNCHANGED) -> np.ndarray:
    return cv.imdecode(np.frombuffer(b, dtype=dtype), flags=flags)


def tobytes(img: mat_u1, ext=".png") -> bytes:
    _, arr = cv.imencode(ext, img)
    return arr.tobytes()


class Piece:
    """Represents the jigsaw piece."""

    mask: mat_u1
    """The alpha channel of the jigsaw piece, which is used as mask."""
    img: mat_u1
    """BGR channel of the jigsaw piece, which is masked by :obj:`.mask`"""
    bbox: Tuple[int, int, int, int]
    """The bounding box of the jigsaw piece in [x, y, w, h]"""
    cont: mat_i4
    """The contour of the jigsaw piece in [N, 1, 2]i4, the last axis represents (x,y)."""

    def __init__(self, img: mat_u1) -> None:
        self.mask = img[:, :, 3:]
        self.img = img[:, :, :3] * (self.mask >= 128)
        self.find_bbox()

    def find_bbox(self):
        """
        The crop method crops the image and saves the contour of the jigsaw piece.
        It also saves a bounding box for that contour, and calculates padding to be used in cropping.

        Use ::obj`.bbox` to get bounding box of the piece, and :obj:`.padding` to get padding size.
        """
        contours, _ = cv.findContours(
            cv.cvtColor(self.img, cv.COLOR_BGR2GRAY), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
        )
        # hierarchy array: (next, prev, child, parent)
        center = (int(self.img.shape[0] // 2), int(self.img.shape[1] // 2))
        contours = [
            contour
            for contour in contours
            if cv.pointPolygonTest(contour, center, False) == 1
            and cv.pointPolygonTest(contour, (0, 0), False) == -1
        ]

        assert len(contours) >= 1
        self.cont = contours[0]

        self.bbox = cv.boundingRect(self.cont)

        if debug:
            debug_out = Path("data/debug")
            debug_out.mkdir(exist_ok=True, parents=True)
            mask = cv.cvtColor(self.strip_mask(), cv.COLOR_GRAY2BGR)
            mask = cv.drawContours(mask, [self.cont - self.bbox[:2]], 0, (0, 0, 255), 1)
            cv.imwrite((debug_out / "tmplmask.png").as_posix(), mask)

    @property
    def padding(self) -> Tuple[int, int, int, int]:
        """The padding of the jigsaw piece sprite in [left, top, right, bottom]"""
        return (
            *self.bbox[:2],
            self.img.shape[1] - self.bbox[2] - self.bbox[0],
            self.img.shape[0] - self.bbox[3] - self.bbox[1],
        )

    @property
    def _yx_range(self) -> Tuple[slice, slice]:
        return (
            slice(self.bbox[1], self.bbox[1] + self.bbox[3]),
            slice(self.bbox[0], self.bbox[0] + self.bbox[2]),
        )

    def strip(self) -> mat_u1:
        """The strip method crops the image and returns exactly the piece w/o any padding.

        Once cropped, use `.bbox` to get bounding box of the piece,
        and use `.padding` to get padding size.
        """
        ys, xs = self._yx_range
        return self.img[ys, xs]

    def strip_mask(self) -> mat_u1:
        """Generate a mask for `cv2.matchTemplate` since the piece is in an irregular shape."""
        ys, xs = self._yx_range
        return self.mask[ys, xs]

    def build_template(self, a: float = 0.3) -> mat_u1:
        """This method attempts to generate a piece view like that on the puzzle.
        In order to help :meth:`cv2.matchTemplate` to get an accurate result.

        It will dim the original piece and draw its contour with white lines.

        :param a: coeff to be multiplied with the image in order to dim it, default as 0.3
        :return: generated piece image.
        """
        spiece = (self.strip() * a).astype("uint8")
        cont = self.cont - self.bbox[:2]
        return cv.drawContours(spiece, [cont], 0, (200, 200, 200), 1)

    def __bytes__(self) -> bytes:
        return tobytes(np.concatenate((self.img, self.mask), -1))


class Jigsaw:
    def __init__(
        self,
        background: bytes,
        sprites: bytes,
        top: int,
        piece_pos: Optional[Tuple[slice, slice]] = None,
    ) -> None:
        """
        :param background: a background image with a gap which has the same shape with the jigsaw piece.
        :param sprites: an image consits of some sprites, including the jigsaw piece.
        :param piece_pos: the piece position on the sprites image, in x-y order.
        :param top: the upper bound (so-called "top") of the gap on the puzzle image.
        """
        self.top = top
        self.background = frombytes(background, flags=cv.IMREAD_COLOR)

        piece = frombytes(sprites)
        if piece_pos is not None:
            xs, ys = piece_pos
            piece = piece[ys, xs]
        self.piece = Piece(piece)

    def save(self):
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
                {
                    "background": tobytes(self.background),
                    "sprites": bytes(self.piece),
                    "top": self.top,
                },
                f,
            )

    @classmethod
    def load(cls, filename):
        # type: (str | Path) -> Jigsaw
        """
        The load function loads a YAML file and use the data to initiate a :class:`Jigsaw`.

        :param filename: Specify the file to be loaded.
        :return: A :class:`Jigsaw` instance.
        """

        import yaml

        with open(filename) as f:
            return cls(**yaml.safe_load(f))

    @property
    def left(self) -> int:
        """Captcha answer."""
        if not hasattr(self, "_left"):
            self._left = self.solve() - self.piece.padding[0]
        return self._left

    def solve(self, left_bound: int = 50) -> int:
        """Solve the captcha using :meth:`cv2.matchTemplate`.

        :return: position with the max confidence. This might be the left of the piece position on the puzzle.
        """
        template = self.piece.build_template()
        left_bound += self.piece.padding[0]

        if not hasattr(self, "confidence"):
            top = self.top + self.piece.padding[1]

            self.confidence = cv.matchTemplate(
                self.background[top : top + self.piece.bbox[3], left_bound:],
                template,
                cv.TM_CCOEFF_NORMED,
                mask=self.piece.strip_mask(),
            )
        max_cfd_x = int(np.argmax(self.confidence)) + left_bound

        if debug:
            debug_out = Path("data/debug")
            debug_out.mkdir(exist_ok=True, parents=True)

            confmap = self.confidence - self.confidence.min()
            confmap /= confmap.max() / 255
            confmap = confmap.astype(np.uint8)
            confmap = np.pad(confmap, ((0, 0), (left_bound, template.shape[1] - 1)))
            confmap = np.tile(confmap, (128, 1))
            confmap = cv.cvtColor(confmap, cv.COLOR_GRAY2BGR)

            bgw_conf = np.concatenate([self.background, confmap], axis=0)
            cv.imwrite((debug_out / "bg_with_conf.png").as_posix(), bgw_conf)
            cv.imwrite((debug_out / "spiece.png").as_posix(), template)

            cont = self.piece.cont + np.array([max_cfd_x - self.piece.padding[0], self.top])
            d = cv.drawContours(self.background, [cont], 0, (0, 0, 255), 2)
            cv.imwrite((debug_out / "contour.png").as_posix(), d)

        return max_cfd_x


def imitate_drag(x1: int, x2: int, y: int) -> Tuple[List[int], List[int]]:
    """
    The imitate_drag function simulates a drag event.

    The function takes one argument, x, which is the number of pixels that the user drags.
    The function returns a tuple of lists containing three integers: [x_coordinate, y_coordinate].
    Each coordinate and time value is randomly generated according to corresponding rules.

    :param x1: Specify the position that the drag starts.
    :param x2: Specify the position that the drag ends.
    :param y: Specify the y-coordinate.
    :return: Two lists consist of the x coordinate and y coordinate
    """

    assert 0 < x1 < x2
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
