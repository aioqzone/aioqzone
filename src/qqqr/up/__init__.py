import logging
import re
from os import environ as env
from random import choice, random
from time import time_ns
from typing import List, Optional, Type

from ..base import LoginBase, LoginSession
from ..constant import StatusCode
from ..event import Emittable, NullEvent
from ..event.login import UpEvent
from ..exception import TencentLoginError
from ..type import APPID, PT_QR_APP, Proxy
from ..utils.daug import du
from ..utils.net import ClientAdapter
from .encrypt import NodeEncoder, PasswdEncoder, TeaEncoder
from .type import CheckResp, LoginResp, VerifyResp

CHECK_URL = "https://ssl.ptlogin2.qq.com/check"
LOGIN_URL = "https://ssl.ptlogin2.qq.com/login"
LOGIN_JS = "https://qq-web.cdn-go.cn/any.ptlogin2.qq.com/v1.3.0/ptlogin/js/c_login_2.js"

log = logging.getLogger(__name__)
UseEncoder = (
    TeaEncoder if env.get("AIOQZONE_PWDENCODER", "").strip().lower() == "python" else NodeEncoder
)


class UpSession(LoginSession):
    def __init__(
        self,
        check_result: CheckResp,
        local_token: str,
        login_sig: str,
        *,
        create_time: float = ...,
    ) -> None:
        super().__init__(create_time=create_time)
        self.local_token = local_token
        self.login_sig = login_sig
        self.check_rst = check_result
        self.verify_rst: Optional[VerifyResp] = None
        self.sms_ticket = ""
        self.sms_code: Optional[str] = None
        self.login_history: List[LoginResp] = []

    @property
    def pastcode(self) -> int:
        if self.login_history:
            return self.login_history[-1].code
        return 0

    @property
    def code(self):
        if self.verify_rst:
            return self.verify_rst.code
        return self.check_rst.code

    @property
    def verifycode(self):
        if self.verify_rst:
            return self.verify_rst.verifycode
        return self.check_rst.verifycode

    @property
    def verifysession(self):
        if self.verify_rst:
            return self.verify_rst.ticket
        return self.check_rst.verifysession


