import typing as t

from tylisten import hookdef

__all__ = [
    "qr_cancelled",
    "qr_fetched",
    "sms_code_input",
    "solve_select_captcha",
    "solve_slide_captcha",
]


@hookdef
def qr_fetched(png: t.Optional[bytes], times: int, qr_renew=False) -> t.Any:
    """
    :param png: Optional QR bytes (png format). If None, the QR is pushed to user's mobile and there is no need to scan.
    :param times: QR **expire** times in this session
    :param qr_renew: this refresh is requested by user
    """


@hookdef
def qr_cancelled() -> t.Any:
    """qr cancelled"""


@hookdef
def sms_code_input(uin: int, phone: str, nickname: str) -> t.Optional[str]:
    """
    :param uin: uin
    :param phone: User's binded phone number.
    :param nickname: Nickname of current login user.
    :return: User received SMS verify code.
    """


@hookdef
def solve_select_captcha(prompt: str, imgs: t.Tuple[bytes, ...]) -> t.Sequence[int]:
    """This hook asks answers for a select captcha.

    :param prompt: the question of the select captcha
    :param imgs: the choice images of the select captcha

    :return: the image indexes which satisfy the question. Empty list will be treated as no answer.
    """
    return ()


@hookdef
def solve_slide_captcha(background: bytes, piece: bytes, init_pos: t.Tuple[int, int]) -> int:
    """This hook asks answers for a slide captcha.

    :param background: the slide captcha background (with a dimmed target area)
    :param piece: the slide piece (corresponding to the target area)
    :param init_pos: the (x, y) position of the initial piece.

    :return: the left position of the target area.
    """
    return 0
