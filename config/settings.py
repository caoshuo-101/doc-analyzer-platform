"""
settings.py - 全局配置管理

使用 Pydantic Settings 实现类型安全的配置管理
支持从 .env 文件加载环境变量
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""

    # ========== 应用配置 ==========
    APP_NAME: str = Field(default="Document Analysis Platform", description="应用名称")
    DEBUG: bool = Field(default=False, description="调试模式")
    API_PREFIX: str = Field(default="/api", description="API路由前缀")

    # ========== 数据库配置 ==========
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/database.db",
        description="数据库连接URL"
    )

    # ========== 主模型配置(通义千问) ==========
    LLM_PROVIDER: str = Field(default="qwen", description="LLM提供商")
    LLM_MODEL: str = Field(default="qwen-plus", description="主模型名称")
    LLM_API_KEY: str = Field(..., description="主模型API密钥")  # ... 表示必填
    LLM_BASE_URL: Optional[str] = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="主模型API基础URL"
    )

    # ========== 备用模型配置(DeepSeek) ==========
    BACKUP_LLM_PROVIDER: str = Field(default="deepseek", description="备用LLM提供商")
    BACKUP_LLM_MODEL: str = Field(default="deepseek-chat", description="备用模型名称")
    BACKUP_LLM_API_KEY: str = Field(..., description="备用模型API密钥")
    BACKUP_LLM_BASE_URL: Optional[str] = Field(
        default="https://api.deepseek.com/v1",
        description="备用模型API基础URL"
    )

    # ========== Embedding配置 ==========
    EMBEDDING_MODEL: str = Field(default="text-embedding-v3", description="向量化模型")
    EMBEDDING_DIMENSION: int = Field(default=1024, description="向量维度")

    # ========== 各场景Temperature配置 ==========
    TEMPERATURE_DOCUMENT_QA: float = Field(default=0.3, description="文档问答温度")
    TEMPERATURE_GENERAL_QA: float = Field(default=0.7, description="通用问答温度")
    TEMPERATURE_CHITCHAT: float = Field(default=0.8, description="闲聊温度")
    TEMPERATURE_HYBRID: float = Field(default=0.5, description="混合问答温度")

    # ========== 检索配置 ==========
    DEFAULT_TOP_K: int = Field(default=3, description="默认返回Top-K文档数")
    RRF_K: int = Field(default=60, description="RRF融合算法参数")

    # ========== 重试配置 ==========
    RETRY_TIMES: int = Field(default=3, description="重试次数")
    RETRY_BACKOFF: float = Field(default=1.0, description="重试退避时间(秒)")

    # ========== 性能配置 ==========
    MAX_CONCURRENT_USERS: int = Field(default=10, description="最大并发用户数")
    REQUEST_TIMEOUT: int = Field(default=30, description="请求超时时间(秒)")

    class Config:
        """Pydantic配置"""
        env_file = ".env"  # 从.env文件加载
        env_file_encoding = "utf-8"
        case_sensitive = True  # 区分大小写

    def get_temperature_for_scene(self, scene: str) -> float:
        """
        根据场景返回对应的temperature值

        参数:
            scene: 场景名称 (document/general/chitchat/hybrid)

        返回:
            float: 对应的temperature值
        """
        mapping = {
            "document": self.TEMPERATURE_DOCUMENT_QA,
            "general": self.TEMPERATURE_GENERAL_QA,
            "chitchat": self.TEMPERATURE_CHITCHAT,
            "hybrid": self.TEMPERATURE_HYBRID
        }
        return mapping.get(scene, self.TEMPERATURE_GENERAL_QA)

    def validate(self) -> bool:
        """
        验证必填配置项

        返回:
            bool: 验证是否通过
        """
        errors = []

        if not self.LLM_API_KEY or self.LLM_API_KEY == "your_qwen_api_key_here":
            errors.append("LLM_API_KEY 未配置或为默认值")

        if not self.BACKUP_LLM_API_KEY or self.BACKUP_LLM_API_KEY == "your_deepseek_api_key_here":
            errors.append("BACKUP_LLM_API_KEY 未配置或为默认值")

        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False

        print("配置验证通过")
        return True


# 创建全局配置实例
settings = Settings()