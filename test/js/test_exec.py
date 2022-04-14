import pytest

from jssupport.execjs import ExecJS
from jssupport.jsdom import JSDOM

pytestmark = pytest.mark.asyncio


def test_version():
    from shutil import which

    if which("node") is None:
        pytest.skip(allow_module_level=True)


async def test_exec():
    asis = ExecJS(js="function a(i){return i;}")
    assert "1" == await asis("a", 1)
    assert "true" == await asis("a", True)
    assert "1" == await ExecJS(js="a=1").get("a")


async def test_bind():
    asis = ExecJS(js="function a(i){return i;}")
    asis = asis.bind("a")
    assert "1" == await asis(1)
    assert "true" == await asis(True)


async def test_check_jsdom():
    dom = JSDOM(src="", ua="", location="", referrer="")
    assert dom.check_jsdom()
