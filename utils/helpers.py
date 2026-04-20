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
    """从文件名生成Skill名称"""
    name = Path(filename).stem
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return name


def format_command(cmd: list) -> str:
    """格式化命令为字符串"""
    return " ".join(cmd)


from pathlib import Path