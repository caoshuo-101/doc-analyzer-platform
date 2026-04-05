"""
faiss_store.py - FAISS向量存储

基于 FAISS 的向量检索实现，支持增删改查
"""

import numpy as np
import faiss
import pickle
import os
from typing import List, Tuple, Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class FaissStore:
    """FAISS向量存储封装"""

    def __init__(self, dimension: int, index_type: str = "FlatL2"):
        """
        初始化FAISS存储

        参数:
            dimension: 向量维度
            index_type: 索引类型 (FlatL2, IDMap)
        """
        self.dimension = dimension
        self.index_type = index_type
        self.index: Optional[faiss.Index] = None
        self.metadatas: List[Dict[str, Any]] = []
        self.doc_ids: List[int] = []
        logger.info(f"FAISS存储初始化完成，维度={dimension}, 类型={index_type}")

    def _create_index(self):
        """创建FAISS索引"""
        if self.index_type == "FlatL2":
            # L2距离索引
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "IDMap":
            # 带ID映射的索引
            self.index = faiss.IndexIDMap(faiss.IndexFlatL2(self.dimension))
        elif self.index_type == "FlatIP":
            # 内积相似度索引
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)

    def add_vectors(
        self,
        vectors: np.ndarray,
        doc_ids: List[int],
        metadatas: List[Dict[str, Any]]
    ):
        """
        添加向量

        参数:
            vectors: 向量矩阵 (n_samples, dimension)
            doc_ids: 文档ID列表
            metadatas: 元数据列表
        """
        if vectors.shape[0] == 0:
            logger.warning("向量为空，跳过添加")
            return

        if self.index is None:
            self._create_index()

        # 确保向量是float32类型
        vectors = vectors.astype(np.float32)

        # 添加到索引
        if self.index_type == "IDMap":
            ids = np.array(doc_ids, dtype=np.int64)
            self.index.add_with_ids(vectors, ids)
        else:
            self.index.add(vectors)

        # 存储元数据
        self.doc_ids.extend(doc_ids)
        self.metadatas.extend(metadatas)

        logger.info(f"添加向量成功，数量: {len(doc_ids)}，总向量数: {self.index.ntotal}")

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10
    ) -> List[Tuple[int, float, Optional[Dict]]]:
        """
        检索相似向量

        参数:
            query_vector: 查询向量 (dimension,)
            top_k: 返回前k个结果

        返回:
            List[Tuple[int, float, Optional[Dict]]]: [(doc_id, distance, metadata), ...]
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("索引为空，无法检索")
            return []

        # 确保查询向量格式正确
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        query_vector = query_vector.astype(np.float32)

        # 执行检索
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))

        # 整理结果
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                # 获取对应的doc_id和metadata
                if self.index_type == "IDMap":
                    doc_id = int(idx)
                else:
                    doc_id = self.doc_ids[idx] if idx < len(self.doc_ids) else idx

                metadata = self.metadatas[idx] if idx < len(self.metadatas) else None
                distance = float(distances[0][i])

                results.append((doc_id, distance, metadata))

        logger.debug(f"FAISS检索完成，结果数: {len(results)}")
        return results

    def delete_vectors(self, doc_ids: List[int]):
        """
        删除向量（FAISS不支持直接删除，需要重建索引）

        参数:
            doc_ids: 要删除的文档ID列表
        """
        if not doc_ids:
            return

        # 找到要保留的向量
        keep_indices = [i for i, doc_id in enumerate(self.doc_ids) if doc_id not in doc_ids]

        if not keep_indices:
            # 全部删除
            self.index = None
            self.doc_ids = []
            self.metadatas = []
            logger.info("删除所有向量")
            return

        # 重建索引
        old_vectors = self.get_all_vectors()
        if old_vectors is not None:
            keep_vectors = old_vectors[keep_indices]
            keep_doc_ids = [self.doc_ids[i] for i in keep_indices]
            keep_metadatas = [self.metadatas[i] for i in keep_indices]

            # 重建索引
            self.index = None
            self.doc_ids = []
            self.metadatas = []
            self.add_vectors(keep_vectors, keep_doc_ids, keep_metadatas)

        logger.info(f"删除向量成功，删除数量: {len(doc_ids)}")

    def get_all_vectors(self) -> Optional[np.ndarray]:
        """
        获取所有向量

        返回:
            Optional[np.ndarray]: 向量矩阵
        """
        if self.index is None or self.index.ntotal == 0:
            return None

        # FAISS 没有直接获取所有向量的方法，需要重新构建
        # 这里返回 None，实际使用时需要从外部维护
        logger.warning("FAISS 不支持直接获取所有向量")
        return None

    def save(self, path: str):
        """
        保存索引和元数据

        参数:
            path: 保存路径（不含扩展名）
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # 保存FAISS索引
        if self.index is not None:
            faiss.write_index(self.index, f"{path}.faiss")

        # 保存元数据
        metadata_path = f"{path}.meta"
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'doc_ids': self.doc_ids,
                'metadatas': self.metadatas,
                'dimension': self.dimension,
                'index_type': self.index_type
            }, f)

        logger.info(f"FAISS索引已保存: {path}")

    def load(self, path: str):
        """
        加载索引和元数据

        参数:
            path: 加载路径（不含扩展名）
        """
        # 加载FAISS索引
        faiss_path = f"{path}.faiss"
        if os.path.exists(faiss_path):
            self.index = faiss.read_index(faiss_path)
            logger.info(f"FAISS索引已加载: {faiss_path}, 向量数: {self.index.ntotal}")

        # 加载元数据
        metadata_path = f"{path}.meta"
        if os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.doc_ids = data['doc_ids']
                self.metadatas = data['metadatas']
                self.dimension = data['dimension']
                self.index_type = data.get('index_type', 'FlatL2')
            logger.info(f"元数据已加载，文档数: {len(self.doc_ids)}")

    def get_stats(self) -> dict:
        """
        获取索引统计信息

        返回:
            dict: 统计信息
        """
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_documents": len(self.doc_ids),
            "dimension": self.dimension,
            "index_type": self.index_type
        }