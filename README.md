# aioqzone

aioqzone封装了一些Qzone接口。

[![python](https://img.shields.io/pypi/pyversions/aioqzone?logo=python&logoColor=white)][home]
[![version](https://img.shields.io/pypi/v/aioqzone?logo=python)][pypi]
[![style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![discuss](https://img.shields.io/badge/dynamic/xml?style=social&logo=telegram&label=Discuss&query=%2F%2Fdiv%5B%40class%3D%22tgme_page_extra%22%5D&url=https%3A%2F%2Ft.me%2Faioqzone_chatroom)](https://t.me/aioqzone_chatrooom)

[English](README_en.md) | 简体中文

> 1. ⚠️ aioqzone 仍在开发阶段，任何功能和接口都有可能在未来的版本中发生变化。
> 2. 🆘 **欢迎有意协助开发/维护的中文开发者**。不仅限于本仓库，[aioqzone][org] 所属的任何仓库都需要您的帮助。

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
- [x] 发布(仅文字)/修改/删除说说
- [ ] 评论相关

### 为什么选择 aioqzone

- [x] 完整的 IDE 类型支持 (typing)
- [x] API 结果类型验证 (pydantic)
- [x] 异步设计
- [x] 易于二次开发
- [x] [文档支持](https://aioqzone.github.io/aioqzone)

__在做了:__

- [ ] 完善的测试覆盖

## 包描述

|包名    |简述  |
|-----------|-------------------|
|aioqzone   |封装Qzone API  |
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
[org]: https://github.com/aioqzone
