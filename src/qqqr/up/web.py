import asyncio
import logging
import re
import typing as t
from contextlib import suppress
from random import choice, random
from time import time_ns

from tenacity import RetryError
from yarl import URL

import qqqr.message as MT
from qqqr.base import LoginBase, LoginSession
from qqqr.constant import StatusCode
from qqqr.exception import TencentLoginError
from qqqr.type import APPID, PT_QR_APP, Proxy
from qqqr.utils.net import ClientAdapter

from ._model import CheckResp, LoginResp, VerifyResp
from .captcha import Captcha
from .encrypt import PasswdEncoder, TeaEncoder

CHECK_URL = "https://ssl.ptlogin2.qq.com/check"
LOGIN_URL = "https://ssl.ptlogin2.qq.com/login"
log = logging.getLogger(__name__)


class UpWebSession(LoginSession):
    def __init__(
        self,
        login_sig: str,
        login_referer: str,
        *,
        create_time: t.Optional[float] = None,
    ) -> None:
        super().__init__(create_time=create_time)
        self.login_sig = login_sig
        self.login_referer = login_referer
        """url fetched in `new`."""
        self.verify_rst: t.Optional[VerifyResp] = None
        self.sms_ticket = ""
        self.sms_code: t.Optional[str] = None
        self.login_history: t.List[LoginResp] = []

    def set_check_result(self, check: CheckResp):
        self.check_rst = check

    @property
    def pastcode(self) -> int:
        if self.login_history:
            return self.login_history[-1].code
        return 0

    @property
    def sid(self) -> str:
        return self.check_rst.session

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

    async def pass_vc(self, solver: "Captcha") -> None:
        """
        The `pass_vc` function is used to pass the verification tcaptcha.
        It is called when :meth:`.try_login` returns a :obj:`StatusCode.NeedCaptcha` code.

        :param solver: the :class:`Captcha` object
        :raise NotImplementedError: if cannot solve this captcha
        :raise TencentLoginError: if failed to pass captcha
        """
        try:
            self.verify_rst = await solver.verify()
        except RetryError as e:
            from qqqr.constant import captcha_status_description

            r: VerifyResp = e.last_attempt.result()
            raise TencentLoginError(
                StatusCode.NeedCaptcha,
                captcha_status_description.get(r.code, r.errMessage),
                subcode=r.code,
            ) from e.last_attempt.exception()

        log.info("成功通过验证码")


class _UpHookMixin:
    def __init__(self, *args, **kwds) -> None:
        super().__init__(*args, **kwds)
        self.sms_code_input = MT.sms_code_input()
        self.solve_select_captcha = MT.solve_select_captcha()


