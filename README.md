# aioqzone

aioqzone is a python package handling Qzone web login and wrapping some common Qzone Http apis.

[简体中文](README_zh-cn.md)

## Features

### Qzone Feature

- [x] QR login
- [x] password login (limited)
- [x] passing captcha (implemented but seems not working...)
- [x] get complete html feeds
- [x] get feed details
- [x] get Qzone album
- [x] like/unlike app
- [ ] post feeds
- [ ] comment

### Why using this package?

- [x] full ide typing support (typing)
- [x] api response validation (pydantic)
- [x] async design
- [x] complete infrastructure to ease your own develop
<!-- - [ ] unittest -->

## Dependency

- nodejs (jssupport)
- pydantic
- opencv-python-headless

## Description

|package    |brief description  |
|-----------|-------------------|
|aioqzone   |qzone api wrapper  |
|jssupport  |exec js            |
|qqqr       |qzone web login    |

## License

- [AGPL-3.0](LICENSE)
