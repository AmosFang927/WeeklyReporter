# WeeklyReporter 新功能说明

## 新增功能

### 1. 数据获取限制 (--limit)

可以设置最大记录数限制，用于测试或快速验证。

**使用方法：**
```bash
# 只获取100条记录
python main.py --limit 100

# 只获取50条记录用于测试
python main.py --limit 50 --start-date 2025-06-17 --end-date 2025-06-18
```

**配置说明：**
- 在 `config.py` 中的 `MAX_RECORDS_LIMIT` 变量控制
- 默认值为 `None`（无限制）
- 通过命令行 `--limit` 参数可以临时设置

### 2. Partner过滤 (--partner)

可以指定只处理特定的Partner，只生成该Partner的报告和邮件。

**使用方法：**
```bash
# 只处理RAMPUP Partner
python main.py --partner RAMPUP

# 只处理OPPO Partner
python main.py --partner OPPO

# 只处理VIVO Partner
python main.py --partner VIVO
```

**配置说明：**
- 在 `config.py` 中的 `TARGET_PARTNER` 变量控制
- 默认值为 `None`（处理所有Partner）
- 通过命令行 `--partner` 参数可以临时设置
- 只会生成指定Partner的Excel文件
- 只会发送该Partner的邮件（如果启用）

### 3. 组合使用

两个功能可以组合使用：

```bash
# 限制100条记录，只处理RAMPUP Partner
python main.py --limit 100 --partner RAMPUP --start-date 2025-06-17 --end-date 2025-06-18
```

## 实际使用场景

### 场景1：快速测试
```bash
# 用少量数据快速测试系统
python main.py --limit 10 --partner RAMPUP
```

### 场景2：单独处理某个Partner
```bash
# 只为RAMPUP生成报告和发送邮件
python main.py --partner RAMPUP
```

### 场景3：开发调试
```bash
# 限制数据量进行开发调试
python main.py --limit 50
```

## 配置文件说明

在 `config.py` 中新增的配置项：

```python
# 数据限制配置
MAX_RECORDS_LIMIT = None  # 最大记录数限制，None表示不限制

# Partner过滤配置  
TARGET_PARTNER = None  # 指定要处理的Partner，None表示处理所有Partner
```

## 相关函数

新增的辅助函数：

- `config.get_target_partners()` - 获取要处理的Partner列表
- `config.is_partner_enabled(partner_name)` - 检查Partner是否在处理范围内

## 影响范围

这两个新功能会影响：

1. **数据获取** - API获取数据时会应用记录数限制
2. **数据处理** - 只处理指定Partner的数据
3. **文件生成** - 只生成指定Partner的Excel文件
4. **邮件发送** - 只发送指定Partner的邮件
5. **飞书上传** - 只上传指定Partner的文件

## 向后兼容性

- 不使用新参数时，系统行为与之前完全一致
- 所有现有功能保持不变
- 配置文件中的默认值确保兼容性 