"""
prompt_loader.py - 提示词加载器

支持热加载、变量插值、缓存管理
"""

import yaml
import os
from typing import Dict, Optional, Any
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class PromptLoader:
    """提示词加载器，支持热加载"""

    def __init__(self, prompts_dir: str = "config/prompts"):
        """
        初始化提示词加载器

        参数:
            prompts_dir: 提示词目录路径
        """
        self.prompts_dir = Path(prompts_dir)
        self.cache: Dict[str, dict] = {}
        self._load_all()
        logger.info(f"提示词加载器初始化完成，目录: {self.prompts_dir}")

    def _load_all(self):
        """加载所有提示词"""
        if not self.prompts_dir.exists():
            logger.warning(f"提示词目录不存在: {self.prompts_dir}")
            return

        for file_path in self.prompts_dir.glob("*.yaml"):
            name = file_path.stem  # 文件名（不含扩展名）
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.cache[name] = yaml.safe_load(f)
                logger.debug(f"加载提示词: {name}")
            except Exception as e:
                logger.error(f"加载提示词失败 {name}: {e}")

        logger.info(f"已加载 {len(self.cache)} 个提示词")

    def get_template(self, name: str) -> str:
        """
        获取提示词模板

        参数:
            name: 提示词名称

        返回:
            str: 模板字符串
        """
        if name not in self.cache:
            raise ValueError(f"提示词 '{name}' 不存在，可用: {list(self.cache.keys())}")

        return self.cache[name]['template']

    def get_temperature(self, name: str) -> float:
        """
        获取温度参数

        参数:
            name: 提示词名称

        返回:
            float: 温度值，默认0.7
        """
        if name not in self.cache:
            return 0.7

        return self.cache[name].get('temperature', 0.7)

    def get_version(self, name: str) -> str:
        """
        获取提示词版本

        参数:
            name: 提示词名称

        返回:
            str: 版本号
        """
        if name not in self.cache:
            return "unknown"

        return self.cache[name].get('version', '1.0')

    def render(self, name: str, **kwargs) -> str:
        """
        渲染提示词，变量插值

        参数:
            name: 提示词名称
            **kwargs: 模板变量

        返回:
            str: 渲染后的提示词
        """
        template = self.get_template(name)

        try:
            rendered = template.format(**kwargs)
            logger.debug(f"渲染提示词成功: {name}")
            return rendered
        except KeyError as e:
            logger.error(f"渲染提示词失败，缺少变量: {e}")
            raise ValueError(f"缺少必要变量 {e}，需要: {self._get_required_vars(template)}")
        except Exception as e:
            logger.error(f"渲染提示词失败: {e}")
            raise

    def _get_required_vars(self, template: str) -> list:
        """
        提取模板中需要的变量

        参数:
            template: 模板字符串

        返回:
            list: 变量名列表
        """
        import re
        # 匹配 {variable} 格式
        pattern = r'\{([^{}]+)\}'
        return re.findall(pattern, template)

    def reload(self):
        """热加载：重新加载所有提示词"""
        self.cache.clear()
        self._load_all()
        logger.info("提示词已热加载")

    def list_prompts(self) -> list:
        """
        列出所有可用的提示词

        返回:
            list: 提示词名称列表
        """
        return list(self.cache.keys())

    def get_info(self, name: str) -> dict:
        """
        获取提示词信息

        参数:
            name: 提示词名称

        返回:
            dict: 提示词信息
        """
        if name not in self.cache:
            return {}

        data = self.cache[name].copy()
        data['template_length'] = len(data.get('template', ''))
        return data

    def preview(self, name: str, max_length: int = 200) -> str:
        """
        预览提示词（截断）

        参数:
            name: 提示词名称
            max_length: 最大长度

        返回:
            str: 预览文本
        """
        template = self.get_template(name)
        if len(template) > max_length:
            return template[:max_length] + "..."
        return template


# 全局单例
prompt_loader = PromptLoader()


# 便捷函数
def get_prompt(name: str, **kwargs) -> str:
    """
    快速获取渲染后的提示词

    参数:
        name: 提示词名称
        **kwargs: 模板变量

    返回:
        str: 渲染后的提示词
    """
    return prompt_loader.render(name, **kwargs)