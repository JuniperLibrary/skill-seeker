#!/usr/bin/env python3
"""Skill 自动 Benchmark —— TODO"自动Benchmark"的全量化落地。

对任意 skill 目录给出可复跑的量化基准分（0-100），五个维度全部机器可判定，
不依赖人眼：

  维度                 权重   判定来源
  ─────────────────────────────────────────────────────────
  机器门禁              40    verify_skill.check 的 8 项，每项 5 分
  深度产物完备          15    INVENTORY / SHRINK_LOG / EVAL / SKILL.md.backup
  EVAL 题集规模         15    实答题 ≥10 且 反幻觉题 ≥2
  盲考成绩              20    EVAL.md 中解析 "x/y"，按比例给分
  溯源抽查记录          10    EVAL.md 溯源表 ≥3 行 ✅ 结论

用法:
    python3 scripts/benchmark_skill.py <skill_dir> [more_dirs...] [--json]

单目录 --json 输出机器可读结果；多目录输出对比总表。退出码：全部 ≥80 为 0，
否则 1（供 CI / UI 门禁复检调用）。
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify_skill import check  # noqa: E402

WEIGHTS = {"gates": 40, "artifacts": 15, "eval_size": 15, "blind_exam": 20, "trace": 10}
BENCHMARK_PASS = 80


def _parse_blind_score(eval_text: str) -> tuple[int, int] | None:
    """从 EVAL.md 解析盲考成绩 "x/y"。

    只在含"成绩"二字的行里找（"实考成绩：12/12""成绩：12/12（实答 10/10…"），
    避免把 "08:30/12:00/17:30" 这类时间串误判成分数。
    """
    for line in eval_text.splitlines():
        if "成绩" not in line:
            continue
        m = re.search(r"(\d+)\s*/\s*(\d+)", line)
        if m:
            x, y = int(m.group(1)), int(m.group(2))
            if y >= 5 and x <= y <= 50:
                return x, y
    return None


def _eval_question_counts(eval_text: str) -> tuple[int, int]:
    """统计 EVAL.md 中实答题与反幻觉题数量（按 Q 行计）。

    三种真实排版都能数对：
    - 独立小节/粗体行含"反幻觉"→ 其后的 Q 行全计反幻觉；
    - 单表内用"未覆盖+拒绝"标注的反幻觉题逐行识别；
    - 章节标题（#）重置反幻觉模式。
    """
    q_row = re.compile(r"^\|\s*\*?\*?q(\d+)\s*\|", re.I)
    real = anti = 0
    anti_mode = False
    for line in eval_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):  # 章节边界重置
            anti_mode = False
            continue
        if not stripped.startswith("|") and "反幻觉" in stripped:
            anti_mode = True
            continue
        m = q_row.match(stripped)
        if m:
            # 反幻觉题的三种标注：反幻觉小节内 / 答案列以"拒…/未覆盖"开头 /
            # 行内同时出现"未覆盖"与"拒"
            is_anti = (
                anti_mode
                or bool(re.search(r"\|\s*\*{0,2}(拒[绝答]|未覆盖)", stripped))
                or ("未覆盖" in stripped and "拒" in stripped)
            )
            if is_anti:
                anti += 1
            else:
                real += 1
    return real, anti


def _trace_rows(eval_text: str) -> int:
    """溯源抽查表中结论为 ✅ 的行数。"""
    return sum(
        1
        for ln in eval_text.splitlines()
        if ln.lstrip().startswith("|") and "✅" in ln
    )


def benchmark(skill_dir: Path) -> dict:
    """对单个 skill 目录打分，返回各维度明细与总分。"""
    skill_dir = Path(skill_dir).expanduser().resolve()
    result: dict = {"dir": str(skill_dir), "name": skill_dir.name, "total": 0}

    # 1. 机器门禁（每项 5 分）
    gate_results = check(skill_dir)
    passed = sum(1 for _, ok, _ in gate_results if ok)
    result["gates"] = {
        "score": passed * 5,
        "max": WEIGHTS["gates"],
        "passed": passed,
        "items": [
            {"name": name, "ok": ok, "detail": detail} for name, ok, detail in gate_results
        ],
    }

    # 2. 深度产物完备（每件 3.75 分）
    artifacts = {
        "INVENTORY.md": skill_dir / "INVENTORY.md",
        "SHRINK_LOG.md": skill_dir / "SHRINK_LOG.md",
        "EVAL.md": skill_dir / "EVAL.md",
        "SKILL.md.backup": skill_dir / "SKILL.md.backup",
    }
    present = [n for n, p in artifacts.items() if p.exists()]
    result["artifacts"] = {
        "score": round(len(present) * WEIGHTS["artifacts"] / 4, 2),
        "max": WEIGHTS["artifacts"],
        "present": present,
        "missing": [n for n in artifacts if n not in present],
    }

    eval_md = skill_dir / "EVAL.md"
    eval_text = eval_md.read_text(encoding="utf-8") if eval_md.exists() else ""

    # 3. EVAL 题集规模（实答 ≥10 得 10 分，反幻觉 ≥2 得 5 分，按比例）
    real, anti = _eval_question_counts(eval_text)
    size_score = min(1.0, real / 10) * 10 + min(1.0, anti / 2) * 5
    result["eval_size"] = {
        "score": round(size_score, 2),
        "max": WEIGHTS["eval_size"],
        "real_questions": real,
        "anti_hallucination_questions": anti,
    }

    # 4. 盲考成绩（解析 x/y，按比例）
    blind = _parse_blind_score(eval_text)
    if blind:
        x, y = blind
        ratio = x / y if y else 0.0
        result["blind_exam"] = {
            "score": round(ratio * WEIGHTS["blind_exam"], 2),
            "max": WEIGHTS["blind_exam"],
            "correct": x,
            "total": y,
        }
    else:
        result["blind_exam"] = {"score": 0, "max": WEIGHTS["blind_exam"], "note": "EVAL.md 未解析到盲考成绩"}

    # 5. 溯源抽查（≥3 行 ✅ 满分，按比例）
    trace = _trace_rows(eval_text)
    result["trace"] = {
        "score": round(min(1.0, trace / 3) * WEIGHTS["trace"], 2),
        "max": WEIGHTS["trace"],
        "confirmed_rows": trace,
    }

    result["total"] = round(
        sum(result[dim]["score"] for dim in WEIGHTS), 2
    )
    result["pass"] = result["total"] >= BENCHMARK_PASS
    return result


def _print_table(results: list[dict]) -> None:
    header = (
        f"{'skill':<24}{'门禁/8':>7}{'产物/15':>8}{'题集/15':>8}{'盲考/20':>8}{'溯源/10':>8}{'总分':>8}  判定"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        g = r["gates"]
        print(
            f"{r['name']:<24}"
            f"{g['passed']:>4}/{8}"
            f"{r['artifacts']['score']:>8.1f}"
            f"{r['eval_size']['score']:>8.1f}"
            f"{r['blind_exam']['score']:>8.1f}"
            f"{r['trace']['score']:>8.1f}"
            f"{r['total']:>8.1f}"
            f"  {'✅ PASS' if r['pass'] else '❌ BELOW %d' % BENCHMARK_PASS}"
        )
    for r in results:
        failed_gates = [i["name"] for i in r["gates"]["items"] if not i["ok"]]
        if failed_gates:
            print(f"  {r['name']} 门禁失败项: {', '.join(failed_gates)}")


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv
    if not args:
        print(__doc__)
        return 2
    results = [benchmark(Path(d)) for d in args]
    if as_json:
        print(json.dumps(results if len(results) > 1 else results[0], ensure_ascii=False, indent=2))
    else:
        _print_table(results)
    return 0 if all(r["pass"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
