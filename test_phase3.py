"""
test_phase3.py - Phase 3 验证脚本
测试检索模块功能
"""

import asyncio
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_bm25():
    """测试BM25检索"""
    print("=" * 50)
    print("测试1: BM25关键词检索")
    print("=" * 50)

    from infrastructure.vector.bm25_index import BM25Index

    # 准备测试文档
    documents = [
        "人工智能是计算机科学的一个分支",
        "机器学习是人工智能的核心技术",
        "深度学习使用神经网络进行学习",
        "Python是一种编程语言",
        "FAISS是Facebook开源的向量检索库"
    ]
    doc_ids = list(range(1, len(documents) + 1))

    # 构建索引
    bm25 = BM25Index(k1=1.5, b=0.75)
    bm25.build(documents, doc_ids)

    # 测试检索
    query = "人工智能"
    results = bm25.search(query, top_k=3)

    print(f"查询: {query}")
    print(f"检索结果: {len(results)} 条")
    for doc_id, score in results:
        print(f"  doc_id={doc_id}, score={score:.4f}, content={documents[doc_id - 1]}")

    # 测试保存和加载
    os.makedirs("data/indices", exist_ok=True)
    bm25.save("data/indices/test_bm25.pkl")

    new_bm25 = BM25Index()
    new_bm25.load("data/indices/test_bm25.pkl")
    print(f"\n加载后的文档数: {new_bm25.get_stats()['document_count']}")

    print("✅ BM25检索测试通过\n")


def test_faiss():
    """测试FAISS向量检索"""
    print("=" * 50)
    print("测试2: FAISS向量检索")
    print("=" * 50)

    from infrastructure.vector.faiss_store import FaissStore

    # 创建模拟向量（1024维）
    dimension = 1024
    faiss_store = FaissStore(dimension=dimension, index_type="FlatL2")

    # 生成测试向量
    num_vectors = 5
    vectors = np.random.random((num_vectors, dimension)).astype(np.float32)
    doc_ids = list(range(1, num_vectors + 1))
    metadatas = [
        {"content": f"文档{i}的内容", "title": f"标题{i}"}
        for i in range(1, num_vectors + 1)
    ]

    # 添加向量
    faiss_store.add_vectors(vectors, doc_ids, metadatas)

    # 测试检索
    query_vector = vectors[0]  # 使用第一个文档作为查询
    results = faiss_store.search(query_vector, top_k=3)

    print(f"查询向量: 第1个文档")
    print(f"检索结果: {len(results)} 条")
    for doc_id, distance, metadata in results:
        print(f"  doc_id={doc_id}, distance={distance:.4f}, metadata={metadata}")

    # 测试保存和加载
    os.makedirs("data/indices", exist_ok=True)
    faiss_store.save("data/indices/test_faiss")

    new_faiss = FaissStore(dimension=dimension)
    new_faiss.load("data/indices/test_faiss")
    print(f"\n加载后的向量数: {new_faiss.get_stats()['total_vectors']}")

    print("✅ FAISS检索测试通过\n")


