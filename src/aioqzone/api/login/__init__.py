"""
Collect some built-in login manager without persistant cookie.
Users can inherit these managers and implement their own persistance logic.
"""

import asyncio
import logging
import typing as t

from aiohttp import ClientError
from tenacity import TryAgain, retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from tylisten import FutureStore

from aioqzone.exception import UnexpectedLoginError
from aioqzone.model import QrLoginConfig, UpLoginConfig
from qqqr.exception import TencentLoginError, UnexpectedInteraction, UserBreak
from qqqr.qr import QrLogin
from qqqr.utils.net import ClientAdapter

from ._base import Loginable

log = logging.getLogger(__name__)

__all__ = [
    "ConstLoginMan",
    "UpLoginManager",
    "QrLoginManager",
    "QrLoginConfig",
    "UpLoginConfig",
]


class ConstLoginMan(Loginable):
    """A basic login manager which uses external provided cookie."""

    def __init__(
        self,
        uin: int,
        cookie: t.Optional[t.Dict[str, str]] = None,
        *,
        ch_login_notify: t.Optional[FutureStore] = None,
    ) -> None:
        super().__init__(uin, ch_login_notify=ch_login_notify)
        self.cookie = {} if cookie is None else cookie

    async def _new_cookie(self) -> t.Dict[str, str]:
        return self.cookie


class UpLoginManager(Loginable):
    def __init__(
        self,
        client: ClientAdapter,
        config: UpLoginConfig,
        *,
        h5=True,
        ch_login_notify: t.Optional[FutureStore] = None,
    ) -> None:
        super().__init__(config.uin, ch_login_notify=ch_login_notify)
        self.client = client
        self.config = config
        self.h5(h5, clear_cookie=False)  # init uplogin

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(min=1, max=6),
        retry=retry_if_exception_type(TryAgain),
        reraise=True,
    )
    async def _new_cookie(self) -> t.Dict[str, str]:
        """
        :raise `TencentLoginError`: Qzone login error.
        :raise `TryAgain`: Network error, or qzone login expired.
        :raise `UnexpectedLoginError`: All uncaught exceptions are wrapped by :exc:`UnexpectedLoginError`.

        .. versionchanged:: 1.1.0

            尽可能减少异常类型。未捕获的异常统一抛出为 :exc:`UnexpectedLoginError`

        :return: cookie dict
        """
        try:
            cookie = await self.uplogin.login()
        except TencentLoginError as e:
            if e.code in (-3000, -10000):
                raise TryAgain from e
            raise
        except NotImplementedError:
            from qqqr.constant import StatusCode

            raise TencentLoginError(StatusCode.NeedSmsVerify, "需要手机验证")
        except (GeneratorExit, ClientError) as e:
            log.warning(f"密码登录：{type(e).__name__}，重试", exc_info=True)
            log.debug(e.args, extra=e.__dict__)
            raise TryAgain from e
        except BaseException as e:
            log.fatal("密码登录异常", exc_info=True)
            raise UnexpectedLoginError from e

        return cookie

    def h5(self, enable=True, clear_cookie=True):
        """Change :obj:`.uplogin` to h5 login proxy.

        :param enable: use h5 mode or not
        :param clear_cookie: remove existing login cookie in :obj:`~Loginable.cookie`!
        """
        if clear_cookie:
            self.cookie.clear()
            self.client.cookie_jar.clear()

        if enable:
            from qqqr.up import UpH5Login as cls
        else:
            from qqqr.up.web import UpWebLogin as cls

        self.uplogin = cls(
            client=self.client,
            uin=self.config.uin,
            pwd=self.config.pwd.get_secret_value(),
            fake_ip=self.config.fake_ip and str(self.config.fake_ip),
            h5=enable,
        )
        self.sms_code_input = self.uplogin.sms_code_input
        self.solve_select_captcha = self.uplogin.captcha.solve_select_captcha
        self.solve_slide_captcha = self.uplogin.captcha.solve_slide_captcha


class QrLoginManager(Loginable):
    def __init__(
        self,
        client: ClientAdapter,
        config: QrLoginConfig,
        *,
        h5=True,
        ch_login_notify: t.Optional[FutureStore] = None,
    ) -> None:
        super().__init__(config.uin, ch_login_notify=ch_login_notify)
        self.client = client
        self.config = config
        self.h5(h5, clear_cookie=False)  # init uplogin

    async def _new_cookie(self) -> t.Dict[str, str]:
        """
        :raise `UnexpectedInteraction`: All exceptions caused by user, such as cancelling the login, or not scanning the QRcode.
        :raise `TryAgain`: Network error, or qzone login expired.
        :raise `UnexpectedLoginError`: All uncaught exceptions are wrapped by :exc:`UnexpectedLoginError`.

        .. versionchanged:: 1.1.0

            尽可能减少异常类型。未捕获的异常统一抛出为 :exc:`UnexpectedLoginError`

        :return: cookie dict
        """
        try:
            cookie = await self.qrlogin.login(
                refresh_times=self.config.max_refresh_times, poll_freq=self.config.poll_freq
            )
        except UnexpectedInteraction:
            raise
        except (KeyboardInterrupt, asyncio.CancelledError) as e:
            raise UserBreak from e
        except (GeneratorExit, ClientError) as e:
            log.warning(f"二维码登录：{type(e).__name__}，重试", exc_info=True)
            log.debug(e.args, extra=e.__dict__)
            raise TryAgain
        except BaseException as e:
            log.fatal("二维码登录异常", exc_info=True)
            raise UnexpectedLoginError from e

        return cookie

    def h5(self, enable=True, clear_cookie=True):
        """Change :obj:`.qrlogin` to h5 login proxy.

        :param enable: use h5 mode or not
        :param clear_cookie: remove existing login cookie in :obj:`~Loginable.cookie`!
        """
        if clear_cookie:
            self.cookie.clear()
            self.client.cookie_jar.clear()

        self.qrlogin = QrLogin(client=self.client, uin=self.uin, h5=enable)

        self.qr_fetched = self.qrlogin.qr_fetched
        self.qr_cancelled = self.qrlogin.qr_cancelled
        self.cancel_qr = self.qrlogin.cancel
        self.refresh_qr = self.qrlogin.refresh
