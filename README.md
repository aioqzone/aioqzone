# aioqzone

aioqzone is a python package handling Qzone web login and wrapping some common Qzone Http apis.

> **PythonVersionAnnouncement**: Finally I've decided downgrade syntax to py37. All 3.7+ syntax-sugars will be removed in later commits. This is a hard decision but I'm developing a lib instead of an app. However py39 or later versions are still recommended.

[![black](https://img.shields.io/badge/python-3.10-blue.svg)][home]
[![QQQR](https://github.com/JamzumSum/aioqzone/actions/workflows/qqqr.yml/badge.svg?branch=beta&event=schedule)](https://github.com/JamzumSum/aioqzone/actions/workflows/qqqr.yml)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[简体中文](README_zh-cn.md)

## Features

### Qzone Feature

- [x] QR login
- [x] password login (limited)
- [ ] passing captcha (implemented but seems not working...)
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

__Working On:__

- [ ] doc support (readthedoc page available soon)
- [ ] test coverage

## Dependency out of `setup.cfg`

- NodeJS (jssupport)

## Description

|package    |brief description  |
|-----------|-------------------|
|aioqzone   |qzone api wrapper  |
|jssupport  |exec js            |
|qqqr       |qzone web login    |

## Examples

You can look for these repos for examples in practice.

### aioqzone plugins

- [aioqzone-feed][aioqzone-feed]: aioqzone plugin providing higher level api for processing feed


## License

```
Copyright (C) 2022 JamzumSum.

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


[home]: https://github.com/JamzumSum/aioqzone "Python wrapper for Qzone web login and Qzone http api"
[aioqzone-feed]: https://github.com/JamzumSum/aioqzone-feed "aioqzone plugin providing higher level api for processing feed"
