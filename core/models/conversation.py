"""
conversation.py - 对话表模型

存储对话历史和会话信息
"""

from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.sql import func
from core.models.base import BaseModel


class Conversation(BaseModel):
    """对话表"""

    __tablename__ = "conversations"

    session_id = Column(String(100), nullable=False, index=True, comment="会话ID")
    knowledge_base_id = Column(Integer, nullable=False, index=True, comment="知识库ID")

    # 角色: user, assistant
    role = Column(String(20), nullable=False, comment="角色")
    content = Column(Text, nullable=False, comment="消息内容")

    # 路由信息
    route_type = Column(String(50), comment="路由类型")

    # 使用的模型
    model_used = Column(String(100), comment="使用的模型")

    # 性能指标
    response_time_ms = Column(Integer, comment="响应时间(毫秒)")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, session={self.session_id}, role={self.role})>"