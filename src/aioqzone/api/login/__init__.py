"""
Collect some built-in login manager without persistant cookie.
Users can inherit these managers and implement their own persistance logic.

.. versionchanged:: 0.14.0

    Removed ``UPLoginMan`` and ``QRLoginMan``. Renamed ``MixedLoginMan`` to :class:`UnifiedLoginManager`.
    For the removed managers, use :class:`.UnifiedLoginManager` instead.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Sequence, Union

from httpx import ConnectError, HTTPError
from tylisten.futstore import FutureStore

from aioqzone.exception import LoginError, SkipLoginInterrupt
from aioqzone.message import LoginMethod
from aioqzone.model import QrLoginConfig, UpLoginConfig
from qqqr.exception import TencentLoginError, UserBreak
from qqqr.qr import QrLogin
from qqqr.up import UpH5Login
from qqqr.utils.net import ClientAdapter

from ._base import Loginable

log = logging.getLogger(__name__)

__all__ = ["ConstLoginMan", "UnifiedLoginManager", "LoginMethod", "QrLoginConfig", "UpLoginConfig"]


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

    .. versionchanged:: 0.14.0

        Renamed to ``UnifiedLoginManager``.
    """

    _order: List[LoginMethod]

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
        self.client = client
        self.channel = FutureStore()

        self.h5(h5, clear_cookie=False)  # init uplogin and qrlogin
        self.sms_code_required = self.uplogin.sms_code_required
        self.sms_code_input = self.uplogin.sms_code_input
        if self.up_config.uin > 0:
            self._order.append("up")

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
        """Returns order of :obj:`LoginMethod`. Assign a :obj:`LoginMethod` :obj:`Sequence` to this to
        change the order of :obj:`LoginMethod`."""
        return self._order

    @order.setter
    def order(self, v: Sequence[LoginMethod]):
        v = list(v)
        if "qr" in v and self.qr_config.uin <= 0:
            raise ValueError(self.qr_config)
        if "up" in v and self.up_config.uin <= 0:
            raise ValueError(self.up_config)
        self._order = v

    async def _try_up_login(self) -> Union[Dict[str, str], str]:
        """
        :raises:
            Exceptions except for :exc:`TencentLoginError`, :exc:`NotImplementedError`,
            :exc:`GeneratorExit`, :exc:`httpx.ConnectError`, :exc:`httpx.HTTPError`

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
        :raises:
            Exceptions except for :exc:`UserBreak`, :exc:`KeyboardInterrupt`, :exc:`asyncio.CancelledError`,
            :exc:`asyncio.TimeoutError`, :exc:`GeneratorExit`, :exc:`httpx.ConnectError`, :exc:`httpx.HTTPError`

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
        :raise `aioqzone.exception.SkipLoginInterrupt`: if :obj:`.order` returns an empty list.
        :raise `aioqzone.exception.LoginError`: if all login methods failed.

        :return: cookie dict
        """
        methods = self.order.copy()
        if not methods:
            log.info("No method selected for this login, raise SkipLoginInterrupt.")
            raise SkipLoginInterrupt

        log.info(f"Methods selected for this login: {methods}")
        loginables = dict(up=self._try_up_login, qr=self._try_qr_login)

        reasons: Dict[LoginMethod, str] = {}
        fail_with = lambda meth, msg: self.channel.add_awaitable(
            self.login_failed.emit(uin=self.uin, method=meth, exc=str(msg))
        )

        for m in methods:
            try:
                result = await loginables[m]()
            except BaseException as e:
                fail_with(m, e)
                break

            if isinstance(result, str):
                fail_with(m, result)
                reasons[m] = result
            else:
                return result

        raise LoginError(reasons=reasons)

    def h5(self, enable=True, clear_cookie=True):
        """Change :obj:`.qrlogin` and :obj:`.uplogin` to h5 login proxy.

        :param enable: use h5 mode or not
        :param clear_cookie: remove existing login cookie in :obj:`~Loginable.cookie`!

        .. versionchanged:: 0.14.1

            Allow user to switch h5 back; Allow to skip clearing cookie.
        """
        if clear_cookie:
            self._cookie.clear()
            self.client.client.cookies.clear()

        if enable:
            from qqqr.up import UpH5Login as cls
        else:
            from qqqr.up.web import UpWebLogin as cls
        self.uplogin = cls(
            client=self.client,
            uin=self.up_config.uin,
            pwd=self.up_config.pwd.get_secret_value(),
            h5=enable,
        )
        self.qrlogin = QrLogin(client=self.client, h5=enable)
