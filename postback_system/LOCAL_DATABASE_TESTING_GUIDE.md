# ByteC Postback 本地数据库测试指南

## 概述

本指南提供了完整的本地数据库测试环境，包括PostgreSQL数据库、pgAdmin管理工具、Adminer轻量级管理工具以及数据可视化查询功能。

## 系统架构

```
本地测试环境架构：
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     pgAdmin     │    │     Adminer     │
│   (端口:5432)   │    │   (端口:8080)   │    │   (端口:8081)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI App   │
                    │   (端口:8000)   │
                    └─────────────────┘
```

## 快速开始

### 1. 环境准备

确保已安装以下工具：
- Docker Desktop
- Python 3.8+
- 终端/命令行工具

### 2. 启动测试环境

```bash
# 进入项目目录
cd postback_system

# 给启动脚本添加执行权限
chmod +x scripts/start_local_db_test.sh

# 启动本地数据库测试环境
./scripts/start_local_db_test.sh
```

### 3. 验证环境

启动成功后，您将看到以下服务：

**PostgreSQL 数据库**
- 主机: `localhost`
- 端口: `5432`
- 数据库: `postback_db`
- 用户: `postback`
- 密码: `postback123`

**pgAdmin 管理工具**
- 访问地址: http://localhost:8080
- 用户: `admin@postback.com`
- 密码: `admin123`

**Adminer 轻量级管理工具**
- 访问地址: http://localhost:8081
- 服务器: `postgres`
- 用户: `postback`
- 密码: `postback123`
- 数据库: `postback_db`

## 数据库结构

### 主要表格

#### 1. 租户表 (tenants)
存储多租户系统中的租户信息

| 字段 | 类型 | 描述 |
|------|------|------|
| id | SERIAL | 主键 |
| tenant_code | VARCHAR(50) | 租户唯一代码 |
| tenant_name | VARCHAR(100) | 租户名称 |
| ts_token | VARCHAR(255) | TS Token |
| tlm_token | VARCHAR(255) | TLM Token |
| is_active | BOOLEAN | 是否激活 |
| created_at | TIMESTAMP | 创建时间 |

#### 2. 转化数据表 (postback_conversions)
存储Postback转化数据

| 字段 | 类型 | 描述 |
|------|------|------|
| id | SERIAL | 主键 |
| tenant_id | INTEGER | 租户ID |
| conversion_id | VARCHAR(50) | 转化ID |
| offer_id | VARCHAR(50) | 广告ID |
| offer_name | TEXT | 广告名称 |
| usd_sale_amount | DECIMAL(15,2) | 美元销售金额 |
| usd_payout | DECIMAL(15,2) | 美元佣金 |
| status | VARCHAR(50) | 状态 |
| received_at | TIMESTAMP | 接收时间 |
| raw_data | JSONB | 原始数据 |

### 预定义视图

#### 1. 转化汇总视图 (v_conversion_summary)
```sql
SELECT * FROM v_conversion_summary;
```

#### 2. 每日统计视图 (v_daily_conversion_stats)
```sql
SELECT * FROM v_daily_conversion_stats;
```

#### 3. 性能统计视图 (v_performance_stats)
```sql
SELECT * FROM v_performance_stats;
```

## 使用pgAdmin进行可视化查询

### 首次设置

1. 打开 http://localhost:8080
2. 使用管理员账户登录：
   - 邮箱: `admin@postback.com`
   - 密码: `admin123`

3. 添加数据库连接：
   - 右键点击 "Servers" → "Register" → "Server"
   - 名称: `Local Postback DB`
   - 主机: `postgres`
   - 端口: `5432`
   - 数据库: `postback_db`
   - 用户: `postback`
   - 密码: `postback123`

### 常用查询示例

#### 1. 查看租户列表
```sql
SELECT 
    tenant_code,
    tenant_name,
    is_active,
    created_at
FROM tenants 
ORDER BY created_at DESC;
```

#### 2. 查看转化数据统计
```sql
SELECT 
    COUNT(*) as total_conversions,
    SUM(usd_sale_amount) as total_amount,
    AVG(usd_sale_amount) as avg_amount,
    COUNT(DISTINCT tenant_id) as unique_tenants
FROM postback_conversions;
```

#### 3. 按租户分组统计
```sql
SELECT 
    t.tenant_name,
    COUNT(p.id) as conversion_count,
    SUM(p.usd_sale_amount) as total_amount,
    AVG(p.usd_sale_amount) as avg_amount
FROM tenants t
LEFT JOIN postback_conversions p ON t.id = p.tenant_id
GROUP BY t.id, t.tenant_name
ORDER BY total_amount DESC;
```

