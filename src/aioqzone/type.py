from typing import Optional, Union
from pydantic import BaseModel
from pydantic.networks import HttpUrl


class FeedData(BaseModel):
    uin: int
    tid: str
    feedstype: str


class LikeData(BaseModel):
    unikey: str
    curkey: str
    appid: int
    typeid: int
    fid: str


class FeedRep(BaseModel):
    ver: int
    appid: int
    typeid: int
    key: str
    abstime: int
    uin: int
    nickname: str
    html: str
    likecnt: Optional[int]
    relycnt: Optional[int]
    commentcnt: Optional[int]


class CommentRep(BaseModel):
    content: str
    create_time: int
    owner: dict
    replyNum: int
    tid: int


class PicRep(BaseModel):
    height: int
    width: int
    url1: HttpUrl
    url2: HttpUrl
    url3: HttpUrl
    is_video: Optional[bool] = False


class VideoInfo(BaseModel):
    cover_height: int
    cover_width: int
    url1: HttpUrl
    url2: HttpUrl
    url3: HttpUrl
    video_id: str


class VideoRep(PicRep):
    video_info: VideoInfo


class FeedDetailRep(BaseModel):
    uin: int
    name: str
    tid: str
    created_time: int

    content: str
    conlist: Optional[list[dict]] = None
    pic: Optional[list[Union[PicRep, VideoRep]]] = None

    cmtnum: int
    commentlist: list[CommentRep]
    fwdnum: int

    source_appid: str
    source_name: Optional[str] = ""


class FeedsCount(BaseModel):
    aboutHostFeeds_new_cnt: int
    replyHostFeeds_new_cnt: int
    myFeeds_new_cnt: int
    friendFeeds_new_cnt: int
    friendFeeds_newblog_cnt: int
    friendFeeds_newphoto_cnt: int
    specialCareFeeds_new_cnt: int
    followFeeds_new_cnt: int
    newfeeds_uinlist: list


class FloatViewPhoto(BaseModel):
    albumId: str
    createTime: str
    desc: dict
    ownerName: str
    ownerUin: int
    photoOwner: int
    tid: str
    topicId: str

    height: int
    width: int

    pre: str
    url: str
    picId: str
    picKey: str

    cmtTotal: int
    fwdnum: int

    likeTotal: int
    likeKey: str
    likeList: list[dict]

    lloc: str
    original_tid: str
    photocubage: int
    phototype: int

    isMultiPic: Optional[bool] = False
    is_weixin_mode: Optional[bool] = False
    is_video: Optional[bool] = False
