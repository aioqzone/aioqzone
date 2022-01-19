from os import environ as env

import pytest
from qqqr.constants import QzoneAppid, QzoneProxy, StatusCode
from qqqr.lc import LCLogin

needuser = pytest.mark.skipif(not env.get('QR_OK', 0), reason='need user interaction')


def setup_module():
    global login
    login = LCLogin(QzoneAppid, QzoneProxy, env.get('TEST_UIN'))
    # login.request()


@needuser
def test_local():
    login.checkLoginList()
    login.login()
