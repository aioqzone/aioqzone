"""
Collect some built-in login manager w/o caching.
Users can inherit these managers and implement their own caching logic.
"""

import asyncio
import logging
from typing import Dict, Optional, Sequence

from httpx import ConnectError, HTTPError
from tylisten import Emitter, VirtualEmitter, null_emitter, null_vemitter
from tylisten.futstore import FutureStore

import aioqzone._messages as MT
from aioqzone.exception import LoginError, SkipLoginInterrupt
from qqqr.constant import QzoneH5Proxy, StatusCode
from qqqr.exception import TencentLoginError, UserBreak
from qqqr.qr import QrLogin
from qqqr.utils.net import ClientAdapter

from ._base import Loginable

log = logging.getLogger(__name__)


class _NextMethodInterrupt(RuntimeError):
    """Internal exception represents the condition that the login method is interrupted and the caller
    could choose the next login method or just to raise a :exc:`.LoginError`.
    """

    pass


class ConstLoginMan(Loginable):
    """Only for test"""

    def __init__(self, uin: int, cookie: dict) -> None:
        super().__init__(uin)
        self._cookie = cookie

    async def _new_cookie(self) -> Dict[str, str]:
        return self._cookie


class _external_futstore:
    def __init__(self, *args, fs: Optional[FutureStore] = None, **kwds) -> None:
        super().__init__(*args, **kwds)
        self.login_notify_channel = fs or FutureStore()


class UPLoginMan(_external_futstore, Loginable):
    """Login manager for username-password login.
    This manager may trigger :meth:`~aioqzone.event.login.LoginEvent.LoginSuccess` and
    :meth:`~aioqzone.event.login.LoginEvent.LoginFailed` hook.
    """

    def __init__(
        self,
        client: ClientAdapter,
        uin: int,
        pwd: str,
        *,
        h5=False,
        fs: Optional[FutureStore] = None,
    ) -> None:
        assert pwd
        super().__init__(fs=fs, uin=uin)
        self.client = client
        if h5:
            from qqqr.constant import QzoneH5Appid as appid
            from qqqr.constant import QzoneH5Proxy as proxy
            from qqqr.up import UpH5Login as cls
        else:
            from qqqr.constant import QzoneAppid as appid
            from qqqr.constant import QzoneProxy as proxy
            from qqqr.up import UpWebLogin as cls
        self.uplogin = cls(self.client, appid, proxy, self.uin, pwd)

    # fmt: off
    @property
    def sms_code_required(self): return self.uplogin.sms_code_required
    @property
    def sms_code_input(self): return self.uplogin.sms_code_input
    # fmt: on

    async def _new_cookie(self) -> Dict[str, str]:
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
        emit_hook = lambda c: self.login_notify_channel.add_awaitable(c)
        emit_fail = lambda exc: emit_hook(
            self.login_failed.emit(uin=self.uin, method="up", exc=str(exc))
        )
        try:
            cookie = await self.uplogin.login()
        except TencentLoginError as e:
            log.warning(str(e))
            emit_fail(e)
            raise
        except NotImplementedError as e:
            log.warning(str(e))
            emit_fail("10009：需要手机验证")
            raise TencentLoginError(
                StatusCode.NeedSmsVerify, "Dynamic code verify not implemented"
            ) from e
        except (GeneratorExit, ConnectError, HTTPError) as e:
            omit_exc_info = isinstance(e, (GeneratorExit, ConnectError))
            log.warning(f"{type(e).__name__} captured, continue.", exc_info=not omit_exc_info)
            log.debug(e.args, extra=e.__dict__)
            emit_fail(e)
            raise _NextMethodInterrupt from e
        except:
            log.fatal("密码登录抛出未捕获的异常.", exc_info=True)
            emit_fail("密码登录期间出现奇怪的错误😰请检查日志以便寻求帮助.")
            raise

        emit_hook(self.login_success.emit(uin=self.uin, method="up"))
        return cookie

    def h5(self):
        """Realloc a :class:`LoginBase` object.

        .. versionadded:: 0.12.6
        """
        from qqqr.constant import QzoneH5Appid as appid
        from qqqr.constant import QzoneH5Proxy as proxy
        from qqqr.up import UpH5Login

        self.uplogin = UpH5Login(self.client, appid, proxy, self.uin, self.uplogin.pwd)


