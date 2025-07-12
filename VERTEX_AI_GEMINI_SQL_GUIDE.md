# Google Vertex AI + Gemini 处理 Google SQL 完整指南

## 📋 项目概述

本项目展示如何使用Google Vertex AI平台的Gemini模型来处理Google Cloud SQL数据，实现智能数据分析和处理。

## 🚀 快速开始

### 1. 环境准备

#### 1.1 系统要求
- Python 3.9+
- Google Cloud SDK
- 有效的Google Cloud账户

#### 1.2 Google Cloud项目设置

```bash
# 1. 创建或选择Google Cloud项目
gcloud projects create YOUR_PROJECT_ID
gcloud config set project YOUR_PROJECT_ID

# 2. 启用必要的API服务
gcloud services enable aiplatform.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

# 3. 创建服务账户
gcloud iam service-accounts create vertex-ai-sql-service \
    --display-name="Vertex AI SQL Service Account"

# 4. 授予必要权限
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:vertex-ai-sql-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:vertex-ai-sql-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:vertex-ai-sql-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.instanceUser"

# 5. 创建服务账户密钥
gcloud iam service-accounts keys create vertex-ai-sql-key.json \
    --iam-account=vertex-ai-sql-service@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

#### 1.3 Cloud SQL实例设置

```bash
# 创建Cloud SQL实例
gcloud sql instances create gemini-sql-instance \
    --database-version=MYSQL_8_0 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YOUR_ROOT_PASSWORD \
    --authorized-networks=0.0.0.0/0

# 创建数据库
gcloud sql databases create gemini_test_db \
    --instance=gemini-sql-instance

# 创建数据库用户
gcloud sql users create gemini_user \
    --instance=gemini-sql-instance \
    --password=YOUR_USER_PASSWORD
```

### 2. 依赖安装

```bash
# 安装Python依赖
pip install -r requirements.txt
```

### 3. 环境变量配置

创建 `.env` 文件：

```bash
# Google Cloud配置
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_APPLICATION_CREDENTIALS=vertex-ai-sql-key.json
VERTEX_AI_LOCATION=us-central1

# Cloud SQL配置
CLOUD_SQL_CONNECTION_NAME=YOUR_PROJECT_ID:us-central1:gemini-sql-instance
CLOUD_SQL_DATABASE=gemini_test_db
CLOUD_SQL_USER=gemini_user
CLOUD_SQL_PASSWORD=YOUR_USER_PASSWORD

# Gemini配置
GEMINI_MODEL=gemini-1.5-pro-002
GEMINI_MAX_TOKENS=8192
GEMINI_TEMPERATURE=0.1
```

## 📦 项目结构

```
vertex_ai_gemini_sql/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── cloud_config.py
├── core/
│   ├── __init__.py
│   ├── vertex_ai_client.py
│   ├── sql_connector.py
│   └── data_processor.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── error_handler.py
├── examples/
│   ├── basic_query.py
│   ├── data_analysis.py
│   └── batch_processing.py
├── tests/
│   ├── test_vertex_ai.py
│   ├── test_sql_connector.py
│   └── test_integration.py
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 核心功能

### 1. Vertex AI + Gemini集成
- 智能SQL查询生成
- 数据分析和洞察
- 自然语言到SQL转换

### 2. Cloud SQL连接
- 安全的数据库连接
- 连接池管理
- 自动重连机制

### 3. 数据处理
- 批量数据处理
- 实时数据分析
- 结果可视化

## 🎯 使用案例

### 1. 基本查询
```python
from core.data_processor import DataProcessor

processor = DataProcessor()
result = processor.analyze_data("分析过去7天的销售趋势")
```

### 2. 智能报告生成
```python
report = processor.generate_report("创建月度销售报告")
```

### 3. 数据预测
```python
prediction = processor.predict_trends("预测下季度销售增长")
```

## 📊 性能优化

- 异步处理支持
- 连接池优化
- 智能缓存机制
- 批处理优化

## 🔐 安全考虑

- 服务账户最小权限原则
- 数据传输加密
- 访问日志记录
- 错误处理和监控

## 📚 相关文档

- [Google Vertex AI文档](https://cloud.google.com/vertex-ai/docs)
- [Gemini API文档](https://ai.google.dev/docs)
- [Cloud SQL连接器](https://cloud.google.com/sql/docs/mysql/connect-connectors)

## 🐛 故障排除

### 常见问题

1. **认证错误**
   - 检查服务账户密钥路径
   - 验证IAM权限设置

2. **连接超时**
   - 检查网络配置
   - 调整超时设置

3. **API限制**
   - 检查配额限制
   - 实现重试机制

## 📞 支持

如有问题，请查看项目Wiki或提交Issue。

---

**版本**: 1.0.0  
**更新日期**: 2025-01-26  
**作者**: WeeklyReporter Team 