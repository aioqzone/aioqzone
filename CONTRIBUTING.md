# Contributing to aioqzone

感谢您对 aioqzone 的兴趣！以下是贡献指南。

## 语言规范

- **代码内文档**：docstring、日志和注释使用**英文**。
- **用户错误信息**：直接打印或发送给用户的错误信息使用**中文**。
- **Issue / PR**：支持**中文或英文**。

## Commit 规范

本项目使用 [Conventional Commits](https://www.conventionalcommits.org/)，并在 CI 中通过 `git-cliff` 自动生成 changelog。

### Commit 前缀

| 前缀 | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `doc` | 文档变更 |
| `test` | 测试相关 |
| `refactor` | 代码重构 |
| `build` | 构建系统或依赖 |
| `ci` | CI/CD 配置 |
| `perf` | 性能优化 |
| `chore` | 杂项任务 |
| `proj` | 项目配置 |
| `fmt` / `style` | 代码格式/样式 |

### 示例

```
feat(api): add support for new Qzone endpoint
fix(login): handle expired session correctly
doc: update CONTRIBUTING.md with language guidelines
```

## 开发流程

1. Fork 本仓库并创建功能分支
2. 安装依赖：`uv sync --no-default-groups --group test`
3. 编写代码并确保通过测试：`uv run pytest test --log-cli-level=WARNING`
4. 运行代码检查：
   ```bash
   uv run ruff check --select I --fix
   uv run ruff format
   ```
5. 提交符合 Conventional Commits 规范的 commit
6. 创建 Pull Request

## 测试

- 测试框架使用 **pytest + pytest-asyncio**
- 异步 fixture 和测试需指定 `loop_scope="module"`
- 部分测试需要环境变量 `TEST_UIN` 和 `TEST_PASSWORD`
- CI 环境下 QR 登录测试会自动跳过

## 分支策略

| 分支 | 用途 |
|------|------|
| `dev` / `dev/**` | 开发分支，自动创建 PR 到 `beta` |
| `beta` | 集成分支，合并后自动部署文档 |
| `release` / `release/**` | 发布分支，合并并打标签后自动发布到 PyPI |

## 许可证

通过提交代码，您同意您的贡献将使用本项目的 [AGPL-3.0-or-later](LICENSE) 许可证。
