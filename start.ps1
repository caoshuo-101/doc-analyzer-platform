# start.ps1 - Windows启动脚本

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "企业级智能文档分析平台" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 检查虚拟环境
if (-not (Test-Path ".venv")) {
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    python -m venv .venv
}

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 安装依赖
Write-Host "安装依赖..." -ForegroundColor Yellow
pip install -r requirements.txt

# 检查.env文件
if (-not (Test-Path ".env")) {
    Write-Host "请先配置 .env 文件" -ForegroundColor Red
    Copy-Item .env.example .env
    Write-Host "已创建 .env 文件，请填写 API Keys" -ForegroundColor Yellow
    exit 1
}

# 启动服务
Write-Host "启动服务..." -ForegroundColor Green
uvicorn app:app --reload --host 0.0.0.0 --port 8000