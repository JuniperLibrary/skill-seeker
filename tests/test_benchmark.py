"""benchmark_skill.py 的解析器与真实案例基准回归。

锁定三类真实 EVAL 排版的解析（独立反幻觉小节 / 单表内"未覆盖+拒绝"标注 /
"拒绝：/拒答："开头标注），以及时间串不误判为盲考成绩。
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from benchmark_skill import (  # noqa: E402
    _eval_question_counts,
    _parse_blind_score,
    benchmark,
)


class TestBlindScoreParsing:
    def test_grade_line_parsed(self):
        assert _parse_blind_score("**成绩：12/12（实答 10/10 + 拒答 2/2）**") == (12, 12)

    def test_shikao_line_parsed(self):
        assert _parse_blind_score("**实考成绩：12/12 通过；反幻觉 3/3 拒答成功。**") == (12, 12)

    def test_time_string_not_a_score(self):
        """08:30/12:00/17:30 不得被解析成 0/17 之类的假成绩。"""
        text = "| Q8 | 日报几点推送？ | 08:30/12:00/17:30，定时非按需 |\n最终 0/17 若干。"
        assert _parse_blind_score(text) is None

    def test_no_score_returns_none(self):
        assert _parse_blind_score("本题集共 12 题，判卷另附。") is None


class TestQuestionCounting:
    def test_bold_anti_section(self):
        """szse 式：题集表后跟粗体"反幻觉题"行，其后 Q 行全计反幻觉。"""
        text = (
            "| Q1 | 甲 | 乙 |\n"
            "| Q2 | 甲 | 乙 |\n"
            "**反幻觉题（正确答案是「承认未覆盖」）**\n"
            "| Q11 | 甲 | 未覆盖：以通知为准 |\n"
            "| Q12 | 甲 | 未覆盖：以文件为准 |\n"
        )
        assert _eval_question_counts(text) == (2, 2)

    def test_inline_marked_anti(self):
        """agent 式：单表内用"未覆盖+拒绝"标注反幻觉题。"""
        text = (
            "| Q1 | 甲 | 正常答案 |\n"
            "| Q11 | 甲 | **未覆盖**（C 类清单）明确拒绝 |\n"
            "| Q12 | 甲 | **未覆盖**，技能应只指出接口属于缺失维度 |\n"
        )
        assert _eval_question_counts(text) == (1, 2)

    def test_jujue_prefix_anti(self):
        """ai-main 式：答案列以"拒绝：/拒答："开头。"""
        text = (
            "| Q6 | 甲 | 拒绝：部署到模拟盘，全平台无实盘 |\n"
            "| Q11 | 甲 | 拒答：API 文档未覆盖 |\n"
            "| Q12 | 甲 | 拒答：算法未公开于白皮书 |\n"
        )
        assert _eval_question_counts(text) == (0, 3)

    def test_boundary_note_is_real_question(self):
        """答案里提到边界但主体是实答的题不计反幻觉（agent Q5）。"""
        text = "| Q5 | 支持股票期货吗 | 标的限债券/利率类，其余未覆盖 | 明确标 C 不编造 |\n"
        assert _eval_question_counts(text) == (1, 0)

    def test_section_header_resets_anti_mode(self):
        text = (
            "## 反幻觉题\n| Q1 | 甲 | 未覆盖 |\n## 另一节\n| Q2 | 甲 | 正常 |\n"
        )
        assert _eval_question_counts(text) == (1, 1)

    def test_grading_table_rows_not_counted(self):
        """判卷记录表（"| Q1 工坊路由 |…"）不是题集行，不重复计数。"""
        text = (
            "| Q1 | 甲 | 乙 |\n"
            "| Q1 工坊路由 | ✅ 引 R2 | ✅ | 对 |\n"
        )
        assert _eval_question_counts(text) == (1, 0)


# ── 真实案例基准回归（存在才跑） ────────────────────────────────────────

REAL_CASES = [
    PROJECT_ROOT / "output" / "bondseek-agent-skill",
    PROJECT_ROOT / "output" / "szse-bond-guide",
    Path.home() / ".opencode" / "skills" / "bondseek-ai-main",
    Path.home() / ".opencode" / "skills" / "szse-bond-guide",
]


class TestRealCaseBenchmarks:
    def test_real_cases_pass_benchmark(self):
        missing = [p for p in REAL_CASES if not p.exists()]
        cases = [p for p in REAL_CASES if p.exists()]
        if not cases:
            import pytest

            pytest.skip("无真实案例目录")
        for case in cases:
            result = benchmark(case)
            assert result["pass"], f"{case.name} 基准 {result['total']} < 80: {result}"
        assert not missing or True  # 缺失的目录静默跳过
