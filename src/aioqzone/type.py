from typing import List, Optional, Union

from pydantic import BaseModel
from pydantic import Field
from pydantic.networks import HttpUrl


class PersudoCurkey(str):
    def __new__(cls, uin: int, abstime: int):
        return str.__new__(cls, cls.build(uin, abstime))

    def __init__(self, uin: int, abstime: int) -> None:
        super().__init__()
        self.uin = uin
        self.abstime = abstime

    @classmethod
    def build(cls, uin: int, abstime: int):
        return str(uin).rjust(12, "0") + str(abstime).rjust(12, "0")

    @classmethod
    def from_str(cls, curkey: str):
        uin = curkey[:12]
        abstime = curkey[12:]
        uin = int(uin.lstrip("0"))
        abstime = int(abstime.lstrip("0"))
        return cls(uin=uin, abstime=abstime)


class AlbumData(BaseModel):
    topicid: str
    pickey: str
    hostuin: int


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
        return str(PersudoCurkey(uin, abstime))

    @staticmethod
    def persudo_unikey(appid: int, uin: int, **kwds):
        if appid == 311:
            fid = kwds.get("fid", None) or kwds.get("key")
            return f"https://user.qzone.qq.com/{uin}/mood/{fid}"

        raise ValueError(appid)


# Below are the response reps of Qzone Apis.
class FeedRep(BaseModel):
    ver: int
    appid: int
    typeid: int
    fid: str = Field(alias="key")
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
    content: str = ""


class CommentRep(HasContent):
    abstime: int = Field(alias="create_time")
    owner: dict
    replyNum: int
    tid: int


class PicRep(BaseModel):
    height: int = 0
    width: int = 0
    url1: HttpUrl
    url2: HttpUrl
    url3: HttpUrl
    is_video: int = False

    def from_url(self, url: HttpUrl):
        self.url1 = self.url2 = self.url3 = url

    @classmethod
    def from_floatview(cls, fv: "FloatViewPhoto"):
        if fv.is_video and fv.video_info:
            return VideoRep.from_floatview(fv)
        else:
            return cls(
                height=fv.height,
                width=fv.width,
                is_video=False,
                url1=fv.url1,
                url2=fv.url2,
                url3=fv.url3,
            )


class VideoInfo(BaseModel):
    cover_height: int = 0  # same as VideoRep.height
    cover_width: int = 0
    thumb: HttpUrl = Field(alias="url1")
    raw: HttpUrl = Field(alias="url3")
    vid: str = Field(alias="video_id")


class VideoInfo2(BaseModel):
    cover_height: int = 0  # same as VideoRep.height
    cover_width: int = 0
    vid: str
    raw: HttpUrl = Field(alias="video_url")


class VideoRep(PicRep):
    video_info: VideoInfo

    @classmethod
    def from_floatview(cls, fv: "FloatViewPhoto"):
        assert fv.is_video
        assert fv.video_info
        return cls(
            height=fv.height,
            width=fv.width,
            is_video=True,
            url1=fv.url1,
            url2=fv.url2,
            url3=fv.url3,
            video_info=VideoInfo(
                cover_height=fv.height,
                cover_width=fv.width,
                url1=fv.url1,
                url3=fv.video_info.raw,
                video_id=fv.video_info.vid,
            ),
        )


class FeedDetailRep(HasContent):
    uin: int
    name: str
    tid: str
    abstime: int = Field(alias="created_time")

    # forward from
    rt_con: Optional[HasContent] = None
    rt_uin: int = 0
    rt_uinname: str = ""
    rt_tid: str = ""
    rt_createTime: str = ""
    rt_abstime: int = Field(default=0, alias="rt_created_time")
    pic: Optional[List[Union[VideoRep, PicRep]]] = None

    cmtnum: int
    commentlist: Optional[List[CommentRep]] = None
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

    url1: HttpUrl = Field(alias="pre")
    url2: HttpUrl = Field(alias="picId")
    url3: HttpUrl = Field(alias="url")
    video_info: Optional[VideoInfo2] = None

    cmtTotal: int
    fwdnum: int

    likeTotal: int
    likeKey: str
    likeList: Optional[List[dict]] = None

    lloc: str
    original_tid: str
    photocubage: int
    phototype: int

    isMultiPic: Optional[bool] = False
    is_weixin_mode: Optional[bool] = False
    is_video: Optional[bool] = False

    @property
    def picKey(self):
        return f"{self.tid},{self.url2}"


class MsgListElm(HasContent):
    cmtnum: int
    fwdnum: int

    createTime: str
    abstime: int = Field(alias="created_time")
    commentlist: list

    fid: str = Field(alias="tid")
    uin: int
    name: str
