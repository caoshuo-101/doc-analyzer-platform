"""
document.py - 文档相关Pydantic模型

定义文档API的请求/响应结构
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    file_name: str = Field(..., description="原始文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小(字节)")
    status: str = Field(..., description="处理状态")
    chunk_count: int = Field(default=0, description="分块数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    doc_id: int = Field(..., description="文档ID")
    status: str = Field(..., description="处理状态")
    chunk_count: int = Field(..., description="分块数量")
    message: str = Field(default="文档上传成功", description="提示消息")


class DocumentStatsResponse(BaseModel):
    """文档统计响应"""
    total: int = Field(..., description="总文档数")
    status: dict = Field(..., description="状态分布")
    total_size_bytes: int = Field(..., description="总大小(字节)")
    total_size_mb: float = Field(..., description="总大小(MB)")