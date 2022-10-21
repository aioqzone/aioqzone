# aioqzone

aioqzone封装了一些Qzone接口。

[![python](https://img.shields.io/pypi/pyversions/aioqzone?logo=python&logoColor=white)][home]
[![QQQR](https://github.com/aioqzone/aioqzone/actions/workflows/qqqr.yml/badge.svg?branch=beta&event=schedule)](https://github.com/aioqzone/aioqzone/actions/workflows/qqqr.yml)
[![version](https://img.shields.io/pypi/v/aioqzone?logo=python)][pypi]
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[English](README_en.md)

## 功能和特点

### Qzone 功能

- [x] 二维码登录
- [x] 密码登录 (受限)
- [x] 计算验证码答案
- [ ] 通过网络环境检测
- [x] 爬取HTML说说
- [x] 爬取说说详细内容
- [x] 爬取空间相册
- [x] 点赞/取消赞
- [x] 发布/修改/删除说说
- [ ] 评论相关

### 为什么选择 aioqzone

- [x] 完整的 IDE 类型支持 (typing)
- [x] API 结果类型验证 (pydantic)
- [x] 异步设计
- [x] 易于二次开发
- [x] [文档支持](https://aioqzone.github.io/aioqzone)

__在做了:__

- [ ] 完善的测试覆盖

## node 依赖

- `jssupport.jsjson.AstLoader` 不需要借助其他进程；
- 要使用 `jssupport.execjs` 和 `jssupport.jsjson.NodeLoader`，您（至少）需要安装 `Node.js` >= v14；
- 要使用 `jssupport.jsdom`，您需要安装 `jsdom` 和 `canvas` 两个 npm 包。
- 验证码部分需要使用 `canvas`，因此您需要正确配置运行环境内的 font config ([#45](https://github.com/aioqzone/aioqzone/issues/45)).

## 包描述

|包名    |简述  |
|-----------|-------------------|
|aioqzone   |封装Qzone API  |
|jssupport  |执行JS            |
|qqqr       |网页登录    |

## 例子

这些仓库提供了一些 aioqzone 的实际使用示例。

### aioqzone 的插件们

- [aioqzone-feed][aioqzone-feed]: 提供了操作 feed 的简单接口

## 许可证

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

- aioqzone 以 [AGPL-3.0](LICENSE) 开源.
- [免责声明](https://aioqzone.github.io/aioqzone/disclaimers.html)


[home]: https://github.com/aioqzone/aioqzone "Python wrapper for Qzone web login and Qzone http api"
[aioqzone-feed]: https://github.com/aioqzone/aioqzone-feed "aioqzone plugin providing higher level api for processing feed"
[pypi]: https://pypi.org/project/aioqzone
