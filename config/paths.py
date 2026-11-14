# 系统路径配置
# 可通过环境变量覆盖

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 输出目录
OUTPUT_ROOT = os.environ.get(
    "SKILL_OUTPUT_ROOT",
    str(PROJECT_ROOT / "output")
)

# 工作目录（用于执行subprocess）
WORK_DIR = os.environ.get(
    "SKILL_WORK_DIR",
    str(PROJECT_ROOT)
)

# 临时文件目录
TEMP_DIR = os.environ.get(
    "SKILL_TEMP_DIR",
    "/tmp/skill-seeker"
)

# 深度蒸馏题目（替代上游默认的"更大"题目，见 prompts/deep_distill.md）
PROMPTS_DIR = PROJECT_ROOT / "prompts"
DEEP_DISTILL_PROMPT = PROMPTS_DIR / "deep_distill.md"