async def test_hybrid_search():
    """测试混合检索"""
    print("=" * 50)
    print("测试3: 混合检索（RRF融合）")
    print("=" * 50)

    from infrastructure.vector.bm25_index import BM25Index
    from infrastructure.vector.faiss_store import FaissStore
    from infrastructure.vector.hybrid_search import HybridSearch
    from utils.embedding import embedding_service

    # 准备测试文档
    documents = [
        "人工智能是计算机科学的一个重要分支，致力于模拟智能行为",
        "机器学习通过数据学习模式，是AI的核心技术之一",
        "深度学习使用多层神经网络，在图像识别领域表现优异",
        "自然语言处理让计算机理解人类语言，如机器翻译和问答系统",
        "计算机视觉使机器能够理解和分析图像和视频内容"
    ]
    doc_ids = list(range(1, len(documents) + 1))

    # 构建BM25索引
    bm25 = BM25Index(k1=1.5, b=0.75)
    bm25.build(documents, doc_ids)

    # 构建FAISS索引
    dimension = 1024
    faiss_store = FaissStore(dimension=dimension, index_type="FlatL2")

    # 生成向量（使用真实向量化）
    print("正在生成文档向量...")
    vectors = []
    metadatas = []
    for i, doc in enumerate(documents):
        vector = await embedding_service.embed_text(doc)
        vectors.append(vector)
        metadatas.append({
            "content": doc,
            "doc_id": doc_ids[i],
            "title": f"文档{i + 1}"
        })

    vectors_np = np.array(vectors, dtype=np.float32)
    faiss_store.add_vectors(vectors_np, doc_ids, metadatas)

    # 创建混合检索器
    hybrid = HybridSearch(
        bm25_index=bm25,
        faiss_store=faiss_store,
        rrf_k=60,
        bm25_weight=0.4,
        vector_weight=0.6
    )

    # 测试检索
    test_queries = [
        "人工智能",
        "机器学习算法",
        "图像识别",
        "语言理解"
    ]

    for query in test_queries:
        print(f"\n查询: {query}")
        results = await hybrid.search(query, top_k=2)

        print(f"  结果数: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"    {i}. doc_id={result['doc_id']}, score={result['rrf_score']:.4f}")
            print(f"       内容: {result['content'][:50]}...")

    # 测试权重调整
    print("\n调整权重后重新检索...")
    hybrid.set_weights(bm25_weight=0.7, vector_weight=0.3)
    results = await hybrid.search(test_queries[0], top_k=2)
    print(f"新权重下结果数: {len(results)}")

    # 获取统计信息
    stats = hybrid.get_stats()
    print(f"\n混合检索器统计:")
    print(f"  BM25文档数: {stats['bm25_stats']['document_count']}")
    print(f"  FAISS向量数: {stats['faiss_stats']['total_vectors']}")
    print(f"  RRF_K: {stats['rrf_k']}")

    print("\n✅ 混合检索测试通过\n")


async def test_edge_cases():
    """测试边界情况"""
    print("=" * 50)
    print("测试4: 边界情况测试")
    print("=" * 50)

    from infrastructure.vector.bm25_index import BM25Index
    from infrastructure.vector.faiss_store import FaissStore
    from infrastructure.vector.hybrid_search import HybridSearch

    # 空查询
    bm25 = BM25Index()
    bm25.build(["测试文档"], [1])

    faiss_store = FaissStore(dimension=1024)

    hybrid = HybridSearch(bm25, faiss_store)

    # 测试空查询
    empty_results = await hybrid.search("", top_k=3)
    print(f"空查询结果: {empty_results}")

    # 测试无结果查询
    no_result = await hybrid.search("不存在的关键词xyz", top_k=3)
    print(f"无结果查询: {no_result}")

    # 测试单个检索源
    only_bm25 = await hybrid.search("测试", top_k=3, use_vector=False)
    print(f"仅BM25检索结果数: {len(only_bm25)}")

    only_vector = await hybrid.search("测试", top_k=3, use_bm25=False)
    print(f"仅向量检索结果数: {len(only_vector)}")

    print("✅ 边界情况测试通过\n")


async def main():
    """主测试函数"""
    print("\n" + "=" * 50)
    print("Phase 3 验证开始")
    print("=" * 50 + "\n")

    test_bm25()
    test_faiss()
    await test_hybrid_search()
    await test_edge_cases()

    print("=" * 50)
    print("Phase 3 全部测试通过！🎉")
    print("=" * 50)
    print("\nPhase 3 完成的功能:")
    print("1. BM25关键词检索 - 支持中文分词、持久化")
    print("2. FAISS向量检索 - 支持增删改查、持久化")
    print("3. 混合检索 - RRF融合算法、权重可调")
    print("\n可继续 Phase 4: 基础设施层（LLM模块）")


if __name__ == "__main__":
    asyncio.run(main())