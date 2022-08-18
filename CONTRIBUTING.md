# Contributing

Welcome to aioqzone community.

## Add API

You can analyse and add new Qzone apis into `aioqzone.api`.

1. Add the request logic in `aioqzone.api.raw.QzoneApi`. You can find examples in this file.
2. Add a `*Resp` in `aioqzone.type.resp`. Then add the pydantic-validated version into `aioqzone.api.DummyQapi`.
3. Add **at least one** test into `test/api/test_raw.py`. It's recommanded to add corresponding ones into `test/api/test_dummy.py`.
4. Create a pull request and wait for review.

## Add Test

Our tests are not fully coveraged. New unittests are needed.

No special rules for tests. Just create a pull request if you've done your work.
