from typing import Dict

from httpx import HTTPStatusError, Response


def raise_for_status(response: Response, *accept_code: int):
    """A checker more strict than :external+httpx:meth:`Response.raise_for_status`.

    :param response: Client response to check.
    :param accept_code: Overwrite codes that can be accepted, If not given, default is `(200, )`

    :raises `httpx.HTTPStatusError`: if status not in :obj:`accept_code`
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
