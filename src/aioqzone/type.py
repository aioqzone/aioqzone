from typing import Optional, Union

from pydantic import BaseModel
from pydantic.networks import HttpUrl


# LikeData is not a response of any API. It's just a type def.
class LikeData(BaseModel):
    unikey: str
    curkey: str
    appid: int
    typeid: int
    fid: str

    @staticmethod
    def persudo_curkey(uin: int, abstime: int):
        return str(uin).ljust(12, '0') + str(abstime).ljust(12, '0')

    @staticmethod
    def persudo_unikey(appid: int, uin: int, **kwds):
        if appid == 311:
            fid = kwds.get('fid', None) or kwds.get('key')
            return f"https://user.qzone.qq.com/{uin}/mood/{fid}"

        raise ValueError(appid)


# Below are the response reps of Qzone Apis.
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


class FeedMoreAux(BaseModel):
    hasMoreFeeds: bool
    dayspac: int
    pagenum: int
    externparam: str
    begintime: int
    endtime: str

    lastaccesstime: str
    lastAccessRelateTime: str

    aisortBeginTime: str
    aisortEndTime: str
    aisortOffset: str
    aisortNextTime: str

    daylist: str
    uinlist: str

    # attach: str
    # searchtype: str
    # error: str
    # hotkey: str
    # icGroupData: list
    # host_level: str
    # friend_level: str
    # hidedNameList: list
    # owner_bitmap: str


class HasContent(BaseModel):
    content: str = ''


class CommentRep(HasContent):
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


class FeedDetailRep(HasContent):
    uin: int
    name: str
    tid: str
    created_time: int

    rt_con: Optional[HasContent] = None
    pic: Optional[list[Union[PicRep, VideoRep]]] = None

    cmtnum: int
    commentlist: list[CommentRep]
    fwdnum: int

    source_appid: str = ""
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

    pre: HttpUrl
    url: HttpUrl
    picId: HttpUrl
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
