"""
Collect some built-in login manager w/o caching.
Users can inherit these managers and implement their own caching logic.
"""

import asyncio
import logging
from typing import Dict, Optional, Sequence

from httpx import ConnectError, HTTPError

from aioqzone.event.login import LoginMethod, QREvent, UPEvent
from aioqzone.exception import LoginError, SkipLoginInterrupt
from jssupport.exception import JsImportError, JsRuntimeError, NodeNotFoundError
from qqqr.constant import StatusCode
from qqqr.event import Emittable, EventManager
from qqqr.exception import HookError, TencentLoginError, UserBreak
from qqqr.qr import QrLogin
from qqqr.up import UpH5Login, UpWebLogin
from qqqr.utils.net import ClientAdapter

from ._base import Loginable

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


class UPLoginMan(Loginable, Emittable[UPEvent]):
    """Login manager for username-password login.
    This manager may trigger :meth:`~aioqzone.event.login.LoginEvent.LoginSuccess` and
    :meth:`~aioqzone.event.login.LoginEvent.LoginFailed` hook.
    """

    def __init__(self, client: ClientAdapter, uin: int, pwd: str, *, h5=False) -> None:
        assert pwd
        super().__init__(uin)
        self.client = client
        if h5:
            cls = UpH5Login
            from qqqr.constant import QzoneH5Appid as appid
            from qqqr.constant import QzoneH5Proxy as proxy
        else:
            cls = UpWebLogin
            from qqqr.constant import QzoneAppid as appid
            from qqqr.constant import QzoneProxy as proxy
        self.uplogin = cls(self.client, appid, proxy, self.uin, pwd)

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


class QRLoginMan(Loginable, Emittable[QREvent]):
    """Login manager for QR login.
    This manager may trigger :meth:`~aioqzone.event.login.LoginEvent.LoginSuccess` and
    :meth:`~aioqzone.event.login.LoginEvent.LoginFailed` hook.
    """

    def __init__(
        self, client: ClientAdapter, uin: int, *, refresh_time: int = 6, h5=False
    ) -> None:
        super().__init__(uin)
        self.client = client
        self.refresh_time = refresh_time
        if h5:
            from qqqr.constant import QzoneH5Appid as appid
            from qqqr.constant import QzoneH5Proxy as proxy
        else:
            from qqqr.constant import QzoneAppid as appid
            from qqqr.constant import QzoneProxy as proxy
        self.qrlogin = QrLogin(self.client, appid, proxy)

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
            cookie = await self.qrlogin.login(self.refresh_time)
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


class MixedLoginMan(EventManager[QREvent, UPEvent], Loginable):
    """A login manager that will try methods according to the given :class:`.QrStrategy`.

    .. versionchanged:: 0.12.0

        Make it a :class:`EventManager`.
    """

    def __init__(
        self,
        client: ClientAdapter,
        uin: int,
        order: Sequence[LoginMethod],
        pwd: Optional[str] = None,
        *,
        refresh_time: int = 6,
        h5=False,
    ) -> None:
        super().__init__(uin)
        self.order = tuple(dict.fromkeys(order))
        self.loginables: Dict[LoginMethod, Loginable] = {}
        if LoginMethod.qr in self.order:
            self.loginables[LoginMethod.qr] = QRLoginMan(
                client=client, uin=uin, refresh_time=refresh_time, h5=h5
            )
        if LoginMethod.up in self.order:
            assert pwd
            self.loginables[LoginMethod.up] = UPLoginMan(client=client, uin=uin, pwd=pwd, h5=h5)
        self.init_hooks()

    def init_hooks(self):
        if LoginMethod.qr in self.order:
            c = self.loginables[LoginMethod.qr]
            if isinstance(c, Emittable):
                c.register_hook(self.inst_of(QREvent))
        if LoginMethod.up in self.order:
            c = self.loginables[LoginMethod.up]
            if isinstance(c, Emittable):
                c.register_hook(self.inst_of(UPEvent))

    def ordered_methods(self) -> Sequence[LoginMethod]:
        """Subclasses can inherit this method to choose a subset of `._order` according to its own policy.

        :return: a subset of `._order`.

        .. versionadded:: 0.9.8.dev1
        """
        return list(self.order)

    async def _new_cookie(self) -> Dict[str, str]:
        """
        :meta public:
        :raises `qqqr.exception.UserBreak`: if qr login is canceled and no succeeding method exist and success.
        :raises `aioqzone.exception.SkipLoginInterrupt`: if all login methods are removed by subclasses.
        :raises `aioqzone.exception.LoginError`: if all login methods failed.
        :raises `SystemExit`: if unexcpected error occured in any login method. Succeeding method will not be used.

        :return: cookie dict
        """
        methods = self.ordered_methods()
        if not methods:
            raise SkipLoginInterrupt

        user_break = None

        for m in methods:
            c = self.loginables[m]
            try:
                return await c._new_cookie()
            except (TencentLoginError, _NextMethodInterrupt, HookError) as e:
                excname = e.__class__.__name__
                log.debug(f"Mixed loginman received {excname}, continue.")
            except UserBreak as e:
                user_break = e
                log.debug("Mixed loginman received UserBreak, continue.")
            except SystemExit:
                log.debug("Mixed loginman captured System Exit, reraise.")
                raise

        if user_break:
            raise UserBreak from user_break

        if LoginMethod.qr not in methods:
            hint = "您可能被限制账密登陆. 扫码登陆仍然可行."
        elif LoginMethod.up not in methods:
            hint = "您可能已被限制登陆."
        else:
            hint = "你在睡觉！"

        raise LoginError(hint, methods_tried=methods)


strategy_to_order = dict(
    forbid=[LoginMethod.up],
    allow=[LoginMethod.up, LoginMethod.qr],
    prefer=[LoginMethod.qr, LoginMethod.up],
    force=[LoginMethod.qr],
)
"""We provide a mapping to transform old "strategy" manner to new "order" manner.

.. versionadded:: 0.12.0
"""
