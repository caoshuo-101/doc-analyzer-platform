"""
gateway.py - 模型网关

负责负载均衡、重试、故障切换
"""

import asyncio
import logging
from typing import List, Optional, AsyncIterator
from infrastructure.llm.base import BaseLLMProvider
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelGateway:
    """模型网关：负责负载均衡、重试、故障切换"""

    def __init__(
        self,
        primary: BaseLLMProvider,
        backups: List[BaseLLMProvider] = None,
        retry_times: int = 3,
        retry_backoff: float = 1.0,
        enable_fallback: bool = True
    ):
        """
        初始化模型网关

        参数:
            primary: 主模型提供者
            backups: 备用模型提供者列表
            retry_times: 每个模型的重试次数
            retry_backoff: 重试退避时间(秒)
            enable_fallback: 是否启用故障切换
        """
        self.primary = primary
        self.backups = backups or []
        self.retry_times = retry_times
        self.retry_backoff = retry_backoff
        self.enable_fallback = enable_fallback
        self.current_provider = primary
        self.call_history = []  # 记录调用历史

        logger.info(
            f"模型网关初始化完成，主模型: {primary.get_provider_name()}, "
            f"备用模型数: {len(self.backups)}, 重试次数: {retry_times}"
        )

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        scene: str = "general",
        max_tokens: int = 2000
    ) -> str:
        """
        生成回答，失败自动切换

        参数:
            prompt: 提示词
            temperature: 温度参数
            scene: 场景名称（用于日志）
            max_tokens: 最大生成token数

        返回:
            str: 生成的回答
        """
        providers = [self.primary] + self.backups if self.enable_fallback else [self.primary]

        for provider_idx, provider in enumerate(providers):
            provider_name = provider.get_provider_name()

            for attempt in range(self.retry_times):
                try:
                    logger.info(
                        f"调用模型 [{provider_name}]，场景: {scene}, "
                        f"尝试: {attempt + 1}/{self.retry_times}"
                    )

                    result = await provider.generate(prompt, temperature, max_tokens)

                    # 记录成功调用
                    self._record_call(provider_name, scene, True, attempt + 1)
                    self.current_provider = provider

                    logger.info(f"模型调用成功 [{provider_name}]")
                    return result

                except Exception as e:
                    logger.warning(
                        f"模型调用失败 [{provider_name}]，尝试 {attempt + 1}: {str(e)}"
                    )

                    if attempt < self.retry_times - 1:
                        # 等待后重试
                        await asyncio.sleep(self.retry_backoff * (attempt + 1))
                    else:
                        # 记录失败
                        self._record_call(provider_name, scene, False, self.retry_times)
                        logger.error(f"模型 [{provider_name}] 所有重试均失败")

        # 所有模型都失败
        error_msg = "所有模型均调用失败，请稍后再试"
        logger.error(error_msg)
        return f"抱歉，{error_msg}。"

    async def stream_generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        scene: str = "general",
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        """
        流式生成，失败自动切换

        参数:
            prompt: 提示词
            temperature: 温度参数
            scene: 场景名称
            max_tokens: 最大生成token数

        返回:
            AsyncIterator[str]: 流式输出
        """
        providers = [self.primary] + self.backups if self.enable_fallback else [self.primary]

        for provider in providers:
            provider_name = provider.get_provider_name()

            try:
                logger.info(f"流式调用模型 [{provider_name}]，场景: {scene}")

                async for chunk in provider.stream_generate(prompt, temperature, max_tokens):
                    yield chunk

                # 记录成功
                self._record_call(provider_name, scene, True, 1)
                self.current_provider = provider
                return

            except Exception as e:
                logger.warning(f"流式调用失败 [{provider_name}]: {str(e)}")
                self._record_call(provider_name, scene, False, 1)
                continue

        # 所有模型都失败
        yield "抱歉，服务暂时不可用，请稍后再试。"

    def _record_call(self, provider: str, scene: str, success: bool, attempts: int):
        """
        记录调用历史

        参数:
            provider: 提供者名称
            scene: 场景名称
            success: 是否成功
            attempts: 尝试次数
        """
        self.call_history.append({
            "provider": provider,
            "scene": scene,
            "success": success,
            "attempts": attempts,
            "timestamp": None  # 可添加时间戳
        })

        # 保持历史记录在100条以内
        if len(self.call_history) > 100:
            self.call_history.pop(0)

    def get_current_provider(self) -> str:
        """获取当前使用的模型"""
        return self.current_provider.get_provider_name()

    def get_stats(self) -> dict:
        """
        获取网关统计信息

        返回:
            dict: 统计信息
        """
        total_calls = len(self.call_history)
        if total_calls == 0:
            return {
                "total_calls": 0,
                "success_rate": 0,
                "current_provider": self.get_current_provider(),
                "providers": {
                    "primary": self.primary.get_provider_name(),
                    "backups": [p.get_provider_name() for p in self.backups]
                }
            }

        success_calls = sum(1 for c in self.call_history if c["success"])

        return {
            "total_calls": total_calls,
            "success_rate": success_calls / total_calls,
            "current_provider": self.get_current_provider(),
            "providers": {
                "primary": self.primary.get_provider_name(),
                "backups": [p.get_provider_name() for p in self.backups]
            },
            "recent_calls": self.call_history[-5:]  # 最近5次调用
        }

    def switch_to_backup(self, backup_index: int = 0):
        """
        手动切换到备用模型

        参数:
            backup_index: 备用模型索引
        """
        if 0 <= backup_index < len(self.backups):
            self.current_provider = self.backups[backup_index]
            logger.info(f"手动切换到备用模型: {self.current_provider.get_provider_name()}")
        else:
            logger.warning(f"备用模型索引 {backup_index} 无效")

    def reset_to_primary(self):
        """重置回主模型"""
        self.current_provider = self.primary
        logger.info("已重置回主模型")