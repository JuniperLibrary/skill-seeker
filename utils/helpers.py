# 辅助函数

import os
import re


def sanitize_api_key(api_key: str, replacement: str = "*******脱敏*******") -> str:
    """脱敏API Key"""
    if not api_key:
        return ""
    return api_key[:4] + "****" + api_key[-4:] if len(api_key) > 8 else "******"


def mask_content(content: str, api_key: str = None, api_secret: str = None) -> str:
    """脱敏日志内容"""
    if not content:
        return ""

    masked = content
    if api_key:
        masked = masked.replace(api_key, "*******脱敏*******")
    if api_secret:
        masked = masked.replace(api_secret, "*******脱敏*******")

    return masked


def generate_skill_name(filename: str) -> str:
    """从文件名生成Skill名称（ASCII安全；非ASCII文件名不再塌缩为纯下划线）"""
    name = Path(filename).stem
    name = re.sub(r'[^a-zA-Z0-9_-]+', '-', name).strip('-_')
    if not name:
        # 全中文等无ASCII可保留时，用可读回退名而不是纯下划线
        from datetime import datetime
        name = "skill-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    return name[:64]


def format_command(cmd: list) -> str:
    """格式化命令为字符串"""
    return " ".join(cmd)


from pathlib import Path