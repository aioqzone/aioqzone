from pathlib import Path
from textwrap import dedent
from typing import Dict, Tuple, cast
from urllib.parse import unquote

from jssupport.execjs import ExecJS, Partial
from jssupport.jsdom import JSDOM
from jssupport.jsjson import json_loads

from ...constant import UA


class CollectEnv(ExecJS):
    """This js env is used to exec `tdc.js`, which will collect MANY information."""

    def __init__(
        self, xlogin_url: str, ipv4: str, ua: str = UA, cookie: str = "", iframe: str = ""
    ) -> None:
        super().__init__()
        self.setup.append(f"let ua=`{ua}`,xlogin=`{xlogin_url}`,ip=`{ipv4}`,cookie=`{cookie}`;")
        self.setup.append(self._windowjs())

    def _windowjs(self):
        js = """const sleep=require("sleep");const{JSDOM}=require("jsdom");location={href:"https://t.captcha.qq.com/template/drag_ele.html",referer:"https://xui.ptlogin2.qq.com/cgi-bin/xlogin"};mouse_events=[];dom=new JSDOM("");document={head:dom.window.document.head,body:dom.window.document.body,location:location,referrer:location['referer'],charset:'UTF-8',cookie:cookie,addEventListener:(e,f)=>{switch(e){case"mousemove":mouse_events.push(f);return}},createElement:(e,o)=>{var elm=new Proxy(dom.window.document.createElement(e,o),{get:(targ,name)=>{if(name=="innerHTML")return targ.inner_html();if(name=="outerHTML")return targ.outer_html();return targ[name]}});switch(e){case"canvas":elm.width=300;elm.height=150;elm.getContext=(e)=>{switch(e){case"2d":return elm.getContext("2d");case"experimental-webgl":return{getSupportedExtensions:()=>{return["WEBGL_debug_renderer_info"]},getExtension:(e)=>{switch(e){case"WEBGL_debug_renderer_info":return{UNMASKED_RENDERER_WEBGL:37446,UNMASKED_VENDOR_WEBGL:37445}}},getParameter:(e)=>{switch(e){case 37446:return"ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero) (0x0000C0DE)), SwiftShader driver)";case 37445:return"Google Inc. (Google)"}}}}};break;case"iframe":elm.contentWindow=window;case"div":elm.style='';break;case"style":elm.sheet=null;elm.remove=()=>{};break}return elm},getElementById:(e)=>{return dom.window.document.getElementById(e)},};screen={width:1408,availHeight:792,height:792,colorDepth:24,pixelDepth:24};navigator={appVersion:ua.substring(8),userAgent:ua,vendor:'Google Inc.',appName:"Netscape",cookieEnabled:true,languages:['zh-CN','en','en-GB','en-US'],platform:'Win32',hardwareConcurrency:8,};CSS={supports:(k,v)=>{if(k=='overscroll-behavior')return true;return false}};function _fake_rpc(servers){this.servers=servers;this.localDescription={sdp:"a=candidate:"+ip};this.createDataChannel=function(e){};this.createOffer=function(cb){}}RTCPeerConnection=new Proxy(_fake_rpc,{construct:(targ,args,newTarget)=>{return new Proxy(new targ(args[0],args[1]),{set:(targ,p,v)=>{if(p=="onicecandidate")v({candidate:{candidate:targ.localDescription.sdp}})}})}});window=new Proxy({name:xlogin,innerHeight:230,innerWidth:300,addEventListener:(e,f)=>{},getComputedStyle:dom.window.getComputedStyle,matchMedia:(e)=>{return{matches:""}}},{get:(targ,name)=>{if(targ[name]!==undefined)return targ[name];return global[name]}});function simulate_slide(xs,ys){mousemove=mouse_events[0];if(mousemove===undefined)return;mean=Math.round(1224/xs.length);for(i=0;i<xs.length;i++){mousemove({type:"mousemove",pageX:xs[i],pageY:ys[i]});sleep.msleep(mean)}};"""
        return dedent(js)

    def load_vm(self, vmcode: str):
        self._vmcode_idx = len(self.setup)
        self.setup.append(vmcode)

    @property
    def vmcode(self) -> str:
        code = self.setup[self._vmcode_idx]
        assert isinstance(code, str)
        return code

    @vmcode.setter
    def vmcode(self, v: str):
        self.setup[self._vmcode_idx] = v

    async def get_data(self):
        self.set_data(ft="qf_7P___H")
        return unquote((await self("window.TDC.getData(!0)")).strip())

    async def get_info(self) -> dict:
        jsobj = await self("window.TDC.getInfo()")
        return cast(dict, json_loads(jsobj))

    def set_data(self, **data):
        self.add_run("window.TDC.setData", data)

    def clear_tc(self):
        self.add_run("window.TDC.clearTc")

    async def get_cookie(self):
        return (await self.get("window.document.cookie")).strip()


class DecryptTDC(CollectEnv):
    def __init__(
        self, xlogin_url: str, ipv4: str, ua: str = UA, cookie: str = "", iframe: str = ""
    ) -> None:
        super().__init__(xlogin_url, ipv4, ua, cookie, iframe)
        self.add_post("process.exit", 0)

    def _windowjs(self):
        with open(Path(__file__).parent / "archive/decrypt.js") as f:
            return super()._windowjs() + f.read()

    async def decrypt(self, collect: str):
        """.. seealso:: https://www.52pojie.cn/thread-1521480-1-1.html"""

        return await self(Partial("dec", self.vmcode, collect))
