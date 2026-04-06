"""
dependencies.py - API依赖注入

提供FastAPI依赖注入函数
"""

from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.connection import get_db
from core.repositories.knowledge_base_repo import KnowledgeBaseRepository
from core.repositories.document_repo import DocumentRepository
from core.repositories.base import BaseRepository
from core.models.conversation import Conversation
from core.services.router_service import RouterService
from core.services.search_service import SearchService
from core.services.document_service import DocumentService
from core.services.conversation_service import ConversationService
from infrastructure.llm.qwen_provider import QwenProvider
from infrastructure.llm.deepseek_provider import DeepSeekProvider
from infrastructure.llm.gateway import ModelGateway
from infrastructure.vector.bm25_index import BM25Index
from infrastructure.vector.faiss_store import FaissStore
from infrastructure.vector.hybrid_search import HybridSearch
from infrastructure.storage.local_storage import LocalStorage
from utils.prompt_loader import prompt_loader
from config.settings import settings


# ========== 全局单例 ==========

# 检索组件
_bm25_index = None
_faiss_store = None
_hybrid_search = None

# LLM组件
_qwen_provider = None
_deepseek_provider = None
_model_gateway = None

# 服务组件
_router_service = None
_search_service = None
_document_service = None
_conversation_service = None
_storage = None


def get_bm25_index() -> BM25Index:
    """获取BM25索引单例"""
    global _bm25_index
    if _bm25_index is None:
        _bm25_index = BM25Index(k1=1.5, b=0.75)
        # 尝试加载已有索引
        import os
        if os.path.exists("data/indices/bm25.pkl"):
            _bm25_index.load("data/indices/bm25.pkl")
    return _bm25_index


def get_faiss_store() -> FaissStore:
    """获取FAISS存储单例"""
    global _faiss_store
    if _faiss_store is None:
        _faiss_store = FaissStore(dimension=settings.EMBEDDING_DIMENSION, index_type="FlatL2")
        import os
        if os.path.exists("data/indices/faiss"):
            _faiss_store.load("data/indices/faiss")
    return _faiss_store


def get_hybrid_search(
    bm25: BM25Index = Depends(get_bm25_index),
    faiss: FaissStore = Depends(get_faiss_store)
) -> HybridSearch:
    """获取混合检索器单例"""
    global _hybrid_search
    if _hybrid_search is None:
        _hybrid_search = HybridSearch(
            bm25_index=bm25,
            faiss_store=faiss,
            rrf_k=settings.RRF_K,
            bm25_weight=0.4,
            vector_weight=0.6
        )
    return _hybrid_search


def get_qwen_provider() -> QwenProvider:
    """获取通义千问提供者"""
    global _qwen_provider
    if _qwen_provider is None:
        _qwen_provider = QwenProvider(
            model_name=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            timeout=settings.REQUEST_TIMEOUT
        )
    return _qwen_provider


def get_deepseek_provider() -> DeepSeekProvider:
    """获取DeepSeek提供者"""
    global _deepseek_provider
    if _deepseek_provider is None:
        _deepseek_provider = DeepSeekProvider(
            model_name=settings.BACKUP_LLM_MODEL,
            api_key=settings.BACKUP_LLM_API_KEY,
            base_url=settings.BACKUP_LLM_BASE_URL,
            timeout=settings.REQUEST_TIMEOUT
        )
    return _deepseek_provider


def get_model_gateway(
    qwen: QwenProvider = Depends(get_qwen_provider),
    deepseek: DeepSeekProvider = Depends(get_deepseek_provider)
) -> ModelGateway:
    """获取模型网关单例"""
    global _model_gateway
    if _model_gateway is None:
        _model_gateway = ModelGateway(
            primary=qwen,
            backups=[deepseek],
            retry_times=settings.RETRY_TIMES,
            retry_backoff=settings.RETRY_BACKOFF,
            enable_fallback=True
        )
    return _model_gateway


def get_storage() -> LocalStorage:
    """获取存储服务单例"""
    global _storage
    if _storage is None:
        _storage = LocalStorage(base_dir="data/documents")
    return _storage


def get_router_service() -> RouterService:
    """获取路由服务单例"""
    global _router_service
    if _router_service is None:
        _router_service = RouterService(config_path="config/routing.yaml")
    return _router_service


def get_search_service(
    hybrid: HybridSearch = Depends(get_hybrid_search)
) -> SearchService:
    """获取检索服务单例"""
    global _search_service
    if _search_service is None:
        _search_service = SearchService(hybrid_search=hybrid)
    return _search_service


async def get_document_service(
    db: AsyncSession = Depends(get_db),
    bm25: BM25Index = Depends(get_bm25_index),
    faiss: FaissStore = Depends(get_faiss_store),
    storage: LocalStorage = Depends(get_storage)
) -> DocumentService:
    """获取文档服务（每次请求新建，因为依赖数据库会话）"""
    doc_repo = DocumentRepository(db)
    kb_repo = KnowledgeBaseRepository(db)

    return DocumentService(
        document_repo=doc_repo,
        kb_repo=kb_repo,
        bm25_index=bm25,
        faiss_store=faiss,
        storage=storage
    )


async def get_conversation_service(
    db: AsyncSession = Depends(get_db)
) -> ConversationService:
    """获取对话服务（每次请求新建，因为依赖数据库会话）"""
    conv_repo = BaseRepository(Conversation, db)
    return ConversationService(
        conversation_repo=conv_repo,
        memory_size=10
    )


async def get_knowledge_base_repo(
    db: AsyncSession = Depends(get_db)
) -> KnowledgeBaseRepository:
    """获取知识库Repository"""
    return KnowledgeBaseRepository(db)


async def get_document_repo(
    db: AsyncSession = Depends(get_db)
) -> DocumentRepository:
    """获取文档Repository"""
    return DocumentRepository(db)


def get_session_id(request: Request) -> str:
    """获取或生成会话ID"""
    session_id = request.query_params.get("session_id")
    if not session_id:
        from uuid import uuid4
        session_id = str(uuid4())
    return session_id