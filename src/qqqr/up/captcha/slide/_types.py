import asyncio
import typing as t

from pydantic import BaseModel, Field

from qqqr.utils.iter import first
from qqqr.utils.net import ClientAdapter

from .._model import FgBindingCfg, FgElemCfg, Sprite
from ..capsess import BaseTcaptchaSession
from .jigsaw import Jigsaw, imitate_drag


class SlideBgElemCfg(Sprite):
    img_url: str
    """relative url to get jigsaw puzzle image (background with dimmed piece shape)."""
    init_pos: t.List[int] = Field(default=[0, 0])
    """sprite init position on captcha (x, y)"""


class SlideCaptchaDisplay(BaseModel):
    bg: SlideBgElemCfg = Field(alias="bg_elem_cfg")
    """Background (puzzle)"""
    fg_binding_list: t.List[FgBindingCfg] = Field(default=[])
    sprites: t.List[FgElemCfg] = Field(alias="fg_elem_list")
    """Foreground sprites"""
    sprite_url: str
    """relative url to get jigsaw piece (and handle) image."""


class SlideCaptchaSession(BaseTcaptchaSession):
    def parse_captcha_data(self):
        super().parse_captcha_data()
        self.render = SlideCaptchaDisplay.model_validate(self.conf.render)
        self.cdn_urls = (
            self._cdn_join(self.render.bg.img_url),
            self._cdn_join(self.render.sprite_url),
        )
        self.cdn_imgs: t.List[bytes] = []

        self.piece_sprite = first(self.render.sprites, lambda s: s.move_cfg)
        assert self.piece_sprite.move_cfg
        if self.piece_sprite.move_cfg.data_type:
            self.data_type = self.piece_sprite.move_cfg.data_type[0]

    async def get_captcha_problem(self, client: ClientAdapter):
        """
        The get_captcha_problem function is a coroutine that accepts a TcaptchaSession object as an argument.
        It then uses the selfion to make an HTTP GET request to the captcha images (the problem). The images
        will be stored in the given selfion.

        :param self: captcha selfion
        :return: None
        """

        async def r(url) -> bytes:
            async with client.get(url) as r:
                r.raise_for_status()
                return await r.content.read()

        self.cdn_imgs = list(await asyncio.gather(*(r(i) for i in self.cdn_urls)))

    def get_jigsaw_solver(self):
        get_slice = lambda i: slice(
            self.piece_sprite.sprite_pos[i],
            self.piece_sprite.sprite_pos[i] + self.piece_sprite.size_2d[i],
        )
        piece_pos = get_slice(0), get_slice(1)

        return Jigsaw(*self.cdn_imgs, piece_pos=piece_pos, top=self.piece_sprite.init_pos[1])

    async def solve_captcha(self):
        """
        The solve_captcha function solves the captcha problem. It assumes that :obj:`TcaptchaSession.cdn_imgs`
        is already initialized, so call :meth:`.get_captcha_problem` firstly.

        It then solve the captcha as that in :class:`.Jigsaw`. The answer is saved into `self`.

        This function will also call :meth:`TDC.set_data` to imitate human behavior when solving captcha.

        :param self: Store the information of the current selfion
        :return: None
        """
        assert self.cdn_imgs

        jig = self.get_jigsaw_solver()
        # BUG: +1 to ensure left > init_pos[0], otherwise it's >=.
        # However if left == init_pos[0] + 1, it is certainly a wrong result.
        left = jig.solve(self.piece_sprite.init_pos[0] + 1)

        xs, ys = imitate_drag(self.piece_sprite.init_pos[0], left, jig.top)
        self.mouse_track.set_result(list(zip(xs, ys)))

        return f"{left},{jig.top}"
