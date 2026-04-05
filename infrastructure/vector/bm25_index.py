"""
bm25_index.py - BM25关键词检索

基于 BM25Okapi 实现的关键词检索，支持中文分词
"""

import jieba
import pickle
import os
from typing import List, Tuple, Optional
from rank_bm25 import BM25Okapi
from utils.logger import get_logger

logger = get_logger(__name__)


class BM25Index:
    """BM25索引封装"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化BM25索引

        参数:
            k1: BM25参数，控制词频饱和度
            b: BM25参数，控制文档长度归一化
        """
        self.k1 = k1
        self.b = b
        self.index: Optional[BM25Okapi] = None
        self.corpus: List[str] = []
        self.doc_ids: List[int] = []
        logger.info(f"BM25索引初始化完成，k1={k1}, b={b}")

    def _tokenize(self, text: str) -> List[str]:
        """
        中文分词

        参数:
            text: 输入文本

        返回:
            List[str]: 分词结果
        """
        # 使用 jieba 进行中文分词
        tokens = list(jieba.cut(text))
        # 过滤掉空字符串和纯空格
        tokens = [t.strip() for t in tokens if t and t.strip()]
        return tokens

    def build(self, corpus: List[str], doc_ids: List[int]):
        """
        构建索引

        参数:
            corpus: 文档内容列表
            doc_ids: 文档ID列表
        """
        if not corpus:
            logger.warning("语料库为空，跳过索引构建")
            return

        self.corpus = corpus
        self.doc_ids = doc_ids

        # 对所有文档进行分词
        tokenized_corpus = [self._tokenize(doc) for doc in corpus]

        # 构建BM25索引
        self.index = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)
        logger.info(f"BM25索引构建完成，文档数: {len(corpus)}")

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        检索文档

        参数:
            query: 查询文本
            top_k: 返回前k个结果

        返回:
            List[Tuple[int, float]]: [(doc_id, score), ...]
        """
        if not self.index:
            logger.warning("索引未构建，请先调用 build()")
            return []

        if not query or not query.strip():
            return []

        # 对查询进行分词
        tokenized_query = self._tokenize(query)

        # 获取所有文档的分数
        scores = self.index.get_scores(tokenized_query)

        # 获取top_k索引
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        # 返回结果
        results = []
        for idx, score in indexed_scores[:top_k]:
            if score > 0:  # 只返回有分数的结果
                doc_id = self.doc_ids[idx] if idx < len(self.doc_ids) else idx
                results.append((doc_id, float(score)))

        logger.debug(f"BM25检索完成，查询: {query[:50]}..., 结果数: {len(results)}")
        return results

    def add_document(self, content: str, doc_id: int):
        """
        增量添加文档

        参数:
            content: 文档内容
            doc_id: 文档ID
        """
        if not content or not content.strip():
            logger.warning("文档内容为空，跳过添加")
            return

        self.corpus.append(content)
        self.doc_ids.append(doc_id)

        # 重建索引（简单实现，大数据量需优化）
        tokenized_corpus = [self._tokenize(doc) for doc in self.corpus]
        self.index = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)
        logger.info(f"添加文档成功，doc_id={doc_id}，当前文档数: {len(self.corpus)}")

    def remove_document(self, doc_id: int):
        """
        删除文档

        参数:
            doc_id: 文档ID
        """
        if doc_id not in self.doc_ids:
            logger.warning(f"文档不存在，doc_id={doc_id}")
            return

        # 找到要删除的索引
        idx = self.doc_ids.index(doc_id)

        # 删除文档
        self.corpus.pop(idx)
        self.doc_ids.pop(idx)

        # 重建索引
        if self.corpus:
            tokenized_corpus = [self._tokenize(doc) for doc in self.corpus]
            self.index = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)
        else:
            self.index = None

        logger.info(f"删除文档成功，doc_id={doc_id}，当前文档数: {len(self.corpus)}")

    def save(self, path: str):
        """
        持久化索引

        参数:
            path: 保存路径
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)

        data = {
            'corpus': self.corpus,
            'doc_ids': self.doc_ids,
            'k1': self.k1,
            'b': self.b
        }

        with open(path, 'wb') as f:
            pickle.dump(data, f)

        logger.info(f"BM25索引已保存: {path}")

    def load(self, path: str):
        """
        加载索引

        参数:
            path: 加载路径
        """
        if not os.path.exists(path):
            logger.warning(f"索引文件不存在: {path}")
            return

        with open(path, 'rb') as f:
            data = pickle.load(f)

        self.k1 = data['k1']
        self.b = data['b']
        self.build(data['corpus'], data['doc_ids'])

        logger.info(f"BM25索引已加载: {path}, 文档数: {len(self.corpus)}")

    def get_stats(self) -> dict:
        """
        获取索引统计信息

        返回:
            dict: 统计信息
        """
        return {
            "document_count": len(self.corpus),
            "has_index": self.index is not None,
            "k1": self.k1,
            "b": self.b
        }