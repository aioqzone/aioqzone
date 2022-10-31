"""
Collect some built-in login manager w/o caching.
Users can inherit these managers and implement their own caching logic.
"""

import asyncio
import logging
from enum import Enum
from typing import Dict, List, Optional, Union

from httpx import ConnectError, HTTPError

from jssupport.exception import JsImportError, JsRuntimeError, NodeNotFoundError
from qqqr.constant import QzoneAppid, QzoneProxy, StatusCode
from qqqr.event.login import QrEvent, UpEvent
from qqqr.exception import HookError, TencentLoginError, UserBreak
from qqqr.qr import QrLogin
from qqqr.up import UpLogin
from qqqr.utils.net import ClientAdapter

from ..event.login import Loginable, LoginMethod, QREvent, UPEvent
from ..exception import LoginError, SkipLoginInterrupt

log = logging.getLogger(__name__)
JsError = JsRuntimeError, JsImportError, NodeNotFoundError


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


class UPLoginMan(Loginable[UPEvent]):
    """Login manager for username-password login.
    This manager may trigger :meth:`~aioqzone.event.login.LoginEvent.LoginSuccess` and
    :meth:`~aioqzone.event.login.LoginEvent.LoginFailed` hook.
    """

    def __init__(self, client: ClientAdapter, uin: int, pwd: str) -> None:
        assert pwd
        super().__init__(uin)
        self.client = client
        self.uplogin = UpLogin(self.client, QzoneAppid, QzoneProxy, self.uin, pwd)

    def register_hook(self, hook: UPEvent):
        self.uplogin.register_hook(hook)
        return super().register_hook(hook)

    async def _new_cookie(self) -> Dict[str, str]:
        """
        :meta public:
        :raises `qqqr.exception.TencentLoginError`: login error when up login.
        :raises `~aioqzone.api.loginman._NextMethodInterrupt`: if acceptable errors occured, for example, http errors.
        :raises `SystemExit`: if unexpected error raised

        :return: cookie dict
        """
        meth = LoginMethod.up
        emit_hook = lambda c: self.add_hook_ref("hook", c)
        try:
            cookie = await self.uplogin.login()
            emit_hook(self.hook.LoginSuccess(meth))
            self.client.cookies.update(cookie)  # optional
            return cookie
        except TencentLoginError as e:
            log.warning(str(e))
            emit_hook(self.hook.LoginFailed(meth, e.msg))
            raise e
        except NotImplementedError as e:
            log.warning(str(e))
            emit_hook(self.hook.LoginFailed(meth, "10009：需要手机验证"))
            raise TencentLoginError(
                StatusCode.NeedSmsVerify, "Dynamic code verify not implemented"
            )
        except JsError as e:
            log.error(str(e), exc_info=e)
            emit_hook(self.hook.LoginFailed(meth, "JS调用出错"))
            raise TencentLoginError(StatusCode.NeedCaptcha, "Failed to pass captcha")
        except GeneratorExit as e:
            log.warning("Generator Exit captured, continue.")
            emit_hook(self.hook.LoginFailed(meth, str(e)))
            raise _NextMethodInterrupt from e
        except ConnectError as e:
            log.warning("Connection Error captured, continue.")
            log.debug(e.request)
            emit_hook(self.hook.LoginFailed(meth, str(e)))
            raise _NextMethodInterrupt from e
        except HTTPError as e:
            log.error("Unknown HTTP Error captured, continue.", exc_info=True)
            emit_hook(self.hook.LoginFailed(meth, str(e)))
            raise _NextMethodInterrupt from e
        except HookError as e:
            log.error(str(e))
            emit_hook(self.hook.LoginFailed(meth, str(e)))
            raise e
        except:
            log.fatal("密码登录抛出未捕获的异常.", exc_info=True)
            msg = "密码登录期间出现奇怪的错误😰请检查日志以便寻求帮助."
            try:
                emit_hook(self.hook.LoginFailed(meth, msg))
            finally:
                exit(1)


