import re
from os import environ as env
from random import choice, random
from time import time_ns
from typing import Awaitable, Callable, Dict, Optional, Type

from httpx import AsyncClient

from ..base import LoginBase, LoginSession
from ..constant import StatusCode
from ..exception import TencentLoginError
from ..type import APPID, PT_QR_APP, Proxy
from .encrypt import NodeEncoder, PasswdEncoder, TeaEncoder
from .type import CheckResp, VerifyResp

CHECK_URL = "https://ssl.ptlogin2.qq.com/check"
LOGIN_URL = "https://ssl.ptlogin2.qq.com/login"
LOGIN_JS = "https://qq-web.cdn-go.cn/any.ptlogin2.qq.com/v1.3.0/ptlogin/js/c_login_2.js"


UseEncoder = (
    TeaEncoder if env.get("AIOQZONE_PWDENCODER", "").strip().lower() == "python" else NodeEncoder
)


class UpSession(LoginSession):
    def __init__(
        self,
        check_result: CheckResp,
        create_time: float = ...,
    ) -> None:
        super().__init__(create_time)
        self.check_rst = check_result
        self.verify_rst: Optional[VerifyResp] = None
        self.sms_ticket = ""

    @property
    def code(self):
        if self.verify_rst:
            return self.verify_rst.errorCode
        return self.check_rst.code

    @property
    def verifycode(self):
        if self.verify_rst:
            return self.verify_rst.randstr
        return self.check_rst.verifycode

    @property
    def verifysession(self):
        if self.verify_rst:
            return self.verify_rst.ticket
        return self.check_rst.verifysession


class UPLogin(LoginBase[UpSession]):
    node = "node"
    _captcha = None
    get_smscode = None
    encode_cls: Type[PasswdEncoder] = UseEncoder

    def __init__(
        self,
        client: AsyncClient,
        app: APPID,
        proxy: Proxy,
        uin: int,
        pwd: str,
        info: Optional[PT_QR_APP] = None,
    ):
        super().__init__(client, app, proxy, info=info)
        assert uin
        assert pwd
        self.uin = uin
        self.pwd = pwd
        self.pwder = self.encode_cls(client, pwd)

    def register_smscode_getter(self, getter: Callable[[], Awaitable[int]]):
        self.get_smscode = getter

    async def deviceId(self) -> str:
        return ""

    async def new(self):
        """check procedure before login. This will return a CheckResult object containing
        verify code, session, etc.

        :raises `aiohttp.ClientResponseError`:

        :return: CheckResult
        """
        data = {
            "regmaster": "",
            "pt_tea": 2,
            "pt_vcode": 1,
            "uin": self.uin,
            "appid": self.app.appid,
            # 'js_ver': 21072114,
            "js_type": 1,
            "login_sig": self.login_sig,
            "u1": self.proxy.s_url,
            "r": random(),
            "pt_uistyle": 40,
        }
        r = await self.client.get(CHECK_URL, params=data)
        r.raise_for_status()
        rlist = re.findall(r"'(.*?)'[,\)]", r.text)
        rdict = dict(
            zip(
                ["code", "verifycode", "salt", "verifysession", "isRandSalt", "ptdrvs", "session"],
                rlist,
            )
        )
        return UpSession(CheckResp.parse_obj(rdict))

    async def sms(self, sess: UpSession):
        """Send verify sms (to get dynamic code)

        :param pt_sms_ticket: corresponding value in cookie, of the key with the same name
        """
        data = {
            "bkn": "",
            "uin": self.uin,
            "aid": self.app.appid,
            "pt_sms_ticket": sess.sms_ticket,
        }
        r = await self.client.get("https://ui.ptlogin2.qq.com/ssl/send_sms_code", params=data)
        rl = re.findall(r"'(.*?)'[,\)]", r.text)
        # ptui_sendSMS_CB('10012', '短信发送成功！')
        assert int(rl[0]) == 10012, rl[1]

    async def login(self, sess: UpSession, pastcode: int = 0, **add) -> Dict[str, str]:
        if sess.code == StatusCode.Authenticated:
            # OK
            pass
        elif sess.code == StatusCode.NeedCaptcha and pastcode == 0:
            # 0 -> 1: OK; !0 -> 1: Error
            cookie = await self.login(await self.passVC(sess), StatusCode.NeedCaptcha)
            return cookie
        elif sess.code == pastcode == StatusCode.NeedVerify:
            # !10009 -> 10009: OK; 10009 -> 10009: Error
            raise TencentLoginError(sess.code, str(sess))
        else:
            raise TencentLoginError(sess.code, str(sess))

        const = {
            "h": 1,
            "t": 1,
            "g": 1,
            "ptredirect": 0,
            "from_ui": 1,
            "ptlang": 2052,
            "js_type": 1,
            "pt_uistyle": 40,
        }
        data = {
            "u": self.uin,
            "p": await self.pwder.encode(sess.check_rst.salt, sess.verifycode),
            "verifycode": sess.verifycode,
            "pt_vcode_v1": 1 if pastcode == StatusCode.NeedCaptcha else 0,
            "pt_verifysession_v1": sess.verifysession,
            "pt_randsalt": sess.check_rst.isRandSalt,
            "u1": self.proxy.s_url,
            "action": f"{3 if pastcode == StatusCode.NeedCaptcha else 2}-{choice([1, 2])}-{int(time_ns() / 1e6)}",
            # 'js_ver': 21072114,
            "login_sig": self.login_sig,
            "aid": self.app.appid,
            "daid": self.app.daid,
            "ptdrvs": sess.check_rst.ptdrvs,
            "sid": sess.check_rst.session,
            "o1vId": await self.deviceId(),
        }
        data.update(const)
        data.update(add)
        self.referer = "https://xui.ptlogin2.qq.com/"
        response = await self.client.get(LOGIN_URL, params=data)
        response.raise_for_status()
        rl = re.findall(r"'(.*?)'[,\)]", response.text)

        rl[0] = int(rl[0])
        if rl[0] == StatusCode.Authenticated:
            pass
        elif rl[0] == StatusCode.NeedVerify:
            sess.sms_ticket = response.cookies.get("pt_sms_ticket") or ""
            if self.get_smscode:
                await self.sms(sess)
                smscode = await self.get_smscode()
                await self.login(sess, StatusCode.NeedVerify, pt_sms_code=smscode)
            else:
                raise NotImplementedError
        else:
            raise TencentLoginError(rl[0], rl[4])

        return await self._get_login_url(rl[2])

    def captcha(self, sid: str):
        if not self._captcha:
            from .captcha import Captcha

            self._captcha = Captcha(self.client, self.app.appid, sid)
        return self._captcha

    async def passVC(self, sess: UpSession):
        c = self.captcha(sess.check_rst.session)
        await c.prehandle(self.xlogin_url)
        sess.verify_rst = await c.verify()
        return sess
