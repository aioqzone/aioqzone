from typing import Optional


class QzoneError(RuntimeError):
    """HTTP OK, but Qzone returns an error code."""

    msg = "unknown"

    def __init__(self, code: int, *args, rdict=None):
        self.code = int(code)
        self.rdict = rdict
        if len(args) > 0 and isinstance(args[0], str):
            self.msg = args[0]
        RuntimeError.__init__(self, *args)

    def __str__(self) -> str:
        return f"Code {self.code}: {self.msg}"


class LoginError(RuntimeError):
    """Login failed for some reasons."""

    def __init__(self, msg: str, strategy: Optional[str] = None) -> None:
        msg = "登陆失败: " + msg
        super().__init__(msg, strategy)
        self.msg = msg
        self.strategy = strategy

    def __str__(self) -> str:
        return f"{self.msg} (strategy={self.strategy})"


class CorruptError(ValueError):
    """Data corrupted in transfer."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class SkipLoginInterrupt(RuntimeError):
    """Login is skipped as intended."""

    pass
