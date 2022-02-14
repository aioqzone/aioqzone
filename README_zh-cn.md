# aioqzone

aioqzone封装了一些Qzone接口。

[![QQQR](https://github.com/JamzumSum/aioqzone/actions/workflows/qqqr.yml/badge.svg?branch=beta&event=schedule)](https://github.com/JamzumSum/aioqzone/actions/workflows/qqqr.yml)

[English](README.md)

## 功能和特点

### Qzone 功能

- [x] 二维码登录
- [x] 密码登录 (受限)
- [x] 计算验证码答案 (答案正确但不能通过)
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

__在做了:__

- [ ] 文档支持
- [ ] 完善的测试覆盖

## `setup.cfg` 之外的依赖

- NodeJS (jssupport)

## 包描述

|包名    |简述  |
|-----------|-------------------|
|aioqzone   |封装Qzone API  |
|jssupport  |执行JS            |
|qqqr       |网页登录    |

## 许可证

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

- aioqzone 以 [AGPL-3.0](LICENSE) 开源.
