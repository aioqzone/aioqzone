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
    abstime: int

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
    # likecnt: Optional[int] = None
    # relycnt: Optional[int] = None
    # commentcnt: Optional[int] = None


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
    height: int = 0
    width: int = 0
    url1: HttpUrl
    url2: HttpUrl
    url3: HttpUrl
    is_video: Optional[int] = False

    def from_url(self, url: HttpUrl):
        self.url1 = self.url2 = self.url3 = url

    @classmethod
    def from_floatview(cls, fv: 'FloatViewPhoto'):
        if fv.is_video and fv.video_info:
            return VideoRep.from_floatview(fv)
        else:
            return cls(
                height=fv.height,
                width=fv.width,
                is_video=False,
                url1=fv.pre,
                url2=fv.picId,
                url3=fv.url,
            )


class VideoInfo(BaseModel):
    cover_height: int = 0    # same as VideoRep.height
    cover_width: int = 0
    url1: HttpUrl
    url3: HttpUrl
    video_id: str


class VideoInfo2(BaseModel):
    cover_height: int = 0    # same as VideoRep.height
    cover_width: int = 0
    vid: str
    video_url: HttpUrl


class VideoRep(PicRep):
    video_info: VideoInfo

    @classmethod
    def from_floatview(cls, fv: 'FloatViewPhoto'):
        assert fv.is_video
        assert fv.video_info
        return cls(
            height=fv.height,
            width=fv.width,
            is_video=True,
            url1=fv.pre,
            url2=fv.picId,
            url3=fv.url,
            video_info=VideoInfo(
                cover_height=fv.height,
                cover_width=fv.width,
                url1=fv.pre,
                url3=fv.video_info.video_url,
                video_id=fv.video_info.vid
            )
        )


class FeedDetailRep(HasContent):
    uin: int
    name: str
    tid: str
    created_time: int

    # forward from
    rt_con: Optional[HasContent] = None
    rt_uin: int = 0
    rt_uinname: str = ""
    rt_tid: str = ""
    rt_createTime: str = ""
    pic: Optional[list[Union[VideoRep, PicRep]]] = None

    cmtnum: int
    commentlist: Optional[list[CommentRep]] = None
    fwdnum: int


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
    # picKey: str   # = tid,picId
    video_info: Optional[VideoInfo2] = None

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