class QRLoginMan(_external_futstore, Loginable):
    """Login manager for QR login.
    This manager may trigger :meth:`~aioqzone.event.login.LoginEvent.LoginSuccess` and
    :meth:`~aioqzone.event.login.LoginEvent.LoginFailed` hook.
    """

    def __init__(
        self,
        client: ClientAdapter,
        uin: int,
        *,
        refresh_times: int = 6,
        poll_freq: float = 3,
        h5=False,
        fs: Optional[FutureStore] = None,
    ) -> None:
        super().__init__(fs=fs, uin=uin)
        self.client = client
        self.refresh_times = refresh_times
        self.poll_freq = poll_freq
        if h5:
            from qqqr.constant import QzoneH5Appid as appid
            from qqqr.constant import QzoneH5Proxy as proxy
        else:
            from qqqr.constant import QzoneAppid as appid
            from qqqr.constant import QzoneProxy as proxy
        self.qrlogin = QrLogin(self.client, appid, proxy)

    # fmt: off
    @property
    def qr_fetched(self): return self.qrlogin.qr_fetched
    @property
    def qr_cancelled(self): return self.qrlogin.qr_cancelled
    @property
    def cancel(self): return self.qrlogin.cancel
    @property
    def refresh(self): return self.qrlogin.refresh
    # fmt: on

    async def _new_cookie(self) -> Dict[str, str]:
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
        emit_hook = lambda c: self.login_notify_channel.add_awaitable(c)
        emit_fail = lambda exc: emit_hook(
            self.login_failed.emit(uin=self.uin, method="qr", exc=str(exc))
        )

        try:
            cookie = await self.qrlogin.login(
                refresh_times=self.refresh_times, poll_freq=self.poll_freq
            )
        except (UserBreak, KeyboardInterrupt, asyncio.CancelledError) as e:
            emit_fail("用户取消了登录")
            if isinstance(e, UserBreak):
                raise
            raise UserBreak from e
        except (asyncio.TimeoutError, GeneratorExit, ConnectError, HTTPError) as e:
            omit_exc_info = isinstance(e, (ConnectError, GeneratorExit, asyncio.TimeoutError))
            log.warning(f"{type(e).__name__} captured, continue.", exc_info=not omit_exc_info)
            log.debug(e.args, extra=e.__dict__)
            emit_fail(e)
            raise _NextMethodInterrupt from e
        except:
            log.fatal("Unexpected error in QR login.", exc_info=True)
            emit_fail("二维码登录期间出现奇怪的错误😰请检查日志以便寻求帮助.")
            raise

        emit_hook(self.login_success.emit(uin=self.uin, method="qr"))
        return cookie

    def h5(self):
        """Realloc a :class:`LoginBase` object.

        .. versionadded:: 0.12.6
        """
        from qqqr.constant import QzoneH5Appid as appid
        from qqqr.constant import QzoneH5Proxy as proxy

        self.qrlogin = QrLogin(self.client, appid, proxy)


class MixedLoginMan(Loginable):
    """A login manager that will try methods according to the given :obj:`.order`.

    .. versionchanged:: 0.12.0

        Make it a :class:`EventManager`.
    """

    qr_fetched: Emitter[MT.qr_fetched]
    qr_cancelled: Emitter[MT.qr_cancelled]
    cancel_qr: VirtualEmitter[MT.qr_cancelled]
    refresh_qr: VirtualEmitter[MT.qr_refresh]
    sms_code_required: Emitter[MT.sms_code_required]
    sms_code_input: VirtualEmitter[MT.sms_code_input]

    def __init__(
        self,
        client: ClientAdapter,
        uin: int,
        order: Sequence[MT.LoginMethod],
        pwd: Optional[str] = None,
        *,
        refresh_times: int = 6,
        poll_freq: float = 3,
        h5=False,
    ) -> None:
        super().__init__(uin)
        self.order = tuple(dict.fromkeys(order))
        self.loginables: Dict[MT.LoginMethod, Loginable] = {}
        self.login_notify_channel = FutureStore()

        if "qr" in self.order:
            self.loginables["qr"] = c = QRLoginMan(
                client=client,
                uin=uin,
                refresh_times=refresh_times,
                poll_freq=poll_freq,
                h5=h5,
                fs=self.login_notify_channel,
            )
            c.login_success = self.login_success
            c.login_failed = self.login_failed
            self.qr_fetched = c.qr_fetched
            self.qr_cancelled = c.qr_cancelled
            self.cancel_qr = c.cancel
            self.refresh_qr = c.refresh
        else:
            self.qr_fetched = self.qr_cancelled = null_emitter
            self.cancel_qr = self.refresh_qr = null_vemitter

        if "up" in self.order:
            assert pwd
            self.loginables["up"] = c = UPLoginMan(
                client=client, uin=uin, pwd=pwd, h5=h5, fs=self.login_notify_channel
            )
            c.login_success = self.login_success
            c.login_failed = self.login_failed
            self.sms_code_required = c.sms_code_required
            self.sms_code_input = c.sms_code_input
        else:
            self.sms_code_required = null_emitter
            self.sms_code_input = null_vemitter

    def ordered_methods(self) -> Sequence[MT.LoginMethod]:
        """Subclasses can inherit this method to choose a subset of `._order` according to its own policy.

        :return: a subset of `._order`.

        .. versionadded:: 0.9.8.dev1
        """
        return list(self.order)

    async def _new_cookie(self) -> Dict[str, str]:
        """
        :meta public:
        :raise `qqqr.exception.UserBreak`: if qr login is canceled and no succeeding method exist and success.
        :raise `aioqzone.exception.SkipLoginInterrupt`: if all login methods are removed by subclasses.
        :raise `aioqzone.exception.LoginError`: if all login methods failed.
        :raises: Any unexpected exceptions.

        :return: cookie dict
        """
        methods = self.ordered_methods()
        if not methods:
            log.info("No method selected for this login, raise SkipLoginInterrupt.")
            raise SkipLoginInterrupt

        user_break = None
        log.info(f"Methods selected for this login: {methods}")

        for m in methods:
            c = self.loginables[m]
            try:
                return await c._new_cookie()
            except (TencentLoginError, _NextMethodInterrupt) as e:
                excname = e.__class__.__name__
                log.info(f"Mixed loginman received {excname}, continue.")
                log.debug(e.args)
            except UserBreak as e:
                user_break = e
                log.info("Mixed loginman received UserBreak, continue.")

        if user_break:
            raise UserBreak from user_break

        if "qr" not in methods:
            hint = "您可能被限制账密登陆. 扫码登陆仍然可行."
        elif "up" not in methods:
            hint = "您可能已被限制登陆."
        else:
            hint = "你在睡觉！"

        raise LoginError(hint, methods_tried=methods)

    def h5(self):
        """Change all manager in :obj:`loginables` to h5 login proxy.

        .. note:: This will remove existing login cookie in :obj:`.cookie`!

        .. versionadded:: 0.12.6
        """
        for v in self.loginables.values():
            if callable(h5 := getattr(v, "h5", None)):
                h5()
