"""
document_repo.py - 文档Repository

提供文档相关的数据访问操作
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from core.models.document import Document
from core.models.knowledge_base import KnowledgeBase
from core.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """文档数据访问层"""

    def __init__(self, session):
        """初始化文档Repository"""
        super().__init__(Document, session)

    async def get_by_knowledge_base(
        self,
        kb_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """
        获取知识库下的所有文档

        参数:
            kb_id: 知识库ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        返回:
            List[Document]: 文档列表
        """
        result = await self.session.execute(
            select(Document)
            .where(Document.knowledge_base_id == kb_id)
            .offset(skip)
            .limit(limit)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: str, limit: int = 100) -> List[Document]:
        """
        根据状态获取文档

        参数:
            status: 文档状态 (uploading, processing, completed, failed)
            limit: 返回数量限制

        返回:
            List[Document]: 文档列表
        """
        result = await self.session.execute(
            select(Document)
            .where(Document.status == status)
            .limit(limit)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_with_knowledge_base(self, doc_id: int) -> Optional[Document]:
        """
        获取文档及其关联的知识库

        参数:
            doc_id: 文档ID

        返回:
            Optional[Document]: 包含知识库的文档实例
        """
        result = await self.session.execute(
            select(Document)
            .where(Document.id == doc_id)
            .options(selectinload(Document.knowledge_base))
        )
        return result.scalar_one_or_none()

    async def get_by_knowledge_base_with_stats(self, kb_id: int) -> Dict[str, Any]:
        """
        获取知识库的文档统计信息

        参数:
            kb_id: 知识库ID

        返回:
            Dict: 统计信息
        """
        # 总数
        total_result = await self.session.execute(
            select(func.count(Document.id))
            .where(Document.knowledge_base_id == kb_id)
        )
        total = total_result.scalar()

        # 各状态统计
        status_result = await self.session.execute(
            select(Document.status, func.count(Document.id))
            .where(Document.knowledge_base_id == kb_id)
            .group_by(Document.status)
        )

        status_stats = {status: count for status, count in status_result}

        # 总文件大小
        size_result = await self.session.execute(
            select(func.sum(Document.file_size))
            .where(Document.knowledge_base_id == kb_id)
        )
        total_size = size_result.scalar() or 0

        return {
            "total": total,
            "status": status_stats,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }

    async def update_status(self, doc_id: int, status: str) -> Optional[Document]:
        """
        更新文档状态

        参数:
            doc_id: 文档ID
            status: 新状态

        返回:
            Optional[Document]: 更新后的文档实例
        """
        return await self.update_by_id(doc_id, status=status)

    async def update_chunk_count(self, doc_id: int, chunk_count: int) -> Optional[Document]:
        """
        更新文档分块数量

        参数:
            doc_id: 文档ID
            chunk_count: 分块数量

        返回:
            Optional[Document]: 更新后的文档实例
        """
        return await self.update_by_id(doc_id, chunk_count=chunk_count)

    async def get_documents_by_ids(self, doc_ids: List[int]) -> List[Document]:
        """
        根据ID列表获取文档

        参数:
            doc_ids: 文档ID列表

        返回:
            List[Document]: 文档列表
        """
        if not doc_ids:
            return []

        result = await self.session.execute(
            select(Document).where(Document.id.in_(doc_ids))
        )
        return list(result.scalars().all())

    async def search_documents(
        self,
        kb_id: int,
        keyword: str,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Document]:
        """
        搜索文档（按标题和文件名）

        参数:
            kb_id: 知识库ID
            keyword: 搜索关键词
            status: 可选的状态过滤
            limit: 返回数量限制

        返回:
            List[Document]: 文档列表
        """
        conditions = [Document.knowledge_base_id == kb_id]

        if keyword:
            conditions.append(
                or_(
                    Document.title.contains(keyword),
                    Document.file_name.contains(keyword)
                )
            )

        if status:
            conditions.append(Document.status == status)

        result = await self.session.execute(
            select(Document)
            .where(and_(*conditions))
            .limit(limit)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_by_knowledge_base(self, kb_id: int) -> int:
        """
        删除知识库下的所有文档

        参数:
            kb_id: 知识库ID

        返回:
            int: 删除的文档数量
        """
        docs = await self.get_by_knowledge_base(kb_id)
        if not docs:
            return 0

        for doc in docs:
            await self.session.delete(doc)

        await self.session.flush()
        return len(docs)