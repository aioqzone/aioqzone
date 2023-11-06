class QzoneError(RuntimeError):
    """HTTP OK, but Qzone returns an error code."""

    msg = "unknown"

    def __init__(self, code: int, *args, robj: object = None):
        self.code = int(code)
        self.robj = robj
        if len(args) > 0 and isinstance(args[0], str):
            self.msg = args[0]
        super().__init__(self, *args)

    def __str__(self) -> str:
        return f"QzoneCode {self.code}: {self.msg}"


class UnexpectedLoginError(RuntimeError):
    """Represents that an unexpected error happens in login process."""

    pass


class CorruptError(ValueError):
    """Data corrupted in transfer."""

    pass
