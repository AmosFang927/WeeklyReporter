# Involve Asia API 工作流功能说明

## 概述
此工作流用于集成 Involve Asia API，实现自动化认证并获取转换数据。

## 功能模块

### 1. API 认证 (Authentication)
- **目的**: 获取访问令牌以访问 Involve Asia API
- **端点**: `POST https://api.involve.asia/api/authenticate`
- **输入参数**:
  - `secret`: API密钥 (存储在.config中)
  - `key`: API键名 (存储在.config中)
- **输出**: Bearer Token

### 2. 获取转换数据 (Get Conversion Data)
- **目的**: 根据日期范围和筛选条件获取转换数据
- **端点**: `POST https://api.involve.asia/api/conversions/range`
- **输入参数**:
  - `page`: 页码 (默认1)
  - `limit`: 每页限制 (默认100)
  - `start_date`: 开始日期 (存储在.config中)
  - `end_date`: 结束日期 (存储在.config中)
  - `preferred_currency`: 首选货币 (存储在.config中)
  - `filters`: 可选筛选条件
- **输出**: 转换数据列表

## 配置要求

### 环境变量/.config文件
```
# API 认证配置
IA_API_SECRET=boiTXnRgB2B3N7rCictjjti1ufNIzKksSURJHwqtC50=
IA_API_KEY=general

# 数据获取配置  
START_DATE=2025-06-16
END_DATE=2025-06-16
PREFERRED_CURRENCY=USD
```

## 工作流步骤
1. 读取配置参数
2. 执行API认证获取Token
3. 使用Token获取转换数据
4. 数据处理和输出

## 错误处理
- API认证失败处理
- 网络连接超时处理
- 数据格式验证 