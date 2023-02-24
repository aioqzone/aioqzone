"""
date: 2021-07-20
"""

from enum import IntEnum

from .type import APPID, Proxy

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54"
AndroidUA = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36 Edg/110.0.1587.50"

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
    RiskyNetwork = 23003
