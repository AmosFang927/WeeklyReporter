# Google Cloud Run 优化版 Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn uvicorn[standard]

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PORT=8080
ENV WORKERS=1
ENV THREADS=8

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/rector/health || exit 1

# 启动命令 - 使用gunicorn + uvicorn ASGI配置
CMD exec gunicorn \
    --bind :$PORT \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 0 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    main:app 