#### 4. 近7天每日转化趋势
```sql
SELECT 
    DATE(received_at) as date,
    COUNT(*) as daily_conversions,
    SUM(usd_sale_amount) as daily_amount
FROM postback_conversions
WHERE received_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(received_at)
ORDER BY date DESC;
```

#### 5. 按状态分组
```sql
SELECT 
    status,
    COUNT(*) as count,
    SUM(usd_sale_amount) as total_amount
FROM postback_conversions
GROUP BY status
ORDER BY count DESC;
```

#### 6. JSON数据查询
```sql
-- 查询包含特定设备类型的记录
SELECT 
    conversion_id,
    raw_data->>'device' as device_type,
    raw_data->>'browser' as browser
FROM postback_conversions
WHERE raw_data ? 'device';

-- 按设备类型统计
SELECT 
    raw_data->>'device' as device_type,
    COUNT(*) as count
FROM postback_conversions
WHERE raw_data ? 'device'
GROUP BY raw_data->>'device'
ORDER BY count DESC;
```

## 使用Adminer进行快速查询

### 访问步骤

1. 打开 http://localhost:8081
2. 填写连接信息：
   - 系统: `PostgreSQL`
   - 服务器: `postgres`
   - 用户名: `postback`
   - 密码: `postback123`
   - 数据库: `postback_db`

### Adminer优势

- 轻量级，加载速度快
- 直观的表格浏览界面
- 支持SQL查询和结果导出
- 可视化的数据库结构图
- 支持数据编辑和导入

## 数据库测试脚本

### 运行完整测试

```bash
# 进入项目目录
cd postback_system

# 运行数据库测试脚本
python scripts/test_database.py
```

### 测试内容

1. **基本查询测试** - 验证数据库连接和基本查询
2. **数据插入测试** - 测试数据写入功能
3. **自定义视图测试** - 验证预定义视图
4. **JSON字段查询测试** - 测试JSONB字段查询
5. **性能查询测试** - 验证查询性能

## 示例数据

系统自动创建以下示例数据：

### 示例租户
- `bytec`: ByteC Technology
- `involve_asia`: Involve Asia
- `test_partner`: Test Partner

### 示例转化数据
- 5条不同类型的转化记录
- 涵盖不同状态：Approved、Pending、Rejected
- 包含JSON格式的原始数据

## 常见问题解决

### 1. 端口冲突

如果遇到端口占用问题：

```bash
# 查看端口占用
lsof -i :5432
lsof -i :8080
lsof -i :8081

# 停止现有服务
docker-compose -f docker-compose.local.yml down
```

### 2. 数据库连接失败

检查数据库状态：
```bash
# 查看容器状态
docker ps

# 查看数据库日志
docker logs postback_postgres

# 手动测试连接
docker exec -it postback_postgres psql -U postback -d postback_db
```

### 3. 重置数据库

```bash
# 停止服务
docker-compose -f docker-compose.local.yml down

# 删除数据卷
docker volume rm postback_system_postgres_data

# 重新启动
./scripts/start_local_db_test.sh
```

## 高级功能

### 1. 数据备份

```bash
# 备份数据库
docker exec postback_postgres pg_dump -U postback postback_db > backup.sql

# 恢复数据库
docker exec -i postback_postgres psql -U postback postback_db < backup.sql
```

### 2. 性能监控

```sql
-- 查看活动连接
SELECT * FROM pg_stat_activity;

-- 查看表统计信息
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables;

-- 查看索引使用情况
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes;
```

### 3. 查询优化

```sql
-- 分析查询计划
EXPLAIN ANALYZE SELECT * FROM postback_conversions WHERE tenant_id = 1;

-- 查看慢查询
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
```

## 生产环境迁移

当需要迁移到生产环境时：

1. 导出数据结构：
```bash
pg_dump -U postback -s postback_db > schema.sql
```

2. 导出数据：
```bash
pg_dump -U postback -a postback_db > data.sql
```

3. 更新配置文件中的数据库连接信息
4. 运行迁移脚本

## 总结

本地数据库测试环境提供了：

- ✅ 完整的PostgreSQL数据库环境
- ✅ 两种可视化管理工具（pgAdmin + Adminer）
- ✅ 预定义的数据模型和示例数据
- ✅ 自动化的测试脚本
- ✅ 常用查询示例和最佳实践
- ✅ 性能监控和优化建议

这个环境非常适合：
- 开发和测试Postback功能
- 学习PostgreSQL和SQL查询
- 验证数据模型设计
- 进行性能测试和优化
- 准备生产环境部署

开始您的数据库测试之旅吧！ 🚀 