"""
knowledge_base.py - 知识库相关Pydantic模型

定义知识库API的请求/响应结构
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreateKnowledgeBaseRequest(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=1, max_length=200, description="知识库名称")
    description: Optional[str] = Field(default=None, max_length=500, description="知识库描述")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "技术文档库",
                "description": "存储技术相关文档"
            }
        }


class UpdateKnowledgeBaseRequest(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="知识库名称")
    description: Optional[str] = Field(default=None, max_length=500, description="知识库描述")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(default=None, description="知识库描述")
    document_count: int = Field(default=0, description="文档数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")


class KnowledgeBaseStatsResponse(BaseModel):
    """知识库统计响应"""
    id: int = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(default=None, description="知识库描述")
    document_count: int = Field(..., description="文档数量")
    total_size_mb: float = Field(..., description="总大小(MB)")
    created_at: datetime = Field(..., description="创建时间")