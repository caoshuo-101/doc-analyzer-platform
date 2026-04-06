"""
search_service.py - 检索服务

封装混合检索能力，提供知识库检索、跨库检索、上下文格式化等功能
"""

from typing import List, Dict, Any, Optional
from infrastructure.vector.hybrid_search import HybridSearch
from infrastructure.vector.bm25_index import BM25Index
from infrastructure.vector.faiss_store import FaissStore
from utils.logger import get_logger

logger = get_logger(__name__)


class SearchService:
    """检索服务"""

    def __init__(
        self,
        hybrid_search: HybridSearch,
        knowledge_base_id: Optional[int] = None
    ):
        """
        初始化检索服务

        参数:
            hybrid_search: 混合检索器实例
            knowledge_base_id: 当前知识库ID
        """
        self.hybrid_search = hybrid_search
        self.knowledge_base_id = knowledge_base_id
        logger.info(f"检索服务初始化完成，知识库ID: {knowledge_base_id}")

    async def search(
        self,
        question: str,
        knowledge_base_id: Optional[int] = None,
        top_k: int = 3,
        use_bm25: bool = True,
        use_vector: bool = True
    ) -> List[Dict[str, Any]]:
        """
        检索文档片段

        参数:
            question: 用户问题
            knowledge_base_id: 知识库ID（覆盖实例默认值）
            top_k: 返回结果数量
            use_bm25: 是否使用BM25检索
            use_vector: 是否使用向量检索

        返回:
            List[Dict]: 检索结果列表，每个结果包含doc_id, content, score, metadata
        """
        kb_id = knowledge_base_id or self.knowledge_base_id

        if not kb_id:
            logger.warning("未指定知识库ID，无法检索")
            return []

        if not question or not question.strip():
            logger.warning("问题为空，返回空结果")
            return []

        logger.info(f"开始检索，知识库ID: {kb_id}, 问题: {question[:50]}...")

        # 执行混合检索
        results = await self.hybrid_search.search(
            query=question,
            top_k=top_k,
            use_bm25=use_bm25,
            use_vector=use_vector
        )

        # 添加知识库ID到结果
        for result in results:
            result['knowledge_base_id'] = kb_id

        logger.info(f"检索完成，返回 {len(results)} 条结果")
        return results

    async def search_across_kb(
        self,
        question: str,
        kb_ids: List[int],
        top_k: int = 3
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        跨知识库检索

        参数:
            question: 用户问题
            kb_ids: 知识库ID列表
            top_k: 每个知识库返回结果数量

        返回:
            Dict[int, List[Dict]]: 按知识库ID分组的结果字典
        """
        if not kb_ids:
            logger.warning("知识库ID列表为空")
            return {}

        logger.info(f"跨知识库检索，知识库数量: {len(kb_ids)}")

        results_by_kb = {}

        for kb_id in kb_ids:
            # 注意：这里需要为每个知识库创建独立的检索器
            # 简化实现：假设当前知识库已经切换
            # 实际使用时需要根据kb_id获取对应的索引
            logger.warning(f"跨知识库检索需要为每个知识库配置独立索引，当前跳过: {kb_id}")
            results_by_kb[kb_id] = []

        return results_by_kb

    async def get_context(
        self,
        question: str,
        knowledge_base_id: Optional[int] = None,
        top_k: int = 3
    ) -> str:
        """
        获取格式化的上下文文本

        参数:
            question: 用户问题
            knowledge_base_id: 知识库ID
            top_k: 检索结果数量

        返回:
            str: 格式化后的上下文字符串，可直接用于提示词
        """
        results = await self.search(question, knowledge_base_id, top_k)

        if not results:
            logger.info("未检索到相关内容，返回空上下文")
            return "暂无相关文档内容。"

        # 格式化上下文
        context_parts = []
        for i, result in enumerate(results, 1):
            content = result.get('content', '')
            if content:
                context_parts.append(f"[片段{i}]\n{content}")

        if not context_parts:
            return "暂无相关文档内容。"

        context = "\n\n".join(context_parts)
        logger.debug(f"上下文生成完成，长度: {len(context)} 字符")
        return context

    async def search_with_scores(
        self,
        question: str,
        knowledge_base_id: Optional[int] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        检索并返回详细信息（包含分数）

        参数:
            question: 用户问题
            knowledge_base_id: 知识库ID
            top_k: 返回结果数量

        返回:
            List[Dict]: 包含详细分数信息的结果列表
        """
        results = await self.search(question, knowledge_base_id, top_k)

        # 添加分数说明
        for result in results:
            rrf_score = result.get('rrf_score', 0)
            result['score_explain'] = f"RRF融合分数: {rrf_score:.4f}"

        return results

    def set_weights(self, bm25_weight: float, vector_weight: float):
        """
        动态调整检索权重

        参数:
            bm25_weight: BM25权重
            vector_weight: 向量检索权重
        """
        self.hybrid_search.set_weights(bm25_weight, vector_weight)
        logger.info(f"检索权重已更新: BM25={bm25_weight}, 向量={vector_weight}")

    def get_stats(self) -> dict:
        """
        获取检索服务统计信息

        返回:
            dict: 统计信息
        """
        return {
            "knowledge_base_id": self.knowledge_base_id,
            "hybrid_search_stats": self.hybrid_search.get_stats(),
            "available": self.hybrid_search is not None
        }