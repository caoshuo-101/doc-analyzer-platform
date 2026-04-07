# 智能文档分析平台


      https://img.shields.io/badge/python-3.10+-blue.svg

      https://img.shields.io/badge/FastAPI-0.115.0-green.svg

      https://img.shields.io/badge/LangChain-0.3.0-orange.svg

      https://img.shields.io/badge/license-MIT-red.svg


      基于 LangChain 的智能文档分析平台 | 混合检索 + 智能路由 + 多模型切换


      快速开始 • 功能特性 • API文档 • 部署指南
    

## 📖 项目简介

智能文档分析平台是一个基于 LangChain 构建的文档问答系统。它能够自动解析、向量化用户上传的文档（PDF、DOCX、TXT），并通过混合检索（BM25关键词检索 + FAISS向量检索）和智能路由技术，为用户提供精准、高效的文档问答体验。

## 核心亮点

- 🚀 开箱即用：提供完整的Web界面，无需编写代码即可使用

- 🧠 智能路由：自动识别问题类型（闲聊/文档问答/混合问答/通用问答）

- 🔍 混合检索：RRF算法融合关键词检索和语义检索

- 🤖 多模型支持：通义千问主模型 + DeepSeek备用模型，自动故障切换

- 💬 多轮对话：支持对话记忆和指代消解（"它"、"那个"等）

- 📁 批量上传：支持拖拽上传，批量处理文档

## 🎯 功能特性

### 文档管理

|功能|说明|
|---|---|
|文档上传|支持 PDF、DOCX、TXT 格式，自动解析和分块|
|批量上传|拖拽或批量选择，自动处理|
|文档检索|基于内容的语义检索和关键词检索|
### 智能问答

|模式|说明|示例问题|
|---|---|---|
|💬 闲聊|日常对话|"你好"、"谢谢"|
|📄 文档问答|严格基于文档回答|"文档里说了什么？"|
|🔀 混合问答|文档+模型理解|"结合文档，你怎么看？"|
|🧠 通用知识|模型自身知识|"什么是人工智能？"|
## 技术架构

```text
用户界面 (Web) → API层 → 服务层 → 基础设施层
                    ↓         ↓           ↓
                 路由服务   检索服务    LLM网关/向量库
```

## 📁 项目结构

```text
doc-analyzer-platform/
├── app.py                 # FastAPI应用入口
├── web/
│   └── index.html        # Web聊天界面
├── api/                  # API接口层
│   ├── routes/          # 路由（知识库/文档/聊天）
│   └── schemas/         # 请求/响应模型
├── core/                # 核心业务层
│   ├── models/          # 数据模型
│   ├── repositories/    # 数据访问
│   └── services/        # 业务服务（路由/检索/文档/对话）
├── infrastructure/      # 基础设施层
│   ├── llm/            # LLM模块（千问/DeepSeek/网关）
│   ├── vector/         # 检索模块（BM25/FAISS/混合检索）
│   └── storage/        # 文件存储
├── config/             # 配置文件
│   ├── settings.py     # 全局配置
│   ├── routing.yaml    # 路由规则
│   ├── search.yaml     # 检索参数
│   └── prompts/        # 提示词模板
├── utils/              # 工具函数
├── data/               # 数据目录（运行时生成）
└── tests/              # 单元测试和集成测试
```

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本

- pip 或 uv 包管理器

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/doc-analyzer-platform.git
cd doc-analyzer-platform
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填写 API Keys
```

需要配置的 API Key：

|变量|说明|获取地址|
|---|---|---|
|LLM_API_KEY|通义千问 API Key|阿里云百炼|
|BACKUP_LLM_API_KEY|DeepSeek API Key|DeepSeek平台|
### 5. 启动服务

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问界面

打开浏览器访问：http://localhost:8000

## 📚 使用指南

### 第一步：上传文档

- 在左侧"上传文档"区域点击或拖拽文件

- 支持 PDF、DOCX、TXT 格式

- 系统自动解析、分块、向量化

### 第二步：开始问答

在聊天框输入问题，例如：

|问题类型|示例|
|---|---|
|文档问答|"根据文档，首次使用扫地机器人要做什么？"|
|混合问答|"结合文档内容，你怎么看充电建议？"|
|闲聊|"你好，你能做什么？"|
|通用知识|"什么是机器学习？"|
### 第三步：多轮对话

系统会自动记住对话历史，支持：

- 指代消解："它支持什么格式？"

- 追问："那第二个步骤呢？"

- 清空对话：刷新页面即可

## 🔧 配置说明

### 路由规则 (config/routing.yaml)

```yaml
routing:
  chitchat:      # 闲聊
    keywords: ["你好", "谢谢", "再见"]
    priority: 1
  hybrid:        # 混合问答
    keywords: ["结合", "理解", "你怎么看"]
    priority: 2
  document:      # 文档问答
    keywords: ["文档", "根据", "总结"]
    priority: 3
  general:       # 通用问答
    priority: 4
```

### 检索参数 (config/search.yaml)

```yaml
search:
  bm25:
    k1: 1.5      # 词频饱和度
    b: 0.75      # 长度归一化
  fusion:
    method: "rrf"
    rrf_k: 60
    final_top_k: 3
  weights:
    bm25: 0.4
    vector: 0.6
```

### 提示词模板 (config/prompts/)

|文件|场景|温度|
|---|---|---|
|chitchat.yaml|闲聊|0.8|
|document_qa.yaml|文档问答|0.3|
|hybrid_qa.yaml|混合问答|0.5|
|general_qa.yaml|通用问答|0.7|
## 📊 性能特性

|特性|说明|
|---|---|
|混合检索|RRF 算法融合 BM25 + FAISS|
|故障切换|主模型失败自动切换备用模型|
|连接池|数据库连接池管理|
|流式响应|SSE 流式输出，降低首字延迟|
|热加载|修改 YAML 配置无需重启|
## 🛠️ 技术栈

|类别|技术|
|---|---|
|Web框架|FastAPI + Uvicorn|
|LLM框架|LangChain|
|向量检索|FAISS|
|关键词检索|BM25Okapi (rank_bm25)|
|中文分词        |jieba|
|数据库        |SQLite + SQLAlchemy (异步)|
|配置管理        |Pydantic Settings|
|文档解析        unstructured / pypdf / python-docx|unstructured / pypdf / python-docx|
> （注：文档部分内容可能由 AI 生成）