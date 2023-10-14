import typing as t

from tylisten import hookdef

__all__ = ["qr_cancelled", "qr_fetched", "qr_refresh", "sms_code_input"]


@hookdef
def qr_fetched(png: bytes, times: int, qr_renew=False):
    """
    :param png: QR bytes (png format)
    :param times: QR **expire** times in this session
    :param qr_renew: this refresh is requested by user
    """


@hookdef
def qr_cancelled():
    """qr cancelled"""


@hookdef
def qr_refresh():
    """qr refreshed"""


@hookdef
def sms_code_input(uin: int, phone: str, nickname: str) -> t.Optional[str]:
    """
    :param uin: uin
    :param phone: User's binded phone number.
    :param nickname: Nickname of current login user.
    :return: User received SMS verify code.
    """
