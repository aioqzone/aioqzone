import httpx

CIPHERS = [
    "ECDHE+AESGCM",
    "ECDHE+CHACHA20",
    "DHE+AESGCM",
    "DHE+CHACHA20",
    "ECDH+AESGCM",
    "DH+AESGCM",
    "RSA+AESGCM",
    "!aNULL",
    "!eNULL",
    "!MD5",
    "!DSS",
]


def ssl_context():
    """Input client should use this context as `verify`."""
    ctx = httpx.create_ssl_context()
    ctx.set_ciphers(":".join(CIPHERS))
    return ctx


async def ja3Detect(client: httpx.AsyncClient) -> dict:
    """Get https://ja3er.com/json"""
    r = await client.get("https://ja3er.com/json")
    d = r.json()
    await r.aclose()
    return d
