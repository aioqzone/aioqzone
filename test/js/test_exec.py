import pytest

from jssupport.execjs import ExecJS, Partial
from jssupport.jsdom import JSDOM

pytestmark = pytest.mark.asyncio


async def test_version():
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


async def test_jsdom():
    assert JSDOM.check_jsdom()

    ua = "cherry"
    location = "http://a.com/here"
    referrer = "http://a.com/past"
    dom = JSDOM(ua=ua, location=location, referrer=referrer)
    assert await dom.get("window.navigator.userAgent") == ua
    assert await dom.get("window.document.location.href") == location
    assert await dom.get("window.document.referrer") == referrer
