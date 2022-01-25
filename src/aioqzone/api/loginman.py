"""
Collect some built-in login manager w/o caching.
Users can inherit these managers and implement their own caching logic.
"""

import asyncio
import logging
from typing import Type, Union

from aiohttp import ClientSession
from qqqr.constants import QzoneAppid, QzoneProxy
from qqqr.exception import TencentLoginError, UserBreak
from qqqr.qr import QRLogin
from qqqr.up import UPLogin, User

from ..exception import LoginError
from ..interface.hook import LoginEvent, QREvent
from ..interface.login import Loginable

logger = logging.getLogger(__name__)


class ConstLoginMan(Loginable):
    """Only for test"""
    def __init__(self, uin: int, cookie: dict) -> None:
        super().__init__(uin)
        self._cookie = cookie

    async def _new_cookie(self) -> dict[str, str]:
        return self._cookie


class UPLoginMan(Loginable):
    hook: LoginEvent

    def __init__(self, sess: ClientSession, uin: int, pwd: str) -> None:
        super().__init__(uin)
        self.sess = sess
        self._pwd = pwd

    async def _new_cookie(self) -> dict[str, str]:
        """
        Raises:
            TencentLoginError
        """
        try:
            login = UPLogin(self.sess, QzoneAppid, QzoneProxy, User(self.uin, self._pwd))
            cookie = await login.login(await login.check())
            asyncio.create_task(self.hook.LoginSuccess())    # schedule in future
            return cookie
        except TencentLoginError as e:
            logger.warning(str(e))
            raise e


class QRLoginMan(Loginable):
    hook: Union[LoginEvent, QREvent]

    def __init__(self, sess: ClientSession, uin: int, refresh_time: int = 6) -> None:
        super().__init__(uin)
        self.sess = sess
        self.refresh = refresh_time

    async def _new_cookie(self) -> dict[str, str]:
        """
        Raises:
            UserBreak: [description]
        """
        assert self.hook
        assert isinstance(self.hook, QREvent)
        assert isinstance(self.hook, LoginEvent)

        man = QRLogin(self.sess, QzoneAppid, QzoneProxy)
        thread = await man.loop(send_callback=self.hook.QrFetched, refresh_time=self.refresh)

        async def tmp_cancel():
            thread.cancel()

        async def tmp_resend():
            assert isinstance(self.hook, QREvent)
            await self.hook.QrFetched(await man.show())

        self.hook.cancel = tmp_cancel
        self.hook.resend = tmp_resend

        try:
            cookie = await thread
            asyncio.create_task(self.hook.LoginSuccess())
            return cookie
        except TimeoutError as e:
            await self.hook.QrFailed()
            logger.warning(str(e))
            await self.hook.LoginFailed(str(e))
            raise e
        except KeyboardInterrupt as e:
            raise UserBreak from e
        except:
            logger.fatal('Unexpected error in QR login.', exc_info=True)
            await self.hook.LoginFailed(str("二维码登录期间出现奇怪的错误😰请检查日志以便寻求帮助."))
            exit(1)
        finally:
            self.hook.cancel = self.hook.resend = None


class MixedLoginMan(UPLoginMan, QRLoginMan):
    def __init__(
        self,
        sess: ClientSession,
        uin: int,
        strategy: str,
        pwd: str = None,
        refresh_time: int = 6
    ) -> None:
        self.strategy = strategy
        if strategy != 'force':
            assert pwd
            UPLoginMan.__init__(self, sess, uin, pwd)
        if strategy != 'forbid':
            QRLoginMan.__init__(self, sess, uin, refresh_time)

    async def _new_cookie(self) -> dict[str, str]:
        """[summary]

        Raises:
            UserBreak
            LoginError: [description]

        Returns:
            dict[str, str]: [description]
        """
        order: list[Type[Loginable]] = {
            'force': [QRLoginMan],
            'prefer': [QRLoginMan, UPLoginMan],
            'allow': [UPLoginMan, QRLoginMan],
            'forbid': [UPLoginMan],
        }[self.strategy]
        for c in order:
            try:
                return await c._new_cookie(self)
            except (TencentLoginError, TimeoutError) as e:
                continue

        if self.strategy == 'forbid':
            msg = "您可能被限制账密登陆. 扫码登陆仍然可行."
        else:
            msg = "您可能已被限制登陆."

        await self.hook.LoginFailed(msg)
        raise LoginError(msg, self.strategy)
