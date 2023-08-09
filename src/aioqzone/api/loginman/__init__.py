"""
Collect some built-in login manager w/o caching.
Users can inherit these managers and implement their own caching logic.

.. versionchanged:: 0.14.0

    Removed ``UPLoginMan`` and ``QRLoginMan``. Renamed ``MixedLoginMan`` to `.UnifiedLoginManager`.
    For the removed to managers, use `.UnifiedLoginManager` instead.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Sequence, Union

from httpx import ConnectError, HTTPError
from tylisten.futstore import FutureStore

import aioqzone._messages as MT
from aioqzone.exception import LoginError, SkipLoginInterrupt
from aioqzone.models.config import QrLoginConfig, UpLoginConfig
from qqqr.exception import TencentLoginError, UserBreak
from qqqr.qr import QrLogin
from qqqr.up import UpH5Login
from qqqr.utils.net import ClientAdapter

from ._base import Loginable

log = logging.getLogger(__name__)


class ConstLoginMan(Loginable):
    """A basic login manager which uses external provided cookie."""

    def __init__(self, uin: int, cookie: Dict[str, str]) -> None:
        super().__init__(uin)
        self._cookie = cookie

    @Loginable.cookie.setter
    def cookie(self, v: Dict[str, str]):
        self._cookie = v

    async def _new_cookie(self) -> Dict[str, str]:
        return self._cookie


class UnifiedLoginManager(Loginable):
    """A login manager that will try methods according to the given :obj:`.order`.

    .. versionchanged:: 0.12.0

        Make it a :class:`EventManager`.

    .. versionchanged:: 0.14.0
    """

    _order: List[MT.LoginMethod]

    def __init__(
        self,
        client: ClientAdapter,
        up_config: Optional[UpLoginConfig] = None,
        qr_config: Optional[QrLoginConfig] = None,
        *,
        h5=True,
    ) -> None:
        self.up_config = up_config or UpLoginConfig()
        self.qr_config = qr_config or QrLoginConfig()
        super().__init__(self.up_config.uin or self.qr_config.uin)

        self._order = []
        self.channel = FutureStore()

        if h5:
            cls = UpH5Login
        else:
            from qqqr.up import UpWebLogin as cls
        self.uplogin = cls(
            client=client, uin=self.up_config.uin, pwd=self.up_config.pwd.get_secret_value(), h5=h5
        )
        self.sms_code_required = self.uplogin.sms_code_required
        self.sms_code_input = self.uplogin.sms_code_input
        if self.up_config.uin > 0:
            self._order.append("up")

        self.qrlogin = QrLogin(client=client, h5=h5)
        self.refresh_times = self.qr_config.max_refresh_times
        self.poll_freq = self.qr_config.poll_freq
        self.qr_fetched = self.qrlogin.qr_fetched
        self.qr_cancelled = self.qrlogin.qr_cancelled
        self.cancel_qr = self.qrlogin.cancel
        self.refresh_qr = self.qrlogin.refresh
        if self.qr_config.uin > 0:
            self._order.append("qr")

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, v: Sequence[MT.LoginMethod]):
        v = list(v)
        if "qr" in v and self.qr_config.uin <= 0:
            raise ValueError(self.qr_config)
        if "up" in v and self.up_config.uin <= 0:
            raise ValueError(self.up_config)
        self._order = v

    async def _try_up_login(self) -> Union[Dict[str, str], str]:
        """
        :meta public:
        :raise `~qqqr.exception.TencentLoginError`: login error when up login.
        :raise `~aioqzone.api.loginman._NextMethodInterrupt`: if acceptable errors occured, for example, http errors.
        :raise `~qqqr.exception.HookError`: an error is raised from hook
        :raises: Any unexpected exception will be reraise.

        .. versionchanged:: 0.12.9

            Do not raise :exc:`SystemExit` any more. Any unexpected error will be reraised.

        :return: cookie dict
        """
        try:
            cookie = await self.uplogin.login()
        except TencentLoginError as e:
            log.warning(e := str(e))
            return e
        except NotImplementedError as e:
            log.warning(str(e))
            return "10009：需要手机验证"
        except (GeneratorExit, ConnectError, HTTPError) as e:
            omit_exc_info = isinstance(e, (GeneratorExit, ConnectError))
            log.warning(f"{type(e).__name__} captured, continue.", exc_info=not omit_exc_info)
            log.debug(e.args, extra=e.__dict__)
            return str(e)
        except:
            log.fatal("密码登录抛出未捕获的异常.", exc_info=True)
            raise
            return "密码登录期间出现奇怪的错误😰请检查日志以便寻求帮助."

        return cookie

    async def _try_qr_login(self) -> Union[Dict[str, str], str]:
        """
        :meta public:
        :raise `~qqqr.exception.UserBreak`: qr polling task is canceled
        :raise `~aioqzone.api.loginman._NextMethodInterrupt`: on exceptions do not break the system, such as timeout, Http errors, etc.
        :raise `~qqqr.exception.HookError`: an error is raised from hook
        :raises: Any unexpected exception will be reraise.

        .. versionchanged:: 0.12.9

            Do not raise :exc:`SystemExit` any more. Any unexpected error will be reraised.

        :return: cookie dict
        """

        try:
            cookie = await self.qrlogin.login(
                refresh_times=self.refresh_times, poll_freq=self.poll_freq
            )
        except (UserBreak, KeyboardInterrupt, asyncio.CancelledError) as e:
            return "用户取消了登录"
        except (asyncio.TimeoutError, GeneratorExit, ConnectError, HTTPError) as e:
            omit_exc_info = isinstance(e, (ConnectError, GeneratorExit, asyncio.TimeoutError))
            log.warning(f"{type(e).__name__} captured, continue.", exc_info=not omit_exc_info)
            log.debug(e.args, extra=e.__dict__)
            return str(e)
        except:
            log.fatal("Unexpected error in QR login.", exc_info=True)
            raise
            return "二维码登录期间出现奇怪的错误😰请检查日志以便寻求帮助."

        return cookie

    async def _new_cookie(self) -> Dict[str, str]:
        """
        :meta public:
        :raise `qqqr.exception.UserBreak`: if qr login is canceled and no succeeding method exist and success.
        :raise `aioqzone.exception.SkipLoginInterrupt`: if all login methods are removed by subclasses.
        :raise `aioqzone.exception.LoginError`: if all login methods failed.
        :raises: Any unexpected exceptions.

        :return: cookie dict
        """
        methods = self.order.copy()
        if not methods:
            log.info("No method selected for this login, raise SkipLoginInterrupt.")
            raise SkipLoginInterrupt

        log.info(f"Methods selected for this login: {methods}")
        loginables = dict(up=self._try_up_login, qr=self._try_qr_login)

        msg = ""
        methods_tried: List[MT.LoginMethod] = []
        fail_with = lambda meth, msg: self.channel.add_awaitable(
            self.login_failed.emit(uin=self.uin, method=meth, exc=str(msg))
        )

        for m in methods:
            methods_tried.append(m)
            try:
                result = await loginables[m]()
            except BaseException as e:
                fail_with(m, e)
                break

            if isinstance(result, str):
                fail_with(m, result)
                meth_name = dict(qr="二维码登录", up="密码登录")[m]
                msg += f"{meth_name}: {result}\n"
            else:
                return result

        raise LoginError(msg, methods_tried=methods_tried)

    def h5(self):
        """Change all manager in :obj:`loginables` to h5 login proxy.

        .. note:: This will remove existing login cookie in :obj:`.cookie`!

        .. versionadded:: 0.12.6
        """
        self.qrlogin = QrLogin(client=self.qrlogin.client, uin=self.qr_config.uin, h5=True)
        self.uplogin = UpH5Login(
            client=self.uplogin.client,
            uin=self.up_config.uin,
            pwd=self.up_config.pwd.get_secret_value(),
            h5=True,
        )
