"""深度蒸馏链路回归测试。

覆盖：
- utils.helpers.generate_skill_name（非 ASCII 文件名不再塌缩为纯下划线）
- scripts.verify_skill（正例全过 + 逐个反例必须被拦）
- core.distiller.SkillDistiller.deep_enhance 题目物化与占位符替换
- 真实产出目录的页锚回归（可回查证据页标记）

运行： python3 -m pytest tests/ -q
"""

import sys
import textwrap
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.helpers import generate_skill_name  # noqa: E402
from scripts.verify_skill import check, LINE_BUDGET  # noqa: E402
from config.paths import DEEP_DISTILL_PROMPT  # noqa: E402
from core.distiller import SkillDistiller  # noqa: E402


# ── generate_skill_name ────────────────────────────────────────────────

def test_name_ascii_preserved():
    assert generate_skill_name("react-tutorial.pdf") == "react-tutorial"


def test_name_full_chinese_does_not_collapse_to_underscores():
    name = generate_skill_name("基于大模型的AI Agent量化交易辅助系统架构文档.pdf")
    assert name
    assert set(name) - {"-", "_"}  # 不允许只剩分隔符
    assert "---" not in name and "___" not in name
    assert not set(name) <= set("_")


def test_name_length_truncated_to_64():
    name = generate_skill_name("x" * 200 + ".pdf")
    assert len(name) <= 64


# ── fixtures：合成 skill 目录 ───────────────────────────────────────────

DEEP_SKILL_MD = textwrap.dedent("""\
    ---
    name: my-skill
    description: 深测用技能。当涉及 X 架构问题时使用；不适用于实现层细节。
    ---

    # my-skill

    ## 核心决策规则（详见 references/rules.md）

    | # | 规则 | 标记 |
    |---|------|------|
    | R1 | 条件一 → 动作一 [证据: 白皮书.md P2] | A |
    | R2 | 条件二 → 动作二 [证据: 白皮书.md P3] | A |
    | R3 | 条件三 → 动作三 [证据: 白皮书.md P3] | B |
    | R4 | 条件四 → 动作四（原文未给出失败处理，未覆盖） | C |
    | R5 | 条件五 → 动作五 [证据: 白皮书.md P4] | A |

    ## 边界与未覆盖

    API 契约、表结构等未覆盖。

    ## 深料指引

    - `references/rules.md` — 规则与锚
    - `INVENTORY.md` — 原料盘点
    """)

RULES_MD = textwrap.dedent("""\
    # 规则

    - R1：a → b [证据: 白皮书.md, P2]
    - R2：c → d [证据: 白皮书.md, P3]
    - R3：e → f（推断）[证据: 白皮书.md P3]
    - R4：g → h，失败处理未给出 [证据: 白皮书.md, P4]
    - R5：i → j [证据: 白皮书.md, P4]
    - 不要做：不要假设 k（未覆盖）
    """)

WHITEPAPER = "--- [证据页 P2] ---\n内容A\n\n--- [证据页 P3] ---\n内容B\n\n--- [证据页 P4] ---\n内容C\n"


@pytest.fixture
def deep_skill(tmp_path):
    d = tmp_path / "my-skill"
    (d / "references").mkdir(parents=True)
    (d / "SKILL.md").write_text(DEEP_SKILL_MD, encoding="utf-8")
    (d / "references" / "rules.md").write_text(RULES_MD, encoding="utf-8")
    (d / "references" / "白皮书.md").write_text(WHITEPAPER, encoding="utf-8")
    (d / "INVENTORY.md").write_text("# INVENTORY\n- 逐字素材 [P2]\n", encoding="utf-8")
    return d


def test_deep_skill_passes_all_gates(deep_skill):
    failed = [f"{n}: {detail}" for n, ok, detail in check(deep_skill) if not ok]
    assert not failed, f"反例门禁未通过: {failed}"


# ── 反例：每个坏点都必须被对应门禁拦下 ─────────────────────────────────

BAD_BODIES = {
    "模板同义反复描述": """\
        ---
        name: my-skill
        description: Use when working with my-skill
        ---

        # boilerplate
        - R1/R2/R3/R4/R5 规则占位
        引用 [P2] [P3] [P4] [P5] 锚占位，未覆盖与不适用占位
        深料指引 references/rules.md 与 INVENTORY.md 存在
        """,
    "name与目录不一致": textwrap.dedent("""\
        ---
        name: other-name
        description: 测试。当涉及 X 时使用；不适用 Y。
        ---

        引用 [P2] [P3] 锚，含未覆盖声明。
        指向 references/rules.md INVENTORY.md
        """),
}


