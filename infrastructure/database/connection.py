"""
connection.py - 数据库连接管理

管理SQLAlchemy异步数据库连接
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from config.settings import settings

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # DEBUG模式下打印SQL
    future=True
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 创建ORM基类
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话依赖注入

    用于FastAPI的Depends，每个请求获取一个数据库会话

    使用方式:
        @app.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库，创建所有表"""
    # 导入所有模型以确保它们被注册
    from core.models import knowledge_base, document, conversation

    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    print("数据库初始化完成")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    print("数据库连接已关闭")