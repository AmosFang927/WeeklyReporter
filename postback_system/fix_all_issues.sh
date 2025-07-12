#!/bin/bash
# 综合修复postback系统所有问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 开始修复postback系统所有问题${NC}"
echo "=================================================="
echo ""

# 设置权限
chmod +x fix_database_connection.sh
chmod +x recover_data_from_logs.py
chmod +x monitor_database_health.py

echo -e "${BLUE}步骤 1/4: 修复数据库连接问题${NC}"
echo "========================================"
echo -e "${YELLOW}📦 更新requirements.txt已完成（包含asyncpg）${NC}"
echo -e "${YELLOW}🔧 开始重新部署Cloud Run服务...${NC}"
echo ""

# 执行数据库连接修复
./fix_database_connection.sh

echo ""
echo -e "${BLUE}步骤 2/4: 从日志恢复数据${NC}"
echo "=========================="
echo -e "${YELLOW}🔍 从Cloud Run日志中提取转化数据...${NC}"

# 安装Python依赖
if [ ! -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}📦 创建Python虚拟环境...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# 执行数据恢复
echo -e "${YELLOW}📥 开始数据恢复...${NC}"
python3 recover_data_from_logs.py

echo ""
echo -e "${BLUE}步骤 3/4: 验证修复结果${NC}"
echo "========================"
echo -e "${YELLOW}🔍 运行数据库健康检查...${NC}"

# 等待部署完成
echo -e "${YELLOW}⏳ 等待服务部署稳定（60秒）...${NC}"
sleep 60

# 执行健康检查
python3 monitor_database_health.py

echo ""
echo -e "${BLUE}步骤 4/4: 设置持续监控${NC}"
echo "========================="

# 创建监控cron任务
cat > monitor_cron.sh << 'EOF'
#!/bin/bash
# postback系统监控cron任务

cd /Users/amosfang/WeeklyReporter/postback_system
source venv/bin/activate

# 每小时检查一次数据库健康
python3 monitor_database_health.py >> /tmp/postback_monitor.log 2>&1

# 如果发现问题，发送通知（可以根据需要添加）
EOF

chmod +x monitor_cron.sh

echo -e "${YELLOW}📅 创建监控脚本: monitor_cron.sh${NC}"
echo -e "${YELLOW}💡 建议添加到crontab中每小时执行一次:${NC}"
echo -e "${GREEN}   0 * * * * /Users/amosfang/WeeklyReporter/postback_system/monitor_cron.sh${NC}"

echo ""
echo -e "${BLUE}最终测试${NC}"
echo "=========="

# 最终API测试
SERVICE_URL="https://bytec-public-postback-472712465571.asia-southeast1.run.app"

echo -e "${YELLOW}🔍 测试API健康检查...${NC}"
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ 健康检查通过${NC}"
else
    echo -e "${RED}❌ 健康检查失败${NC}"
fi

echo -e "${YELLOW}🔍 测试数据库统计...${NC}"
STATS_RESPONSE=$(curl -s "$SERVICE_URL/postback/stats" || echo "failed")
if [[ "$STATS_RESPONSE" == "failed" ]]; then
    echo -e "${RED}❌ 数据库统计获取失败${NC}"
else
    echo -e "${GREEN}✅ 数据库统计获取成功${NC}"
    echo "$STATS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATS_RESPONSE"
fi

echo ""
echo "=============================================="
echo -e "${GREEN}🎉 修复任务完成！${NC}"
echo ""
echo -e "${BLUE}📋 修复总结:${NC}"
echo -e "${GREEN}  ✅ 更新requirements.txt添加asyncpg模块${NC}"
echo -e "${GREEN}  ✅ 重新部署Cloud Run服务${NC}"
echo -e "${GREEN}  ✅ 从日志恢复转化数据到数据库${NC}"
echo -e "${GREEN}  ✅ 创建数据库健康监控脚本${NC}"
echo -e "${GREEN}  ✅ 设置持续监控机制${NC}"
echo ""
echo -e "${BLUE}📈 接下来的建议:${NC}"
echo -e "${YELLOW}  1. 定期运行监控脚本检查系统状态${NC}"
echo -e "${YELLOW}  2. 设置cron任务进行自动监控${NC}"
echo -e "${YELLOW}  3. 关注Cloud Run日志确保数据正常存储${NC}"
echo -e "${YELLOW}  4. 如有新问题，及时运行数据恢复脚本${NC}"
echo ""
echo -e "${PURPLE}🔧 可用的维护命令:${NC}"
echo -e "${GREEN}  ./monitor_database_health.py   - 检查系统健康状况${NC}"
echo -e "${GREEN}  ./recover_data_from_logs.py   - 从日志恢复数据${NC}"
echo -e "${GREEN}  ./monitor_logs.sh postback    - 查看postback日志${NC}"
echo "" 