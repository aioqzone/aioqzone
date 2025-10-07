============================
Examples
============================

This page provides a collection of examples of aioqzone usage.

Login
============================

.. tab:: QR code login

    .. code-block:: python

        from aioqzone.api import QrLoginConfig, QrLoginManager
        from qqqr.utils.net import ClientAdapter

        with ClientAdapter() as client:
            mgr = QrLoginManager(client, config=QrLoginConfig(uin=env.uin))

    User-Agent is automatically set when login.

.. tab:: uin-password login

    .. code-block:: python

        from aioqzone.api import UpLoginConfig, UpLoginManager
        from qqqr.utils.net import ClientAdapter

        with ClientAdapter() as client:
            mgr = UpLoginManager(
                client,
                config=UpLoginConfig.model_validate(
                    dict(uin=env.uin, pwd=env.password, fake_ip="8.8.8.8")
                ),
            )

    User-Agent is automatically set when login.

.. tab:: external cookie login

    You can surely disable auto login and use external cookie:

    .. code-block:: python

        import json
        from os import environ

        from aioqzone.api.login import ConstLoginMan
        from qqqr.utils.net import ClientAdapter

        with open("your_external_cookie.json") as f:
            cookie = json.load(f)
        with ClientAdapter() as client:
            mgr = ConstLoginMan(cookie)

    User-Agent is **NOT** automatically set, remember to change it:

    .. code-block:: python

        from qqqr.utils.net import ClientAdapter
        from qqqr.utils.net import use_mobile_ua

        with ClientAdapter() as client:
            use_mobile_ua(client)

        ...

    If you'd like to use external cookie with auto login, just assign cookie dict to login manager:

    .. code-block:: python

        import json
        from os import environ

        from aioqzone.api.login import QrLoginManager
        from qqqr.utils.net import ClientAdapter

        with open("your_external_cookie.json") as f:
            cookie = json.load(f)
        with ClientAdapter() as client:
            mgr = QrLoginManager(client, config=QrLoginConfig(uin=env.uin))
            mgr.cookie = cookie  # assign external cookie to login manager

Receiving Messages from Login Manager
----------------------------------------------

.. seealso:: :doc:`/aioqzone/messages`

You can receive QR code image from QR code login manager:

.. code-block:: python

    import io

    from PIL import Image as image

    man = QrLoginManager(client, config=QrLoginConfig(uin=env.uin))
    man.qr_fetched.add_impl(
        lambda png, times, qr_renew=False: image.open(io.BytesIO(png)).show() if png else None
    )

.. todo:: other messages

Create Qzone H5 API
============================

.. tab:: QR code login

    .. code-block:: python

        from aioqzone.api import QzoneH5Api
        from aioqzone.api.login import QrLoginManager
        from qqqr.utils.net import ClientAdapter

        with ClientAdapter() as client:
            mgr = QrLoginManager(client, config=QrLoginConfig(uin=env.uin))
            api = QzoneH5Api(client, mgr)

.. tab:: uin-password login

    .. code-block:: python

        from aioqzone.api import UpLoginConfig, UpLoginManager
        from qqqr.utils.net import ClientAdapter

        with ClientAdapter() as client:
            mgr = UpLoginManager(
                client,
                config=UpLoginConfig.model_validate(
                    dict(uin=env.uin, pwd=env.password, fake_ip="8.8.8.8")
                ),
            )
            api = QzoneH5Api(client, mgr)

fetch feed flow
=========================================

.. tab:: from self index page

    .. code-block:: python

        feed_flow = await api.index()

.. tab:: from specific profile page

    .. code-block:: python

        feed_flow = await api.profile(uin=123456789)

Fetching (self) feed flow is a preliminary step for most operations, as it gets ``qzonetoken`` from Qzone server,
which is used in most operations.

fetch next page of feed flow
=========================================

As feed flow is paginated, you can fetch next page of feed flow:

.. tab:: self index page

    .. code-block:: python

        attach_info = None
        while True:
            resp = await api.get_active_feeds(attach_info=attach_info)
            attach_info = resp.attach_info
            if not resp.has_more:
                break

