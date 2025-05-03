import typing as t


class TencentLoginError(RuntimeError):
    """This exception represents that an error occured in Qzone **login**,
    with at least an error code."""

    def __init__(
        self, code: int, msg: str, *args: object, subcode: t.Optional[int] = None
    ) -> None:
        self.code = code
        self.msg = msg
        self.subcode = subcode
        super().__init__(*args)

    def __str__(self) -> str:
        subcode = "" if self.subcode is None else f"({self.subcode})"
        return f"Code {self.code}{subcode}: {self.msg}"


class UnexpectedInteraction(RuntimeError):
    """Represents that user didn't interact as expected."""

    def __init__(self, description: str, *args) -> None:
        super().__init__(description, *args)


class UserBreak(UnexpectedInteraction):
    """Represents that user cancels the login spontaneously.

    .. versionchanged:: 1.1.0

        Inherit from :exc:`UnexpectedInteraction`.
    """

    def __init__(self) -> None:
        super().__init__("用户取消了登录")


class UserTimeout(UnexpectedInteraction):
    """Represents that user doesn't interact as expected in a time.

    .. versionadded:: 1.1.0
    """

    def __init__(self, expected_interaction: str = "") -> None:
        super().__init__("用户未响应请求")
        self.expected_interaction = expected_interaction
