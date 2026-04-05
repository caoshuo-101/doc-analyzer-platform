"""
hybrid_search.py - 混合检索

结合 BM25 关键词检索和 FAISS 向量检索，使用 RRF 算法融合结果
"""

from typing import List, Tuple, Dict, Any
from infrastructure.vector.bm25_index import BM25Index
from infrastructure.vector.faiss_store import FaissStore
from utils.embedding import embedding_service
from utils.logger import get_logger

logger = get_logger(__name__)


class HybridSearch:
    """混合检索器"""

    def __init__(
        self,
        bm25_index: BM25Index,
        faiss_store: FaissStore,
        rrf_k: int = 60,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5
    ):
        """
        初始化混合检索器

        参数:
            bm25_index: BM25索引实例
            faiss_store: FAISS存储实例
            rrf_k: RRF融合参数，控制排名分数
            bm25_weight: BM25权重
            vector_weight: 向量检索权重
        """
        self.bm25_index = bm25_index
        self.faiss_store = faiss_store
        self.rrf_k = rrf_k
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight

        logger.info(f"混合检索器初始化完成，RRF_K={rrf_k}, BM25权重={bm25_weight}, 向量权重={vector_weight}")

    async def search(
        self,
        query: str,
        top_k: int = 3,
        use_bm25: bool = True,
        use_vector: bool = True
    ) -> List[Dict[str, Any]]:
        """
        执行混合检索

        参数:
            query: 查询文本
            top_k: 最终返回的结果数量
            use_bm25: 是否使用BM25检索
            use_vector: 是否使用向量检索

        返回:
            List[Dict]: 检索结果，包含内容、分数、元数据等
        """
        if not query or not query.strip():
            logger.warning("查询为空")
            return []

        results = {}

        # 1. BM25关键词检索
        if use_bm25 and self.bm25_index.index is not None:
            bm25_results = self.bm25_index.search(query, top_k=top_k * 3)
            self._add_to_results(results, bm25_results, 'bm25')
            logger.debug(f"BM25检索结果数: {len(bm25_results)}")

        # 2. 向量检索
        if use_vector and self.faiss_store.index is not None:
            query_vector = await embedding_service.embed_text(query)
            import numpy as np
            query_vector_np = np.array(query_vector, dtype=np.float32)
            vector_results = self.faiss_store.search(query_vector_np, top_k=top_k * 3)
            self._add_to_results(results, vector_results, 'vector')
            logger.debug(f"向量检索结果数: {len(vector_results)}")

        # 3. RRF融合
        fused_results = self._rrf_fusion(results)

        # 4. 获取详细内容
        final_results = await self._get_detailed_results(fused_results, top_k)

        logger.info(f"混合检索完成，查询: {query[:50]}..., 结果数: {len(final_results)}")
        return final_results

    def _add_to_results(
        self,
        results: Dict[int, Dict],
        search_results: List[Tuple[int, float, Any]],
        source: str
    ):
        """
        将检索结果添加到结果字典

        参数:
            results: 结果字典
            search_results: 检索结果列表
            source: 结果来源 (bm25/vector)
        """
        for item in search_results:
            doc_id = item[0]
            score = item[1]

            if doc_id not in results:
                results[doc_id] = {
                    'doc_id': doc_id,
                    'bm25_rank': None,
                    'vector_rank': None,
                    'bm25_score': None,
                    'vector_score': None,
                    'metadata': item[2] if len(item) > 2 else None
                }

            if source == 'bm25':
                results[doc_id]['bm25_rank'] = score
                results[doc_id]['bm25_score'] = score
            else:  # vector
                results[doc_id]['vector_rank'] = score
                results[doc_id]['vector_score'] = score

    def _rrf_fusion(self, results: Dict[int, Dict]) -> List[Tuple[int, float]]:
        """
        RRF (Reciprocal Rank Fusion) 融合算法

        参数:
            results: 结果字典

        返回:
            List[Tuple[int, float]]: [(doc_id, rrf_score), ...]
        """
        fused_scores = {}

        for doc_id, data in results.items():
            rrf_score = 0.0

            # BM25排名贡献
            if data['bm25_rank'] is not None:
                rrf_score += self.bm25_weight / (self.rrf_k + data['bm25_rank'])

            # 向量检索排名贡献
            if data['vector_rank'] is not None:
                rrf_score += self.vector_weight / (self.rrf_k + data['vector_rank'])

            if rrf_score > 0:
                fused_scores[doc_id] = rrf_score

        # 按分数排序
        sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_results

    async def _get_detailed_results(
        self,
        fused_results: List[Tuple[int, float]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        获取详细的结果信息

        参数:
            fused_results: 融合后的结果列表
            top_k: 返回数量

        返回:
            List[Dict]: 详细结果
        """
        detailed_results = []

        for doc_id, rrf_score in fused_results[:top_k]:
            # 查找文档内容和元数据
            content = ""
            metadata = None

            # 从 FAISS 中查找元数据
            if self.faiss_store.doc_ids and doc_id in self.faiss_store.doc_ids:
                idx = self.faiss_store.doc_ids.index(doc_id)
                if idx < len(self.faiss_store.metadatas):
                    metadata = self.faiss_store.metadatas[idx]
                    content = metadata.get('content', '') or metadata.get('text', '')

            # 如果 FAISS 中没有，从 BM25 中查找
            if not content and self.bm25_index.doc_ids and doc_id in self.bm25_index.doc_ids:
                idx = self.bm25_index.doc_ids.index(doc_id)
                if idx < len(self.bm25_index.corpus):
                    content = self.bm25_index.corpus[idx]

            detailed_results.append({
                'doc_id': doc_id,
                'content': content,
                'rrf_score': rrf_score,
                'metadata': metadata or {}
            })

        return detailed_results

    def set_weights(self, bm25_weight: float, vector_weight: float):
        """
        动态调整权重

        参数:
            bm25_weight: BM25权重
            vector_weight: 向量检索权重
        """
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        logger.info(f"权重已更新: BM25={bm25_weight}, 向量={vector_weight}")

    def get_stats(self) -> dict:
        """
        获取统计信息

        返回:
            dict: 统计信息
        """
        return {
            'bm25_stats': self.bm25_index.get_stats() if self.bm25_index else {},
            'faiss_stats': self.faiss_store.get_stats() if self.faiss_store else {},
            'rrf_k': self.rrf_k,
            'bm25_weight': self.bm25_weight,
            'vector_weight': self.vector_weight
        }