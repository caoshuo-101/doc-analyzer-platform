"""
documents.py - 文档API路由

提供文档的上传、删除、查询等接口
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List

from api.schemas.common import ResponseModel, PaginationParams, PaginationResponse
from api.schemas.document import DocumentResponse, DocumentUploadResponse, DocumentStatsResponse
from api.dependencies import get_document_service, get_knowledge_base_repo
from core.services.document_service import DocumentService
from core.repositories.knowledge_base_repo import KnowledgeBaseRepository
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["文档管理"])


@router.post("/upload", response_model=ResponseModel)
async def upload_document(
    knowledge_base_id: int = Form(..., description="知识库ID"),
    file: UploadFile = File(..., description="文档文件"),
    doc_service: DocumentService = Depends(get_document_service),
    kb_repo: KnowledgeBaseRepository = Depends(get_knowledge_base_repo)
):
    """
    上传文档

    - **knowledge_base_id**: 知识库ID
    - **file**: 上传的文件（支持pdf、docx、txt）
    """
    # 检查知识库是否存在
    kb = await kb_repo.get_by_id(knowledge_base_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"知识库不存在: {knowledge_base_id}"
        )

    # 检查文件类型
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ["pdf", "docx", "txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file_ext}，仅支持 pdf, docx, txt"
        )

    try:
        # 读取文件内容
        content = await file.read()

        # 上传并处理文档
        result = await doc_service.upload_document(
            knowledge_base_id=knowledge_base_id,
            file_content=content,
            file_name=file.filename,
            file_type=file_ext
        )

        return ResponseModel(
            code=200,
            message="文档上传成功",
            data=DocumentUploadResponse(
                doc_id=result["doc_id"],
                status=result["status"],
                chunk_count=result["chunk_count"],
                message="文档处理完成"
            ).model_dump()
        )

    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败: {str(e)}"
        )


@router.get("/{doc_id}", response_model=ResponseModel)
async def get_document(
    doc_id: int,
    doc_service: DocumentService = Depends(get_document_service)
):
    """
    获取文档详情
    """
    doc = await doc_service.get_document(doc_id)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档不存在: {doc_id}"
        )

    return ResponseModel(
        code=200,
        message="success",
        data=doc
    )


@router.get("/knowledge-base/{kb_id}", response_model=ResponseModel)
async def list_documents(
    kb_id: int,
    pagination: PaginationParams = Depends(),
    doc_service: DocumentService = Depends(get_document_service),
    kb_repo: KnowledgeBaseRepository = Depends(get_knowledge_base_repo)
):
    """
    获取知识库下的文档列表
    """
    # 检查知识库是否存在
    kb = await kb_repo.get_by_id(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"知识库不存在: {kb_id}"
        )

    # 获取文档列表
    docs = await doc_service.list_documents(
        knowledge_base_id=kb_id,
        skip=pagination.skip,
        limit=pagination.page_size
    )

    # 获取总数
    stats = await doc_service.get_document_stats(kb_id)

    return ResponseModel(
        code=200,
        message="success",
        data=PaginationResponse(
            items=docs,
            total=stats["total"],
            page=pagination.page,
            page_size=pagination.page_size,
            pages=(stats["total"] + pagination.page_size - 1) // pagination.page_size
        ).model_dump()
    )


@router.delete("/{doc_id}", response_model=ResponseModel)
async def delete_document(
    doc_id: int,
    doc_service: DocumentService = Depends(get_document_service)
):
    """
    删除文档
    """
    success = await doc_service.delete_document(doc_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档不存在: {doc_id}"
        )

    return ResponseModel(
        code=200,
        message="文档删除成功"
    )


@router.get("/knowledge-base/{kb_id}/stats", response_model=ResponseModel)
async def get_document_stats(
    kb_id: int,
    doc_service: DocumentService = Depends(get_document_service),
    kb_repo: KnowledgeBaseRepository = Depends(get_knowledge_base_repo)
):
    """
    获取知识库的文档统计信息
    """
    # 检查知识库是否存在
    kb = await kb_repo.get_by_id(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"知识库不存在: {kb_id}"
        )

    stats = await doc_service.get_document_stats(kb_id)

    return ResponseModel(
        code=200,
        message="success",
        data=DocumentStatsResponse(
            total=stats["total"],
            status=stats["status"],
            total_size_bytes=stats["total_size_bytes"],
            total_size_mb=stats["total_size_mb"]
        ).model_dump()
    )