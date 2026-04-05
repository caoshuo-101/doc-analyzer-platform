"""
qwen_provider.py - 通义千问LLM实现

封装DashScope API调用，兼容OpenAI接口
"""

from typing import AsyncIterator, Optional
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from infrastructure.llm.base import BaseLLMProvider
from utils.logger import get_logger

logger = get_logger(__name__)


class QwenProvider(BaseLLMProvider):
    """通义千问提供者"""

    def __init__(
        self,
        model_name: str = "qwen-plus",
        api_key: str = None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout: int = 30
    ):
        """
        初始化通义千问提供者

        参数:
            model_name: 模型名称 (qwen-turbo, qwen-plus, qwen-max)
            api_key: API密钥
            base_url: API基础URL
            timeout: 请求超时时间
        """
        super().__init__(model_name, api_key, base_url, timeout)
        self._async_client = None
        logger.info(f"通义千问提供者初始化完成，模型: {model_name}")

    def _get_async_client(self) -> AsyncOpenAI:
        """获取异步客户端"""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
        return self._async_client

    def get_llm(self, temperature: float = 0.7) -> ChatOpenAI:
        """返回LangChain兼容的LLM实例"""
        return ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=temperature,
            timeout=self.timeout,
            max_tokens=2000
        )

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
        if not self.validate_config():
            logger.error("通义千问API Key未配置")
            return "抱歉，通义千问服务未配置，请检查API Key设置。"

        try:
            client = self._get_async_client()

            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )

            result = response.choices[0].message.content
            logger.debug(f"通义千问生成成功，输入长度: {len(prompt)}, 输出长度: {len(result)}")
            return result

        except Exception as e:
            logger.error(f"通义千问生成失败: {e}")
            raise

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
        if not self.validate_config():
            logger.error("通义千问API Key未配置")
            yield "抱歉，通义千问服务未配置，请检查API Key设置。"
            return

        try:
            client = self._get_async_client()

            stream = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"通义千问流式生成失败: {e}")
            yield f"生成失败: {str(e)}"

    def get_provider_name(self) -> str:
        """返回提供者名称"""
        return "qwen"

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.api_key and self.api_key != "your_qwen_api_key_here")