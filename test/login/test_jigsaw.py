from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from qqqr.constant import QzoneAppid, QzoneProxy
from qqqr.up import UpWebLogin
from qqqr.up.captcha import Captcha, TcaptchaSession
from qqqr.up.captcha.jigsaw import Jigsaw, imitate_drag

if TYPE_CHECKING:
    from test.conftest import test_env

    from qqqr.utils.net import ClientAdapter


@pytest_asyncio.fixture(scope="module")
async def captcha(client: ClientAdapter, env: test_env):
    login = UpWebLogin(client, QzoneAppid, QzoneProxy, env.uin, env.pwd.get_secret_value())
    upsess = await login.new()
    await login.check(upsess)
    captcha = login.captcha(upsess.check_rst.session)
    yield captcha


@pytest_asyncio.fixture(scope="module")
async def sess(client: ClientAdapter, captcha: Captcha):
    sess = await captcha.new()

    async def r(url):
        async with client.get(url) as r:
            r.raise_for_status()
            return r.content

    sess.cdn_imgs = list(await asyncio.gather(*(r(i) for i in sess.cdn_urls)))
    yield sess


@pytest.fixture(scope="module")
def jigsaw(sess: TcaptchaSession):
    piece_pos = tuple(
        slice(
            sess.piece_sprite.sprite_pos[i],
            sess.piece_sprite.sprite_pos[i] + sess.piece_sprite.size_2d[i],
        )
        for i in range(2)
    )
    yield Jigsaw(*sess.cdn_imgs, piece_pos=piece_pos, top=sess.piece_sprite.init_pos[1])


class TestPiece:
    def test_strip(self, jigsaw: Jigsaw):
        spiece = jigsaw.piece.strip()
        assert spiece.dtype.name == "uint8"
        assert spiece.shape[-1] == 3

    def test_strip_mask(self, jigsaw: Jigsaw):
        mask = jigsaw.piece.strip_mask()
        assert mask.dtype.name == "uint8"
        assert mask.shape[-1] == 1

    def test_template(self, jigsaw: Jigsaw):
        template = jigsaw.piece.build_template()
        assert template.dtype.name == "uint8"
        assert template.shape[-1] == 3


def test_solve(jigsaw: Jigsaw):
    left = jigsaw.solve() - jigsaw.piece.padding[0]
    assert left > 0


def test_imitate(sess: TcaptchaSession, jigsaw: Jigsaw):
    left = jigsaw.solve() - jigsaw.piece.padding[0]
    xs, ys = imitate_drag(sess.piece_sprite.init_pos[0], left, sess.piece_sprite.init_pos[1])
    assert len(xs) == len(ys)
