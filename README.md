# Skill Seeker

文档一键蒸馏成 AI Skill 的 Web 工具

## 项目概述

这是一个 **Streamlit Web 应用**，用于将文档（PDF、DOCX、EPub）一键蒸馏成 AI Skill。

### 核心功能

| 功能 | 说明 |
|------|------|
| **多模型支持** | 支持 8+ AI 提供商：Anthropic Claude、OpenAI、Google Gemini、智谱AI、通义千问、豆包、DeepSeek、Moonshot AI、百度千帆 |
| **多平台输出** | 支持 OpenCode、Claude、Cursor、OpenAI、Gemini、Markdown、LangChain、Chroma 等格式 |
| **AI 增强** | 3 级增强（0-2），自动提取关键概念、生成结构化文档 |
| **OCR 支持** | 可识别扫描版/图片 PDF |

### 技术架构

- **前端**: Streamlit Web UI
- **核心处理**: 调用 `skill-seekers` CLI 工具执行文档蒸馏
- **输出**: 生成 SKILL.md + references/ + opencode.json 打包文件
- **架构**: 分层设计（配置层、核心层、工具层、UI层）

### 项目结构

```
skill-seeker/
├── skill_web.py           # 主入口（UI层）
├── config/                # 配置层
│   ├── models.py         # AI模型配置
│   └── settings.py       # 应用设置
├── core/                 # 核心层
│   ├── distiller.py      # 蒸馏处理
│   └── history.py        # 历史记录管理
├── ui/                   # UI组件
└── utils/                # 工具层
    ├── file_utils.py     # 文件处理
    └── helpers.py        # 辅助函数
```

### 代码分层

| 模块 | 职责 |
|------|------|
| `config/` | 配置层：AI模型提供商、API配置、应用常量 |
| `core/` | 核心层：蒸馏逻辑、历史记录管理 |
| `utils/` | 工具层：文件处理、日志脱敏等 |
| `skill_web.py` | UI层：Streamlit页面渲染 |

## Skill 完整目录结构

根据 OpenCode 官方文档，一个完整的 Skill 包含以下目录和文件：

```
skill-name/
├── SKILL.md                    # 【必须】核心技能定义文件
├── scripts/                    # 可执行脚本目录
│   └── *.py|.sh               # 辅助执行脚本
├── assets/                     # 静态资源目录
│   └── *.*                     # 图片、模板等资源文件
├── .claude/                    # Claude Code 兼容目录
│   └── skills/
│       └── {skill-name}/      # Claude兼容技能
│           └── SKILL.md
└── .agents/                    # Agent 兼容目录
    └── skills/
        └── {skill-name}/       # Agent兼容技能
            └── SKILL.md
```

### 目录说明

| 目录/文件 | 必选 | 说明 |
|-----------|------|------|
| `SKILL.md` | ✅ | 核心技能文件，必须包含 YAML frontmatter（name、description） |
| `scripts/` | ❌ | 可执行代码目录，AI 可调用执行 |
| `assets/` | ❌ | 静态资源目录，存放图片、模板等文件 |
| `.claude/` | ❌ | Claude Code 兼容性目录 |
| `.agents/` | ❌ | Agent 兼容性目录 |

### YAML Frontmatter 格式

```yaml
---
name: skill-name           # 【必须】必须与目录名完全一致
description: Brief description of what the skill does and when to use it.
version: "1.0"
license: MIT
compatibility: opencode   # 可选，兼容平台
---
```

### 语义环境说明

OpenCode 的语义环境目录包括：

| 目录 | 优先级 | 说明 |
|------|-------|------|
| `.opencode/skills/` | 项目级 | 项目本地技能，会覆盖全局 |
| `.claude/skills/` | 项目级 | Claude Code 兼容 |
| `.agents/skills/` | 项目级 | Agent 兼容 |
| `~/.config/opencode/skills/` | 全局 | XDG 配置目录 |
| `~/.claude/skills/` | 全局 | Claude 全局技能 |
| `~/.agents/skills/` | 全局 | Agent 全局技能 |

安装 Skill 时：
- 项目级：将 `{skill-name}/` 复制到 `.opencode/skills/` 下
- 全局级：复制到 `~/.config/opencode/skills/` 下

## 环境配置

### 1. 创建虚拟环境（推荐使用 uv）

```bash
# 安装 uv（如果没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install streamlit skill-seekers
```

or 使用 uv：

```bash
uv pip install streamlit skill-seekers
```

### 3. 运行

```bash
streamlit run skill_web.py
```

## 依赖说明

| 依赖 | 用途 |
|------|------|
| streamlit | Web UI框架 |
| skill-seekers | 文档蒸馏CLI工具 |
