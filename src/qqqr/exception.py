from typing import Callable


class TencentLoginError(RuntimeError):
    """This exception represents that an error occured in Qzone **login**,
    with at least an error code."""

    def __init__(
        self,
        code: int,
        msg: str,
        *args: object,
        subcode: int = ...,
    ) -> None:
        self.code = code
        self.msg = msg
        self.subcode = subcode
        super().__init__(*args)

    def __str__(self) -> str:
        subcode = "" if self.subcode is ... else f"({self.subcode})"
        return f"Code {self.code}{subcode}: {self.msg}"


class UserBreak(RuntimeError):
    """Represents that user cancels the login spontaneously.

    .. versionchanged:: 0.12.10

        Do not inherit from :exc:`KeyboardInterrupt`.
    """

    def __init__(self) -> None:
        super().__init__()
