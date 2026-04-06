"""
app.py - FastAPI应用入口

创建FastAPI应用，注册路由，配置中间件
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from api.routes import knowledge_bases, documents, chat
from infrastructure.database.connection import init_db, close_db
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    logger.info("应用启动中...")

    # 初始化数据库
    await init_db()

    # 确保数据目录存在
    import os
    os.makedirs("data/documents", exist_ok=True)
    os.makedirs("data/indices", exist_ok=True)
    os.makedirs("web", exist_ok=True)

    logger.info(f"应用启动完成，环境: {'调试' if settings.DEBUG else '生产'}")

    yield

    # 关闭时执行
    logger.info("应用关闭中...")
    await close_db()
    logger.info("应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="企业级智能文档分析平台 - 基于LangChain的文档问答系统",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(knowledge_bases.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)
app.include_router(chat.router, prefix=settings.API_PREFIX)

# 挂载静态文件目录（Web界面）
app.mount("/web", StaticFiles(directory="web", html=True), name="web")


@app.get("/")
async def root():
    """根路径 - 重定向到Web界面"""
    return RedirectResponse(url="/web/index.html")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )