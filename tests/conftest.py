"""
conftest.py - pytest配置文件

提供测试夹具和全局配置
"""

import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.connection import init_db, close_db, AsyncSessionLocal, get_db
from app import app


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """初始化测试数据库"""
    await init_db()
    yield
    await close_db()


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    """提供HTTP客户端"""
    from httpx import AsyncClient, ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client