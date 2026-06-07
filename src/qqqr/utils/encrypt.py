"""Qzone encryption utilities.

Implements :func:`hash33` (string hash) and :func:`gtk` (p_skey token
computation used by Qzone APIs).
"""


def hash33(key: str, phash: int = 0):
    """Qzone's ``hash33`` string hash algorithm.

    :param key: input string
    :param phash: initial hash value (default 0)
    :returns: hashed integer (masked to 31 bits)
    """
    for c in key:
        phash += (phash << 5) + ord(c)
    return 0x7FFFFFFF & phash


def gtk(p_skey: str):
    """Compute the ``gtk`` token from a ``p_skey``.

    :param p_skey: the p_skey cookie value
    :returns: gtk integer
    """
    return hash33(p_skey, phash=5381)
