from aioqzone.exception import QzoneError


def test_qzone_error_str():
    """QzoneError __str__ should return code and msg correctly"""
    err = QzoneError(10001, "test message")
    assert err.code == 10001
    assert err.msg == "test message"
    assert str(err) == "QzoneCode 10001: test message"


def test_qzone_error_with_robj():
    """QzoneError should support robj parameter"""
    robj = {"detail": "test"}
    err = QzoneError(-3000, robj=robj)
    assert err.robj is robj


def test_qzone_error_default_msg():
    """QzoneError should use default msg when no msg provided"""
    err = QzoneError(0)
    assert err.msg == "unknown"
    assert "unknown" in str(err)


def test_qzone_error_args_not_contain_self():
    """QzoneError args should not contain self (core of original bug)"""
    err = QzoneError(10001, "test message")
    assert err.args == ("test message",), "args should contain only the message"
    for arg in err.args:
        assert arg is not err, "args should not contain self"
