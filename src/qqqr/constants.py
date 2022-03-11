"""
date: 2021-07-20
"""

from enum import IntEnum

from .type import APPID, Proxy

QzoneProxy = Proxy(
    "https://qzs.qq.com/qzone/v6/portal/proxy.html",
    "https://qzs.qzone.qq.com/qzone/v5/loginsucc.html?para=izone",
)

QzoneAppid = APPID(549000912, 5)


class StatusCode(IntEnum):
    # Unified
    Authenticated = 0
    # QR
    Expired = 65
    Waiting = 66
    Scanned = 67
    # UP
    NeedCaptcha = 1
    WrongPassword = 3
    ForceQR = 10005
    NeedVerify = 10009  # Means, notify the owner
    RiskyNetwork = 23003
