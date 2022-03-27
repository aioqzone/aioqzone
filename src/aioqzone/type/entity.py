"""This module defines feed text entities. Entities take place of "contents" since this simplifies
and details the works of rich-text stringify.

.. versionadded:: 0.5.0.dev0
"""

from typing import List, Optional, Union

from pydantic import BaseModel, Field


class HasContent(BaseModel):
    content: str = ""


class ConEntity(BaseModel):
    """Base class for all content entities. All entities has a #type."""

    type: int


class TextEntity(ConEntity):
    """Text."""

    con: str = ""


class AtEntity(ConEntity):
    """At. like: ``@bot``"""

    nick: str = ""
    uin: int


class EmEntity(ConEntity):
    """Emoji. like: ``[em]e100[/em]``"""

    eid: int


RespEntities = Union[AtEntity, TextEntity]
"""Entities that occurs in Qzone responses."""


class HasConEntity(HasContent):
    entities: Optional[List[RespEntities]] = Field(default=None, alias="conlist")
