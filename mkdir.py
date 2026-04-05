import os


def create_project_structure():
    """根据开发文档创建企业级智能文档分析平台的项目目录和文件"""

    # 项目根目录
    base_dir = "doc-analyzer-platform"

    # 定义所有需要创建的目录
    directories = [
        f"{base_dir}/config/prompts",
        f"{base_dir}/core/models",
        f"{base_dir}/core/repositories",
        f"{base_dir}/core/services",
        f"{base_dir}/infrastructure/llm",
        f"{base_dir}/infrastructure/vector",
        f"{base_dir}/infrastructure/storage",
        f"{base_dir}/infrastructure/database",
        f"{base_dir}/api/routes",
        f"{base_dir}/api/schemas",
        f"{base_dir}/utils",
        f"{base_dir}/tests/unit",
        f"{base_dir}/tests/integration",
        f"{base_dir}/data/documents",
        f"{base_dir}/data/indices",
    ]

    # 定义所有需要创建的文件（包含路径）
    files = [
        f"{base_dir}/app.py",
        f"{base_dir}/.env.example",
        f"{base_dir}/.gitignore",
        f"{base_dir}/README.md",
        f"{base_dir}/requirements.txt",
        f"{base_dir}/config/__init__.py",
        f"{base_dir}/config/settings.py",
        f"{base_dir}/config/routing.yaml",
        f"{base_dir}/config/search.yaml",
        f"{base_dir}/config/prompts/__init__.py",
        f"{base_dir}/config/prompts/document_qa.yaml",
        f"{base_dir}/config/prompts/general_qa.yaml",
        f"{base_dir}/config/prompts/chitchat.yaml",
        f"{base_dir}/config/prompts/hybrid_qa.yaml",
        f"{base_dir}/core/__init__.py",
        f"{base_dir}/core/models/__init__.py",
        f"{base_dir}/core/models/base.py",
        f"{base_dir}/core/models/knowledge_base.py",
        f"{base_dir}/core/models/document.py",
        f"{base_dir}/core/models/conversation.py",
        f"{base_dir}/core/repositories/__init__.py",
        f"{base_dir}/core/repositories/base.py",
        f"{base_dir}/core/repositories/knowledge_base_repo.py",
        f"{base_dir}/core/repositories/document_repo.py",
        f"{base_dir}/core/services/__init__.py",
        f"{base_dir}/core/services/router_service.py",
        f"{base_dir}/core/services/search_service.py",
        f"{base_dir}/core/services/document_service.py",
        f"{base_dir}/core/services/conversation_service.py",
        f"{base_dir}/infrastructure/__init__.py",
        f"{base_dir}/infrastructure/llm/__init__.py",
        f"{base_dir}/infrastructure/llm/base.py",
        f"{base_dir}/infrastructure/llm/qwen_provider.py",
        f"{base_dir}/infrastructure/llm/deepseek_provider.py",
        f"{base_dir}/infrastructure/llm/gateway.py",
        f"{base_dir}/infrastructure/vector/__init__.py",
        f"{base_dir}/infrastructure/vector/faiss_store.py",
        f"{base_dir}/infrastructure/vector/bm25_index.py",
        f"{base_dir}/infrastructure/vector/hybrid_search.py",
        f"{base_dir}/infrastructure/storage/__init__.py",
        f"{base_dir}/infrastructure/storage/local_storage.py",
        f"{base_dir}/infrastructure/database/__init__.py",
        f"{base_dir}/infrastructure/database/connection.py",
        f"{base_dir}/infrastructure/database/init.sql",
        f"{base_dir}/api/__init__.py",
        f"{base_dir}/api/dependencies.py",
        f"{base_dir}/api/routes/__init__.py",
        f"{base_dir}/api/routes/documents.py",
        f"{base_dir}/api/routes/chat.py",
        f"{base_dir}/api/routes/knowledge_bases.py",
        f"{base_dir}/api/schemas/__init__.py",
        f"{base_dir}/api/schemas/common.py",
        f"{base_dir}/api/schemas/document.py",
        f"{base_dir}/api/schemas/chat.py",
        f"{base_dir}/api/schemas/knowledge_base.py",
        f"{base_dir}/utils/__init__.py",
        f"{base_dir}/utils/text_splitter.py",
        f"{base_dir}/utils/embedding.py",
        f"{base_dir}/utils/prompt_loader.py",
        f"{base_dir}/utils/logger.py",
        f"{base_dir}/tests/__init__.py",
        f"{base_dir}/tests/conftest.py",
        f"{base_dir}/tests/unit/test_router_service.py",
        f"{base_dir}/tests/unit/test_search_service.py",
        f"{base_dir}/tests/unit/test_document_service.py",
        f"{base_dir}/tests/integration/test_api_documents.py",
        f"{base_dir}/tests/integration/test_api_chat.py",
        f"{base_dir}/tests/integration/test_llm_gateway.py",
    ]

    # 创建目录
    for dir_path in directories:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ 创建目录: {dir_path}/")
        except Exception as e:
            print(f"❌ 创建目录失败 {dir_path}: {e}")

    # 创建文件
    for file_path in files:
        try:
            # 确保文件所在目录存在（对于深层文件，上面已创建目录，但保险起见）
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 如果文件不存在，创建空文件
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    # 为特定文件添加初始内容
                    if file_path.endswith(".gitignore"):
                        f.write(
                            "# Python\n__pycache__/\n*.pyc\n.env\n/data/\n*.db\n*.faiss\n*.meta\n\n# IDE\n.vscode/\n.idea/\n")
                    elif file_path.endswith("README.md"):
                        f.write(
                            "# 企业级智能文档分析平台\n\n基于 LangChain 的智能文档分析平台，支持混合检索、智能路由和多模型切换。\n\n## 快速开始\n\n1. 复制 .env.example 为 .env 并配置API密钥\n2. 安装依赖: pip install -r requirements.txt\n3. 运行: uvicorn app:app --reload\n")
                    elif file_path.endswith("requirements.txt"):
                        f.write(
                            "# Web框架\nfastapi==0.115.0\nuvicorn[standard]==0.30.0\n\n# LLM框架\nlangchain==0.3.0\nlangchain-community==0.3.0\nlangchain-openai==0.2.0\n\n# 向量检索\nfaiss-cpu==1.8.0\nrank-bm25==0.2.2\njieba==0.42.1\nnumpy==1.26.0\n\n# 文档解析\nlangchain-community[pdf]==0.3.0\npython-docx==1.1.0\nunstructured==0.15.0\n\n# 数据库\nsqlalchemy==2.0.35\naiosqlite==0.20.0\n\n# 配置与工具\npydantic==2.9.0\npydantic-settings==2.5.0\npython-dotenv==1.0.1\npyyaml==6.0.2\n\n# 异步支持\naiofiles==24.1.0\nhttpx==0.27.0\n\n# 测试\npytest==8.3.0\npytest-asyncio==0.24.0\n")
                    elif file_path.endswith(".env.example"):
                        f.write(
                            "# 应用配置\nAPP_NAME=Document Analysis Platform\nDEBUG=false\nAPI_PREFIX=/api\n\n# 数据库\nDATABASE_URL=sqlite+aiosqlite:///./data/database.db\n\n# 主模型配置(通义千问)\nLLM_PROVIDER=qwen\nLLM_MODEL=qwen-plus\nLLM_API_KEY=your_qwen_api_key_here\nLLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1\n\n# 备用模型配置(DeepSeek)\nBACKUP_LLM_PROVIDER=deepseek\nBACKUP_LLM_MODEL=deepseek-chat\nBACKUP_LLM_API_KEY=your_deepseek_api_key_here\nBACKUP_LLM_BASE_URL=https://api.deepseek.com/v1\n\n# Embedding配置\nEMBEDDING_MODEL=text-embedding-v3\nEMBEDDING_DIMENSION=1024\n\n# 各场景Temperature配置\nTEMPERATURE_DOCUMENT_QA=0.3\nTEMPERATURE_GENERAL_QA=0.7\nTEMPERATURE_CHITCHAT=0.8\nTEMPERATURE_HYBRID=0.5\n\n# 检索配置\nDEFAULT_TOP_K=3\nRRF_K=60\n\n# 重试配置\nRETRY_TIMES=3\nRETRY_BACKOFF=1.0\n\n# 性能配置\nMAX_CONCURRENT_USERS=10\nREQUEST_TIMEOUT=30\n")
                    else:
                        # 对于Python文件，添加标准文件头注释
                        if file_path.endswith(".py") and not file_path.endswith("__init__.py"):
                            f.write(
                                f'"""\n{os.path.basename(file_path)} - 模块说明\n\n根据开发文档实现相应功能\n"""\n\n')
                        else:
                            pass  # 创建空文件
            print(f"✅ 创建文件: {file_path}")
        except Exception as e:
            print(f"❌ 创建文件失败 {file_path}: {e}")

    print("\n🎉 项目结构创建完成！")
    print(f"项目根目录: {os.path.abspath(base_dir)}")
    print("\n下一步操作:")
    print("1. cd doc-analyzer-platform")
    print("2. python -m venv venv")
    print("3. 复制 .env.example 为 .env 并配置API密钥")
    print("4. pip install -r requirements.txt")
    print("5. uvicorn app:app --reload")


if __name__ == "__main__":
    create_project_structure()