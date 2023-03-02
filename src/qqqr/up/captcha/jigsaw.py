import io
from os import environ as env
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

import numpy as np
from numpy.fft import fft2, ifft2
from PIL import Image as image

if TYPE_CHECKING:
    mat_u1 = np.ndarray[Any, np.dtype[np.uint8]]
    mat_i4 = np.ndarray[Any, np.dtype[np.int32]]
else:
    mat_u1 = mat_i4 = np.ndarray

debug = bool(env.get("AIOQZONE_JIGSAW_DEBUG"))


def frombytes(b: bytes, dtype=np.uint8) -> mat_u1:
    buf = io.BytesIO(b)
    return np.asarray(image.open(buf), dtype=dtype)


def tobytes(img: mat_u1, format="png") -> bytes:
    buf = io.BytesIO()
    image.fromarray(img).save(buf, format)
    return buf.getvalue()


def conv2d(x: np.ndarray, k: np.ndarray, axes=(0, 1)):
    """
    :return: f8 array, with the shape of `x.shape - (k.shape - 1)`
    """
    kh, kw = k.shape[axes[0]], k.shape[axes[1]]
    out_shape = x.shape[axes[0]], x.shape[axes[1]]
    back = ifft2((fft2(x, axes=axes)) * fft2(k, axes=axes, s=out_shape), axes=axes)
    return back.real[kh - 1 :, kw - 1 :]


def corr_norm_mask_match(x: mat_u1, tmpl: mat_u1, mask: mat_u1):
    r"""``TM_CCORR_NORMED`` mode in opecv matchTemplate.

    .. math::

        R(x,y)= \frac{\sum_{x',y'} (T(x',y') \cdot I(x+x',y+y') \cdot M(x',y')^2)}{\sqrt{\sum_{x',y'} \left( T(x',y') \cdot M(x',y') \right)^2 \cdot \sum_{x',y'} \left( I(x+x',y+y') \cdot M(x',y') \right)^2}}
    """
    mask_template = mask * tmpl
    mask_template = np.flip(mask_template, axis=(0, 1))
    mask_template = mask_template / np.linalg.norm(mask_template, axis=(0, 1))
    corr = conv2d(x, mask_template)
    img_norm = np.sqrt(conv2d(np.power(x, 2), mask))
    img_norm[img_norm < 1e-12] = +np.inf
    return (corr / img_norm).sum(axis=-1)


def hdiff_corr_norm_mask_match(x: mat_u1, tmpl: mat_u1, mask: mat_u1):
    x = x.astype(np.int16)
    tmpl = tmpl.astype(np.int16)
    x_diff = x[:, 1:] - x[:, :-1]
    t_diff = tmpl[:, 1:] - tmpl[:, :-1]
    mask_u = mask[:, 1:] * mask[:, :-1]
    return corr_norm_mask_match(x_diff, t_diff, mask_u)


def vdiff_corr_norm_mask_match(x: mat_u1, tmpl: mat_u1, mask: mat_u1):
    x = x.astype(np.int16)
    tmpl = tmpl.astype(np.int16)
    y_diff = x[1:] - x[:-1]
    t_diff = tmpl[1:] - tmpl[:-1]
    mask_u = mask[1:] * mask[:-1]
    return corr_norm_mask_match(y_diff, t_diff, mask_u)


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
        super().__init__()
        self.mask = img[:, :, 3:]
        self.img = img[:, :, :3] * (self.mask >= 128)
        self.find_bbox()

    def find_bbox(self):
        """
        The crop method crops the image and saves the contour of the jigsaw piece.
        It also saves a bounding box for that contour, and calculates padding to be used in cropping.

        Use ::obj`.bbox` to get bounding box of the piece, and :obj:`.padding` to get padding size.
        """
        bool_map = self.img.mean(axis=-1) > 170
        accum_h = bool_map.sum(axis=0)
        accum_w = bool_map.sum(axis=1)

        h_center = bool_map.shape[1] // 2
        v_center = bool_map.shape[0] // 2

        bound_l = np.argwhere(accum_h[:h_center]).min()
        bound_r = np.argwhere(accum_h[h_center:]).max() + h_center

        bound_t = np.argwhere(accum_w[:v_center]).min()
        bound_b = np.argwhere(accum_w[v_center:]).max() + v_center

        self.bbox = (bound_l, bound_t, bound_r - bound_l, bound_b - bound_t)

        if debug:
            debug_out = Path("data/debug")
            debug_out.mkdir(exist_ok=True, parents=True)
            image.fromarray(self.mask[..., 0]).save(debug_out / "mask.png")

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
        """Generate a mask for :meth:`corr_norm_mask_match` since the piece is in an irregular shape."""
        ys, xs = self._yx_range
        return self.mask[ys, xs]

    def build_template(self, a: float = 0.3) -> mat_u1:
        """This method attempts to generate a piece view like that on the puzzle by dimming the original piece.
        In order to get an accurate result.

        :param a: coeff to be multiplied with the image in order to dim it, default as 0.3
        :return: generated piece image.
        """
        return (self.strip() * a).round().astype(np.uint8)

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
        super().__init__()
        self.top = top
        self.background = frombytes(background)

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
        """Solve the captcha using :meth:`corr_norm_mask_match`.

        :return: position with the max confidence. This might be the left of the piece position on the puzzle.
        """
        if not hasattr(self, "confidence"):
            template = self.piece.build_template()
            left_bound += self.piece.padding[0]
            top = self.top + self.piece.padding[1]

            x = self.background[top : top + self.piece.bbox[3], left_bound:]
            mask = (self.piece.strip_mask() > 170).astype(np.uint8)
            h_cfd = hdiff_corr_norm_mask_match(x, template, mask)
            v_cfd = vdiff_corr_norm_mask_match(x, template, mask)
            self.confidence = h_cfd + v_cfd

            if debug:
                debug_out = Path("data/debug")
                debug_out.mkdir(exist_ok=True, parents=True)

                def cfd_bands(confidence, h=50):
                    confmap = confidence - self.confidence.min()
                    confmap /= confmap.max() / 255
                    confmap = confmap.astype(np.uint8)
                    confmap = np.pad(confmap, ((0, 0), (left_bound, template.shape[1] - 1)))
                    confmap = np.tile(confmap[:, :, None], (h, 1, 3))
                    return confmap

                bgw_conf = np.concatenate(
                    [
                        self.background,
                        cfd_bands(h_cfd),
                        cfd_bands(v_cfd),
                        cfd_bands(self.confidence),
                    ],
                    axis=0,
                )
                image.fromarray(bgw_conf).save(debug_out / "bg_with_conf.png")
                image.fromarray(template).save(debug_out / "spiece.png")

        max_cfd_x = int(np.argmax(self.confidence)) + left_bound
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
