from typing import Dict

from aiohttp import ClientResponse
from aiohttp.client_exceptions import ClientResponseError


def raise_for_status(response: ClientResponse, *accept_code: int):
    """A checker more strict than `ClientResponse.raise_for_status`.

    :param response: Client response to check.
    :param accept_code: Overwrite codes that can be accepted, If not given, default is `(200, )`

    :raises `aiohttp.ClientResponseError`: if status not in :obj:`accept_code`
    """
    accept_code = accept_code or (200,)
    if response.status not in accept_code:
        raise ClientResponseError(
            response.request_info,
            response.history,
            status=response.status,
            message=response.reason or "",
            headers=response.headers,
        )


def get_all_cookie(response: ClientResponse) -> Dict[str, str]:
    cookies = response.headers.getall("Set-Cookie")
    cookie_kv = (i.split(";")[0].split("=", maxsplit=1) for i in cookies)
    d = {}
    for t in cookie_kv:
        if len(t) < 2:
            continue
        k, v = t
        d[k] = d.get(k) or v
    return d
