class TencentLoginError(RuntimeError):
    """This exception represents an error that occured in Qzone login,
    with at least an error code."""

    def __init__(self, code: int, msg: str, *args: object, subcode: int = ...) -> None:
        self.code = code
        self.msg = msg
        if subcode != ...:
            self.subcode = subcode
        super().__init__(*args)

    def __str__(self) -> str:
        return f"Code {self.code}: {self.msg}"


class UserBreak(KeyboardInterrupt):
    """This exception should be raised when user cancel the login spontaneously."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
