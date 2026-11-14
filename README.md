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
| **🔬 深度蒸馏** | 深度题目对 skill 做二次蒸馏：开工契约（四问）→ 四阶段（盘点→建证→瘦身→自证）→ 机器门禁 8 项 ALL PASS 才算交付（见下文） |

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

## 🔬 深度蒸馏（deeper, not bigger）

上游 `skill-seekers` 默认题目的验证标准是"SKILL.md 应更大（200-1000+ 行）"，且 workflow
执行时拿不到文档内容，因此产出偏"搬运式结构"。深度蒸馏用 `prompts/deep_distill.md`
作为新题目，在文档已解析落盘后对 skill 目录做二次蒸馏。

### 开工契约（四问，写进题目开头，答不出必须显式写"缺"）

1. **顶尖专家会做什么** —— 审源料定切分策略、写蒸馏契约（能答什么/拒答什么）、结论挂证据锚、独立盲考、机器门禁不过不交付
2. **从哪些最原始素材入手** —— 原始文档字节、TOC 目录树、逐页 raw text、原始字段表与错误码全表、元数据、上游转换器的失败产物（反面证据）；禁止只吃二手整理稿
3. **用什么方法和工具** —— TOC 切分（PyMuPDF `get_toc`）、页锚 [P#] + grep 检索性测试、四阶段管线、≤120 行瘦身铁律、A/B/C 证据分级
4. **谁来证明结果正确** —— 机器门禁 `scripts/verify_skill.py`（8 项非人判定）、独立盲考官（禁读原文，≥10 实答题 + 2 反幻觉题）、溯源回查（每条规则可在切分文件 grep 命中）

### 四道铁律

1. **做深⊥做大**：只能替换与压缩，SKILL.md ≤120 行，每段要么是决策规则要么是证据指针
2. **证据锚定**：每条断言标注页锚 `[证据页 P#]`（或文件:行号），并区分 A=文档明说 / B=合理推断 / C=未覆盖（D=OCR 未核验）
3. **不许编造**：范围外问题一律答"未覆盖"，边界必须显式写出
4. **先备份**：改写前备份 SKILL.md.backup

四阶段：盘点原料（逐字素材/结论性文本/缺失维度）→ 精读建证（决策规则 R# + 证据锚）→
重写瘦身（SHRINK_LOG 记录删除项）→ 盲测自证（10 道盲测题 + 2 道反幻觉题 + 溯源核对 + 机器门禁）。

### 产出物

```
skill-name/
├── SKILL.md          # 重写后的调度层（≤120行）
├── SKILL.md.backup   # 原版备份
├── INVENTORY.md      # 原料分类与缺失维度（开头含四问作答）
├── SHRINK_LOG.md     # 删除了什么、为什么
├── EVAL.md           # 盲测题集 + 判卷记录 + 机器门禁结果
├── PROMPT.md         # 生成的深度题目（UI 深度蒸馏时）
└── references/rules.md  # 全部决策规则与逐条证据锚
```

### 机器门禁（第三方证明，非人判定）

```bash
python3 scripts/verify_skill.py output/<skill-name>
# 8 项检查：frontmatter 触发词 / name==目录名 / 无模板同义反复 / ≤120 行 /
# 无断链引用 / 规则带锚 / 页锚可回查 / 显式边界声明 → ALL PASS
```

### 使用方式

```python
# 方式1：仅生成深度题目，再自行用任意本地 agent 执行
from core.distiller import SkillDistiller
SkillDistiller(Path("output")).deep_enhance("skill-name")

# 方式2：无头执行（Claude Code）
SkillDistiller(Path("output")).deep_enhance(
    "skill-name",
    agent_cmd='claude -p --dangerously-skip-permissions "$(cat {prompt_file})"',
)
```

### Web UI（证据驱动）

- 顶部**契约区**：四问答案明示，UI 的"题目"与深度题目同源
- 新建页：上传 → 深度蒸馏 → **执行后自动跑机器门禁并逐项展示**，失败红字提示不带病交付
- 历史页：门禁复检按钮 + 四阶段产物（INVENTORY/SHRINK_LOG/EVAL/PROMPT）内嵌预览
- 侧栏不再有"AI 增强等级"滑杆——深度靠门禁与盲考，不靠等级

### 验证记录（三形态真实案例，独立盲考官判卷）

| 案例 | 形态 | 结果 |
|---|---|---|
| bondseek-agent-skill | 小架构 DOCX | 盲考 12/12、反幻觉 3/3、门禁 ALL PASS |
| bondseek-ai-main | 图片型白皮书 PDF（Vision OCR）| 盲考 12/12、门禁 ALL PASS |
| szse-bond-guide | 规则密集监管 PDF（112 页/65 条 TOC）| 盲考 12/12、溯源 6/6、门禁 8/8 |

上游根治病灶已同步送达：PR #482/#483/#484/#486/#489/#490/#491 + Issue #485（见 `docs/上游改进提案_蒸馏深度.md`）。

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
