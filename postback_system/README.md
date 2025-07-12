# Postback数据处理系统

🆕 添加自然语言查询功能


创建GCP Cloud SQL PostgreSQL实例，配置网络和安全设置
ByteC2024PostBack_CloudSQL_20250708
将现有PostgreSQL数据迁移到Cloud SQL实例
更新Cloud Run配置连接Cloud SQL，配置VPC连接器
部署更新后的postback服务到bytec-public-postback

配置Looker Studio连接Cloud SQL，创建数据可视化仪表板
使用AppSheet创建Partner配置管理界面
配置BigQuery数据同步和Vertex AI自然语言查询功能
端到端测试整个GCP原生系统

## 系统概述

这是一个实时接收和处理电商转化回传数据的系统，专为Shopee、TikTok Shop等电商平台设计，支持Involve Asia的Postback标准。

## 主要功能

- ✅ **实时Postback接收**: 支持GET/POST方式接收转化数据
- ✅ **多租户管理**: 基于TS Token、TLM Token、TS Parameter的租户识别
- ✅ **数据验证与清洗**: 自动验证和清洗转化数据
- ✅ **重复检测**: 避免重复数据的影响
- ✅ **PostgreSQL存储**: 高性能数据存储和查询
- ✅ **REST API**: 完整的数据查询和管理接口
- ⭐ **扩展性**: 预留ML/AI接口，支持未来智能分析

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Postback数据处理系统                        │
├─────────────────────────────────────────────────────────────┤
│  📥 接收层 (FastAPI)                                         │
│  ├── GET /postback/ (URL参数接收)                            │
│  ├── POST /postback/ (JSON数据接收)                          │
│  ├── Token验证中间件                                         │
│  └── 租户识别与路由                                           │
├─────────────────────────────────────────────────────────────┤
│  🗄️ 数据层 (PostgreSQL)                                      │
│  ├── 转化数据存储                                             │
│  ├── 租户配置管理                                             │
│  ├── 数据清洗与验证                                           │
│  └── 自动过期清理                                             │
├─────────────────────────────────────────────────────────────┤
│  🔌 服务层                                                   │
│  ├── RESTful API                                            │
│  ├── 数据查询与统计                                           │
│  ├── 异常检测                                                │
│  └── ML特征工程 (预留)                                        │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
cd postback_system
pip install -r requirements.txt

# 设置环境变量
export DATABASE_URL="postgresql+asyncpg://postback:postback123@localhost:5432/postback_db"
export DEBUG=true
```

### 2. 数据库设置

```bash
# 安装PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# 创建数据库和用户
createdb postback_db
psql postback_db -c "CREATE USER postback WITH PASSWORD 'postback123';"
psql postback_db -c "GRANT ALL PRIVILEGES ON DATABASE postback_db TO postback;"
```

### 3. 启动服务

```bash
# 开发模式启动
python main.py

# 生产模式启动
uvicorn main:app --host 0.0.0.0 --port 8000
```

服务启动后访问：
- 🏠 主页: http://localhost:8000
- 📖 API文档: http://localhost:8000/docs
- 💚 健康检查: http://localhost:8000/health

## API使用示例

### Postback数据接收

#### GET方式 (标准Involve Asia格式)

```bash
curl "http://localhost:8000/postback/?conversion_id=12345&offer_id=100&usd_sale_amount=50.00&usd_payout=5.00&ts_token=your-token"
```

#### POST方式 (JSON格式)

```bash
curl -X POST "http://localhost:8000/postback/?ts_token=your-token" \
     -H "Content-Type: application/json" \
     -d '{
       "conversion_id": "12345",
       "offer_id": "100",
       "usd_sale_amount": 50.00,
       "usd_payout": 5.00,
       "status": "Approved"
     }'
```

### 数据查询

```bash
# 查询转换数据
curl "http://localhost:8000/postback/conversions?page=1&page_size=10"

# 获取统计信息
curl "http://localhost:8000/postback/stats?hours=24"
```

## 支持的Postback参数

### 核心参数
- `conversion_id`: 转换唯一ID **(必填)**
- `offer_id`: Offer ID
- `offer_name`: 广告主名称
- `datetime_conversion`: 转换时间 (YYYY-MM-DD HH:MM:SS)
- `order_id`: 订单ID

### 金额参数
- `sale_amount_local`: 本地货币金额
- `myr_sale_amount`: 马来西亚林吉特金额
- `usd_sale_amount`: 美元金额
- `payout_local`: 本地货币佣金
- `myr_payout`: 马来西亚林吉特佣金
- `usd_payout`: 美元佣金
- `conversion_currency`: 货币代码 (ISO 4217)

### 自定义参数
- `adv_sub` ~ `adv_sub5`: 广告主自定义参数
- `aff_sub` ~ `aff_sub4`: 发布商自定义参数

### Token参数
- `ts_token`: TS Token (租户识别)
- `ts_param`: TS Parameter (租户识别)
- `tlm_token`: TLM Token (租户识别)

## 多租户配置

系统支持多租户模式，每个租户可以有独立的：
- Token配置
- 数据保留策略
- 重复检测规则
- 请求限制

### 租户识别优先级
1. `ts_token` 匹配
2. `ts_param` 匹配  
3. `tlm_token` 匹配
4. 使用默认租户

## 数据管理

### 自动清理
- 支持按租户配置的数据保留天数自动清理
- 默认保留7天数据
- 可通过租户配置自定义保留策略

### 重复检测
- 基于 `tenant_id` + `conversion_id` 检测重复
- 可按租户配置启用/禁用
- 重复数据会被标记但不会丢弃

## 监控与日志

### 健康检查
```bash
curl http://localhost:8000/health
```

### 系统信息
```bash
curl http://localhost:8000/info
```

### 日志等级
- 支持 DEBUG, INFO, WARNING, ERROR 等级
- 生产环境建议使用 INFO 等级

## 扩展功能 (Phase 3&4 预留)

系统已预留以下扩展接口：

### 1. 机器学习集成
- 特征工程接口
- 模型训练数据导出
- 预测结果集成

### 2. 智能分析
- 异常检测算法
- 转化率预测
- 用户行为分析

### 3. 可视化Dashboard
- 实时数据监控
- 统计图表
- 自定义报表

## 部署建议

### 本地开发
```bash
python main.py
```

### 生产部署
```bash
# Docker方式
docker build -t postback-system .
docker run -p 8000:8000 postback-system

# 直接部署
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Google Cloud部署
```bash
# 使用Cloud Run
gcloud run deploy postback-system --source . --platform managed
```

## 性能指标

- 📊 **处理能力**: 每日10万+ 转化数据
- ⚡ **响应时间**: < 100ms (P95)
- 💾 **存储**: PostgreSQL + 自动清理
- 🔄 **可用性**: 99.9%+ (生产环境)

## 技术栈

- **后端**: FastAPI + Python 3.8+
- **数据库**: PostgreSQL + SQLAlchemy
- **缓存**: Redis (可选)
- **监控**: 内置健康检查
- **部署**: Docker + Uvicorn

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库配置
   echo $DATABASE_URL
   # 测试连接
   psql $DATABASE_URL -c "SELECT 1"
   ```

2. **Token验证失败**
   - 检查租户配置
   - 确认Token格式正确
   - 查看应用日志

3. **性能问题**
   - 检查数据库索引
   - 调整连接池大小
   - 增加worker数量

## 联系与支持

如有问题请查看：
- 📖 API文档: `/docs`
- 📋 健康状态: `/health`
- 📊 系统信息: `/info` 