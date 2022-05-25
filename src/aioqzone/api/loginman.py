"""
Collect some built-in login manager w/o caching.
Users can inherit these managers and implement their own caching logic.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Type

from aiohttp import ClientSession

from jssupport.exception import JsImportError, JsRuntimeError, NodeNotFoundError
from qqqr.constants import QzoneAppid, QzoneProxy, StatusCode
from qqqr.exception import TencentLoginError, UserBreak
from qqqr.qr import QRLogin
from qqqr.up import UPLogin, User

from ..exception import LoginError
from ..interface.hook import LoginMethod, QREvent, UPEvent
from ..interface.login import Loginable

logger = logging.getLogger(__name__)
JsError = JsRuntimeError, JsImportError, NodeNotFoundError


class ConstLoginMan(Loginable):
    """Only for test"""

    def __init__(self, uin: int, cookie: dict) -> None:
        super().__init__(uin)
        self._cookie = cookie

    async def _new_cookie(self) -> Dict[str, str]:
        return self._cookie


class UPLoginMan(Loginable[UPEvent]):
    def __init__(self, sess: ClientSession, uin: int, pwd: str) -> None:
        Loginable.__init__(self, uin)
        self.sess = sess
        self._pwd = pwd

    async def _new_cookie(self) -> Dict[str, str]:
        """
        :raises `qqqr.exception.TencentLoginError`: login error when up login.
        :raises `SystemExit`: if unexpected error raised
        """
        meth = LoginMethod.up
        try:
            login = UPLogin(self.sess, QzoneAppid, QzoneProxy, User(self.uin, self._pwd))
            cookie = await login.login(await login.check())
            self.add_hook_ref("hook", self.hook.LoginSuccess(meth))
            self.sess.cookie_jar.update_cookies(cookie)
            return cookie
        except TencentLoginError as e:
            self.add_hook_ref("hook", self.hook.LoginFailed(meth, e.msg))
            logger.warning(str(e))
            raise e
        except NotImplementedError as e:
            self.add_hook_ref("hook", self.hook.LoginFailed(meth, "10009：需要手机验证"))
            logger.warning(str(e))
            raise TencentLoginError(StatusCode.NeedVerify, "Dynamic code verify not implemented")
        except JsError as e:
            self.add_hook_ref("hook", self.hook.LoginFailed(meth, "JS调用出错"))
            logger.error(str(e), exc_info=e)
            raise TencentLoginError(StatusCode.NeedCaptcha, "Failed to pass captcha")
        except:
            logger.fatal("Unexpected error in QR login.", exc_info=True)
            try:
                await self.hook.LoginFailed(meth, "密码登录期间出现奇怪的错误😰请检查日志以便寻求帮助.")
            finally:
                exit(1)


class QRLoginMan(Loginable[QREvent]):
    hook: QREvent

    def __init__(self, sess: ClientSession, uin: int, refresh_time: int = 6) -> None:
        Loginable.__init__(self, uin)
        self.sess = sess
        self.refresh = refresh_time

    async def _new_cookie(self) -> Dict[str, str]:
        """
        :raises `qqqr.exception.UserBreak`: qr polling task is canceled
        :raises `TimeoutError`: qr polling task timeout
        :raises `SystemExit`: if unexpected error raised when polling
        """
        meth = LoginMethod.qr
        man = QRLogin(self.sess, QzoneAppid, QzoneProxy)
        task = man.loop(send_callback=self.hook.QrFetched, refresh_time=self.refresh)

        async def tmp_cancel():
            task.cancel()

        async def tmp_resend():
            await self.hook.QrFetched(await man.show())  # must be sent at once

        self.hook.cancel = tmp_cancel
        self.hook.resend = tmp_resend
        emit_hook = lambda c: self.add_hook_ref("hook", c)

        try:
            cookie = await task
            emit_hook(self.hook.LoginSuccess(meth))
            self.sess.cookie_jar.update_cookies(cookie)
            return cookie
        except TimeoutError as e:
            logger.warning(str(e))
            emit_hook(self.hook.LoginFailed(meth, str(e)))
            raise e
        except KeyboardInterrupt as e:
            raise UserBreak from e
        except:
            logger.fatal("Unexpected error in QR login.", exc_info=True)
            msg = "二维码登录期间出现奇怪的错误😰请检查日志以便寻求帮助."
            try:
                await self.hook.LoginFailed(meth, msg)
            finally:
                exit(1)
        finally:
            self.hook.cancel = self.hook.resend = None


class MixedLoginMan(UPLoginMan, QRLoginMan):
    class QrStrategy(str, Enum):
        force = "force"
        prefer = "prefer"
        allow = "allow"
        forbid = "forbid"

    def __init__(
        self,
        sess: ClientSession,
        uin: int,
        strategy: QrStrategy,
        pwd: Optional[str] = None,
        refresh_time: int = 6,
    ) -> None:
        self.strategy = strategy
        if strategy != "force":
            assert pwd
            UPLoginMan.__init__(self, sess, uin, pwd)
        if strategy != "forbid":
            QRLoginMan.__init__(self, sess, uin, refresh_time)

    async def _new_cookie(self) -> Dict[str, str]:
        """

        :raises `qqqr.exception.UserBreak`: qr login canceled
        :raises `aioqzone.exception.LoginError`: not logined
        :raises `SystemExit`: unexcpected error

        :return: cookie
        """
        order: List[Type[Loginable]] = {
            "force": [QRLoginMan],
            "prefer": [QRLoginMan, UPLoginMan],
            "allow": [UPLoginMan, QRLoginMan],
            "forbid": [UPLoginMan],
        }[self.strategy]
        for c in order:
            try:
                return await c._new_cookie(self)
            except (TencentLoginError, TimeoutError) as e:
                continue
            # UserBreak, SystemExit: raise as is

        if self.strategy == "forbid":
            msg = "您可能被限制账密登陆. 扫码登陆仍然可行."
        elif self.strategy != "force":
            msg = "您可能已被限制登陆."
        else:
            msg = "你在睡觉！"

        self.add_hook_ref("hook", self.hook.LoginFailed(LoginMethod.mixed, msg))
        raise LoginError(msg, self.strategy)


QrStrategy = MixedLoginMan.QrStrategy