class UpLogin(LoginBase[UpSession], Emittable[UpEvent]):
    node = "node"
    _captcha = None
    encode_cls: Type[PasswdEncoder] = UseEncoder

    def __init__(
        self,
        client: ClientAdapter,
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

    async def deviceId(self) -> str:
        return ""

    async def new(self):
        """Create a :class:`UpSession`. This will call `check` api of Qzone, and receive result
        about whether this login needs a captcha, sms verification, etc.

        :raises `httpx.HTTPStatusError`:

        :return: a up login session
        """
        async with self.client.get(self.xlogin_url) as r:
            r.raise_for_status()
            local_token = r.cookies["pt_local_token"]
            login_sig = r.cookies["pt_login_sig"]

        data = {
            "regmaster": "",
            "pt_tea": 2,
            "pt_vcode": 1,
            "uin": self.uin,
            "appid": self.app.appid,
            # 'js_ver': 21072114,
            "js_type": 1,
            "login_sig": login_sig,
            "u1": self.proxy.s_url,
            "r": random(),
            "pt_uistyle": 40,
        }
        async with self.client.get(CHECK_URL, params=data) as r:
            r.raise_for_status()
            rl = re.findall(r"'(.*?)'[,\)]", r.text)

        rdict = dict(
            zip(
                ["code", "verifycode", "salt", "verifysession", "isRandSalt", "ptdrvs", "session"],
                rl,
            )
        )
        return UpSession(CheckResp.parse_obj(rdict), local_token, login_sig)

    async def send_sms_code(self, sess: UpSession):
        """Send verify sms (to get dynamic code)

        :param sess: The up login session to send sms code
        """
        data = {
            "bkn": "",
            "uin": self.uin,
            "aid": self.app.appid,
            "pt_sms_ticket": sess.sms_ticket,
        }
        async with self.client.get(
            "https://ui.ptlogin2.qq.com/ssl/send_sms_code", params=data
        ) as r:
            rl = re.findall(r"'(.*?)'[,\)]", r.text)
        # ptui_sendSMS_CB('10012', '短信发送成功！')
        if int(rl[0]) != 10012:
            raise TencentLoginError(sess.pastcode, rl[1])

    async def try_login(self, sess: UpSession):
        """
        Check if current session meets the login condition.
        It takes a session object and returns response of this try.

        :param sess: Store the session information
        :return: A login response
        """

        const = {
            "h": 1,
            "t": 1,
            "g": 1,
            "ptredirect": 0,
            "from_ui": 1,
            "ptlang": 2052,
            "js_type": 1,
            "pt_uistyle": 40,
            # 'js_ver': 21072114,
        }
        data = {
            "u": self.uin,
            "p": await self.pwder.encode(sess.check_rst.salt, sess.verifycode),
            "verifycode": sess.verifycode,
            "pt_vcode_v1": int(sess.verify_rst is not None),
            "pt_verifysession_v1": sess.verifysession,
            "pt_randsalt": sess.check_rst.isRandSalt,
            "u1": self.proxy.s_url,
            "action": f"{3 if sess.verify_rst is not None else 2}-{choice([1, 2])}-{int(time_ns() / 1e6)}",
            "login_sig": sess.login_sig,
            "aid": self.app.appid,
            "daid": self.app.daid,
            "ptdrvs": sess.check_rst.ptdrvs,
            "sid": sess.check_rst.session,
            "o1vId": await self.deviceId(),
        }
        if sess.sms_code:
            data["pt_sms_code"] = sess.sms_code
        self.referer = "https://xui.ptlogin2.qq.com/"

        async with self.client.get(LOGIN_URL, params=du(data, const)) as response:
            response.raise_for_status()

        rl = re.findall(r"'(.*?)'[,\)]", response.text)
        resp = LoginResp.parse_obj(dict(zip(["code", "", "url", "", "msg", "nickname"], rl)))
        if resp.code == StatusCode.NeedSmsVerify:
            sess.sms_ticket = response.cookies.get("pt_sms_ticket") or ""
        log.debug(resp)
        return resp

    async def login(self):
        sess = await self.new()
        if sess.code == StatusCode.NeedCaptcha:
            await self.passVC(sess)

        while True:
            resp = await self.try_login(sess)
            pastcode = sess.pastcode
            sess.login_history.append(resp)
            if resp.code == StatusCode.Authenticated:
                sess.login_url = str(resp.url)
                return await self._get_login_url(sess)
            elif resp.code == StatusCode.NeedSmsVerify:
                if pastcode == StatusCode.NeedSmsVerify:
                    raise TencentLoginError(resp.code, "重复要求动态验证码")
                if isinstance(self.hook, NullEvent):
                    # fast return so we won't always request smscode which may risk test account.
                    raise TencentLoginError(resp.code, "未实现的功能：输入验证码")
                if self.hook.GetSmsCode.__qualname__ == UpEvent.GetSmsCode.__qualname__:
                    # TODO: bad condition
                    raise TencentLoginError(resp.code, "未实现的功能：输入验证码")
                await self.send_sms_code(sess)
                try:
                    sess.sms_code = await self.hook.GetSmsCode(resp.msg, resp.nickname)
                except:
                    sess.sms_code = None
                if sess.sms_code is None:
                    raise TencentLoginError(resp.code, "未获得动态验证码")
            else:
                raise TencentLoginError(resp.code, resp.msg)

    def captcha(self, sid: str):
        """
        The captcha function is used to build and cache a :class:`Captcha` instance.
        It takes in a string, which is the session id got from :meth:`.new`, and returns the :class:`Captcha` instance.


        :param sid: Pass the session id to the captcha function
        :return: An instance of the captcha class
        """

        if not self._captcha:
            from .captcha import Captcha

            self._captcha = Captcha(self.client, self.app.appid, sid, str(self.xlogin_url))
        return self._captcha

    async def passVC(self, sess: UpSession):
        """
        The passVC function is used to pass the verification tcaptcha.
        It is called when :meth:`.try_login` returns a :obj:`StatusCode.NeedCaptcha` code.

        :param sess: the session object
        :return: The session with :obj:`~UpSession.verify_rst` is set.
        """

        c = self.captcha(sess.check_rst.session)
        sess.verify_rst = await c.verify()
        return sess
