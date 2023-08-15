from aioqzone.model import *
from aioqzone.utils.entity import finfo_box_entities, split_entities


def test_text_entity():
    txt = """foo[em]e100[/em][em]e400399[/em]bar@{uin:12345,nick:spam}foobar[em]e400599[/em]{url:https://example.com&a=1%20,text:网页链接}end"""
    entities = split_entities(txt)
    assert entities == [
        TextEntity(con="foo"),
        EmEntity(eid=100),
        EmEntity(eid=400399),
        TextEntity(con="bar"),
        AtEntity(uin=12345, nick="spam"),
        TextEntity(con="foobar"),
        EmEntity(eid=400599),
        LinkEntity(url="https://example.com&a=1%20"),
        TextEntity(con="end"),
    ]


def test_finfo_entity():
    from lxml.html import fromstring

    html = """
    foo<img src="http://qzonestyle.gtimg.cn/qzone/em/e100.png"><img src="http://qzonestyle.gtimg.cn/qzone/em/e400399.png">bar<a href="https://user.qzone.qq.com/12345">@spam</a>foobar<img src="http://qzonestyle.gtimg.cn/qzone/em/e400599.png"><a href="https://example.com&a=1%20">网页链接</a>end"""
    entities = finfo_box_entities(fromstring(html))
    assert entities == [
        TextEntity(con="foo"),
        EmEntity(eid=100),
        EmEntity(eid=400399),
        TextEntity(con="bar"),
        AtEntity(uin=12345, nick="spam"),
        TextEntity(con="foobar"),
        EmEntity(eid=400599),
        LinkEntity(url="https://example.com&a=1%20"),
        TextEntity(con="end"),
    ]
