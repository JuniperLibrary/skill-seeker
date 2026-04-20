# 文件处理工具

import tempfile
import shutil
from pathlib import Path
from typing import List


def save_uploaded_file(uploaded_file, temp_dir: str = None) -> Path:
    """保存上传的文件到临时目录"""
    if temp_dir is None:
        temp_dir = tempfile.gettempdir()

    temp_path = Path(temp_dir) / uploaded_file.name
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return temp_path


def get_file_size_mb(file_size: int) -> float:
    """获取文件大小（MB）"""
    return round(file_size / 1024 / 1024, 2)


def clean_directory(path: Path):
    """清理目录"""
    if path.exists() and path.is_dir():
        shutil.rmtree(path)


def ensure_directory(path: Path):
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)


def list_zip_files(directory: Path) -> List[Path]:
    """列出目录中的所有zip文件"""
    if not directory.exists():
        return []
    return list(directory.glob("*.zip"))