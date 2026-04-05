"""
embedding.py - 向量化服务

提供文本向量化功能，支持单条和批量处理
"""

from typing import List, Optional
import numpy as np
from openai import AsyncOpenAI
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """向量化服务"""

    def __init__(self):
        """初始化向量化服务"""
        # 使用原生 OpenAI 客户端，更稳定
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        logger.info(f"向量化服务初始化完成，模型: {self.model}，维度: {self.dimension}")

    async def embed_text(self, text: str) -> List[float]:
        """
        单文本向量化

        参数:
            text: 输入文本

        返回:
            List[float]: 向量表示
        """
        try:
            # 确保文本不为空
            if not text or not text.strip():
                logger.warning("文本为空，返回零向量")
                return [0.0] * self.dimension

            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )

            vector = response.data[0].embedding
            logger.debug(f"文本向量化成功，文本长度: {len(text)}")
            return vector

        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            # 返回零向量作为降级方案
            return [0.0] * self.dimension

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量文本向量化

        参数:
            texts: 文本列表

        返回:
            List[List[float]]: 向量列表
        """
        if not texts:
            return []

        # 过滤空文本
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return [[0.0] * self.dimension for _ in texts]

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=valid_texts,
                encoding_format="float"
            )

            # 按原始顺序组织结果
            result_vectors = []
            text_index = 0
            for original_text in texts:
                if original_text and original_text.strip():
                    result_vectors.append(response.data[text_index].embedding)
                    text_index += 1
                else:
                    result_vectors.append([0.0] * self.dimension)

            logger.info(f"批量向量化成功，数量: {len(valid_texts)}")
            return result_vectors

        except Exception as e:
            logger.error(f"批量向量化失败: {e}")
            # 返回零向量列表作为降级方案
            return [[0.0] * self.dimension for _ in texts]

    async def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """
        对分块结果进行向量化

        参数:
            chunks: 分块列表，每个元素包含 text 和 metadata

        返回:
            List[dict]: 添加了 vector 字段的分块列表
        """
        if not chunks:
            return []

        texts = [chunk.get("text", "") for chunk in chunks]
        vectors = await self.embed_documents(texts)

        for chunk, vector in zip(chunks, vectors):
            chunk["vector"] = vector

        logger.info(f"分块向量化完成，块数: {len(chunks)}")
        return chunks

    def numpy_to_list(self, vectors: np.ndarray) -> List[List[float]]:
        """
        将numpy数组转换为列表

        参数:
            vectors: numpy数组

        返回:
            List[List[float]]: 向量列表
        """
        return vectors.tolist()

    def list_to_numpy(self, vectors: List[List[float]]) -> np.ndarray:
        """
        将列表转换为numpy数组

        参数:
            vectors: 向量列表

        返回:
            np.ndarray: numpy数组
        """
        if not vectors:
            return np.array([])
        return np.array(vectors, dtype=np.float32)


# 全局单例
embedding_service = EmbeddingService()