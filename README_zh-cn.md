# aioqzone

aioqzone is a python package handling Qzone web login and wrapping some common Qzone Http apis.

[![QQQR](https://github.com/JamzumSum/aioqzone/actions/workflows/qqqr.yml/badge.svg?branch=beta&event=schedule)](https://github.com/JamzumSum/aioqzone/actions/workflows/qqqr.yml)

[English](README.md)

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

__Working On:__

- [ ] doc support
- [ ] test coverage

## Dependency out of `setup.cfg`

- nodejs (jssupport)

## Description

|package    |brief description  |
|-----------|-------------------|
|aioqzone   |qzone api wrapper  |
|jssupport  |exec js            |
|qqqr       |qzone web login    |

## License

- [AGPL-3.0](LICENSE)
