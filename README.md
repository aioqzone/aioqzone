# aioqzone

aioqzone is a python package handling Qzone web login and wrapping some common Qzone Http apis.

[![python](https://img.shields.io/pypi/pyversions/aioqzone?logo=python&logoColor=white)][home]
[![QQQR](https://github.com/aioqzone/aioqzone/actions/workflows/qqqr.yml/badge.svg?branch=beta&event=schedule)](https://github.com/aioqzone/aioqzone/actions/workflows/qqqr.yml)
[![version](https://img.shields.io/pypi/v/aioqzone?logo=python)][pypi]
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[简体中文](https://github.com/aioqzone/aioqzone/blob/beta/README_zh-cn.md)

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
- [x] [doc support](https://aioqzone.github.io/aioqzone)

__Working On:__

- [ ] test coverage

## Node Dependencies

- `jssupport.jsjson.AstLoader` needn't outside processes.
- To use `jssupport.execjs` and `jssupport.jsjson.NodeLoader`, you need to have `Node.js` installed (at least).
- To use  `jssupport.jsdom`, you need to have npm packages `jsdom` and `canvas` to be installed.

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


[home]: https://github.com/aioqzone/aioqzone "Python wrapper for Qzone web login and Qzone http api"
[aioqzone-feed]: https://github.com/aioqzone/aioqzone-feed "aioqzone plugin providing higher level api for processing feed"
[pypi]: https://pypi.org/project/aioqzone
