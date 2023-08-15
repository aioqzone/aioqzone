import re
from typing import List

from lxml.html import HtmlElement

from aioqzone.model import AtEntity, ConEntity, EmEntity, LinkEntity, TextEntity

entity_rules = r"""
(?P<em>\[em\])?     # emoji entity start
(?(em)
    e(?P<eid>\d+)   # emoji id
    \[/em\]         # emoji entiry end

    |               # otherwise

    (?P<at>@)?
    (?(at)

    \{                          # at entiry start
        uin:(?P<uin>\d+),       # at uin
        nick:(?P<nick>.+?)      # at nickname
    \}                          # at entiry end

    |

    \{                          # link entity start
        url:(?P<url>[^,]+),     # link url
        text:(?P<text>[^\}]*)   # link text
    \}

    )

)
"""


RE_ENTITY = re.compile(entity_rules, re.VERBOSE)


def finfo_box_entities(finfo: HtmlElement) -> List[ConEntity]:
    def yield_children(elm: HtmlElement):
        if elm.text is not None:
            yield elm.text
        for e in iter(elm):
            yield e
            if e.tail is not None:
                yield e.tail

    entities: List[ConEntity] = []
    for e in yield_children(finfo):
        if isinstance(e, str):
            entities.append(TextEntity(con=e))
            continue
        assert isinstance(e, HtmlElement)

        if e.tag == "img":
            if m := re.match(r"https?://[\w\.]+/qzone/em/e(\d+)\.\w{3}", e.get("src", "")):
                entities.append(EmEntity(eid=int(m.group(1))))
                continue
        elif e.tag == "a":
            uin = re.match(r"https?://user.qzone.qq.com/(\d+)/?", e.get("href", ""))
            if uin:
                nick = (e.text or "@")[1:]
                entities.append(AtEntity(uin=int(uin.group(1)), nick=nick))
                continue
            entities.append(LinkEntity(url=e.get("href", ""), text=e.text))
            continue

        # by default we add a text entity which content is the html text content
        entities.append(TextEntity(con=e.text_content()))
    return entities


def split_entities(s: str) -> List[ConEntity]:
    entities: List[ConEntity] = []
    pos = 0
    for m in RE_ENTITY.finditer(s):
        start, end = m.span()
        if pos != start:
            entities.append(TextEntity(con=s[pos:start]))
        if m.group("em"):
            entities.append(EmEntity(eid=int(m.group("eid"))))
        elif m.group("at"):
            entities.append(AtEntity(nick=m.group("nick"), uin=int(m.group("uin"))))
        elif m.group("url"):
            entities.append(LinkEntity(url=m.group("url"), text=m.group("text")))
        pos = end
    if pos < len(s):
        entities.append(TextEntity(con=s[pos:]))
    return entities
