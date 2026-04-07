"""
knowledge_base.py - 知识库表模型

存储知识库的基本信息
"""

from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.orm import relationship
from core.models.base import BaseModel


class KnowledgeBase(BaseModel):
    """知识库表"""

    __tablename__ = "knowledge_bases"

    name = Column(String(200), nullable=False, unique=True, index=True, comment="知识库名称")
    description = Column(Text, comment="知识库描述")
    document_count = Column(Integer, default=0, comment="文档数量")

    # 关系：一个知识库有多个文档
    # 使用字符串引用避免循环导入
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, name={self.name}, docs={self.document_count})>"