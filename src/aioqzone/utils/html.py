"""
Use this module to get some data from Qzone html feed
"""
import logging
import re
from typing import cast, Iterable, Optional, Union

from lxml.html import fromstring
from lxml.html import HtmlElement
from pydantic import BaseModel
from pydantic import HttpUrl

from aioqzone.api.raw import QzoneApi
from aioqzone.type import PicRep

logger = logging.getLogger(__name__)


class HtmlInfo(BaseModel):
    """Some info that must be extract from html response"""
    feedstype: int
    complete: bool
    unikey: Optional[Union[HttpUrl, str]] = None
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
            complete=not len(toggle),
            unikey=likebtn.get('data-unikey'),
            curkey=likebtn.get('data-curkey'),
            islike=likebtn.get('data-islike'),
        )


class HtmlContent(BaseModel):
    content: str = ''
    pic: Optional[list[PicRep]] = None
    album: Optional[QzoneApi.AlbumData] = None

    @classmethod
    def from_html(cls, html: Union[HtmlElement, str], hostuin: int = 0):
        root: HtmlElement = fromstring(html) if isinstance(html, str) else html
        mxsafe = lambda i: max(i, key=len) if i else HtmlElement()
        img_data = lambda a: {k[5:]: v for k, v in a.attrib.items() if k.startswith('data-')}

        def load_src(a: Iterable[HtmlElement]) -> Optional[HttpUrl]:
            o: Optional[HtmlElement] = next(filter(lambda i: i.tag == 'img', a), None)
            if o is None: return
            src: str = o.get('src', '')
            if src.startswith('http'):
                return cast(HttpUrl, src)

            m = re.search(r"trueSrc:'(http.*?)'", o.get('onload', ''))
            if m: return cast(HttpUrl, m.group(1).replace('\\', ''))

            if 'onload' in o.attrib:
                logger.warning('cannot parse @onload: ' + o.get('onload'))
            elif 'src' in o.attrib:
                logger.warning('cannot parse @src: ' + o.get('src'))
            else:
                logger.warning(f'WTF is this? {dict(o.attrib)}')

        finfo = mxsafe(root.cssselect('div.f-info'))
        lia: list[HtmlElement] = root.cssselect('div.f-ct a.img-item')

        try:
            album = QzoneApi.AlbumData.parse_obj(img_data(lia[0]) | {'hostuin': hostuin})
        except:
            album = None

        pic = [
            PicRep(
                height=(data := img_data(a)).get('height', 0),
                width=data.get('width', 0),
                url1=src,
                url2=src,
                url3=src
            ) for a in lia if (src := load_src(a))    # type: ignore
        ]
        return cls(content=finfo.text_content(), pic=pic, album=album)