class QRLoginMan(Loginable[QREvent]):
    """Login manager for QR login.
    This manager may trigger :meth:`~aioqzone.event.login.LoginEvent.LoginSuccess` and
    :meth:`~aioqzone.event.login.LoginEvent.LoginFailed` hook.
    """

    def __init__(self, client: ClientAdapter, uin: int, refresh_time: int = 6) -> None:
        Loginable.__init__(self, uin)
        self.client = client
        self.refresh = refresh_time
        self.qrlogin = QrLogin(self.client, QzoneAppid, QzoneProxy)

    def register_hook(self, hook: QREvent):
        self.qrlogin.register_hook(hook)
        return super().register_hook(hook)

    async def _new_cookie(self) -> Dict[str, str]:
        """
        :meta public:
        :raises `qqqr.exception.UserBreak`: qr polling task is canceled
        :raises `~aioqzone.api.loginman._NextMethodInterrupt`: on exceptions do not break the system, such as timeout, Http errors, etc.
        :raises: `qqqr.exception.HookError`: an error is raised from hook
        :raises `SystemExit`: on unexpected error raised when polling

        :return: cookie dict
        """
        meth = LoginMethod.qr
        emit_hook = lambda c: self.add_hook_ref("hook", c)
        self.hook.cancel_flag.clear()
        self.hook.refresh_flag.clear()

        try:
            cookie = await self.qrlogin.login()
            emit_hook(self.hook.LoginSuccess(meth))
            self.client.cookies.update(cookie)
            return cookie
        except asyncio.TimeoutError as e:
            log.warning(str(e))
            emit_hook(self.hook.LoginFailed(meth, str(e)))
            raise _NextMethodInterrupt from e
        except KeyboardInterrupt as e:
            emit_hook(self.hook.LoginFailed(meth, "用户取消了登录"))
            raise UserBreak from e
        except GeneratorExit as e:
            log.warning("Generator Exit captured, continue.")
            emit_hook(self.hook.LoginFailed(meth, str(e)))
            raise _NextMethodInterrupt from e
        except ConnectError as e:
            log.warning("Connection Error captured, continue.")
            log.debug(e.request)
            emit_hook(self.hook.LoginFailed(meth, str(e)))
            raise _NextMethodInterrupt from e
        except HTTPError as e:
            log.error("Unknown HTTP Error captured, continue.", exc_info=True)
            log.debug(e.request)
            emit_hook(self.hook.LoginFailed(meth, str(e)))
            raise _NextMethodInterrupt from e
        except HookError as e:
            log.error(str(e))
            emit_hook(self.hook.LoginFailed(meth, str(e)))
            raise e
        except:
            log.fatal("Unexpected error in QR login.", exc_info=True)
            msg = "二维码登录期间出现奇怪的错误😰请检查日志以便寻求帮助."
            try:
                emit_hook(self.hook.LoginFailed(meth, msg))
            finally:
                exit(1)
        finally:
            self.hook.cancel_flag.clear()
            self.hook.refresh_flag.clear()


class QrStrategy(str, Enum):
    """Represents QR strategy."""

    force = "force"
    prefer = "prefer"
    allow = "allow"
    forbid = "forbid"


class MixedLoginEvent(QREvent, UPEvent):
    def __instancecheck__(self, o: object) -> bool:
        return isinstance(o, QREvent) and isinstance(o, UPEvent)

    def __subclasscheck__(self, cls: type) -> bool:
        return issubclass(cls, QREvent) and issubclass(cls, UPEvent)


class MixedLoginMan(Loginable[MixedLoginEvent]):
    """A login manager that will try methods according to the given :class:`.QrStrategy`."""

    def __init__(
        self,
        client: ClientAdapter,
        uin: int,
        strategy: QrStrategy,
        pwd: Optional[str] = None,
        refresh_time: int = 6,
    ) -> None:
        super().__init__(uin)
        self.strategy = strategy
        self._order: List[Loginable] = []
        if strategy != QrStrategy.force:
            assert pwd
            self._order.append(UPLoginMan(client, uin, pwd))
        if strategy != QrStrategy.forbid:
            self._order.append(QRLoginMan(client, uin, refresh_time))
        if strategy == QrStrategy.prefer:
            self._order = self._order[::-1]

        # use a unified task store
        self._tasks = self._order[0]._tasks
        for i in self._order:
            i._tasks = self._tasks

    def register_hook(self, hook: Union[MixedLoginEvent, QrEvent, UpEvent]):
        for c in self._order:
            if isinstance(c, QRLoginMan) and isinstance(hook, QREvent):
                c.register_hook(hook)
            if isinstance(c, UPLoginMan) and isinstance(hook, UPEvent):
                c.register_hook(hook)

    def ordered_methods(self) -> List[Loginable]:
        """Subclasses can inherit this method to choose a subset of `._order` according to its own policy.

        :return: a subset of `._order`.

        .. versionadded:: 0.9.8.dev1
        """
        return self._order

    async def _new_cookie(self) -> Dict[str, str]:
        """
        :meta public:
        :raises `qqqr.exception.UserBreak`: if qr login is canceled and no succeeding method exist and success.
        :raises `aioqzone.exception.SkipLoginInterrupt`: if all login methods are removed by subclasses.
        :raises `aioqzone.exception.LoginError`: if all login methods failed.
        :raises `SystemExit`: if unexcpected error occured in any login method. Succeeding method will not be used.

        :return: cookie dict
        """
        if not self._order:
            raise SkipLoginInterrupt
        user_break = None

        for c in self.ordered_methods():
            try:
                return await c._new_cookie()
            except (TencentLoginError, _NextMethodInterrupt, HookError) as e:
                excname = e.__class__.__name__
                log.debug(f"Mixed loginman received {excname}, continue.")
            except UserBreak as e:
                user_break = e
                log.debug("Mixed loginman received UserBreak, continue.")
            except SystemExit as e:
                log.debug("Mixed loginman captured System Exit, reraise.")
                raise e

        if user_break:
            raise UserBreak from user_break

        if self.strategy == "forbid":
            hint = "您可能被限制账密登陆. 扫码登陆仍然可行."
        elif self.strategy != "force":
            hint = "您可能已被限制登陆."
        else:
            hint = "你在睡觉！"

        raise LoginError(hint, self.strategy)
