# aioqzone

aioqzone is a python package handling Qzone web login and wrapping some common Qzone Http apis.

[![python](https://img.shields.io/pypi/pyversions/aioqzone?logo=python&logoColor=white)][home]
[![version](https://img.shields.io/pypi/v/aioqzone?logo=python)][pypi]
[![style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![discuss](https://img.shields.io/badge/dynamic/xml?style=social&logo=telegram&label=Discuss&query=%2F%2Fdiv%5B%40class%3D%22tgme_page_extra%22%5D&url=https%3A%2F%2Ft.me%2Faioqzone_chatroom)](https://t.me/aioqzone_chatrooom)

English | [简体中文](README.md)

> aioqzone is under active development. Any functionality and interface may be changed.

## Features

### Qzone Feature

- [x] QR login
- [x] password login (limited)
- [x] solve captcha
- [ ] pass network environment verification
- [x] get complete html feeds
- [x] get feed details
- [x] get Qzone album
- [x] like/unlike app
- [x] publish/update/delete text feeds
- [ ] comment

### Why using this package?

- [x] full ide typing support (typing)
- [x] api response validation (pydantic)
- [x] async design
- [x] complete infrastructure to ease your own develop
- [x] [doc support](https://aioqzone.github.io/aioqzone)

__Working On:__

- [ ] test coverage

## Description

|package    |brief description  |
|-----------|-------------------|
|aioqzone   |qzone api wrapper  |
|qqqr       |qzone web login    |

## Examples

You can look for these repos for examples in practice.

### aioqzone plugins

- [aioqzone-feed][aioqzone-feed]: aioqzone plugin providing higher level api for processing feed


## License

```
Copyright (C) 2022 aioqzone.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

- [AGPL-3.0](LICENSE)
- [Disclaimers](https://aioqzone.github.io/aioqzone/disclaimers.html)


[home]: https://github.com/aioqzone/aioqzone "Python wrapper for Qzone web login and Qzone http api"
[aioqzone-feed]: https://github.com/aioqzone/aioqzone-feed "aioqzone plugin providing higher level api for processing feed"
[pypi]: https://pypi.org/project/aioqzone
