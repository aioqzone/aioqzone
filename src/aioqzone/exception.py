from typing import Mapping

from aioqzone.model import LoginMethod

_meth_name = dict(up="密码登录", qr="二维码登录")  # type: dict[LoginMethod, str]


class QzoneError(RuntimeError):
    """HTTP OK, but Qzone returns an error code."""

    msg = "unknown"

    def __init__(self, code: int, *args, rdict=None):
        self.code = int(code)
        self.rdict = rdict
        if len(args) > 0 and isinstance(args[0], str):
            self.msg = args[0]
        super().__init__(self, *args)

    def __str__(self) -> str:
        return f"Code {self.code}: {self.msg}"


class LoginError(RuntimeError):
    """Login failed for some reasons.

    .. versionchanged:: 0.12.9

        ``methods_tried`` is not optional.

    .. versionchanged:: 0.14.1

        ``msg`` and ``methods_tried`` is merged to a single parameter :obj:`reasons`.
    """

    def __init__(
        self,
        reasons: Mapping[LoginMethod, str],
    ) -> None:
        super().__init__(reasons)
        self.reasons = reasons

    @property
    def methods_tried(self):
        """Login methods that have been tried in this login."""
        return tuple(self.reasons.keys())

    def __str__(self) -> str:
        return "；".join(f"{_meth_name[k]}：{v}" for k, v in self.reasons.items())


class CorruptError(ValueError):
    """Data corrupted in transfer."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class SkipLoginInterrupt(RuntimeError):
    """Login is skipped as intended."""

    pass
