from aiohttp import ClientResponse
from aiohttp.client_exceptions import ClientResponseError


def raise_for_status(response: ClientResponse, *accept_code: int):
    """A checker more strict than `ClientResponse.raise_for_status`.

    Args:
        response (ClientResponse): Client Response. Default is None, means `(200, )`

    Raises:
        `ClientResponseError`: if status not in `accept_code`
    """
    accept_code = accept_code or (200, )
    if response.status not in accept_code:
        raise ClientResponseError(
            response.request_info,
            response.history,
            status=response.status,
            message=response.reason,
            headers=response.headers
        )
