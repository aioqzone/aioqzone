import logging
import re
from os import environ as env
from random import choice, random
from time import time_ns
from typing import List, Optional, Type

from httpx import URL

from qqqr.base import LoginBase, LoginSession
from qqqr.constant import StatusCode
from qqqr.event import Emittable
from qqqr.event.login import UpEvent
from qqqr.exception import TencentLoginError
from qqqr.type import APPID, PT_QR_APP, Proxy
from qqqr.utils.daug import du
from qqqr.utils.net import ClientAdapter

from .encrypt import NodeEncoder, PasswdEncoder, TeaEncoder
from .type import CheckResp, LoginResp, VerifyResp

CHECK_URL = "https://ssl.ptlogin2.qq.com/check"
LOGIN_URL = "https://ssl.ptlogin2.qq.com/login"

LEGACY_ENCODER = env.get("AIOQZONE_PWDENCODER", "").strip().lower() == "node"

log = logging.getLogger(__name__)


class UpWebSession(LoginSession):
    def __init__(
        self,
        login_sig: str,
        login_referer: str,
        *,
        create_time: float = ...,
    ) -> None:
        super().__init__(create_time=create_time)
        self.login_sig = login_sig
        self.login_referer = login_referer
        """url fetched in `new`."""
        self.verify_rst: Optional[VerifyResp] = None
        self.sms_ticket = ""
        self.sms_code: Optional[str] = None
        self.login_history: List[LoginResp] = []

    def set_check_result(self, check: CheckResp):
        self.check_rst = check

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


class UpWebLogin(LoginBase[UpWebSession], Emittable[UpEvent]):
    """
    .. versionchanged:: 0.12.4

        TeaEncoder is used as the default password encoder. A `legacy_encoder` paramater is added to force
        using the former `NodeEncoder`. It can also be configured by set :envvar:`AIOQZONE_PWDENCODER` to "node".
        Note that the paramater in code, i.e. `legacy_encoder`, takes precedence.
    """

    def __init__(
        self,
        client: ClientAdapter,
        app: APPID,
        proxy: Proxy,
        uin: int,
        pwd: str,
        info: Optional[PT_QR_APP] = None,
        *,
        legacy_encoder=LEGACY_ENCODER,
    ):
        super().__init__(client, app, proxy, info=info)
        assert pwd
        self.uin = uin
        self.pwd = pwd
        if legacy_encoder:
            self.pwder = NodeEncoder(client, pwd)
        else:
            self.pwder = TeaEncoder(pwd)

    @property
    def login_page_url(self):
        params = {
            "hide_title_bar": 1,
            "style": 22,
            "daid": self.app.daid,
            "low_login": 0,
            "qlogin_auto_login": 1,
            "no_verifyimg": 1,
            "link_target": "blank",
            "appid": self.app.appid,
            "target": "self",
            "s_url": self.proxy.s_url,
            "proxy_url": self.proxy.proxy_url,
            "pt_no_auth": 1,
        }
        if self.info:
            if self.info.app:
                params["pt_qr_app"] = self.info.app
            if self.info.link:
                params["pt_qr_link"] = self.info.link
            if self.info.register:
                params["self_regurl"] = self.info.register
            if self.info.help:
                params["pt_qr_help_link"] = self.info.help

        return URL("https://xui.ptlogin2.qq.com/cgi-bin/xlogin").copy_with(params=params)

    async def deviceId(self) -> str:
        """a js fingerprint.

        .. seealso:: https://github.com/fingerprintjs/fingerprintjs
        """
        return ""

    async def new(self):
        """Create a :class:`UpWebSession`. This will call `check` api of Qzone, and receive result
        about whether this login needs a captcha, sms verification, etc.

        :raises `httpx.HTTPStatusError`:

        :return: a up login session
        """
        async with self.client.get(self.login_page_url) as r:
            r.raise_for_status()
            return UpWebSession(r.cookies["pt_login_sig"], str(r.url))

    async def check(self, sess: UpWebSession):
        data = {
            "regmaster": "",
            "pt_tea": 2,
            "pt_vcode": 1,
            "uin": self.uin,
            "appid": self.app.appid,
            # 'js_ver': 21072114,
            "js_type": 1,
            "login_sig": sess.login_sig,
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
        sess.set_check_result(CheckResp.parse_obj(rdict))

    async def send_sms_code(self, sess: UpWebSession):
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

    async def try_login(self, sess: UpWebSession):
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
        }
        data = {
            "u": self.uin,
            "p": await self.pwder.encode(sess.check_rst.salt, sess.verifycode),
            "verifycode": sess.verifycode,
            "pt_vcode_v1": int(sess.verify_rst is not None),
            "pt_verifysession_v1": sess.verifysession,
            "pt_randsalt": sess.check_rst.isRandSalt,
            "u1": self.proxy.s_url,
            "login_sig": sess.login_sig,
            "aid": self.app.appid,
            "daid": self.app.daid,
            "action": f"{3 if sess.verify_rst is not None else 2}-{choice([1, 2])}-{int(time_ns() / 1e6)}",
            "ptdrvs": sess.check_rst.ptdrvs,
            "sid": sess.check_rst.session,
            "o1vId": await self.deviceId(),
        }
        if sess.sms_code:
            data["pt_sms_code"] = sess.sms_code
        self.referer = sess.login_referer

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
        await self.check(sess)

        if sess.code == StatusCode.NeedCaptcha:
            log.warning("需通过防水墙")
            await self.pass_vc(sess)
            if sess.verify_rst is None or not sess.verify_rst.ticket:
                raise TencentLoginError(StatusCode.NeedCaptcha, "internal error when passing vc")

        while True:
            resp = await self.try_login(sess)
            pastcode = sess.pastcode
            sess.login_history.append(resp)
            if resp.code == StatusCode.Authenticated:
                sess.login_url = str(resp.url)
                return await self._get_login_url(sess)
            elif resp.code == StatusCode.NeedSmsVerify:
                log.warning("需用户短信验证")
                if pastcode == StatusCode.NeedSmsVerify:
                    raise TencentLoginError(resp.code, "重复要求动态验证码")
                if UpEvent.GetSmsCode.__name__ in self.hook.__dict__:
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
        The `captcha` function is used to build a :class:`Captcha` instance.
        It takes in a string, which is the session id got from :meth:`.new`, and returns the :class:`Captcha` instance.


        :param sid: Pass the session id to the captcha function
        :return: An instance of the captcha class
        """

        from .captcha import Captcha

        return Captcha(self.client, self.app.appid, sid, str(self.login_page_url))

    async def pass_vc(self, sess: UpWebSession):
        """
        The `pass_vc` function is used to pass the verification tcaptcha.
        It is called when :meth:`.try_login` returns a :obj:`StatusCode.NeedCaptcha` code.

        :param sess: the session object
        :return: The session with :obj:`~UpWebSession.verify_rst` is set.
        """

        for retry in range(4):
            c = self.captcha(sess.check_rst.session)
            sess.verify_rst = await c.verify()
            if sess.verify_rst.ticket:
                break
            log.warning(f"ticket is empty. retry={retry}")
        else:
            raise TencentLoginError(sess.code, "ticket is always empty")

        log.info("verify success!")
        return sess
