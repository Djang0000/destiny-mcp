# 🔮 destiny-mcp

**All-in-one Chinese metaphysics MCP server. One command, all the astrology.**

命理综合 MCP 服务器：`uvx destiny-mcp` 一键安装，即刻在 Claude Code 中使用八字排盘和黄历查询。

[![PyPI](https://img.shields.io/badge/pypi-destiny--mcp-blue)](https://pypi.org/project/destiny-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

| 工具 | 功能 | 说明 |
|------|------|------|
| `bazi_paipan` | 八字排盘 | 输入公历生日 → 四柱（年月日时）+ 日主 + 纳音 + 生肖 |
| `huangli` | 黄历查询 | 查看今日干支和生肖 |

> ⚠️ **定位**：轻量、离线、零配置。精确排盘（真太阳时、十神、大运）请搭配 [openfate-bazi MCP](https://github.com/openfate/bazi-mcp) 和 [mingai MCP](https://www.npmjs.com/package/@mingai/mcp) 使用。

## 🚀 Quick Start

```bash
# 1. Install and run (auto-downloads via uvx)
uvx destiny-mcp

# 2. Add to Claude Code .mcp.json
```
```json
{
  "mcpServers": {
    "destiny": {
      "command": "uvx",
      "args": ["destiny-mcp"]
    }
  }
}
```

Then restart Claude Code. Ask in natural language:
> 「帮我排一下 2001年1月13日10点50分的八字」
> 「今天黄历是什么」

## 🏗️ Recommended Full Astrology Stack

destiny-mcp 是命理 MCP 生态的「入口层」。搭配以下 MCP 获得完整能力：

```
uvx destiny-mcp        ← 八字快速排盘 + 黄历（当前项目）
npx @openfate/bazi-mcp  ← 真太阳时校正 + 合冲刑害 + 大运流年
npx @mingai/mcp         ← 紫微斗数 + 大六壬 + 奇门遁甲 + 塔罗
npx chinese-astrology-skill ← 秤骨算命
```

## 📦 Install from source

```bash
git clone https://github.com/Djang0000/destiny-mcp.git
cd destiny-mcp
pip install -e .
```

## 🤝 Sponsorship

如果这个项目对你有帮助，请考虑 [GitHub Sponsors](https://github.com/sponsors/Djang0000) 支持 🙏

## 📜 License

MIT © 2026 Djang0000
