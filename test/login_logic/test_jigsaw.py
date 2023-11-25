from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

pytest.importorskip("numpy")

import pytest_asyncio

from qqqr.up import UpH5Login
from qqqr.up.captcha import Captcha
from qqqr.up.captcha.slide import *

if TYPE_CHECKING:
    from test.conftest import test_env

    from qqqr.utils.net import ClientAdapter


@pytest_asyncio.fixture(scope="module")
async def login(client: ClientAdapter, env: test_env):
    login = UpH5Login(client, env.uin, env.password.get_secret_value())
    yield login


@pytest_asyncio.fixture(scope="module")
async def captcha(login: UpH5Login):
    upsess = await login.new()
    await login.check(upsess)
    captcha = login.captcha_solver(upsess.check_rst.session)
    yield captcha


@pytest_asyncio.fixture(scope="module")
async def sess(client: ClientAdapter, captcha: Captcha):
    sess = await captcha.new()
    if not isinstance(sess, SlideCaptchaSession):
        pytest.skip("not a slide captcha")

    await sess.get_captcha_problem(client)
    yield sess


@pytest.fixture(scope="module")
def jigsaw(sess: SlideCaptchaSession):
    yield sess.get_jigsaw_solver()


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


def test_imitate(sess: SlideCaptchaSession, jigsaw: Jigsaw):
    left = jigsaw.solve() - jigsaw.piece.padding[0]
    xs, ys = imitate_drag(sess.piece_sprite.init_pos[0], left, sess.piece_sprite.init_pos[1])
    assert len(xs) == len(ys)
