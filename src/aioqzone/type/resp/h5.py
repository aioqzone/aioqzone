from typing import List, Optional, Set, Union

from pydantic import BaseModel, Field, root_validator
from pydantic.networks import HttpUrl


class FeedCount(BaseModel):
    active_cnt: int = 0
    passive_cnt: int = 0
    gamebar_cnt: int = 0
    gift_cnt: int = 0
    visitor_cnt: int = 0


class RightInfo(BaseModel):
    ugc_right: int
    allow_uins: List = Field(default_factory=list)


class FeedCommon(BaseModel):
    appid: int
    time: int
    curkey: HttpUrl = Field(alias="curlikekey")
    orgkey: Union[HttpUrl, str] = Field(alias="orglikekey")
    ugckey: str
    ugcrightkey: str
    right_info: RightInfo
    wup_feeds_type: int

    subid: int = 0
    feedsid: str = ""
    feedstype: int = 0
    originaltype: int = 0


class UserInfo(BaseModel):
    nickname: str
    uin: int

    @root_validator(pre=True)
    def unpack_user(cls, v: dict):
        if "user" in v:
            return v["user"]
        return v


class FeedSummary(BaseModel):
    summary: str
    hasmore: bool = False


class LikeInfo(BaseModel):
    isliked: bool = False
    likeNum: int = Field(alias="num", default_factory=int)
    likemans: List[UserInfo] = Field(default_factory=list)


class PhotoUrl(BaseModel):
    height: int
    width: int
    url: Union[HttpUrl, str] = ""

    md5: str
    size: int

    def __hash__(self) -> int:
        o = (self.__class__.__name__, self.height, self.width, self.url)
        return hash(o)


class PhotoUrls(BaseModel):
    urls: Set[PhotoUrl]

    @root_validator(pre=True)
    def unpack_urls(cls, v: dict):
        return dict(urls=list(v.values()))

    @property
    def largest(self) -> PhotoUrl:
        return max(self.urls, key=lambda p: p.height * p.width)


class FeedVideo(BaseModel):
    videoid: str
    videourl: Union[HttpUrl, str] = ""
    # videourls: dict
    coverurl: PhotoUrls
    videotime: int

    videotype: int = 0
    albumid: str = ""
    video_max_playtime: int = 0


class PicData(BaseModel):
    photourl: PhotoUrls
    videodata: FeedVideo
    videoflag: int = 0

    albumid: str
    curkey: str = Field(alias="curlikekey")


class FeedPic(BaseModel):
    albumid: str
    uin: int
    picdata: List[PicData]


class CommentItem(LikeInfo):
    commentid: int
    commentLikekey: HttpUrl
    content: str
    date: int
    user: UserInfo
    isDeleted: bool = False

    likeNum: int = Field(default_factory=int)
    replynum: int
    commentpic: List = Field(default_factory=list)
    replys: List = Field(default_factory=list)
    # picdata: dict


class FeedComment(BaseModel):
    num: int = 0
    unreadCnt: int = 0
    comments: List[CommentItem] = Field(default_factory=list)


class HasCommon(BaseModel):
    common: FeedCommon


class HasUserInfo(BaseModel):
    userinfo: UserInfo


class HasSummary(BaseModel):
    summary: FeedSummary


class HasMedia(BaseModel):
    pic: Optional[FeedPic]
    video: Optional[FeedVideo]


class ShareInfo(BaseModel):
    summary: str
    title: str
    photourl: PhotoUrl
    qq_url: Union[HttpUrl, str] = ""
    weixin_url: Union[HttpUrl, str] = ""


class Share(HasCommon):
    common: FeedCommon = Field(alias="cell_comm")
    share_info: ShareInfo

    @root_validator(pre=True)
    def unpack_share_info(cls, v: dict):
        if "operation" in v:
            v["share_info"] = v["operation"].get("share_info", {})
        return v


class FeedOriginal(HasCommon, HasUserInfo, HasSummary, HasMedia):
    common: FeedCommon = Field(alias="cell_comm")
    userinfo: UserInfo = Field(alias="cell_userinfo")
    summary: FeedSummary = Field(alias="cell_summary")
    pic: Optional[FeedPic] = Field(alias="cell_pic")
    video: Optional[FeedVideo] = Field(alias="cell_video")


class FeedData(HasCommon, HasSummary, HasMedia, HasUserInfo):
    common: FeedCommon = Field(alias="comm")
    like: LikeInfo = Field(default_factory=LikeInfo)

    comment: FeedComment = Field(default_factory=FeedComment)
    original: Union[FeedOriginal, Share, None]

    @property
    def abstime(self):
        return self.common.time


class FeedPageResp(BaseModel):
    """Represents RESPonse from get feed page operation.
    Used to validate response data in :meth:`aioqzone.api.h5.QzoneH5API.index`
    and :meth:`aioqzone.api.h5.QzoneH5API.getActivateFeeds`
    """

    hasmore: bool = False
    attachinfo: str = ""
    newcnt: int

    undeal_info: FeedCount
    vFeeds: List[FeedData]
