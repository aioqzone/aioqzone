class QzoneError(RuntimeError):
    """HTTP OK, but Qzone returns an error code.
    """
    def __init__(self, code: int, *args, rdict=None) -> None:
        self.code = code
        self.rdict = rdict
        super().__init__(*args)
