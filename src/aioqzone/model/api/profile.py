"""
Qzone uses different feed schemes for ``/mqzone/profile``. This module patches :mod:`.feed`.
"""

import typing as t

from pydantic import (
    AliasPath,
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from .feed import (
    CommentItem,
    FeedComment,
    FeedOperation,
    FeedPic,
    FeedSummary,
    FeedVideo,
    HasCommon,
    HasFid,
    HasSummary,
    LikeInfo,
    PhotoUrls,
    Share,
    UserInfo,
    Visitor,
)


class QzoneProfile(BaseModel):
    nickname: str
    face: HttpUrl

    age: int = 0
    gender: t.Optional[int] = None

    city: str = ""
    country: str = ""
    province: str = ""

    isFamousQzone: bool = False
    is_concerned: bool = False
    is_special: int

    vip: int = 0
    viplevel: int = 0
    viptype: int = 0


class ProfilePicData(BaseModel):
    photourl: PhotoUrls
    commentcount: int
    desc: str = ""
    ismylike: int = 0


class ProfileFeedPic(FeedPic):
    picdata: t.List[ProfilePicData] = Field(validation_alias=AliasPath("picdata", "pic"))


class HasMedia(BaseModel):
    pic: t.Optional[ProfileFeedPic] = None
    video: t.Optional[FeedVideo] = None


class ProfileLikeInfo(LikeInfo):
    likemans: t.Optional[t.List[UserInfo]] = None


class ProfileCommentItem(CommentItem):
    commentLikekey: t.Optional[str] = None
    commentpic: t.Optional[t.List] = Field(
        default=None, validation_alias=AliasPath("commentpic", "pic")
    )
    replys: t.Optional[t.List] = None


class ProfileComment(FeedComment):
    comments: t.List[ProfileCommentItem] = Field(default_factory=list)


class ProfileFeedOriginal(HasFid, HasCommon, HasSummary, HasMedia):
    @model_validator(mode="before")
    def remove_prefix(cls, v: dict[str, t.Any]):
        return {k.removeprefix("cell_"): i for k, i in v.items()}

    @field_validator("summary")
    @classmethod
    def remove_colon(cls, v: FeedSummary):
        v.summary = v.summary.removeprefix("：")
        return v


class ProfileFeedData(HasFid, HasCommon, HasSummary, HasMedia):
    like: ProfileLikeInfo = Field(default_factory=ProfileLikeInfo)

    comment: ProfileComment = Field(default_factory=ProfileComment)
    original: t.Union[ProfileFeedOriginal, Share, None] = Field(
        default=None, union_mode="left_to_right"
    )
    operation: FeedOperation = Field(default_factory=FeedOperation)

    visitor: Visitor = Field(default_factory=Visitor)
