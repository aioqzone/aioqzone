"""
Use this module to get some data from Qzone html feed
"""
import logging
import re
from typing import Iterable, List, Optional, Union, cast

from lxml.html import HtmlElement, fromstring
from pydantic import BaseModel, HttpUrl

from qqqr.utils.daug import di

from ..type.entity import RespEntities, TextEntity
from ..type.internal import AlbumData
from ..type.resp import PicRep

logger = logging.getLogger(__name__)


class HtmlInfo(BaseModel):
    """Some info that must be extract from html response"""

    nickname: str = ""
    feedstype: int
    topicid: str
    complete: bool
    unikey: Optional[Union[HttpUrl, str]] = None
    curkey: Optional[Union[HttpUrl, str]] = None
    islike: int = 0

    @classmethod
    def from_html(cls, html: str):
        root: HtmlElement = fromstring(html)
        safe = lambda i: i[0] if i else HtmlElement()

        # nickname
        nick = safe(root.cssselect("div.f-single-head div.f-nick"))
        nickname: str = nick.text_content().strip()

        # feed data
        elm_fd = safe(root.cssselect('div.f-single-content i[name="feed_data"]'))

        # like data
        ffoot = safe(root.cssselect("div.f-single-foot"))
        likebtn = safe(ffoot.cssselect("a.qz_like_prase") + ffoot.cssselect("a.qz_like_btn_v3"))

        # cut toggle
        toggle = safe(root.cssselect('div.f-info a[data-cmd="qz_toggle"]'))

        return root, cls(
            nickname=nickname,
            feedstype=elm_fd.get("data-feedstype", None),
            topicid=elm_fd.get("data-topicid", None),
            complete=not len(toggle),
            unikey=likebtn.get("data-unikey", None),
            curkey=likebtn.get("data-curkey", None),
            islike=likebtn.get("data-islike", 0),
        )


class HtmlContent(BaseModel):
    entities: Optional[List[RespEntities]]
    pic: Optional[List[PicRep]] = None
    album: Optional[AlbumData] = None

    @classmethod
    def from_html(cls, html: Union[HtmlElement, str], hostuin: int = 0):
        """Construct a `HtmlContent` object from a html string or an `~lxml.html.HtmlElement`.

        :param html: html string or an `~lxml.html.HtmlElement`
        :param hostuin: used to specify :obj:`~AlbumData.hostuin` field in `.AlbumData`.
        This is optional since you can modify the :obj:`album` field of the return val.
        """
        root: HtmlElement = fromstring(html) if isinstance(html, str) else html
        mxsafe = lambda i: max(i, key=len) if i else HtmlElement()
        img_data = lambda a: {k[5:]: v for k, v in a.attrib.items() if k.startswith("data-")}

        def load_src(a: Iterable[HtmlElement]) -> Optional[HttpUrl]:
            o: Optional[HtmlElement] = next(filter(lambda i: i.tag == "img", a), None)
            if o is None:
                return
            src: str = o.get("src", "")
            if src.startswith("http"):
                return cast(HttpUrl, src)

            m = re.search(r"trueSrc:'(http.*?)'", o.get("onload", ""))
            if m:
                return cast(HttpUrl, m.group(1).replace("\\", ""))

            if "onload" in o.attrib:
                logger.warning("cannot parse @onload: " + o.get("onload", ""))
            elif "src" in o.attrib:
                logger.warning("cannot parse @src: " + o.get("src", ""))
            else:
                logger.warning(f"WTF is this? {dict(o.attrib)}")

        finfo = mxsafe(root.cssselect("div.f-info"))
        lia: List[HtmlElement] = root.cssselect("div.f-ct a.img-item")

        try:
            album = AlbumData.parse_obj(di(img_data(lia[0]), hostuin=hostuin))
        except:
            album = None

        pic = []
        for a in lia:
            src = load_src(a)  # type: ignore
            if not src:
                continue
            data = img_data(a)
            pic.append(
                PicRep(
                    height=data.get("height", 0),
                    width=data.get("width", 0),
                    url1=src,
                    url2=src,
                    url3=src,
                )
            )

        # TODO
        alltxt = TextEntity(type=2, con=finfo.text_content())
        return cls(entities=[alltxt], pic=pic, album=album)
