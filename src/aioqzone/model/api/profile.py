"""
Qzone uses different feed schemes for ``/mqzone/profile``. This module patches :mod:`.feed`.
"""
import typing as t

from pydantic import AliasPath, BaseModel, Field, field_validator, model_validator

from .feed import (
    CommentItem,
    FeedComment,
    FeedCommon,
    FeedPic,
    FeedSummary,
    HasFid,
    HasSummary,
    HasUserInfo,
    LikeInfo,
    PhotoUrls,
    RightInfo,
    Share,
    ShareInfo,
    removeprefix,
)


class ProfileFeedCommon(FeedCommon):
    ugckey: str = ""
    ugcrightkey: str = ""
    right_info: RightInfo = Field(default_factory=RightInfo)
    wup_feeds_type: int = 0


class HasCommon(BaseModel):
    common: ProfileFeedCommon = Field(validation_alias="comm")


class ProfilePicData(BaseModel):
    photourl: PhotoUrls
    commentcount: int
    desc: str = ""
    ismylike: int = 0


class ProfileFeedPic(FeedPic):
    picdata: t.List[ProfilePicData] = Field(validation_alias=AliasPath("picdata", "pic"))


class HasMedia(BaseModel):
    pic: t.Optional[ProfileFeedPic] = None


class ProfileCommentItem(CommentItem):
    commentLikekey: t.Optional[str] = None
    commentpic: t.Optional[t.List] = Field(
        default=None, validation_alias=AliasPath("commentpic", "pic")
    )
    replys: t.Optional[t.List] = None


class ProfileComment(FeedComment):
    comments: t.List[ProfileCommentItem] = Field(default_factory=list)


class ProfileFeedOriginal(HasFid, HasCommon, HasUserInfo, HasSummary, HasMedia):
    @model_validator(mode="before")
    def remove_prefix(cls, v: dict):
        return {removeprefix(k, "cell_"): i for k, i in v.items()}

    @field_validator("summary")
    @classmethod
    def remove_colon(cls, v: FeedSummary):
        v.summary = removeprefix(v.summary, "：")
        return v


class ProfileFeedData(HasFid, HasCommon, HasSummary, HasMedia, HasUserInfo):
    like: LikeInfo = Field(default_factory=LikeInfo)

    comment: ProfileComment = Field(default_factory=ProfileComment)
    original: t.Union[ProfileFeedOriginal, Share, None] = Field(
        default=None, union_mode="left_to_right"
    )
    share_info: ShareInfo = Field(
        default_factory=ShareInfo, validation_alias=AliasPath("operation", "share_info")
    )
