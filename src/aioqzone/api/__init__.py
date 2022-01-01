"""
Make some easy to use api from basic wrappers.
"""
from typing import Optional, Union

from pydantic import BaseModel

from .raw import QzoneApi


class DummyQapi(QzoneApi):
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

    async def feeds3_html_more(self, pagenum: int, trans: QzoneApi.FeedsMoreTransaction = None):
        r = await super().feeds3_html_more(pagenum, trans=trans)
        return [self.FeedRep.parse_obj(i) for i in r['data']]

    async def emotion_getcomments(self, feedData: QzoneApi.FeedData):
        r = await super().emotion_getcomments(feedData)
        return str.strip(r['newFeedXML'])

    class CommentRep(BaseModel):
        content: str
        create_time: int
        owner: dict
        replyNum: int
        tid: int

    class PicRep(BaseModel):
        height: int
        width: int
        url1: str
        url2: str
        url3: str
        is_video: Optional[bool] = False

    class VideoInfo(BaseModel):
        cover_height: int
        cover_width: int
        url1: str
        url2: str
        url3: str
        video_id: str

    class VideoRep(PicRep):
        video_info: 'DummyQapi.VideoInfo'

    class FeedDetailRep(BaseModel):
        uin: int
        name: str
        tid: str
        created_time: int

        content: str
        conlist: Optional[list[dict]] = None
        pic: Optional[list[Union['DummyQapi.PicRep', 'DummyQapi.VideoRep']]] = None

        cmtnum: int
        commentlist: list['DummyQapi.CommentRep']
        fwdnum: int

        source_appid: str
        source_name: Optional[str] = ""

    async def emotion_msgdetail(self, owner: int, fid: str):
        r = await super().emotion_msgdetail(owner, fid)
        return self.FeedDetailRep.parse_obj(r)

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

    async def get_feeds_count(self):
        r = await super().get_feeds_count()
        return self.FeedsCount.parse_obj(r)

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

    async def floatview_photo_list(self, album: QzoneApi.AlbumData, num: int):
        r = await super().floatview_photo_list(album, num)
        return [DummyQapi.FloatViewPhoto.parse_obj(i) for i in r['photos']]
