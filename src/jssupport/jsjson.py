import json
import logging
from typing import Callable, Union

from .execjs import ExecJS

logger = logging.getLogger(__name__)
JsonDict = dict[Union[str, int], 'JsonValue']
JsonList = list['JsonValue']
JsonValue = Union[bool, int, str, JsonDict, JsonList]

jsonStringify = ExecJS(js='').bind('JSON.stringify', new=False)


def json_loads(
    js: str,
    try_load_first: bool = True,
    parser: Callable[[str], JsonValue] = json.loads
) -> JsonValue:
    """Convert js obj (str rep) to python obj (instance)

    Args:
        js (str): js object. in the format of js code string.
        try_load_first (bool, optional): try to parse string with `parser` firstly. Defaults to True.
        parser: json parser. Defaults to `json.loads`.

    Returns:
        JsonValue: python object reps the same content as that given in js code.
    """
    if try_load_first:
        try:
            return parser(js)
        except json.JSONDecodeError:
            pass

    json_str = jsonStringify(js, asis=True)
    try:
        return parser(json_str)
    except json.JSONDecodeError as e:
        logger.exception('Failed to decode json input!')
        logger.debug('json_str=%s', json_str)
        raise e
