"""
Use this module to get some data from Qzone html feed
"""
import logging
import re
from typing import Optional, Union, cast

from lxml.html import HtmlElement, fromstring
from pydantic import AnyHttpUrl, BaseModel, HttpUrl
from aioqzone.api.raw import QzoneApi

logger = logging.getLogger(__name__)


class HtmlInfo(BaseModel):
    """Some info that must be extract from html response"""
    feedstype: int
    complete: bool
    unikey: Optional[Union[AnyHttpUrl, str]] = None
    curkey: Optional[Union[HttpUrl, str]] = None
    islike: Optional[int] = 0

    @classmethod
    def from_html(cls, html: str):
        root: HtmlElement = fromstring(html)
        safe = lambda i: i[0] if i else HtmlElement()

        # feed data
        elm_fd = safe(root.cssselect('div.f-single-content i[name="feed_data"]'))

        # like data
        ffoot = safe(root.cssselect('div.f-single-foot'))
        likebtn = safe(ffoot.cssselect('a.qz_like_prase') + ffoot.cssselect('a.qz_like_btn_v3'))

        # cut toggle
        toggle = safe(root.cssselect('div.f-info a[data-cmd="qz_toggle"]'))

        return root, cls(
            feedstype=elm_fd.get("data-feedstype"),
            complete=not toggle,
            unikey=likebtn.get('data-unikey'),
            curkey=likebtn.get('data-curkey'),
            islike=likebtn.get('data-islike'),
        )


class HtmlContent(BaseModel):
    content: str = ''
    pic: Optional[list[HttpUrl]] = None
    album: Optional[QzoneApi.AlbumData] = None

    @classmethod
    def from_html(cls, html: Union[HtmlElement, str], hostuin: int = 0):
        root: HtmlElement = fromstring(html) if isinstance(html, str) else html
        mxsafe = lambda i: max(i, key=len) if i else HtmlElement()
        finfo = mxsafe(root.cssselect('div.f-info'))

        def load_src(ls: list[HtmlElement]):
            for a in ls:
                src = next(filter(lambda i: i.tag == 'img', a)).get('src', '')    # type: ignore
                if src.startswith('http'):
                    yield src
                    continue

                m = re.search(r"trueSrc:'(http.*?)'", a.get('onload', ''))
                if m: yield cast(HttpUrl, m.group(1).replace('\\', ''))

                if 'onload' in a.attrib:
                    logger.warning('cannot parse @onload: ' + a.get('onload'))
                elif 'src' in a.attrib:
                    logger.warning('cannot parse @src: ' + a.get('src'))
                else:
                    logger.warning(f'WTF is this? {dict(a.attrib)}')

        lia = root.cssselect('div.f-ct a.img-item')
        data = {k[5:]: v for k, v in lia[0].attrib.items() if k.startswith('data-')}

        return cls(
            content=finfo.text_content(),
            pic=list(load_src(lia)),
            album=QzoneApi.AlbumData.parse_obj(data | {'hostuin': hostuin})
        )
