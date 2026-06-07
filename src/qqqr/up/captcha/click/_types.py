"""Click captcha stub (under construction).

.. warning::
    This captcha type is not yet supported and will raise
    :class:`NotImplementedError` if triggered.
"""

from .._model import PrehandleResp
from ..capsess import BaseTcaptchaSession


class ClickCaptchaSession(BaseTcaptchaSession):
    """Click captcha session (stub — raises NotImplementedError).

    .. warning::
        This captcha type is currently under construction.
    """

    def __init__(self, session: str, prehandle: PrehandleResp) -> None:
        super().__init__(session, prehandle)
        self.mouse_track.set_result(None)