.. tab:: specific profile page

    .. code-block:: python

        attach_info = None
        while True:
            resp = await api.get_feeds(uin=123456789, attach_info=attach_info)
            attach_info = resp.attach_info
            if not resp.has_more:
                break

.. seealso::

    `aioqzone-feed <https://github.com/aioqzone/aioqzone-feed>`_ provides a high-level
    interface for fetching feed flow.

fetch avatar from uin
=========================================

This is a no-login API, you can fetch avatar without login state.

.. code-block:: python

    size = 100  # avatar size, can be 100, 640
    resp = await api.avatar(123456789, size)
    with open("out/avatar.png", "wb") as f:
        f.write(resp.avatar)

upload photo
=========================================

Uploading photo is a two-step process. The first is :meth:`QzoneH5API.upload_pic`, which should
be called per-image. The response is file length and md5. The second is `:meth:`QzoneH5API.preupload_photos` ,
which is called once for multiple images, and the response is a list of :class:`PicInfo`, including
image url, image id, etc.

.. code-block:: python

    import asyncio

    images = ["image_a.jpg", "image_b.jpg", "image_c.jpg"]
    hashes = await asyncio.gather(
        *map(api.upload_pic, images)
    )
    pic_infos = await api.preupload_photos(hashes)

.. hint::

    You can specify quality of uploaded image by setting ``quality`` parameter of :meth:`QzoneH5API.upload_pic`.

Mood operation
=========================

upload mood
-------------------------

.. code-block:: python

    from aioqzone.model import UgcRight

    MOOD_TEXT = "Hello, world!"
    picinfo = [...]  # list of PicInfo, can be empty
    feed = await api.publish_mood(
        MOOD_TEXT, photos=picinfo, sync_weibo=False, ugc_right=UgcRight.self
    )

.. hint::

    You can specify mood visibility by setting ``ugc_right`` parameter of :meth:`QzoneH5API.publish_mood` .

delete mood
-------------------------

.. code-block:: python

    # get appid from fetch feed. common appid of mood without sharing is 311.
    delete_response = await api.delete_ugc(feed.fid, appid)

get mood detail
-------------------------

.. code-block:: python

    # fetching feed
    feed_flow = await api.get_active_feeds()
    feed_dict = {i.fid: i for i in feed_flow.vFeeds}
    fetched_feed = feed_dict[feed.fid]

    detail = await api.shuoshuo(
        fetched_feed.fid, fetched_feed.userinfo.uin, fetched_feed.common.appid
    )

like/unlike mood
=========================

.. code-block:: python

    from aioqzone.model import LikeData

    # get appid, curkey and unikey from fetch feed
    # common appid of mood without sharing is 311.

    # for feeds without forward, curkey and unikey are the same.
    # you can construct them by host uin and fid:
    # unikey = LikeData.persudo_unikey(appid, hostuin, feed.fid)

    await api.internal_dolike_app(appid, unikey, curkey=unikey, like=True)  # like
    await api.internal_dolike_app(appid, unikey, curkey=unikey, like=False) # unlike

mood comment
=========================

add comment
-------------------------

.. tab:: w/o picture

    .. code-block:: python

        COMMENT_TEXT = "Nice mood!"
        comment = await api.add_comment(
            hostuin, feed.fid, appid, COMMENT_TEXT, busi_param=fetched_feed.operation.busi_param
        )

    .. tip:: ``busi_param`` is optional, but recommended.

.. tab:: w/ picture

    .. code-block:: python

        COMMENT_TEXT = "Nice mood!"
        picinfo = [...]  # list of PicInfo
        comment_pic = await api.add_comment(
            hostuin, feed.fid, appid, COMMENT_TEXT, [i.url for i in picinfo]
        )

    .. attention::

        Picture comment uses legacy html Qzone API, which has a html response.
        Currently ``commentId`` cannot be parsed from the response.

delete comment
-------------------------

.. code-block:: python

    await api.delete_comment(ownuin, fetched_feed.topicId, comment.commentid)

check feed update
============================

.. admonition:: Speculation

    Call this api every 5 minutes might keep your login cookie alive within one day (or several days).
    Otherwise the login state will expire in several hours.

.. code-block:: python

    await api.mfeeds_get_count()
