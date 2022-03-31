import pytest

from jssupport.execjs import ExecJS

pytestmark = pytest.mark.asyncio


def test_version():
    if ExecJS().version() is None:
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