class UpWebLogin(_UpHookMixin, LoginBase[UpWebSession]):
    """
    .. versionchanged:: 0.12.4

        `TeaEncoder` is used as the default password encoder. A `legacy_encoder` paramater is added to force
        using the former `NodeEncoder`. It can also be configured by set :envvar:`AIOQZONE_PWDENCODER` to "node".
        Note that the paramater in code, i.e. `legacy_encoder`, takes precedence.

    .. versionchanged:: 0.13.0.dev1

        `TeaEncoder` is the only encoder. ``NodeEncoder`` is removed.
    """

    def __init__(
        self,
        client: ClientAdapter,
        uin: int,
        pwd: str,
        h5=True,
        app: t.Optional[APPID] = None,
        proxy: t.Optional[Proxy] = None,
        info: t.Optional[PT_QR_APP] = None,
    ):
        super().__init__(client, h5=h5, app=app, proxy=proxy, info=info)
        self.uin = uin
        self.pwd = pwd
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

        return URL("https://xui.ptlogin2.qq.com/cgi-bin/xlogin").with_query(params)

    async def deviceId(self) -> str:
        """a js fingerprint.

        .. seealso:: https://github.com/fingerprintjs/fingerprintjs
        """
        return ""  # TODO

    async def new(self):
        """Create a :class:`UpWebSession`. This will call `check` api of Qzone, and receive result
        about whether this login needs a captcha, sms verification, etc.

        :raise `httpx.HTTPStatusError`:

        :return: a up login session
        """
        async with self.client.get(self.login_page_url) as r:
            r.raise_for_status()
            return UpWebSession(r.cookies["pt_login_sig"].value, str(r.url))

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
            rl = re.findall(r"'(.*?)'[,\)]", await r.text())

        rdict = dict(
            zip(
                ["code", "verifycode", "salt", "verifysession", "isRandSalt", "ptdrvs", "session"],
                rl,
            )
        )
        sess.set_check_result(CheckResp.model_validate(rdict))

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
            rl = re.findall(r"'(.*?)'[,\)]", await r.text())
        # ptui_sendSMS_CB('10012', '短信发送成功！')
        if int(rl[0]) != 10012:
            raise TencentLoginError(sess.pastcode, rl[1])

    async def _make_login_param(self, sess: UpWebSession):
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
        data.update(const)
        return data

    async def try_login(self, sess: UpWebSession):
        """
        Check if current session meets the login condition.
        It takes a session object and returns response of this try.

        :param sess: Store the session information
        :return: A login response
        """
        async with self.client.get(
            LOGIN_URL, params=await self._make_login_param(sess)
        ) as response:
            response.raise_for_status()
            rl = re.findall(r"'(.*?)'[,\)]", await response.text())

        resp = LoginResp.model_validate(dict(zip(["code", "", "url", "", "msg", "nickname"], rl)))
        if resp.code == StatusCode.NeedSmsVerify:
            sess.sms_ticket = ""
            if m := response.cookies.get("pt_sms_ticket"):
                sess.sms_ticket = m.value
        log.debug(resp)
        return resp

    async def login(self):
        sess = await self.new()
        await self.check(sess)

        if sess.code == StatusCode.NeedCaptcha:
            log.warning("需通过防水墙")

            if (solver := self.captcha_solver(sess.sid)) is None:
                raise TencentLoginError(StatusCode.NeedCaptcha, "未安装依赖，无法识别验证码")

            try:
                await sess.pass_vc(solver)
            except NotImplementedError:
                raise TencentLoginError(StatusCode.NeedCaptcha, "未能识别验证码")
            if sess.verify_rst is None or not sess.verify_rst.ticket:
                raise TencentLoginError(StatusCode.NeedCaptcha, "验证过程出现错误")

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
                if not self.sms_code_input.has_impl:
                    # fast return so we won't always request smscode which may risk test account.
                    raise TencentLoginError(resp.code, "未实现的功能：输入验证码")
                await self.send_sms_code(sess)
                with suppress(BaseException):
                    sms_code = await asyncio.wait_for(
                        self.sms_code_input(uin=self.uin, phone=resp.msg, nickname=resp.nickname),
                        timeout=60,
                    )
                    if sms_code and len(sms_code := sms_code.strip()) >= 4:
                        sess.sms_code = sms_code
                if sess.sms_code is None:
                    raise TencentLoginError(resp.code, "未获得动态(SMS)验证码")
            else:
                raise TencentLoginError(resp.code, resp.msg)

    def captcha_solver(self, sid: t.Union[str, UpWebSession]):
        """
        The `captcha` function is used to build a :class:`Captcha` instance.
        It takes in a string, which is the session id got from :meth:`.new`, and returns the :class:`Captcha` instance.


        :param sid: Pass the session id to the captcha function
        :return: An instance of the captcha class, or None if dependency not installed.
        """

        try:
            import chaosvm
            import numpy
            import PIL
        except ImportError:
            log.warning("captcha extras not installed. Install `aioqzone[captcha]` and retry.")
            log.debug("ImportError as follows:", exc_info=True)
            return

        if isinstance(sid, UpWebSession):
            sid = sid.sid

        solver = Captcha(self.client, self.app.appid, sid, str(self.login_page_url))
        solver.solve_select_captcha = self.solve_select_captcha
        return solver
