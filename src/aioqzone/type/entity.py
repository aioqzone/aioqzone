"""This module defines feed text entities. Entities take place of "contents" since this simplifies
and details the works of rich-text stringify.

.. versionadded:: 0.5.0.dev0
"""

from typing import List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl


class HasContent(BaseModel):
    content: str = ""


class ConEntity(BaseModel):
    """Base class for all content entities. All entities has a numeric :obj:`type`."""

    pass


class TextEntity(ConEntity):
    """Text.

    Two objects of this class are considered equal, if their :obj:`con` is equal.
    """

    con: str = ""

    def __eq__(self, other) -> bool:
        return isinstance(other, TextEntity) and self.con == other.con


class AtEntity(ConEntity):
    """Mention. like: ``@{uin:123456,nick:foobar}``, ``@foobar``

    Two objects of this class are considered equal, if their :obj:`uin` is equal.
    """

    uin: int
    nick: str = ""

    def __eq__(self, other) -> bool:
        return isinstance(other, AtEntity) and self.uin == other.uin


class EmEntity(ConEntity):
    """Emoji. like: ``[em]e100[/em]``

    Two objects of this class are considered equal, if their :obj:`eid` is equal.
    """

    eid: int

    def __eq__(self, other):
        return isinstance(other, EmEntity) and self.eid == other.eid


class LinkEntity(ConEntity):
    """Link. like ``{url:https://example.com,text:网页链接}``

    .. versionadded:: 0.12.13
    """

    url: Union[HttpUrl, str]
    text: str = "网页链接"


class HasConEntity(HasContent):
    entities: Optional[List[ConEntity]] = Field(default=None, alias="conlist")
