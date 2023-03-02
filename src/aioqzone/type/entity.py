"""This module defines feed text entities. Entities take place of "contents" since this simplifies
and details the works of rich-text stringify.

.. versionadded:: 0.5.0.dev0
"""

from typing import List, Optional, Union

from pydantic import BaseModel, Field


class HasContent(BaseModel):
    content: str = ""


class ConEntity(BaseModel):
    """Base class for all content entities. All entities has a numeric :obj:`type`."""

    pass


class TextEntity(ConEntity):
    """Text, type=2.

    Two objects of this class are considered equal, if their :obj:`con` is equal."""

    con: str = ""

    def __eq__(self, other) -> bool:
        return isinstance(other, TextEntity) and self.con == other.con


class AtEntity(ConEntity):
    """At, type=0. like: ``@bot``

    Two objects of this class are considered equal, if their :obj:`uin` is equal."""

    nick: str = ""
    uin: int

    def __eq__(self, other) -> bool:
        return isinstance(other, AtEntity) and self.uin == other.uin


class EmEntity(ConEntity):
    """Emoji, type=-1. like: ``[em]e100[/em]``

    Two objects of this class are considered equal, if their :obj:`eid` is equal."""

    eid: int

    def __eq__(self, other):
        return isinstance(other, EmEntity) and self.eid == other.eid


RespEntities = Union[AtEntity, TextEntity]
"""Entities that occurs in Qzone responses."""


class HasConEntity(HasContent):
    entities: Optional[List[RespEntities]] = Field(default=None, alias="conlist")
