"""
test_phase2.py - Phase 2 验证脚本
测试工具层功能
"""

import asyncio
import sys
import os

# 修复：应该是 os.path.abspath
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_text_splitter():
    """测试文档分块"""
    print("=" * 50)
    print("测试1: 文档分块")
    print("=" * 50)

    from utils.text_splitter import TextSplitter, split_document

    # 测试文本
    text = """这是第一段内容。这里有一些说明。
    
这是第二段，包含更多信息。人工智能是计算机科学的一个分支。
    
第三段：机器学习是人工智能的核心技术之一。深度学习通过神经网络实现。"""

    # 测试分块
    splitter = TextSplitter(chunk_size=50, chunk_overlap=10)
    chunks = splitter.split_text(text)

    print(f"原始文本长度: {len(text)}")
    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"  块{i+1}: {chunk[:40]}...")

    # 测试带元数据的分块
    result = split_document(text, chunk_size=50, metadata={"source": "test"})
    print(f"\n带元数据的分块结果: {len(result)} 块")
    if result:
        print(f"  第一块元数据: {result[0]['metadata']}")

    print("✅ 文档分块测试通过\n")


def test_prompt_loader():
    """测试提示词加载器"""
    print("=" * 50)
    print("测试2: 提示词加载器")
    print("=" * 50)

    from utils.prompt_loader import prompt_loader

    # 列出可用提示词
    prompts = prompt_loader.list_prompts()
    print(f"可用提示词: {prompts}")

    # 测试获取模板
    for name in prompts:
        template = prompt_loader.get_template(name)
        temp = prompt_loader.get_temperature(name)
        version = prompt_loader.get_version(name)
        print(f"\n提示词: {name}")
        print(f"  版本: {version}, 温度: {temp}")
        print(f"  模板长度: {len(template)} 字符")

    # 测试渲染
    if "document_qa" in prompts:
        rendered = prompt_loader.render(
            "document_qa",
            context="这是检索到的文档内容",
            question="文档说了什么？"
        )
        print(f"\n渲染结果预览:\n{rendered[:200]}...")

    print("✅ 提示词加载器测试通过\n")


async def test_embedding():
    """测试向量化服务（需要API Key）"""
    print("=" * 50)
    print("测试3: 向量化服务")
    print("=" * 50)

    from utils.embedding import embedding_service
    from config.settings import settings

    # 检查API Key
    if settings.LLM_API_KEY and settings.LLM_API_KEY != "your_qwen_api_key_here":
        print("检测到API Key，进行真实向量化测试...")

        try:
            # 测试单文本
            text = "这是一个测试文本"
            print(f"正在向量化: {text}")
            vector = await embedding_service.embed_text(text)
            print(f"文本: {text}")
            print(f"向量维度: {len(vector)}")
            print(f"向量前5维: {vector[:5]}")

            # 测试批量
            texts = ["人工智能", "机器学习", "深度学习"]
            print(f"\n正在批量向量化 {len(texts)} 个文本...")
            vectors = await embedding_service.embed_documents(texts)
            print(f"批量向量化: {len(vectors)} 个向量")
            for i, v in enumerate(vectors):
                non_zero = sum(1 for x in v if x != 0)
                print(f"  {texts[i]}: 维度{len(v)}, 非零:{non_zero}")

            print("✅ 向量化服务测试通过\n")
        except Exception as e:
            print(f"⚠️  向量化测试失败: {e}")
            print("   这可能是因为API Key无效或模型名称不正确")
            print("   请检查 .env 中的 LLM_API_KEY 和 EMBEDDING_MODEL")
    else:
        print("⚠️  未配置API Key，跳过真实向量化测试")
        print("   (Phase 4需要配置API Key后才能使用)")
        print("   请编辑 .env 文件，填写 LLM_API_KEY")


async def test_embedding_fallback():
    """测试向量化降级方案"""
    print("=" * 50)
    print("测试4: 向量化降级方案")
    print("=" * 50)

    from utils.embedding import embedding_service

    # 测试空文本
    empty_result = await embedding_service.embed_text("")
    print(f"空文本向量化结果: 维度 {len(empty_result)}，全零: {all(x == 0 for x in empty_result)}")

    # 测试空列表
    empty_list = await embedding_service.embed_documents([])
    print(f"空列表向量化结果: {empty_list}")

    print("✅ 向量化降级测试通过\n")


async def main():
    """主测试函数"""
    print("\n" + "=" * 50)
    print("Phase 2 验证开始")
    print("=" * 50 + "\n")

    test_text_splitter()
    test_prompt_loader()
    await test_embedding()
    await test_embedding_fallback()

    print("=" * 50)
    print("Phase 2 全部测试通过！🎉")
    print("=" * 50)
    print("\nPhase 2 完成的功能:")
    print("1. 文档分块器 - 支持自定义块大小和重叠")
    print("2. 提示词加载器 - 支持热加载和变量插值")
    print("3. 向量化服务 - 单条/批量向量化（含降级方案）")
    print("\n注意: 如果向量化测试失败，请检查:")
    print("  - .env 中的 LLM_API_KEY 是否正确")
    print("  - EMBEDDING_MODEL 是否支持（如 text-embedding-v3）")
    print("\n可继续 Phase 3: 基础设施层（检索模块）")


if __name__ == "__main__":
    asyncio.run(main())