"""
logger.py - 日志配置模块

提供统一的日志记录功能
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    level: str = "INFO",
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    设置并返回logger实例

    参数:
        name: logger名称，默认为root logger
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        format_string: 自定义日志格式

    返回:
        logging.Logger: 配置好的logger实例
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # 设置格式
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(console_handler)

    return logger


# 创建默认logger实例
default_logger = setup_logger("doc-analyzer")

# 为常用模块创建logger
def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的logger

    参数:
        name: logger名称，通常使用 __name__

    返回:
        logging.Logger: logger实例
    """
    return logging.getLogger(name)