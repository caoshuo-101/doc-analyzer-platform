"""
chat.py - 聊天相关Pydantic模型

定义聊天API的请求/响应结构
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class ChatRequest(BaseModel):
    """聊天请求"""
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    knowledge_base_id: int = Field(..., ge=1, description="知识库ID")
    session_id: Optional[str] = Field(default=None, description="会话ID，不传则自动生成")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "文档里说了什么？",
                "knowledge_base_id": 1,
                "session_id": "session_001"
            }
        }
    )


class ChatResponse(BaseModel):
    """聊天响应"""
    model_config = ConfigDict(protected_namespaces=())  # 禁用protected namespace检查

    answer: str = Field(..., description="回答内容")
    route: str = Field(..., description="路由类型")
    session_id: str = Field(..., description="会话ID")
    model_used: Optional[str] = Field(default=None, description="使用的模型")
    response_time_ms: Optional[int] = Field(default=None, description="响应时间(毫秒)")


class ConversationMessage(BaseModel):
    """对话消息"""
    role: str = Field(..., description="角色(user/assistant)")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(..., description="时间戳")


class ConversationHistoryResponse(BaseModel):
    """对话历史响应"""
    session_id: str = Field(..., description="会话ID")
    messages: List[ConversationMessage] = Field(..., description="消息列表")
    total_messages: int = Field(..., description="总消息数")
    conversation_rounds: int = Field(..., description="对话轮数")


class RouteExplainResponse(BaseModel):
    """路由解释响应"""
    route: str = Field(..., description="路由类型")
    reason: str = Field(..., description="决策原因")
    matched_keyword: Optional[str] = Field(default=None, description="匹配的关键词")
    priority: Optional[int] = Field(default=None, description="优先级")