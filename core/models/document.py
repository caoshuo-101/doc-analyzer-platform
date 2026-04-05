"""
document.py - 文档表模型

存储文档的元数据信息
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from core.models.base import BaseModel


class Document(BaseModel):
    """文档表"""

    __tablename__ = "documents"

    title = Column(String(500), nullable=False, comment="文档标题")
    file_name = Column(String(500), nullable=False, comment="原始文件名")
    file_path = Column(String(1000), nullable=False, comment="文件存储路径")
    file_type = Column(String(50), comment="文件类型(pdf/docx/txt)")
    file_size = Column(Integer, comment="文件大小(字节)")

    # 文档状态: uploading, processing, completed, failed
    status = Column(String(20), default="processing", comment="处理状态")

    # 分块信息
    chunk_count = Column(Integer, default=0, comment="分块数量")

    # 外键
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, index=True)

    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title}, kb_id={self.knowledge_base_id})>"