FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个项目
COPY . .

# 设置权限
RUN chmod +x /app/postback_system/reporter_agent/main.py

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "-m", "postback_system.reporter_agent.main", "api", "--host", "0.0.0.0", "--port", "8080"] 