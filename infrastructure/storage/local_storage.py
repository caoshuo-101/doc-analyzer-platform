"""
local_storage.py - 本地文件存储

提供文件的保存、读取、删除等基础操作
"""

import os
import shutil
from pathlib import Path
from typing import Optional
import aiofiles
from utils.logger import get_logger

logger = get_logger(__name__)


class LocalStorage:
    """本地文件存储"""

    def __init__(self, base_dir: str = "data/documents"):
        """
        初始化本地存储

        参数:
            base_dir: 基础存储目录
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"本地存储初始化完成，目录: {self.base_dir}")

    async def save_file(
        self,
        file_content: bytes,
        original_name: str,
        subdir: str = ""
    ) -> str:
        """
        保存文件

        参数:
            file_content: 文件内容
            original_name: 原始文件名
            subdir: 子目录（可选）

        返回:
            str: 保存的文件路径
        """
        # 生成唯一文件名
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_name = f"{timestamp}_{original_name}"

        # 构建完整路径
        if subdir:
            file_dir = self.base_dir / subdir
            file_dir.mkdir(parents=True, exist_ok=True)
            file_path = file_dir / unique_name
        else:
            file_path = self.base_dir / unique_name

        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)

        logger.info(f"文件保存成功: {file_path}")
        return str(file_path)

    async def read_file(self, file_path: str) -> str:
        """
        读取文件内容

        参数:
            file_path: 文件路径

        返回:
            str: 文件内容
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            content = await f.read()

        logger.debug(f"文件读取成功: {file_path}")
        return content

    async def delete_file(self, file_path: str) -> bool:
        """
        删除文件

        参数:
            file_path: 文件路径

        返回:
            bool: 是否删除成功
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"文件不存在，无法删除: {file_path}")
            return False

        path.unlink()
        logger.info(f"文件删除成功: {file_path}")
        return True

    async def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在

        参数:
            file_path: 文件路径

        返回:
            bool: 是否存在
        """
        return Path(file_path).exists()

    async def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小

        参数:
            file_path: 文件路径

        返回:
            int: 文件大小（字节）
        """
        path = Path(file_path)
        if not path.exists():
            return 0
        return path.stat().st_size