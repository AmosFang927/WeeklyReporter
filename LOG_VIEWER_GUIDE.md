# Reporter-Agent 日志查看工具使用指南

## 🛠️ 工具概述

`view_logs.sh` 是为 `reporter-agent` Cloud Run 服务定制的日志查看工具，支持两种查看模式：

- **Recent模式**: 查看历史日志
- **Tail模式**: 实时跟踪日志输出

## 📋 基本用法

### 1. Recent模式 - 查看最近日志

```bash
# 基本用法
./view_logs.sh recent [条数] [小时]

# 示例
./view_logs.sh recent                  # 查看最近20条日志 (1小时内)
./view_logs.sh recent 50               # 查看最近50条日志 (1小时内)
./view_logs.sh recent 100 3            # 查看最近100条日志 (3小时内)
```

**功能特点**：
- 📊 显示指定数量的历史日志
- ⏰ 可设置时间范围
- 📈 按时间倒序显示
- 🔍 包含时间戳、严重级别、消息内容

### 2. Tail模式 - 实时跟踪日志

```bash
# 实时跟踪
./view_logs.sh tail
```

**功能特点**：
- 🔄 实时显示新产生的日志
- 💡 按 `Ctrl+C` 停止跟踪
- 🌊 持续流式输出
- ⚡ 低延迟显示新日志

## 🎯 使用场景

### 任务监控
```bash
# 查看当前任务执行情况
./view_logs.sh recent 30

# 实时监控任务进度
./view_logs.sh tail
```

### 问题排查
```bash
# 查看最近的错误信息
./view_logs.sh recent 100 6

# 实时追踪问题
./view_logs.sh tail
```

### 性能分析
```bash
# 查看详细的执行日志
./view_logs.sh recent 50 2
```

## 📊 日志输出格式

输出包含三列信息：

| 列名 | 说明 | 示例 |
|------|------|------|
| TIMESTAMP | 时间戳 (UTC) | 2025-07-06T06:19:16.319591Z |
| SEVERITY | 严重级别 | INFO, WARNING, ERROR |
| TEXT_PAYLOAD | 日志消息内容 | 📊 第 9 页: 获取到 100 条记录 |

## 🔍 日志内容解读

### 常见日志标识

- 🚀 **任务启动**: `[Cloud Scheduler] 开始执行WeeklyReporter任务`
- 📊 **数据获取**: `正在获取第 X 页数据`
- 📈 **进度更新**: `进度: X/Y 页 (总条数)`
- 💰 **金额统计**: `总金额: $XXX.XX USD`
- 📧 **邮件发送**: `邮件已发送给`
- ✅ **任务完成**: `工作流执行成功`
- ❌ **错误信息**: `执行失败`

### 任务状态跟踪

1. **认证阶段**: API token获取
2. **数据获取**: 分页获取转换数据
3. **数据处理**: Excel文件生成
4. **通知发送**: 邮件和飞书通知
5. **任务完成**: 最终结果摘要

## ⚡ 快速操作

### 常用命令组合

```bash
# 快速检查最新状态
./view_logs.sh recent 10

# 详细任务历史
./view_logs.sh recent 100 4

# 监控新任务执行
./view_logs.sh tail
```

### 实时监控工作流

1. 启动实时监控：`./view_logs.sh tail`
2. 在另一个终端触发任务：`gcloud scheduler jobs run reporter-agent-daily --location=asia-southeast1`
3. 观察任务执行全过程
4. 按 `Ctrl+C` 停止监控

## 🛠️ 技术细节

### 配置信息
- **项目ID**: solar-idea-463423-h8
- **服务名**: reporter-agent
- **区域**: asia-southeast1

### 过滤条件
```bash
resource.type=cloud_run_revision AND resource.labels.service_name=reporter-agent
```

### 默认设置
- Recent模式默认: 20条日志，1小时内
- 输出格式: 表格形式，包含时间戳、级别、内容

## 💡 提示和技巧

1. **性能优化**: 较大的时间范围和条数可能需要更长时间
2. **实时监控**: tail模式适合监控任务执行过程
3. **问题排查**: recent模式适合回溯分析问题
4. **组合使用**: 先用recent了解历史，再用tail监控新变化

---

**💻 快速开始**: `./view_logs.sh recent` 查看最新日志状态！ 