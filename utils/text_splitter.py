"""
text_splitter.py - 文档分块工具

提供文档智能分块功能，支持多种分块策略
"""

from typing import List, Dict, Any
import re


class TextSplitter:
    """文本分块器"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: List[str] = None
    ):
        """
        初始化分块器

        参数:
            chunk_size: 每个块的最大字符数
            chunk_overlap: 块之间的重叠字符数
            separators: 分隔符列表，优先级从高到低
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        if separators is None:
            self.separators = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        else:
            self.separators = separators

    def split_text(self, text: str) -> List[str]:
        """
        分割文本为多个块

        参数:
            text: 原始文本

        返回:
            List[str]: 文本块列表
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # 确定结束位置
            end = min(start + self.chunk_size, len(text))

            # 如果还没到末尾，尝试在分隔符处切分
            if end < len(text):
                end = self._find_split_point(text, start, end)

            # 提取块
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # 移动开始位置（考虑重叠）
            start = end - self.chunk_overlap if end - self.chunk_overlap > start else end

        return chunks

    def _find_split_point(self, text: str, start: int, end: int) -> int:
        """
        寻找最佳切分点

        参数:
            text: 完整文本
            start: 块开始位置
            end: 理想结束位置

        返回:
            int: 实际切分位置
        """
        # 在理想位置附近寻找分隔符
        search_range = min(200, self.chunk_size // 4)
        search_start = max(start, end - search_range)
        search_text = text[search_start:end + search_range]

        for separator in self.separators:
            # 从后往前找分隔符
            last_sep = search_text.rfind(separator)
            if last_sep != -1:
                return search_start + last_sep + len(separator)

        # 没找到合适分隔符，返回原位置
        return end

    def split_document(
            self,
            content: str,
            metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        分割文档并附加元数据

        参数:
            content: 文档内容
            metadata: 文档元数据（会复制到每个块）

        返回:
            List[Dict]: 包含文本和元数据的块列表
        """
        chunks = self.split_text(content)

        result = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "chunk_index": i,
                "chunk_count": len(chunks),
                "chunk_size": len(chunk),
                **(metadata or {})
            }
            result.append({
                "text": chunk,
                "metadata": chunk_metadata
            })

        return result


class DocumentSplitter:
    """文档分块器（支持不同文档类型）"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = TextSplitter(chunk_size, chunk_overlap)

    def split_pdf(self, pages: List[str], metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        分割PDF文档

        参数:
            pages: 页面文本列表
            metadata: 元数据

        返回:
            List[Dict]: 分块结果
        """
        all_chunks = []

        for page_num, page_text in enumerate(pages):
            page_metadata = {
                "page_number": page_num + 1,
                "source_type": "pdf",
                **(metadata or {})
            }
            chunks = self.splitter.split_document(page_text, page_metadata)
            all_chunks.extend(chunks)

        return all_chunks

    def split_docx(self, paragraphs: List[str], metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        分割DOCX文档

        参数:
            paragraphs: 段落文本列表
            metadata: 元数据

        返回:
            List[Dict]: 分块结果
        """
        # 合并段落为完整文本
        full_text = "\n".join(paragraphs)

        doc_metadata = {
            "source_type": "docx",
            **(metadata or {})
        }

        return self.splitter.split_document(full_text, doc_metadata)

    def split_txt(self, content: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        分割TXT文档

        参数:
            content: 文本内容
            metadata: 元数据

        返回:
            List[Dict]: 分块结果
        """
        txt_metadata = {
            "source_type": "txt",
            **(metadata or {})
        }

        return self.splitter.split_document(content, txt_metadata)


# 便捷函数
def split_document(
    content: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    快速分割文档

    参数:
        content: 文档内容
        chunk_size: 块大小
        chunk_overlap: 重叠大小
        metadata: 元数据

    返回:
        List[Dict]: 分块结果
    """
    splitter = TextSplitter(chunk_size, chunk_overlap)
    return splitter.split_document(content, metadata)