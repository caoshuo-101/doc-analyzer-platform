"""
test_phase1.py - Phase 1 验证脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_settings():
    """测试配置加载"""
    print("=" * 50)
    print("测试1: 配置加载")
    print("=" * 50)

    from config.settings import settings

    print(f"应用名称: {settings.APP_NAME}")
    print(f"调试模式: {settings.DEBUG}")
    print(f"API前缀: {settings.API_PREFIX}")
    print(f"数据库URL: {settings.DATABASE_URL}")
    print(f"主模型: {settings.LLM_MODEL}")
    print(f"备用模型: {settings.BACKUP_LLM_MODEL}")

    # 测试temperature获取
    print(f"\n文档问答temperature: {settings.get_temperature_for_scene('document')}")
    print(f"闲聊temperature: {settings.get_temperature_for_scene('chitchat')}")

    # 验证配置（会显示缺少API Key）
    settings.validate()

    print("✅ 配置测试通过\n")


def test_logger():
    """测试日志"""
    print("=" * 50)
    print("测试2: 日志模块")
    print("=" * 50)

    from utils.logger import get_logger, default_logger

    logger = get_logger(__name__)
    logger.info("这是一条INFO日志")
    logger.warning("这是一条WARNING日志")
    logger.error("这是一条ERROR日志")

    print("✅ 日志测试通过\n")


async def test_database():
    """测试数据库连接"""
    print("=" * 50)
    print("测试3: 数据库连接")
    print("=" * 50)

    from infrastructure.database.connection import init_db, close_db, get_db

    # 确保data目录存在
    os.makedirs("data", exist_ok=True)

    # 初始化数据库
    await init_db()

    # 测试会话
    async for session in get_db():
        print(f"数据库会话: {session}")
        break

    await close_db()

    print("✅ 数据库测试通过\n")


async def test_models():
    """测试数据模型"""
    print("=" * 50)
    print("测试4: 数据模型")
    print("=" * 50)

    from core.models.knowledge_base import KnowledgeBase
    from core.models.document import Document
    from core.models.conversation import Conversation

    # 创建测试实例
    kb = KnowledgeBase(name="测试知识库", description="这是一个测试")
    print(f"知识库实例: {kb}")
    print(f"转字典: {kb.to_dict()}")

    doc = Document(
        title="测试文档",
        file_name="test.pdf",
        file_path="/data/test.pdf",
        knowledge_base_id=1
    )
    print(f"文档实例: {doc}")

    conv = Conversation(
        session_id="test_session",
        knowledge_base_id=1,
        role="user",
        content="你好"
    )
    print(f"对话实例: {conv}")

    print("✅ 数据模型测试通过\n")


async def main():
    """主测试函数"""
    print("\n" + "=" * 50)
    print("Phase 1 验证开始")
    print("=" * 50 + "\n")

    test_settings()
    test_logger()
    await test_database()
    await test_models()

    print("=" * 50)
    print("Phase 1 全部测试通过！🎉")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())