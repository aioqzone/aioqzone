from typing import Awaitable, Dict, Union

from httpx import URL, AsyncClient, HTTPStatusError, Response, Timeout


def raise_for_status(response: Response, *accept_code: int):
    """A checker more strict than :meth:`~httpx.Response.raise_for_status`.

    :param response: Client response to check.
    :param accept_code: Overwrite codes that can be accepted, If not given, default is `(200, )`

    :raise `httpx.HTTPStatusError`: if status not in :obj:`accept_code`
    """
    accept_code = accept_code or (200,)
    if response.status_code not in accept_code:
        raise HTTPStatusError(
            f"{response.status_code} {response.reason_phrase}",
            request=response.request,
            response=response,
        )


def get_all_cookie(response: Response) -> Dict[str, str]:
    """An adapter to get all response cookies from a response object."""
    cookies = response.cookies
    d = {}
    for k in cookies:
        if not d.get(k):
            d[k] = cookies[k]
    return d


class ClientAdapter:
    __slots__ = ("client",)

    class RequestClosure:
        __slots__ = ("response", "__async")

        def __init__(self, response: Awaitable[Response]) -> None:
            super().__init__()
            self.__async = response
            self.response = None

        async def __aenter__(self):
            self.response = await self.__async
            return self.response

        async def __aexit__(self, *_):
            if self.response:
                await self.response.aclose()
                self.response = None

    def __init__(self, client: AsyncClient) -> None:
        """
        .. versionchanged:: 0.9.4a4

            `timeout` of the client will be overwrite.
        """
        super().__init__()
        self.client = client
        client.timeout = Timeout(None)

    @property
    def referer(self):
        return self.client.headers["Referer"]

    @referer.setter
    def referer(self, value: str):
        self.client.headers["Referer"] = value

    @property
    def ua(self):
        return self.client.headers["User-Agent"]

    @ua.setter
    def ua(self, value: str):
        self.client.headers["User-Agent"] = value

    @property
    def headers(self):
        return self.client.headers

    @property
    def cookies(self):
        return self.client.cookies

    def get(self, url: Union[URL, str], *args, **kwds):
        return self.RequestClosure(self.client.get(url, *args, **kwds))

    def post(self, url: Union[URL, str], *args, **kwds):
        return self.RequestClosure(self.client.post(url, *args, **kwds))

    def use_mobile_ua(self):
        ua = self.ua.lower()
        if not any(i in ua for i in ["android", "ios"]):
            from qqqr.constant import AndroidUA

            self.ua = AndroidUA
