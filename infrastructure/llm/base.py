"""
base.py - LLM抽象基类

定义所有LLM提供者必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from langchain_core.language_models import BaseLLM


class BaseLLMProvider(ABC):
    """LLM提供者抽象基类"""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化LLM提供者

        参数:
            model_name: 模型名称
            api_key: API密钥
            base_url: API基础URL
            timeout: 请求超时时间(秒)
        """
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    @abstractmethod
    def get_llm(self, temperature: float = 0.7) -> BaseLLM:
        """
        返回LangChain兼容的LLM实例

        参数:
            temperature: 温度参数，控制随机性

        返回:
            BaseLLM: LangChain LLM实例
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        生成回答

        参数:
            prompt: 提示词
            temperature: 温度参数
            max_tokens: 最大生成token数

        返回:
            str: 生成的回答
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        """
        流式生成回答

        参数:
            prompt: 提示词
            temperature: 温度参数
            max_tokens: 最大生成token数

        返回:
            AsyncIterator[str]: 流式输出的token
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        返回提供者名称

        返回:
            str: 提供者名称
        """
        pass

    def validate_config(self) -> bool:
        """
        验证配置是否有效

        返回:
            bool: 配置是否有效
        """
        if not self.api_key or self.api_key == "your_qwen_api_key_here":
            return False
        return True