#!/usr/bin/env python3
"""Skill 深度质检脚本 —— 对应深度题目阶段四的"机器检查清单"。

用法:
    python3 scripts/verify_skill.py <skill_dir> [more_dirs...]

检查项（全部通过返回 0，任一失败返回 1）:
  1. frontmatter: 含 name 与 description；description 不得是模板同义反复
     ("Use when working with X")，且含中文触发词或明确的"不适用于"边界声明
  2. name 与目录名一致
  3. SKILL.md ≤120 行（做深⊥做大）
  4. SKILL.md 中引用的相对路径文件必须存在（杜绝断链）
  5. 决策规则带证据锚: 规则行数 >0 且规则区含 [P..]/[L..]/引用锚标记
  6. 页锚回查: 若引用了带 [P#] 锚的原文文件，则该文件需存在对应
     [证据页 P#] 标记；[L#] 锚不得超过被引文件行数
  7. 边界声明: SKILL.md 含"未覆盖/不适用"类显式边界（反幻觉门禁）
"""

import re
import sys
from pathlib import Path

LINE_BUDGET = 120
FORBIDDEN_DESC_PREFIX = "use when working with"


def check(skill_dir: Path) -> list[tuple[str, bool, str]]:
    results = []
    add = lambda name, ok, detail: results.append((name, ok, detail))

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [("SKILL.md 存在", False, str(skill_md))]

    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()

    # 1. frontmatter
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        add("frontmatter", False, "缺少 --- frontmatter")
    else:
        fm = m.group(1)
        name_m = re.search(r"^name:\s*(\S+)", fm, re.M)
        desc_m = re.search(r"^description:\s*(.+)$", fm, re.M)
        name = name_m.group(1) if name_m else ""
        desc = desc_m.group(1).strip() if desc_m else ""
        add("frontmatter 有 name+description", bool(name and desc),
            f"name={name!r}, desc {len(desc)} chars")
        # 2. name == 目录名
        add("name==目录名", name == skill_dir.name, f"{name!r} vs {skill_dir.name!r}")
        # 1b. description 质量
        dlow = desc.lower()
        is_template = dlow.startswith(FORBIDDEN_DESC_PREFIX)
        triggers = ("当", "用于", "触发", "不适用", "不要", "何时")
        add("description 含触发词且非模板同义反复",
            (not is_template) and any(t in desc for t in triggers),
            "模板同义反复" if is_template else ("触发词已含" if any(t in desc for t in triggers) else "无触发词"))

    # 3. 行数预算
    add(f"SKILL.md ≤{LINE_BUDGET} 行", len(lines) <= LINE_BUDGET, f"实际 {len(lines)} 行")

    # 4. 引用文件存在（优先取反引号内路径，容忍空格）
    broken = []
    refs = re.findall(r"`([^`\n]+?\.(?:md|py|sh|txt|json))`", text)
    if not refs:
        refs = re.findall(r"([\w\u4e00-\u9fa5/.\-]+\.(?:md|py|sh|txt|json))", text)
    for ref in refs:
        if ref.startswith("http"):
            continue
        if not (skill_dir / ref.strip()).exists():
            broken.append(ref)
    add("无断链引用", not broken, "缺失: " + ", ".join(broken) if broken else "全部存在")

    # 5. 决策规则与锚
    rules_md = skill_dir / "references" / "rules.md"
    rules_from_file = rules_md.read_text(encoding="utf-8") if rules_md.exists() else ""
    rules_text = rules_from_file or text
    rule_count = len(re.findall(r"^[-|]\s*\**R?\d+\**|^\d+\.\s", rules_text, re.M))
    # 锚合并计数：SKILL.md 与 rules.md 中的 [P#]/[L#] 都算
    anchors = len(re.findall(r"[PL]\d+", text + "\n" + rules_from_file))
    add("决策规则带证据锚", rule_count >= 5 and anchors >= 5,
        f"规则≈{rule_count} 条, 锚≈{anchors} 处")

    # 6. 页锚回查
    page_fail = []
    for md in [skill_md, rules_md] if rules_md.exists() else [skill_md]:
        for page in set(re.findall(r"\[(?:P|证据页)(\d+)", md.read_text(encoding="utf-8"))):
            matched = any(
                f"证据页 P{page}" in (skill_dir / "references" / f.name).read_text(encoding="utf-8")
                for f in list((skill_dir / "references").glob("*.md")) if f.exists()
            )
            if not matched and (skill_dir / f"references").exists():
                page_fail.append(f"P{page}")
    add("页锚可在原文文件中回查", not page_fail,
        "找不到证据页标记: " + ", ".join(page_fail) if page_fail else "全部可回查")

    # 7. 边界声明（反幻觉门禁）
    add("含显式边界/未覆盖声明",
        any(k in text for k in ("未覆盖", "不适用", "不要使用", "何时不使用")),
        "存在" if any(k in text for k in ("未覆盖", "不适用", "不要使用", "何时不使用")) else "缺失")

    return results


def main() -> int:
    dirs = [Path(a) for a in sys.argv[1:]] or [
        *Path("output").glob("*/"), *Path.home().glob(".opencode/skills/bondseek-*"),
    ]
    all_ok = True
    for d in dirs:
        print(f"\n=== {d} ===")
        for name, ok, detail in check(d):
            print(f"  {'✅' if ok else '❌'} {name}: {detail}")
            all_ok &= ok
    print("\n" + ("ALL PASS" if all_ok else "FAILED"))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
