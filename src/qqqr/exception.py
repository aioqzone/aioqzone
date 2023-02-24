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
        return f"Code {self.code}({self.subcode}): {self.msg}"


class UserBreak(KeyboardInterrupt):
    """Represents that user cancels the login spontaneously."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class HookError(RuntimeError):
    """Once we await a hook, we expect that if the hook is broken, it will not mess up our
    own error handling. It is convenient to wrap an exception raise from hooks with this error.

    If the caller catches a `HookError`, it is recommended to omit the error. If something is broken
    by the hook, or something must be retrieved by the hook is not available, then it is recommended to
    reraise the exception.

    Omit the error if you can:
    >>> try:
    >>>     await hook_guard(inform_user)('hello')
    >>> except HookError as e:
    >>>     log.error("Hook raises an error", exc_info=e.__cause__) # do not reraise

    Reraise only when you have to:
    >>> try:
    >>>     need_input(await hook_guard(read_from_user)())
    >>> except HookError as e:
    >>>     raise e
    """

    def __init__(self, hook: Callable) -> None:
        self.hook = hook
        super().__init__(f"Error in hook: {hook.__qualname__}")
