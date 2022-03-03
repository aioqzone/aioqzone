def hash33(key: str, phash: int = 0):
    # str.hash33
    for c in key:
        phash += (phash << 5) + ord(c)
    return 0x7FFFFFFF & phash


def gtk(p_skey: str):
    return hash33(p_skey, phash=5381)
