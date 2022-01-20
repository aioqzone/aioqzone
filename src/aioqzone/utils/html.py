"""
Use this module to get some data from Qzone html feed
"""

from typing import Optional, Union

from lxml.html import HtmlElement, fromstring
from pydantic import AnyUrl, BaseModel


class HtmlInfo(BaseModel):
    """Some info that must be extract from html response"""
    feedstype: int
    complete: bool
    unikey: Optional[Union[AnyUrl, str]] = None
    curkey: Optional[str] = None
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

        return cls(
            feedstype=elm_fd.get("data-feedstype"),
            complete=not toggle,
            unikey=likebtn.get('data-unikey'),
            curkey=likebtn.get('data-curkey'),
            islike=likebtn.get('islike'),
        )
