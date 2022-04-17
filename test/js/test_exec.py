import pytest

from jssupport.execjs import ExecJS, Partial
from jssupport.jsdom import JSDOM

pytestmark = pytest.mark.asyncio


def test_version():
    if not ExecJS.check_node():
        pytest.skip(allow_module_level=True)


async def test_exec():
    asis = ExecJS()
    asis.setup.append("function a(i){return i;}")
    assert "1" == await asis(Partial("a", 1))
    assert "true" == await asis(Partial("a", True))
    assert "1" == await ExecJS().add_setup("a=1;", 0).get("a")


async def test_bind():
    asis = ExecJS()
    asis.setup.append("function a(){return Math.random();}")
    asis = asis.bind("a()")
    assert await asis() != await asis()


async def test_check_jsdom():
    dom = JSDOM(src="", ua="", location="", referrer="")
    assert dom.check_jsdom()
