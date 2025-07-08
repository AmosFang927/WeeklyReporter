# Supabase集成方案

## 1. Supabase项目设置

### 创建Supabase项目
```bash
# 安装Supabase CLI
npm install -g supabase

# 登录Supabase
supabase login

# 初始化项目
supabase init

# 启动本地开发环境
supabase start
```

### 数据库迁移脚本
```sql
-- 在Supabase中创建相同的表结构
CREATE TABLE conversions (
    id SERIAL PRIMARY KEY,
    conversion_id VARCHAR(255) UNIQUE NOT NULL,
    tenant_id INTEGER DEFAULT 1,
    sub_id VARCHAR(255),
    media_id VARCHAR(255),
    click_id VARCHAR(255),
    usd_sale_amount DECIMAL(15,2),
    usd_payout DECIMAL(15,2),
    offer_name VARCHAR(500),
    datetime_conversion TIMESTAMP WITH TIME ZONE,
    raw_parameters JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 启用实时功能
ALTER PUBLICATION supabase_realtime ADD TABLE conversions;
```

## 2. 数据同步策略

### 选项A：实时同步（推荐）
```python
# supabase_sync.py
import asyncio
import asyncpg
from supabase import create_client
import os

SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-anon-key"
LOCAL_DB_URL = "postgresql://postback:postback123@localhost:5432/postback_db"

async def sync_to_supabase():
    """实时同步本地数据到Supabase"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    local_conn = await asyncpg.connect(LOCAL_DB_URL)
    
    # 监听本地数据库变更
    # 实现增量同步逻辑
```

### 选项B：定时批量同步
```bash
# 每小时同步一次
0 * * * * /usr/local/bin/python3 /path/to/supabase_sync.py
```

## 3. Cursor CLI集成

### 数据库操作脚本
```bash
#!/bin/bash
# supabase_cli.sh

# 直接查询Supabase
function query_supabase() {
    curl -X POST "https://your-project.supabase.co/rest/v1/rpc/custom_query" \
         -H "apikey: your-api-key" \
         -H "Content-Type: application/json" \
         -d "{\"query\": \"$1\"}"
}

# 自然语言查询转换
function nl_query() {
    local question="$1"
    # 调用AI服务转换为SQL
    local sql=$(curl -X POST "https://api.openai.com/v1/chat/completions" \
                     -H "Authorization: Bearer $OPENAI_API_KEY" \
                     -H "Content-Type: application/json" \
                     -d "{
                         \"model\": \"gpt-4\",
                         \"messages\": [{
                             \"role\": \"user\",
                             \"content\": \"Convert this question to SQL for a conversions table: $question\"
                         }]
                     }")
    
    # 执行生成的SQL
    query_supabase "$sql"
}
``` 