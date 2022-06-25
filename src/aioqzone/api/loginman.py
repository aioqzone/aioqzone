"""
Collect some built-in login manager w/o caching.
Users can inherit these managers and implement their own caching logic.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Union

from jssupport.exception import JsImportError, JsRuntimeError, NodeNotFoundError
from qqqr.constant import QzoneAppid, QzoneProxy, StatusCode
from qqqr.event.login import QrEvent, UpEvent
from qqqr.exception import TencentLoginError, UserBreak
from qqqr.qr import QrLogin
from qqqr.up import UpLogin
from qqqr.utils.net import ClientAdapter

from ..event.login import Loginable, LoginMethod, QREvent, UPEvent
from ..exception import LoginError

log = logging.getLogger(__name__)
JsError = JsRuntimeError, JsImportError, NodeNotFoundError


class ConstLoginMan(Loginable):
    """Only for test"""

    def __init__(self, uin: int, cookie: dict) -> None:
        super().__init__(uin)
        self._cookie = cookie

    async def _new_cookie(self) -> Dict[str, str]:
        return self._cookie


class UPLoginMan(Loginable[UPEvent]):
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
        :raises `qqqr.exception.TencentLoginError`: login error when up login.
        :raises `SystemExit`: if unexpected error raised
        """
        meth = LoginMethod.up
        try:
            cookie = await self.uplogin.login()
            self.add_hook_ref("hook", self.hook.LoginSuccess(meth))
            self.client.cookies.update(cookie)  # optional
            return cookie
        except TencentLoginError as e:
            self.add_hook_ref("hook", self.hook.LoginFailed(meth, e.msg))
            log.warning(str(e))
            raise e
        except NotImplementedError as e:
            self.add_hook_ref("hook", self.hook.LoginFailed(meth, "10009：需要手机验证"))
            log.warning(str(e))
            raise TencentLoginError(
                StatusCode.NeedSmsVerify, "Dynamic code verify not implemented"
            )
        except JsError as e:
            self.add_hook_ref("hook", self.hook.LoginFailed(meth, "JS调用出错"))
            log.error(str(e), exc_info=e)
            raise TencentLoginError(StatusCode.NeedCaptcha, "Failed to pass captcha")
        except GeneratorExit as e:
            log.warning("GeneratorExit captured, login cancelled.")
            raise e
        except:
            log.fatal("Unexpected error in QR login.", exc_info=True)
            try:
                await self.hook.LoginFailed(meth, "密码登录期间出现奇怪的错误😰请检查日志以便寻求帮助.")
            finally:
                exit(1)


class QRLoginMan(Loginable[QREvent]):
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
        :raises `qqqr.exception.UserBreak`: qr polling task is canceled
        :raises `TimeoutError`: qr polling task timeout
        :raises `SystemExit`: if unexpected error raised when polling
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
        except TimeoutError as e:
            log.warning(str(e))
            emit_hook(self.hook.LoginFailed(meth, str(e)))
            raise e
        except KeyboardInterrupt as e:
            raise UserBreak from e
        except GeneratorExit as e:
            log.warning("GeneratorExit captured, login cancelled.")
            raise e
        except:
            log.fatal("Unexpected error in QR login.", exc_info=True)
            msg = "二维码登录期间出现奇怪的错误😰请检查日志以便寻求帮助."
            try:
                await self.hook.LoginFailed(meth, msg)
            finally:
                exit(1)
        finally:
            self.hook.cancel_flag.clear()
            self.hook.refresh_flag.clear()


class QrStrategy(str, Enum):
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

    def register_hook(self, hook: Union[MixedLoginEvent, QrEvent, UpEvent]):
        for c in self._order:
            if isinstance(c, QRLoginMan) and isinstance(hook, QREvent):
                c.register_hook(hook)
            if isinstance(c, UPLoginMan) and isinstance(hook, UPEvent):
                c.register_hook(hook)

    async def _new_cookie(self) -> Dict[str, str]:
        """
        :raises `qqqr.exception.UserBreak`: qr login canceled
        :raises `aioqzone.exception.LoginError`: not logined
        :raises `SystemExit`: unexcpected error

        :return: cookie
        """
        for c in self._order:
            try:
                return await c._new_cookie()
            except (TencentLoginError, TimeoutError, GeneratorExit) as e:
                continue
            # except (UserBreak, SystemExit, SystemError) as e:
            #     raise e

        if self.strategy == "forbid":
            msg = "您可能被限制账密登陆. 扫码登陆仍然可行."
        elif self.strategy != "force":
            msg = "您可能已被限制登陆."
        else:
            msg = "你在睡觉！"

        raise LoginError(msg, self.strategy)
