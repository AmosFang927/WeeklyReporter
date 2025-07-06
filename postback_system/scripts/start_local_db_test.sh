#!/bin/bash
# 启动本地数据库测试环境
# 包含PostgreSQL、pgAdmin、Adminer和Redis

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ByteC Postback系统本地数据库测试环境 ===${NC}"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}错误：Docker未运行。请先启动Docker Desktop。${NC}"
    exit 1
fi

# 检查端口占用
check_port() {
    local port=$1
    local service=$2
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${YELLOW}警告：端口 $port 已被占用（$service）${NC}"
        read -p "是否继续？可能会有冲突 (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

echo -e "${BLUE}检查端口占用...${NC}"
check_port 5432 "PostgreSQL"
check_port 8080 "pgAdmin"
check_port 8081 "Adminer"
check_port 6379 "Redis"

# 清理旧容器（如果存在）
echo -e "${BLUE}清理旧容器...${NC}"
docker-compose -f docker-compose.local.yml down > /dev/null 2>&1 || true

# 启动服务
echo -e "${BLUE}启动数据库服务...${NC}"
docker-compose -f docker-compose.local.yml up -d postgres redis

echo -e "${BLUE}等待数据库启动...${NC}"
sleep 10

# 检查数据库连接
echo -e "${BLUE}检查数据库连接...${NC}"
until docker exec postback_postgres pg_isready -U postback -d postback_db > /dev/null 2>&1; do
    echo -e "${YELLOW}等待PostgreSQL启动...${NC}"
    sleep 2
done

echo -e "${GREEN}✓ PostgreSQL已启动${NC}"

# 启动管理工具
echo -e "${BLUE}启动数据库管理工具...${NC}"
docker-compose -f docker-compose.local.yml up -d pgadmin adminer

echo -e "${BLUE}等待管理工具启动...${NC}"
sleep 5

# 显示访问信息
echo -e "${GREEN}=== 数据库测试环境已启动 ===${NC}"
echo
echo -e "${GREEN}数据库连接信息：${NC}"
echo "  主机: localhost"
echo "  端口: 5432"
echo "  数据库: postback_db"
echo "  用户: postback"
echo "  密码: postback123"
echo

echo -e "${GREEN}管理工具访问地址：${NC}"
echo "  pgAdmin: http://localhost:8080"
echo "    用户: admin@postback.com"
echo "    密码: admin123"
echo
echo "  Adminer: http://localhost:8081"
echo "    服务器: postgres"
echo "    用户: postback"
echo "    密码: postback123"
echo "    数据库: postback_db"
echo

echo -e "${GREEN}Redis连接信息：${NC}"
echo "  主机: localhost"
echo "  端口: 6379"
echo "  数据库: 0"
echo

# 检查数据是否正确导入
echo -e "${BLUE}检查示例数据...${NC}"
tenant_count=$(docker exec postback_postgres psql -U postback -d postback_db -t -c "SELECT COUNT(*) FROM tenants;" | tr -d ' ')
conversion_count=$(docker exec postback_postgres psql -U postback -d postback_db -t -c "SELECT COUNT(*) FROM postback_conversions;" | tr -d ' ')

echo -e "${GREEN}✓ 租户数量: $tenant_count${NC}"
echo -e "${GREEN}✓ 转化数据数量: $conversion_count${NC}"

# 显示常用查询
echo -e "${BLUE}=== 常用查询示例 ===${NC}"
echo -e "${YELLOW}查看租户列表：${NC}"
echo "SELECT tenant_code, tenant_name, is_active FROM tenants;"
echo

echo -e "${YELLOW}查看转化统计：${NC}"
echo "SELECT * FROM v_conversion_summary;"
echo

echo -e "${YELLOW}查看每日统计：${NC}"
echo "SELECT * FROM v_daily_conversion_stats;"
echo

echo -e "${YELLOW}查看性能统计：${NC}"
echo "SELECT * FROM v_performance_stats;"
echo

# 询问是否启动API服务
echo -e "${BLUE}是否启动FastAPI服务进行完整测试？${NC}"
read -p "启动API服务 (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}启动API服务...${NC}"
    
    # 设置环境变量
    export $(cat config.local.test.env | grep -v '^#' | xargs)
    
    # 启动FastAPI服务
    if command -v uvicorn &> /dev/null; then
        echo -e "${GREEN}使用uvicorn启动API服务...${NC}"
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
        API_PID=$!
        sleep 3
        
        # 测试API连接
        if curl -s http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}✓ API服务已启动: http://localhost:8000${NC}"
            echo -e "${GREEN}  健康检查: http://localhost:8000/health${NC}"
            echo -e "${GREEN}  API文档: http://localhost:8000/docs${NC}"
        else
            echo -e "${RED}API服务启动失败${NC}"
        fi
    else
        echo -e "${YELLOW}未找到uvicorn，请手动启动API服务：${NC}"
        echo "cd postback_system && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    fi
fi

# 提供测试命令
echo -e "${BLUE}=== 测试命令 ===${NC}"
echo -e "${YELLOW}直接数据库查询：${NC}"
echo "docker exec -it postback_postgres psql -U postback -d postback_db"
echo

echo -e "${YELLOW}查看日志：${NC}"
echo "docker-compose -f docker-compose.local.yml logs -f"
echo

echo -e "${YELLOW}停止服务：${NC}"
echo "docker-compose -f docker-compose.local.yml down"
echo

echo -e "${GREEN}=== 环境启动完成 ===${NC}"
echo -e "${GREEN}可以开始进行数据库测试了！${NC}" 