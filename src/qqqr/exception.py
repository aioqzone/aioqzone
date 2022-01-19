class TencentLoginError(RuntimeError):
    def __init__(self, code: int, msg: str, *args: object) -> None:
        self.code = code
        self.msg = msg
        super().__init__(*args)

    def __str__(self) -> str:
        return f"Code {self.code}: {self.msg}"


class UserBreak(KeyboardInterrupt):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
