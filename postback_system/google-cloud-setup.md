# 🚀 ByteC Postback 系统 - Google Cloud 完整部署方案

## 🎯 方案概述

**目标域名：** `https://bytec-postback.run.app/involve/event`  
**架构：** 本地开发 → Docker 容器化 → Google Cloud Run 部署  
**成本：** 完全免费（每月200万请求内）

## 📁 项目结构

```
postback_system/
├── Dockerfile.cloudrun          # Google Cloud Run 优化版
├── cloudbuild.yaml             # 自动化CI/CD配置  
├── google-cloud-config/        # GCP配置文件
│   ├── app.yaml               # App Engine配置（备用）
│   ├── cloudrun-service.yaml  # Cloud Run服务配置
│   └── load-balancer.yaml     # 负载均衡器配置
├── scripts/                   # 部署脚本
│   ├── local-tunnel.sh        # 本地公网暴露
│   ├── deploy-local.sh        # 本地Docker部署
│   └── deploy-cloudrun.sh     # Cloud Run部署
└── .env.cloudrun             # Cloud Run环境变量
```

## 🌟 第一阶段：本地Docker化部署

### 1.1 创建Cloud Run优化的Dockerfile

```dockerfile
# Google Cloud Run优化版本
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PORT=8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/postback/health || exit 1

# 启动命令
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
```

### 1.2 创建本地部署脚本

```bash
#!/bin/bash
# scripts/deploy-local.sh

echo "🚀 启动 ByteC Postback 本地部署..."

# 构建Docker镜像
docker build -f Dockerfile.cloudrun -t bytec-postback:local .

# 停止现有容器
docker stop bytec-postback 2>/dev/null || true
docker rm bytec-postback 2>/dev/null || true

# 启动容器
docker run -d \
  --name bytec-postback \
  --restart unless-stopped \
  -p 8080:8080 \
  -e DATABASE_URL="postgresql+asyncpg://postback:postback123@host.docker.internal:5432/postback_db" \
  -e DEBUG=true \
  -e LOG_LEVEL=INFO \
  bytec-postback:local

echo "✅ 本地服务已启动: http://localhost:8080"
echo "🔍 健康检查: http://localhost:8080/postback/health"
echo "📡 Postback端点: http://localhost:8080/postback/involve/event"
```

### 1.3 公网暴露方案

```bash
#!/bin/bash
# scripts/local-tunnel.sh

echo "🌐 创建公网隧道..."

# 方案A: Google Cloud SDK 隧道（推荐）
if command -v gcloud &> /dev/null; then
    echo "使用 Google Cloud SDK 隧道..."
    gcloud compute ssh --zone=asia-southeast1-a tunnel-instance \
        --ssh-flag="-L 8080:localhost:8080" \
        --ssh-flag="-N" &
    
    echo "✅ 隧道地址: https://bytec-postback-dev.run.app"
    
# 方案B: ngrok 作为备用
elif command -v ngrok &> /dev/null; then
    echo "使用 ngrok 隧道..."
    ngrok http 8080 --subdomain=bytec-postback &
    
    echo "✅ 隧道地址: https://bytec-postback.ngrok.io"
    
# 方案C: Cloudflare Tunnel
else
    echo "安装 Cloudflare Tunnel..."
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i cloudflared-linux-amd64.deb
    
    cloudflare tunnel --url localhost:8080 --name bytec-postback
fi

echo "🔗 测试命令:"
echo "curl 'https://your-tunnel-url/postback/involve/event?conversion_id=test123&ts_token=default-ts-token'"
```

## 🚀 第二阶段：Google Cloud Run 部署

### 2.1 环境准备

```bash
# 安装Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 登录和项目设置
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 启用必要的API
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    container.googleapis.com
```

### 2.2 Cloud Run服务配置

```yaml
# google-cloud-config/cloudrun-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: bytec-postback
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/ingress-status: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        autoscaling.knative.dev/minScale: "0"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/memory: "512Mi"
        run.googleapis.com/cpu: "1000m"
    spec:
      serviceAccountName: bytec-postback-sa
      containers:
      - image: gcr.io/YOUR_PROJECT_ID/bytec-postback:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              key: database-url
              name: bytec-postback-secrets
        - name: DEBUG
          value: "false"
        - name: LOG_LEVEL  
          value: "INFO"
        resources:
          limits:
            cpu: 1000m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /postback/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /postback/health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 2.3 自动化部署脚本

```bash
#!/bin/bash
# scripts/deploy-cloudrun.sh

PROJECT_ID="your-project-id"
SERVICE_NAME="bytec-postback"
REGION="asia-southeast1"

echo "🚀 部署到 Google Cloud Run..."

# 构建并推送镜像
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .

# 部署到Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080 \
    --set-env-vars DEBUG=false,LOG_LEVEL=INFO

# 获取服务URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format 'value(status.url)')

echo "✅ 部署完成!"
echo "🌐 服务地址: $SERVICE_URL"
echo "📡 Postback端点: $SERVICE_URL/postback/involve/event"
echo "🔍 健康检查: $SERVICE_URL/postback/health"

# 配置自定义域名
echo "🌟 配置自定义域名..."
gcloud run domain-mappings create \
    --service $SERVICE_NAME \
    --domain bytec-postback.run.app \
    --region $REGION

echo "🎯 最终域名: https://bytec-postback.run.app/postback/involve/event"
```

## 📊 第三阶段：监控和优化

### 3.1 Cloud Monitoring 配置

```yaml
# google-cloud-config/monitoring.yaml
displayName: "ByteC Postback 监控"
conditions:
  - displayName: "高错误率告警"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="bytec-postback"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0.05
  - displayName: "响应时间告警"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision"'
      comparison: COMPARISON_GREATER_THAN  
      thresholdValue: 2000
```

### 3.2 自动扩缩容配置

```bash
# 配置水平自动扩缩容
gcloud run services update bytec-postback \
    --region=asia-southeast1 \
    --min-instances=0 \
    --max-instances=20 \
    --concurrency=100 \
    --cpu-throttling=false
```

## 🧪 测试验证

### 本地测试
```bash
# 启动本地环境
./scripts/deploy-local.sh

# 测试健康检查
curl http://localhost:8080/postback/health

# 测试Postback
curl "http://localhost:8080/postback/involve/event?conversion_id=test123&ts_token=default-ts-token"
```

### 生产测试
```bash
# 测试生产环境
curl "https://bytec-postback.run.app/postback/health"

# 测试Postback功能
curl "https://bytec-postback.run.app/postback/involve/event?conversion_id=prod123&ts_token=default-ts-token"
```

## 💰 成本估算

**Google Cloud Run 免费额度：**
- ✅ 每月200万请求免费
- ✅ 每月40万GB-秒CPU时间免费  
- ✅ 每月80万GB-秒内存时间免费
- ✅ 自动SSL证书免费
- ✅ 全球CDN免费

**预估月成本：** $0（在免费额度内）

## 🔄 环境切换

```bash
# 本地开发
export ENVIRONMENT=local
./scripts/deploy-local.sh

# 云端生产
export ENVIRONMENT=production  
./scripts/deploy-cloudrun.sh
```

## 📞 技术支持

遇到问题时的检查清单：
1. ✅ Docker镜像构建成功
2. ✅ 数据库连接正常
3. ✅ 环境变量配置正确
4. ✅ 网络端口开放
5. ✅ Google Cloud权限足够

**下一步需要配置什么？**
1. Google Cloud项目ID
2. 数据库连接信息  
3. 域名DNS设置
4. 监控告警配置 