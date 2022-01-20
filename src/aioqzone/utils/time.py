from datetime import date, timedelta
import time


def time_ms(ts: float = None):
    """int timestamp in ms.

    Args:
        ts (float, optional): timestamp in seconds. Defaults to `time.time()`.

    Returns:
        int: ms timestamp
    """
    return round((ts or time.time()) * 1000)


def dayspac(ts1: float, ts2: float = None):
    """return ts2 - ts1

    Args:
        ts1 (float): past timestamp, in seconds, like `time.time()`
        ts2 (float, optional): timestamp, in seconds. Defaults to `time.time()`.

    Returns:
        float: dayspac in float
    """
    d = date.fromtimestamp(ts2 or time.time()) - date.fromtimestamp(ts1)
    return d.seconds / 86400
