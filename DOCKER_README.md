# WeeklyReporter Docker 部署指南

## 🐋 Docker 容器化部署

### 快速开始

#### 1. 构建镜像
```bash
docker build -t weeklyreporter .
```

#### 2. 运行容器（单次执行）
```bash
docker run --rm -v $(pwd)/output:/app/output weeklyreporter
```

#### 3. 使用 Docker Compose（推荐）
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f weeklyreporter

# 停止服务
docker-compose down
```

### 🔧 配置说明

#### 环境变量
可以通过环境变量覆盖配置：

```bash
docker run -e INVOLVE_ASIA_API_SECRET="your_secret" \
           -e PREFERRED_CURRENCY="USD" \
           weeklyreporter
```

#### 卷映射
- `./output:/app/output` - 输出文件目录
- `./temp:/app/temp` - 临时文件目录

### 📅 定时运行

#### 方法1：使用 cron（宿主机）
```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每日中午12点）
0 12 * * * docker run --rm -v $(pwd)/output:/app/output weeklyreporter
```

#### 方法2：使用调度器容器
```bash
# 启动调度器服务
docker-compose up -d weeklyreporter-scheduler
```

#### 方法3：修改 Dockerfile 使用内置调度器
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# 设置 cron 任务
RUN echo "0 12 * * * cd /app && python main.py" > /etc/cron.d/weeklyreporter
RUN chmod 0644 /etc/cron.d/weeklyreporter
RUN crontab /etc/cron.d/weeklyreporter

CMD ["cron", "-f"]
```

### 🚀 部署选项

#### 开发环境
```bash
# 交互式运行（调试用）
docker run -it --rm -v $(pwd):/app weeklyreporter bash
```

#### 生产环境
```bash
# 后台运行（保持容器活跃）
docker run -d --name weeklyreporter \
           --restart unless-stopped \
           -v $(pwd)/output:/app/output \
           weeklyreporter \
           python -c "import time; time.sleep(86400)"

# 手动触发执行
docker exec weeklyreporter python main.py
```

### 🔍 监控和日志

#### 查看容器状态
```bash
docker ps
docker stats weeklyreporter
```

#### 查看日志
```bash
# 实时日志
docker logs -f weeklyreporter

# 最近100行日志
docker logs --tail 100 weeklyreporter
```

#### 进入容器调试
```bash
docker exec -it weeklyreporter bash
```

### 🐛 故障排除

#### 权限问题
```bash
# 确保输出目录有写权限
chmod 755 output temp
```

#### 时区问题
```bash
# 在 docker-compose.yml 中设置时区
environment:
  - TZ=Asia/Shanghai
```

#### 网络问题
```bash
# 测试 API 连通性
docker run --rm weeklyreporter curl -I https://api.involve.asia
```

### 📦 镜像优化

#### 多阶段构建（可选）
```dockerfile
# 构建阶段
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "main.py"]
```

### 🔐 安全建议

1. **不要在镜像中硬编码敏感信息**
2. **使用环境变量传递配置**
3. **定期更新基础镜像**
4. **使用非 root 用户运行（可选）**

```dockerfile
# 创建非 root 用户
RUN useradd -m -s /bin/bash appuser
USER appuser
``` 