"""
date: 2021-07-20
"""

from enum import IntEnum

from .type import APPID, Proxy

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54"

QzoneProxy = Proxy(
    "https://qzs.qq.com/qzone/v6/portal/proxy.html",
    "https://qzs.qzone.qq.com/qzone/v5/loginsucc.html?para=izone",
)
"""Built-in web Qzone Proxy."""

QzoneAppid = APPID(549000912, 5)
"""Built-in web Qzone appid and daid."""


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
    RiskyNetwork = 23003
