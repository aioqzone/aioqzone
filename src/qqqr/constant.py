"""
date: 2021-07-20
"""

from enum import IntEnum

from .type import APPID, Proxy

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
AndroidUA = "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36 Edg/119.0.0.0"

QzoneProxy = Proxy(
    "https://qzs.qzone.qq.com/qzone/v5/loginsucc.html?para=izone",
    "https://qzs.qq.com/qzone/v6/portal/proxy.html",
)
"""Built-in web Qzone Proxy."""

QzoneH5Proxy = Proxy(
    "https://h5.qzone.qq.com/mqzone/index",
)
"""Built-in H5 Qzone Proxy."""

QzoneAppid = APPID(549000912, 5)
"""Built-in web Qzone appid and daid."""
QzoneH5Appid = APPID(549000929, 5)
"""Built-in H5 Qzone appid and daid."""


class StatusCode(IntEnum):
    """Qzone response code in login."""

    # Unified
    Authenticated = 0
    # QR
    Expired = 65
    Waiting = 66
    Scanned = 67
    # UP
    NeedCaptcha = 1
    WrongPassword = 3
    InvalidArguments = 7
    ForceQR = 10005
    NeedSmsVerify = 10009  # Means, notify the owner
    NoMobile = 10015
    RiskyNetwork = 23003
    RateLimit = 23011


captcha_status_description = {
    0: "verifySuccess",
    9: "verifyFailRefresh",
    12: "verifyError",
    20: "verifySessionTimeout",
    50: "verifyFail",
    30: "verifyHybrid",
    51: "verifyHybrid",
    52: "verifyError",
    206: "verifySessionTimeout",
}
