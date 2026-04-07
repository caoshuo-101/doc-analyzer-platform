"""
knowledge_bases.py - 知识库API路由

提供知识库的CRUD操作接口
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.connection import get_db
from core.repositories.knowledge_base_repo import KnowledgeBaseRepository
from api.schemas.common import ResponseModel, PaginationParams, PaginationResponse
from api.schemas.knowledge_base import (
    CreateKnowledgeBaseRequest,
    UpdateKnowledgeBaseRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseStatsResponse
)
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/knowledge-bases", tags=["知识库管理"])


@router.post("", response_model=ResponseModel)
async def create_knowledge_base(
    request: CreateKnowledgeBaseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建知识库

    - **name**: 知识库名称（唯一）
    - **description**: 知识库描述（可选）
    """
    repo = KnowledgeBaseRepository(db)

    # 检查名称是否已存在
    existing = await repo.get_by_name(request.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"知识库名称已存在: {request.name}"
        )

    # 创建知识库
    kb = await repo.create(
        name=request.name,
        description=request.description
    )

    await db.commit()

    return ResponseModel(
        code=200,
        message="知识库创建成功",
        data=KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=kb.document_count,
            created_at=kb.created_at,
            updated_at=kb.updated_at
        ).model_dump()
    )


@router.get("", response_model=ResponseModel)
async def list_knowledge_bases(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    获取知识库列表（分页）
    """
    repo = KnowledgeBaseRepository(db)

    # 获取分页数据
    result = await repo.paginate(
        page=pagination.page,
        per_page=pagination.page_size,
        order_by="created_at",
        descending=True
    )

    items = [
        KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=kb.document_count,
            created_at=kb.created_at,
            updated_at=kb.updated_at
        )
        for kb in result["items"]
    ]

    return ResponseModel(
        code=200,
        message="success",
        data=PaginationResponse(
            items=[item.model_dump() for item in items],
            total=result["total"],
            page=result["page"],
            page_size=result["per_page"],
            pages=result["pages"]
        ).model_dump()
    )


@router.get("/{kb_id}", response_model=ResponseModel)
async def get_knowledge_base(
    kb_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取知识库详情
    """
    repo = KnowledgeBaseRepository(db)
    kb = await repo.get_by_id(kb_id)

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"知识库不存在: {kb_id}"
        )

    return ResponseModel(
        code=200,
        message="success",
        data=KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=kb.document_count,
            created_at=kb.created_at,
            updated_at=kb.updated_at
        ).model_dump()
    )


@router.put("/{kb_id}", response_model=ResponseModel)
async def update_knowledge_base(
    kb_id: int,
    request: UpdateKnowledgeBaseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    更新知识库信息
    """
    repo = KnowledgeBaseRepository(db)

    # 检查知识库是否存在
    kb = await repo.get_by_id(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"知识库不存在: {kb_id}"
        )

    # 更新字段
    update_data = request.model_dump(exclude_unset=True)
    if update_data:
        for key, value in update_data.items():
            setattr(kb, key, value)
        await db.flush()
        await db.refresh(kb)

    await db.commit()

    return ResponseModel(
        code=200,
        message="知识库更新成功",
        data=KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=kb.document_count,
            created_at=kb.created_at,
            updated_at=kb.updated_at
        ).model_dump()
    )


@router.delete("/{kb_id}", response_model=ResponseModel)
async def delete_knowledge_base(
    kb_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除知识库（会同时删除所有关联文档）
    """
    repo = KnowledgeBaseRepository(db)

    # 检查知识库是否存在
    kb = await repo.get_by_id(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"知识库不存在: {kb_id}"
        )

    # 删除知识库（级联删除文档）
    await repo.delete_by_id(kb_id)
    await db.commit()

    return ResponseModel(
        code=200,
        message="知识库删除成功"
    )


@router.get("/{kb_id}/stats", response_model=ResponseModel)
async def get_knowledge_base_stats(
    kb_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取知识库统计信息
    """
    from core.repositories.document_repo import DocumentRepository

    kb_repo = KnowledgeBaseRepository(db)
    doc_repo = DocumentRepository(db)

    # 检查知识库是否存在
    kb = await kb_repo.get_by_id(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"知识库不存在: {kb_id}"
        )

    # 获取统计信息
    stats = await doc_repo.get_by_knowledge_base_with_stats(kb_id)

    return ResponseModel(
        code=200,
        message="success",
        data=KnowledgeBaseStatsResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=stats["total"],
            total_size_mb=stats["total_size_mb"],
            created_at=kb.created_at
        ).model_dump()
    )