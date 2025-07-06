#!/bin/bash
# ByteC Postback 本地部署脚本
# 用于在本地环境中运行Docker化的Postback系统

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="bytec-postback"
IMAGE_NAME="bytec-postback:local"
CONTAINER_NAME="bytec-postback"
LOCAL_PORT="8080"
DATABASE_URL="postgresql+asyncpg://postback:postback123@host.docker.internal:5432/postback_db"

echo -e "${BLUE}🚀 启动 ByteC Postback 本地部署...${NC}"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动Docker${NC}"
    exit 1
fi

# 检查并创建网络
if ! docker network ls | grep -q "bytec-network"; then
    echo -e "${YELLOW}📡 创建Docker网络...${NC}"
    docker network create bytec-network
fi

# 构建Docker镜像
echo -e "${YELLOW}🏗️ 构建Docker镜像...${NC}"
docker build -f Dockerfile.cloudrun -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker镜像构建失败${NC}"
    exit 1
fi

# 停止并删除现有容器
echo -e "${YELLOW}🛑 停止现有容器...${NC}"
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# 启动新容器
echo -e "${YELLOW}🐳 启动Docker容器...${NC}"
docker run -d \
  --name $CONTAINER_NAME \
  --network bytec-network \
  --restart unless-stopped \
  -p $LOCAL_PORT:8080 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e DEBUG=true \
  -e LOG_LEVEL=INFO \
  -e HOST=0.0.0.0 \
  -e PORT=8080 \
  -e WORKERS=1 \
  -e THREADS=4 \
  $IMAGE_NAME

# 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 5

# 健康检查
echo -e "${YELLOW}🔍 执行健康检查...${NC}"
for i in {1..30}; do
    if curl -f -s http://localhost:$LOCAL_PORT/postback/health > /dev/null; then
        echo -e "${GREEN}✅ 服务健康检查通过${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ 服务启动失败或健康检查超时${NC}"
        echo -e "${YELLOW}📋 查看容器日志:${NC}"
        docker logs $CONTAINER_NAME --tail 20
        exit 1
    fi
    echo -e "${YELLOW}⏳ 等待服务启动... ($i/30)${NC}"
    sleep 2
done

# 显示服务信息
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 ByteC Postback 本地部署成功！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📍 本地服务地址:${NC}     http://localhost:$LOCAL_PORT"
echo -e "${BLUE}🔍 健康检查:${NC}         http://localhost:$LOCAL_PORT/postback/health"
echo -e "${BLUE}📡 Postback端点:${NC}     http://localhost:$LOCAL_PORT/postback/involve/event"
echo -e "${BLUE}📊 API文档:${NC}          http://localhost:$LOCAL_PORT/docs"
echo -e "${BLUE}📋 服务信息:${NC}         http://localhost:$LOCAL_PORT/info"
echo ""
echo -e "${YELLOW}🧪 测试命令:${NC}"
echo "curl 'http://localhost:$LOCAL_PORT/postback/involve/event?conversion_id=test123&ts_token=default-ts-token'"
echo ""
echo -e "${YELLOW}📋 容器管理命令:${NC}"
echo "查看日志:    docker logs $CONTAINER_NAME -f"
echo "停止服务:    docker stop $CONTAINER_NAME"
echo "重启服务:    docker restart $CONTAINER_NAME"
echo "删除容器:    docker rm -f $CONTAINER_NAME"
echo ""
echo -e "${BLUE}🌐 下一步: 运行 './scripts/local-tunnel.sh' 创建公网隧道${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" 