from os import environ as env

import aioqzone.api.loginman as api
import pytest
from aioqzone.interface.hook import LoginEvent, QREvent
from qqqr.exception import TencentLoginError


@pytest.fixture(scope='class')
def up():
    man = api.UPLoginMan(env.get('TEST_UIN'), env.get('TEST_PASSWORD'))
    man.register_hook(LoginEvent())
    return man


@pytest.mark.incremental
class TestUP:
    def test_newcookie(self, up: api.UPLoginMan):
        try:
            assert 'p_skey' in up.new_cookie()
        except TencentLoginError:
            pytest.skip('Login failed.')

    def test_cookie(self, up: api.UPLoginMan):
        assert up.cookie

    def test_gtk(self, up: api.UPLoginMan):
        assert up.gtk


@pytest.fixture(scope='class')
def qr():
    import cv2 as cv
    import numpy as np

    class inner_qrevent(QREvent, LoginEvent):
        def QrFetched(self, png: bytes):
            def frombytes(b: bytes, dtype='uint8', flags=cv.IMREAD_COLOR) -> np.ndarray:
                return cv.imdecode(np.frombuffer(b, dtype=dtype), flags=flags)

            cv.destroyAllWindows()
            cv.imshow('Scan and login', frombytes(png))
            cv.waitKey()

    man = api.QRLoginMan(env.get('TEST_UIN'))
    man.register_hook(inner_qrevent())
    return man


@pytest.mark.needuser
class TestQR:
    def test_newcookie(self, qr: api.QRLoginMan):
        assert 'p_skey' in qr.new_cookie()

    def test_cookie(self, qr: api.QRLoginMan):
        assert qr.cookie

    def test_gtk(self, qr: api.QRLoginMan):
        assert qr.gtk

    def test_cancel(self, qr: api.QRLoginMan):
        qr.new_cookie()
        qr.hook.cancel()

    def test_resend(self, qr: api.QRLoginMan):
        qr.new_cookie()
        qr.hook.resend()
