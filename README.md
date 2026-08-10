# claude-code-config

我个人的 [Claude Code](https://code.claude.com) 全局配置备份，换设备 / 重装环境时一键恢复。

## 包含内容

| 文件 | 对应位置 | 作用 |
|---|---|---|
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | 全局提示词：任务持续执行原则、方案先确认再执行、复杂任务才问要不要用多智能体协作等 |
| `settings.json` | `~/.claude/settings.json` | 默认模型/主题 + 状态栏配置 |
| `statusline.py` | `~/.claude/statusline.py` | 终端状态栏脚本 |
| `install.sh` | — | 一键恢复脚本 |

## 恢复方法

```bash
git clone https://github.com/ForceMind/claude-code-config.git
cd claude-code-config
./install.sh
```

`install.sh` 会：
- 把 `CLAUDE.md`、`statusline.py` 复制到 `~/.claude/`，如目标已存在且内容不同，先备份成 `xxx.bak.<时间戳>` 再覆盖；
- 把 `settings.json` 里的键（`model` / `theme` / `statusLine`）**合并**进现有的 `~/.claude/settings.json`，不会丢掉这台机器上已有的其他设置（比如权限白名单）；
- 全程不会静默覆盖任何文件。

## 状态栏效果

单行纯文字（不用 emoji），事件驱动刷新（新消息 / 会话开始等触发，参考 [官方 statusLine 文档](https://code.claude.com/docs/en/statusline.md)）：

```
main | Sonnet 5 | ctx 34% | tok 95.9k | cost $1.23(est) | 5h 22% reset 3h19m | 7d 71% reset 2d4h
```

- **分支**：对当前工作目录跑 `git branch --show-current`，非 git 目录不显示。
- **Token / 上下文占比**：来自最近一次 API 响应的 `context_window` 字段。
- **花费**：`cost.total_cost_usd`，**是客户端估算值、不是真实账单**，且 `/clear` 后清零，不跨会话累计。
- **5 小时 / 7 天额度与重置倒计时**：`rate_limits` 字段，**只有 Claude.ai Pro/Max 订阅登录才会下发**；API Key / Console 按量计费不会有这块数据，脚本会自动隐藏，不报错。
- 占比 ≥90% 红色、≥70% 黄色、其余绿色。

脚本用标准库 `python3` 解析 stdin JSON，没有额外依赖（没用 `jq`，避免新机器上要先装东西）。

## 手动修改后如何同步

在任意一台机器上改了 `~/.claude/CLAUDE.md` 或 `~/.claude/settings.json`，想同步回仓库：

```bash
cp ~/.claude/CLAUDE.md ~/.claude/statusline.py ./
cp ~/.claude/settings.json ./settings.json   # 提交前检查一下有没有混入本机专属的敏感配置
git add -A && git commit -m "sync" && git push
```
