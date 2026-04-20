# 历史记录管理

import shutil
from pathlib import Path
from typing import List, Dict, Optional


def get_history_skills(output_root: Path) -> List[Dict]:
    """获取历史记录列表"""
    if not output_root.exists():
        return []

    skills = []
    for item in output_root.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                skills.append({
                    "name": item.name,
                    "path": item,
                    "has_zip": any(f.suffix == '.zip' for f in item.iterdir())
                })

    return sorted(skills, key=lambda x: x["path"].stat().st_mtime, reverse=True)


def read_skill_content(skill_path: Path, filename: str = "SKILL.md") -> str:
    """读取Skill文件内容"""
    file_path = skill_path / filename
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return ""


def delete_skill(skill_path: Path) -> bool:
    """删除Skill"""
    if skill_path.exists():
        shutil.rmtree(skill_path)
        return True
    return False