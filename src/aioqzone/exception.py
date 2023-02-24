from typing import Optional, Sequence


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
    """Login failed for some reasons."""

    def __init__(self, msg: str, methods_tried: Optional[Sequence] = None) -> None:
        msg = "登陆失败: " + msg
        super().__init__(msg, methods_tried)
        self.msg = msg
        self.methods_tried = methods_tried or []

    def __str__(self) -> str:
        return f"{self.msg} (tried={self.methods_tried})"


class CorruptError(ValueError):
    """Data corrupted in transfer."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class SkipLoginInterrupt(RuntimeError):
    """Login is skipped as intended."""

    pass