@pytest.mark.parametrize("bad_case", BAD_BODIES)
def test_bad_skill_rejected(deep_skill, bad_case):
    bad = deep_skill.parent / f"my-skill-{bad_case.replace('/', '-')}"
    bad.mkdir()
    for p in deep_skill.rglob("*"):
        if p.is_file():
            (bad / p.relative_to(deep_skill)).parent.mkdir(parents=True, exist_ok=True)
            (bad / p.relative_to(deep_skill)).write_bytes(p.read_bytes())
    (bad / "SKILL.md").write_text(textwrap.dedent(BAD_BODIES[bad_case]), encoding="utf-8")

    names_ok = {name for name, ok, _ in check(bad) if ok}
    gate = {"模板同义反复描述": "description 含触发词且非模板同义反复",
            "name与目录不一致": "name==目录名"}[bad_case]
    assert gate not in names_ok, f"{gate} 未能拦下反例 {bad_case}"


def test_line_budget_is_enforced():
    assert LINE_BUDGET == 120


def test_missing_referenced_file_fails(deep_skill):
    md = deep_skill / "SKILL.md"
    md.write_text(md.read_text(encoding="utf-8").replace(
        "`references/rules.md`", "`references/nope.md`"), encoding="utf-8")
    names_ok = {name for name, ok, _ in check(deep_skill) if ok}
    assert "无断链引用" not in names_ok


# ── distiller.deep_enhance：题目物化 ───────────────────────────────────

def test_deep_enhance_materializes_prompt(tmp_path, monkeypatch, capsys):
    skill_name = "demo-skill"
    d = tmp_path / skill_name
    (d / "references").mkdir(parents=True)
    (d / "SKILL.md").write_text(DEEP_SKILL_MD, encoding="utf-8")
    (d / "references" / "rules.md").write_text(RULES_MD, encoding="utf-8")

    distiller = SkillDistiller(tmp_path)
    prompt_file = distiller.deep_enhance(skill_name, agent_cmd=None)

    assert prompt_file is not None and prompt_file.exists()
    text = prompt_file.read_text(encoding="utf-8")
    assert "{skill_dir}" not in text and "{source_files}" not in text
    assert skill_name in text and "references/rules.md" in text


def test_prompt_carries_four_question_contract():
    """开工契约：四问必须显式存在于深度题目，防止将来退化成'更大'。"""
    prompt_text = DEEP_DISTILL_PROMPT.read_text(encoding="utf-8")
    for marker in (
        "开工契约",
        "顶尖专家",
        "最原始素材",
        "方法和工具",
        "谁证明结果正确",
    ):
        assert marker in prompt_text, f"深度题目缺少契约要素：{marker}"


# ── 真实产出目录回归（存在才跑） ────────────────────────────────────────

REAL_SKILL = PROJECT_ROOT / "output" / "bondseek-agent-skill"
REAL_SKILL_MAIN = Path.home() / ".opencode" / "skills" / "bondseek-ai-main"
REAL_SKILL_SZSE = PROJECT_ROOT / "output" / "szse-bond-guide"
REAL_SKILL_SZSE_INSTALLED = Path.home() / ".opencode" / "skills" / "szse-bond-guide"


@pytest.mark.skipif(not REAL_SKILL.exists(), reason="真实产出目录不存在")
def test_real_agent_skill_gates():
    failed = [n for n, ok, _ in check(REAL_SKILL) if not ok]
    assert not failed


@pytest.mark.skipif(not REAL_SKILL_MAIN.exists(), reason="真实安装目录不存在")
def test_real_main_skill_gates():
    failed = [n for n, ok, _ in check(REAL_SKILL_MAIN) if not ok]
    assert not failed


@pytest.mark.skipif(
    not REAL_SKILL_SZSE.exists() and not REAL_SKILL_SZSE_INSTALLED.exists(),
    reason="szse-bond-guide 真实目录不存在",
)
def test_real_szse_skill_gates():
    """第三形态真实案例（112页规则密集监管PDF）：产出目录或官方安装副本任一存在即校验。"""
    target = REAL_SKILL_SZSE if REAL_SKILL_SZSE.exists() else REAL_SKILL_SZSE_INSTALLED
    failed = [n for n, ok, _ in check(target) if not ok]
    assert not failed
