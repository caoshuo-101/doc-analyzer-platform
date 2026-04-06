"""
knowledge_base_repo.py - 知识库Repository

提供知识库相关的数据访问操作
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from core.models.knowledge_base import KnowledgeBase
from core.models.document import Document
from core.repositories.base import BaseRepository


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    """知识库数据访问层"""

    def __init__(self, session):
        """初始化知识库Repository"""
        super().__init__(KnowledgeBase, session)

    async def get_by_name(self, name: str) -> Optional[KnowledgeBase]:
        """
        根据名称获取知识库

        参数:
            name: 知识库名称

        返回:
            Optional[KnowledgeBase]: 知识库实例或None
        """
        result = await self.session.execute(
            select(KnowledgeBase).where(KnowledgeBase.name == name)
        )
        return result.scalar_one_or_none()

    async def get_with_documents(self, kb_id: int) -> Optional[KnowledgeBase]:
        """
        获取知识库及其关联的文档

        参数:
            kb_id: 知识库ID

        返回:
            Optional[KnowledgeBase]: 包含文档的知识库实例
        """
        result = await self.session.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.id == kb_id)
            .options(selectinload(KnowledgeBase.documents))
        )
        return result.scalar_one_or_none()

    async def get_all_with_stats(self) -> List[Dict[str, Any]]:
        """
        获取所有知识库及其统计信息

        返回:
            List[Dict]: 包含知识库信息和文档数量的列表
        """
        # 使用子查询获取每个知识库的文档数量
        subquery = (
            select(Document.knowledge_base_id, func.count(Document.id).label("doc_count"))
            .group_by(Document.knowledge_base_id)
            .subquery()
        )

        result = await self.session.execute(
            select(
                KnowledgeBase,
                func.coalesce(subquery.c.doc_count, 0).label("document_count")
            )
            .outerjoin(subquery, KnowledgeBase.id == subquery.c.knowledge_base_id)
        )

        items = []
        for kb, doc_count in result:
            items.append({
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "document_count": doc_count,
                "created_at": kb.created_at,
                "updated_at": kb.updated_at
            })

        return items

    async def update_document_count(self, kb_id: int) -> int:
        """
        更新知识库的文档数量

        参数:
            kb_id: 知识库ID

        返回:
            int: 更新后的文档数量
        """
        # 统计文档数量
        result = await self.session.execute(
            select(func.count(Document.id))
            .where(Document.knowledge_base_id == kb_id)
        )
        doc_count = result.scalar()

        # 更新知识库
        await self.update_by_id(kb_id, document_count=doc_count)

        return doc_count

    async def search_by_name(self, keyword: str, limit: int = 10) -> List[KnowledgeBase]:
        """
        根据名称关键词搜索知识库

        参数:
            keyword: 搜索关键词
            limit: 返回数量限制

        返回:
            List[KnowledgeBase]: 知识库列表
        """
        result = await self.session.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.name.contains(keyword))
            .limit(limit)
        )
        return list(result.scalars().all())