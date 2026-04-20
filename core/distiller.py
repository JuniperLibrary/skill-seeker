# 蒸馏核心处理

import subprocess
import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional


class SkillDistiller:
    """Skill蒸馏器"""

    def __init__(self, output_root: Path, env_config: Dict = None):
        self.output_root = output_root
        self.env_config = env_config or {}
        from config.paths import WORK_DIR
        self.cwd = WORK_DIR

    def create_skill(
        self,
        input_file: Path,
        skill_name: str,
        preset: str = "standard",
        enhance_level: int = 2,
        use_ocr: bool = False,
        password: str = None,
    ) -> subprocess.CompletedProcess:
        """执行Skill蒸馏"""
        cmd = [
            "skill-seekers", "create",
            str(input_file),
            "--name", skill_name,
            "--preset", preset,
            "--enhance-level", str(enhance_level),
            "--output", str(self.output_root / skill_name)
        ]

        if use_ocr:
            cmd.append("--ocr")
        if password:
            cmd.extend(["--password", password])

        run_env = os.environ.copy()
        run_env.update(self.env_config)

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=self.cwd,
            env=run_env
        )

    def list_skills(self) -> List[Dict]:
        """列出所有已蒸馏的Skill"""
        if not self.output_root.exists():
            return []

        skills = []
        for item in self.output_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    skills.append({
                        "name": item.name,
                        "path": item,
                        "has_zip": any(f.suffix == '.zip' for f in item.iterdir())
                    })

        return sorted(skills, key=lambda x: x["path"].stat().st_mtime, reverse=True)

    def delete_skill(self, skill_name: str) -> bool:
        """删除Skill"""
        skill_path = self.output_root / skill_name
        if skill_path.exists():
            shutil.rmtree(skill_path)
            return True
        return False

    def package_for_platform(
        self,
        skill_name: str,
        platform: str = "opencode"
    ) -> Path:
        """为指定平台打包"""
        from pathlib import Path
        output_dir = self.output_root / skill_name

        if platform == "opencode":
            return self._package_opencode(output_dir, skill_name)
        else:
            return self._package_platform(output_dir, skill_name, platform)

    def _package_opencode(self, output_dir: Path, skill_name: str) -> Path:
        """打包OpenCode格式"""
        opencode_dir = output_dir / f"{skill_name}-opencode"
        opencode_zip = output_dir / f"{skill_name}-opencode.zip"
        opencode_skill_dir = opencode_dir / ".opencode" / "skills" / skill_name
        opencode_skill_dir.mkdir(parents=True, exist_ok=True)

        skill_md_path = output_dir / "SKILL.md"
        source_dir = output_dir / "source"

        if skill_md_path.exists():
            shutil.copy2(skill_md_path, opencode_skill_dir / "SKILL.md")
        if source_dir.exists():
            shutil.copytree(source_dir, opencode_skill_dir / "source", dirs_exist_ok=True)

        opencode_config = {
            "$schema": "https://opencode.ai/config.json",
            "skill": {
                "name": skill_name,
                "version": "1.0.0",
                "description": f"基于文档蒸馏生成的OpenCode Skill：{skill_name}"
            },
            "permission": {
                "skill": {
                    skill_name: "allow",
                    "*": "ask"
                }
            }
        }
        with open(opencode_dir / "opencode.json", "w", encoding="utf-8") as f:
            json.dump(opencode_config, f, indent=2, ensure_ascii=False)

        readme_content = f"""# {skill_name} - OpenCode Skill
## 安装使用方法
### 方法1：项目本地使用（推荐）
1. 将本压缩包所有内容解压到你的项目根目录
2. 确保解压后目录结构为：`你的项目/.opencode/skills/{skill_name}/SKILL.md`
3. 重启OpenCode，代理会自动发现并加载该Skill
### 方法2：全局安装使用
1. 解压压缩包，找到 `.opencode/skills/{skill_name}` 文件夹
2. 将该文件夹复制到全局配置目录
3. 重启OpenCode，该Skill会在所有项目中生效
"""
        with open(opencode_dir / "README_OpenCode.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

        shutil.make_archive(str(opencode_zip).replace(".zip", ""), "zip", opencode_dir)
        return opencode_zip

    def _package_platform(
        self,
        output_dir: Path,
        skill_name: str,
        platform: str
    ) -> Path:
        """打包通用平台格式"""
        platform_dir = output_dir / f"{skill_name}-{platform}"
        platform_zip = output_dir / f"{skill_name}-{platform}.zip"
        platform_dir.mkdir(parents=True, exist_ok=True)

        skill_md_path = output_dir / "SKILL.md"
        source_dir = output_dir / "source"

        if skill_md_path.exists():
            shutil.copy2(skill_md_path, platform_dir / "SKILL.md")
        if source_dir.exists():
            shutil.copytree(source_dir, platform_dir / "source", dirs_exist_ok=True)

        readme_content = f"""# {skill_name} - {platform} 平台Skill
## 核心文件说明
- SKILL.md：蒸馏后的核心知识
- source/：原始文档解析后的源文件
## 安装使用方法
请参考对应平台的使用教程
"""
        with open(platform_dir / f"README_{platform}.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

        shutil.make_archive(str(platform_zip).replace(".zip", ""), "zip", platform_dir)
        return platform_zip