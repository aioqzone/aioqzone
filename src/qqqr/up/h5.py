import logging
import re

from httpx import URL

from qqqr.constant import StatusCode
from qqqr.utils.daug import du

from .type import CheckResp, LoginResp
from .web import UpWebLogin, UpWebSession

log = logging.getLogger(__name__)

CHECK_URL = "https://ui.ptlogin2.qq.com/ssl/check"
LOGIN_URL = "https://ui.ptlogin2.qq.com/ssl/login"


class UpH5Login(UpWebLogin):
    def __init__(self, client, app, proxy, uin: int, pwd: str, info=None):
        super().__init__(client, app, proxy, uin, pwd, info)
        lwua = self.client.ua.lower()
        if not any(i in lwua for i in ["android", "ios"]):
            from qqqr.constant import AndroidUA

            self.client.ua = AndroidUA

    @property
    def login_page_url(self):
        params = dict(
            pt_hide_ad=1,
            style=9,
            appid=self.app.appid,
            pt_no_auth=1,
            pt_wxtest=1,
            daid=self.app.daid,
            s_url=self.proxy.s_url,
        )
        return URL("https://ui.ptlogin2.qq.com/cgi-bin/login").copy_with(params=params)

    async def check(self, sess: UpWebSession):
        data = dict(
            pt_tea=2,
            uin=458973857,
            appid=549000929,
            ptlang=2052,
            regmaster="",
            pt_uistyle=9,
            o1vId=await self.deviceId(),
            r=0.5004446805302833,
        )
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

    async def try_login(self, sess: UpWebSession):
        """
        Check if current session meets the login condition.
        It takes a session object and returns response of this try.

        :param sess: Store the session information
        :return: A login response
        """

        const = {
            "regmaster": "",
            "h": 1,
            "g": 1,
            "ptredirect": 1,
            "from_ui": 1,
            "ptlang": 2052,
            "pt_uistyle": 9,
            "fp": "loginerroralert",
            "low_login_enable": 0,
            "device": 2,
            "pt_3rd_aid": 0,
        }
        data = {
            "u": self.uin,
            "p": await self.pwder.encode(sess.check_rst.salt, sess.verifycode),
            "verifycode": sess.verifycode,
            "pt_vcode_v1": int(sess.verify_rst is not None),
            "pt_verifysession_v1": sess.verifysession,
            "pt_randsalt": sess.check_rst.isRandSalt,
            "u1": self.proxy.s_url,
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
