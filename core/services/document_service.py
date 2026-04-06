"""
document_service.py - 文档管理服务

提供文档的上传、解析、分块、向量化、存储等完整生命周期管理
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from core.repositories.document_repo import DocumentRepository
from core.repositories.knowledge_base_repo import KnowledgeBaseRepository
from utils.text_splitter import TextSplitter, split_document
from utils.embedding import embedding_service
from infrastructure.vector.bm25_index import BM25Index
from infrastructure.vector.faiss_store import FaissStore
from infrastructure.storage.local_storage import LocalStorage
from utils.logger import get_logger

logger = get_logger(__name__)


class DocumentService:
    """文档管理服务"""

    def __init__(
        self,
        document_repo: DocumentRepository,
        kb_repo: KnowledgeBaseRepository,
        bm25_index: BM25Index,
        faiss_store: FaissStore,
        storage: LocalStorage
    ):
        """
        初始化文档服务

        参数:
            document_repo: 文档数据访问层
            kb_repo: 知识库数据访问层
            bm25_index: BM25索引实例
            faiss_store: FAISS存储实例
            storage: 文件存储实例
        """
        self.document_repo = document_repo
        self.kb_repo = kb_repo
        self.bm25_index = bm25_index
        self.faiss_store = faiss_store
        self.storage = storage
        self.text_splitter = TextSplitter(chunk_size=500, chunk_overlap=50)
        logger.info("文档管理服务初始化完成")

    async def upload_document(
        self,
        knowledge_base_id: int,
        file_content: bytes,
        file_name: str,
        file_type: str
    ) -> Dict[str, Any]:
        """
        上传并处理文档

        参数:
            knowledge_base_id: 知识库ID
            file_content: 文件内容（字节）
            file_name: 原始文件名
            file_type: 文件类型（pdf/docx/txt）

        返回:
            Dict: 文档信息和处理状态
        """
        # 1. 验证知识库存在
        kb = await self.kb_repo.get_by_id(knowledge_base_id)
        if not kb:
            raise ValueError(f"知识库不存在: {knowledge_base_id}")

        # 2. 保存原始文件
        file_path = await self.storage.save_file(
            file_content=file_content,
            original_name=file_name,
            subdir=f"kb_{knowledge_base_id}"
        )

        # 3. 创建文档记录
        doc = await self.document_repo.create(
            title=file_name.rsplit('.', 1)[0],
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_size=len(file_content),
            status="processing",
            knowledge_base_id=knowledge_base_id
        )
        logger.info(f"文档记录创建成功: doc_id={doc.id}")

        try:
            # 4. 解析文档内容
            content = await self.storage.read_file(file_path)
            parsed_content = await self._parse_document(content, file_type)

            # 5. 分块处理（使用 TextSplitter）
            chunks = self.text_splitter.split_document(
                content=parsed_content,
                metadata={
                    "doc_id": doc.id,
                    "doc_title": doc.title,
                    "knowledge_base_id": knowledge_base_id,
                    "file_name": file_name,
                    "file_type": file_type
                }
            )

            # 6. 向量化
            chunks_with_vectors = await embedding_service.embed_chunks(chunks)

            # 7. 更新文档分块数量
            await self.document_repo.update_chunk_count(doc.id, len(chunks_with_vectors))

            # 8. 添加到检索索引
            await self._add_to_indices(chunks_with_vectors, doc.id)

            # 9. 更新文档状态
            await self.document_repo.update_status(doc.id, "completed")

            # 10. 更新知识库文档数量
            await self.kb_repo.update_document_count(knowledge_base_id)

            logger.info(f"文档处理完成: doc_id={doc.id}, chunks={len(chunks_with_vectors)}")

            return {
                "doc_id": doc.id,
                "status": "completed",
                "chunk_count": len(chunks_with_vectors),
                "file_path": file_path
            }

        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            await self.document_repo.update_status(doc.id, "failed")
            raise

    async def _parse_document(self, content: str, file_type: str) -> str:
        """
        解析文档内容（内部方法）

        参数:
            content: 原始内容
            file_type: 文件类型

        返回:
            str: 解析后的文本内容
        """
        # 简化实现：根据文件类型解析
        # 实际项目中可使用unstructured、pypdf、python-docx等库
        if file_type == "txt":
            return content
        elif file_type == "pdf":
            # TODO: 使用pypdf解析PDF
            return content
        elif file_type == "docx":
            # TODO: 使用python-docx解析DOCX
            return content
        else:
            return content

    async def _add_to_indices(self, chunks: List[Dict], doc_id: int):
        """
        添加到检索索引（内部方法）

        参数:
            chunks: 分块列表（包含向量）
            doc_id: 文档ID
        """
        # 提取文本和向量
        texts = [chunk["text"] for chunk in chunks]
        vectors = [chunk["vector"] for chunk in chunks]

        # 生成块ID
        chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]

        # 添加到BM25
        for text, chunk_id in zip(texts, chunk_ids):
            self.bm25_index.add_document(text, chunk_id)

        # 添加到FAISS
        import numpy as np
        vectors_np = np.array(vectors, dtype=np.float32)
        self.faiss_store.add_vectors(
            vectors=vectors_np,
            doc_ids=chunk_ids,
            metadatas=chunks
        )

        logger.info(f"添加到索引完成: doc_id={doc_id}, chunks={len(chunks)}")

    async def delete_document(self, doc_id: int) -> bool:
        """
        删除文档

        参数:
            doc_id: 文档ID

        返回:
            bool: 是否删除成功
        """
        # 1. 获取文档信息
        doc = await self.document_repo.get_by_id(doc_id)
        if not doc:
            logger.warning(f"文档不存在: {doc_id}")
            return False

        knowledge_base_id = doc.knowledge_base_id

        # 2. 删除文件
        await self.storage.delete_file(doc.file_path)

        # 3. 从索引中删除
        # 注意：需要根据doc_id找到所有chunk_id并删除
        # 简化实现：重建索引（生产环境需优化）

        # 4. 删除文档记录
        await self.document_repo.delete_by_id(doc_id)

        # 5. 更新知识库文档数量
        await self.kb_repo.update_document_count(knowledge_base_id)

        logger.info(f"文档删除成功: doc_id={doc_id}")
        return True

    async def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        获取文档信息

        参数:
            doc_id: 文档ID

        返回:
            Optional[Dict]: 文档信息
        """
        doc = await self.document_repo.get_by_id(doc_id)
        if not doc:
            return None

        return {
            "id": doc.id,
            "title": doc.title,
            "file_name": doc.file_name,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        }

    async def list_documents(
        self,
        knowledge_base_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出知识库下的文档

        参数:
            knowledge_base_id: 知识库ID
            skip: 跳过的记录数
            limit: 返回的最大记录数

        返回:
            List[Dict]: 文档信息列表
        """
        docs = await self.document_repo.get_by_knowledge_base(
            kb_id=knowledge_base_id,
            skip=skip,
            limit=limit
        )

        return [
            {
                "id": doc.id,
                "title": doc.title,
                "file_name": doc.file_name,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": doc.status,
                "chunk_count": doc.chunk_count,
                "created_at": doc.created_at
            }
            for doc in docs
        ]

    async def get_document_stats(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        获取文档统计信息

        参数:
            knowledge_base_id: 知识库ID

        返回:
            Dict: 统计信息
        """
        return await self.document_repo.get_by_knowledge_base_with_stats(knowledge_base_id)

    async def reprocess_document(self, doc_id: int) -> Dict[str, Any]:
        """
        重新处理文档（用于失败的文档）

        参数:
            doc_id: 文档ID

        返回:
            Dict: 处理结果
        """
        doc = await self.document_repo.get_by_id(doc_id)
        if not doc:
            raise ValueError(f"文档不存在: {doc_id}")

        # 更新状态为处理中
        await self.document_repo.update_status(doc_id, "processing")

        try:
            # 读取文件内容
            content = await self.storage.read_file(doc.file_path)
            parsed_content = await self._parse_document(content, doc.file_type)

            # 重新分块和向量化
            chunks = self.text_splitter.split_document(
                content=parsed_content,
                metadata={"doc_id": doc.id, "doc_title": doc.title}
            )

            chunks_with_vectors = await embedding_service.embed_chunks(chunks)

            # 更新分块数量
            await self.document_repo.update_chunk_count(doc.id, len(chunks_with_vectors))

            # 更新状态
            await self.document_repo.update_status(doc_id, "completed")

            logger.info(f"文档重新处理完成: doc_id={doc_id}")

            return {
                "doc_id": doc_id,
                "status": "completed",
                "chunk_count": len(chunks_with_vectors)
            }

        except Exception as e:
            logger.error(f"文档重新处理失败: {e}")
            await self.document_repo.update_status(doc_id, "failed")
            raise