# Contributing

Welcome to aioqzone community.

## Add API

You can analyse and add new Qzone apis into `aioqzone.api`.

1. Add the request logic in `QzoneWebRawAPI`/`QzoneH5RawAPI`. You can find examples in this file.
2. Add a `*Resp` in `aioqzone.type.resp`. Then add the pydantic-validated version into `QzoneWebAPI`/`QzoneH5API`.
3. Add **at least one** test into `test/api/test_raw.py`. It's recommanded to add corresponding ones into `test/api/test_web.py` or `test/api/test_h5.py`.
4. Create a pull request and wait for review.

## Add Test

Our tests are not fully coveraged. New unittests are needed.

No special rules for tests. Just create a pull request if you've done your work.
