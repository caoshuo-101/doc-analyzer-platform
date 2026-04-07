"""
conversation_service.py - 对话管理服务

管理对话历史、短期记忆、指代消解等功能
"""

from typing import List, Dict, Any, Optional
from core.repositories.base import BaseRepository
from core.models.conversation import Conversation
from utils.logger import get_logger

logger = get_logger(__name__)


class ConversationService:
    """对话管理服务"""

    def __init__(
        self,
        conversation_repo: BaseRepository,
        memory_size: int = 10
    ):
        """
        初始化对话服务

        参数:
            conversation_repo: 对话数据访问层
            memory_size: 短期记忆轮数（保留最近N轮对话）
        """
        self.conversation_repo = conversation_repo
        self.memory_size = memory_size
        self._session_cache: Dict[str, List[Dict]] = {}
        logger.info(f"对话服务初始化完成，记忆轮数: {memory_size}")

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        knowledge_base_id: Optional[int] = None,
        route_type: Optional[str] = None,
        model_used: Optional[str] = None,
        response_time_ms: Optional[int] = None
    ) -> Conversation:
        """
        添加消息到对话历史

        参数:
            session_id: 会话ID
            role: 角色（user/assistant）
            content: 消息内容
            knowledge_base_id: 知识库ID
            route_type: 路由类型
            model_used: 使用的模型
            response_time_ms: 响应时间（毫秒）

        返回:
            Conversation: 创建的对话记录
        """
        conversation = await self.conversation_repo.create(
            session_id=session_id,
            knowledge_base_id=knowledge_base_id or 0,
            role=role,
            content=content,
            route_type=route_type,
            model_used=model_used,
            response_time_ms=response_time_ms
        )

        # 更新缓存
        if session_id not in self._session_cache:
            self._session_cache[session_id] = []

        self._session_cache[session_id].append({
            "role": role,
            "content": content,
            "timestamp": conversation.created_at
        })

        # 限制缓存大小
        if len(self._session_cache[session_id]) > self.memory_size * 2:
            self._session_cache[session_id] = self._session_cache[session_id][-self.memory_size * 2:]

        logger.debug(f"消息已添加: session={session_id}, role={role}")
        return conversation

    async def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取对话历史

        参数:
            session_id: 会话ID
            limit: 返回数量限制

        返回:
            List[Dict]: 对话历史列表
        """
        # 优先从缓存读取
        if session_id in self._session_cache:
            history = self._session_cache[session_id]
            if limit:
                history = history[-limit:]
            return history

        # 从数据库读取
        # 简化实现：返回空列表
        logger.warning(f"会话缓存不存在: {session_id}")
        return []

    async def clear_memory(self, session_id: str):
        """
        清空记忆

        参数:
            session_id: 会话ID
        """
        if session_id in self._session_cache:
            self._session_cache[session_id] = []
            logger.info(f"会话记忆已清空: {session_id}")

    async def get_context_for_question(
        self,
        question: str,
        session_id: str,
        max_history: int = 5
    ) -> str:
        """
        获取上下文（支持追问）

        参数:
            question: 当前问题
            session_id: 会话ID
            max_history: 最大历史轮数

        返回:
            str: 格式化的上下文字符串
        """
        history = await self.get_history(session_id, limit=max_history * 2)

        if not history:
            return ""

        # 格式化历史对话
        context_parts = []
        for msg in history:
            role = "用户" if msg["role"] == "user" else "助手"
            context_parts.append(f"{role}: {msg['content']}")

        context = "\n".join(context_parts)
        logger.debug(f"生成上下文: session={session_id}, 历史轮数={len(history)//2}")
        return context

    async def resolve_reference(self, question: str, session_id: str) -> str:
        """
        解析指代（"它"、"那个"等）

        参数:
            question: 当前问题
            session_id: 会话ID

        返回:
            str: 解析后的完整问题
        """
        # 检查是否需要解析指代
        indicators = ["它", "这个", "那个", "这些", "那些", "上文", "刚才"]
        needs_resolution = any(indicator in question for indicator in indicators)

        if not needs_resolution:
            return question

        # 获取最近一次对话
        history = await self.get_history(session_id, limit=2)
        if not history:
            return question

        # 找到最近的用户问题
        last_user_question = None
        for msg in reversed(history):
            if msg["role"] == "user":
                last_user_question = msg["content"]
                break

        if last_user_question:
            # 简化实现：在问题前添加上下文
            resolved = f"参考之前的问题「{last_user_question}」，现在问：{question}"
            logger.debug(f"指代解析: {question} -> {resolved}")
            return resolved

        return question

    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话统计信息

        参数:
            session_id: 会话ID

        返回:
            Dict: 统计信息
        """
        history = await self.get_history(session_id)

        user_messages = [m for m in history if m["role"] == "user"]
        assistant_messages = [m for m in history if m["role"] == "assistant"]

        return {
            "session_id": session_id,
            "total_messages": len(history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "conversation_rounds": len(user_messages),
            "memory_size": self.memory_size
        }