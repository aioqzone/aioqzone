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
    time: int
    appid: int
    typeid: int = Field(alias="feedstype")
    curkey: Union[HttpUrl, str] = Field(alias="curlikekey")
    orgkey: Union[HttpUrl, str] = Field(alias="orglikekey")
    ugckey: str
    """an underscore-joined string including `uin`, `appid`, `ugcrightkey`"""
    ugcrightkey: str
    """an identifier, for most 311 feeds, it equals to cellid (fid)."""
    right_info: RightInfo
    wup_feeds_type: int

    subid: int = 0
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
    summary: str = ""
    hasmore: bool = False

    @root_validator(pre=True)
    def add_hasmore(cls, v: dict):
        if "hasmore" not in v:
            if len(v.get("summary", "")) >= 499:
                v["hasmore"] = True
        return v


class LikeInfo(BaseModel):
    isliked: bool = False
    likeNum: int = Field(alias="num", default_factory=int)
    likemans: List[UserInfo] = Field(default_factory=list)


class PhotoUrl(BaseModel):
    height: int
    width: int
    url: HttpUrl

    md5: str = ""
    size: int = 0

    def __hash__(self) -> int:
        o = (self.__class__.__name__, self.height, self.width, self.url)
        return hash(o)

    def __eq__(self, o) -> bool:
        return (
            isinstance(o, PhotoUrl)
            and (o.url == self.url)
            and (o.width == self.width)
            and (o.height == self.height)
        )


class PhotoUrls(BaseModel):
    urls: Set[PhotoUrl]

    @root_validator(pre=True)
    def unpack_urls(cls, v: dict):
        return dict(urls=list(v.values()))

    @property
    def largest(self) -> PhotoUrl:
        return max(self.urls, key=lambda p: p.height * p.width)

    @property
    def smallest(self) -> PhotoUrl:
        return min(self.urls, key=lambda p: p.height * p.width)


class FeedVideo(BaseModel):
    videoid: str
    videourl: HttpUrl
    # videourls: dict
    coverurl: PhotoUrls
    videotime: int

    videotype: int = 0
    albumid: str = ""
    video_max_playtime: int = 0


class PicData(BaseModel):
    photourl: PhotoUrls
    videodata: Optional[FeedVideo] = None
    videoflag: int = 0

    albumid: str
    curkey: str = Field(alias="curlikekey")

    origin_size: int
    origin_height: int
    origin_width: int
    origin_phototype: int = 0

    @root_validator(pre=True)
    def remove_useless_data(cls, v: dict):
        if "videodata" in v:
            if not v["videodata"]["videourl"]:
                del v["videodata"]
        return v


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

    @property
    def abstime(self):
        return self.common.time


class HasUserInfo(BaseModel):
    userinfo: UserInfo


class HasSummary(BaseModel):
    summary: FeedSummary = Field(default_factory=FeedSummary)


class HasMedia(BaseModel):
    pic: Optional[FeedPic]
    video: Optional[FeedVideo]


class ShareInfo(BaseModel):
    summary: str = ""
    title: str = ""
    photourl: Optional[PhotoUrls] = None

    @root_validator(pre=True)
    def remove_empty_photourl(cls, v: dict):
        if not v.get("photourl"):
            v["photourl"] = None
        return v


class Share(HasCommon):
    common: FeedCommon = Field(alias="cell_comm")


class FeedOriginal(HasCommon, HasUserInfo, HasSummary, HasMedia):
    cellid: str = ""
    common: FeedCommon = Field(alias="cell_comm")
    userinfo: UserInfo = Field(alias="cell_userinfo")
    summary: FeedSummary = Field(alias="cell_summary")
    pic: Optional[FeedPic] = Field(alias="cell_pic")
    video: Optional[FeedVideo] = Field(alias="cell_video")

    @root_validator(pre=True)
    def unpack_cellid(cls, v: dict):
        if "cell_id" in v:
            v["cellid"] = v["cell_id"]["cellid"]
        return v


class FeedData(HasCommon, HasSummary, HasMedia, HasUserInfo):
    cellid: str = ""
    common: FeedCommon = Field(alias="comm")
    like: LikeInfo = Field(default_factory=LikeInfo)

    comment: FeedComment = Field(default_factory=FeedComment)
    original: Union[FeedOriginal, Share, None]
    share_info: ShareInfo = Field(default_factory=ShareInfo)

    @root_validator(pre=True)
    def unpack_cellid(cls, v: dict):
        if "id" in v:
            v["cellid"] = v["id"]["cellid"]
        return v

    @root_validator(pre=True)
    def unpack_share_info(cls, v: dict):
        if "operation" in v:
            v["share_info"] = v["operation"].get("share_info", {})
        return v


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
