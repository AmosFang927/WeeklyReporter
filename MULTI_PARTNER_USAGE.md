# 多个Partner功能使用说明

## 功能概述

现在WeeklyReporter支持在单次运行中指定多个Partner进行处理，通过命令行参数`--partner`可以指定一个或多个Partner。

## 使用方法

### 1. 处理单个Partner
```bash
# 只处理RAMPUP
python main.py --partner RAMPUP

# 只处理YueMeng
python main.py --partner YueMeng
```

### 2. 处理多个Partner（用逗号分隔）
```bash
# 处理RAMPUP和YueMeng
python main.py --partner RAMPUP,YueMeng

# 处理所有三个Partner
python main.py --partner RAMPUP,YueMeng,TestPartner
```

### 3. 结合其他参数使用
```bash
# 限制100条记录，只处理RAMPUP和YueMeng
python main.py --limit 100 --partner RAMPUP,YueMeng

# 指定日期范围，处理多个Partner
python main.py --start-date 2025-06-17 --end-date 2025-06-18 --partner RAMPUP,YueMeng

# 完整示例：限制记录数、指定日期、处理多个Partner
python main.py --limit 100 --start-date 2025-06-17 --end-date 2025-06-18 --partner RAMPUP,YueMeng
```

### 4. 处理所有Partner
```bash
# 明确指定处理所有Partner
python main.py --partner all

# 不指定Partner（默认处理所有Partner）
python main.py
```

## 命令行参数格式

### --partner 参数说明
- **单个Partner**: `--partner RAMPUP`
- **多个Partner**: `--partner RAMPUP,YueMeng`（用逗号分隔，不要有空格）
- **所有Partner**: `--partner all`（明确指定处理所有Partner）
- **包含空格的处理**: 系统会自动去除Partner名称前后的空格
- **无效Partner**: 如果指定的Partner不存在，系统会显示警告并跳过

### 支持的Partner列表
当前系统支持以下Partner（在`config.py`中配置）：
- `RAMPUP` - 包含RAMPUP、RPID*等Sources
- `YueMeng` - 包含OEM2、OEM3等Sources  
- `MKK` - 包含MKK等Sources
- `ByteC` - 特殊报表Partner，处理所有Sources
- `TestPartner` - 测试用Partner

## 处理逻辑

1. **参数解析**: 系统解析`--partner`参数，将逗号分隔的字符串转换为Partner列表
2. **配置应用**: 将指定的Partner列表应用到全局配置`config.TARGET_PARTNER`
3. **数据过滤**: 在数据处理过程中，只处理指定Partner对应的Sources数据
4. **文件生成**: 只为指定的Partner生成Excel文件
5. **邮件发送**: 只向指定Partner的收件人发送邮件

## 示例输出

当运行 `python main.py --partner RAMPUP,YueMeng` 时，系统会显示：

```
📋 指定处理的Partner: ['RAMPUP', 'YueMeng']
🎯 实际启用的Partners: ['RAMPUP', 'YueMeng']
   ✅ RAMPUP: True
   ✅ YueMeng: True
   ❌ TestPartner: False
```

## 注意事项

1. **Partner名称大小写敏感**: 确保Partner名称与配置文件中完全一致
2. **逗号分隔无空格**: 多个Partner之间用逗号分隔，不要添加空格
3. **无效Partner处理**: 如果所有指定的Partner都无效，系统会回退到处理所有Partner
4. **配置依赖**: Partner必须在`config.py`的`PARTNER_SOURCES_MAPPING`中预先配置

## 技术实现

### 配置函数更新
- `get_target_partners()`: 支持返回多个Partner的列表
- `is_partner_enabled()`: 支持检查Partner是否在指定的列表中

### 数据结构支持
- `config.TARGET_PARTNER`: 支持字符串（单个）或列表（多个）格式
- 向后兼容：现有的单个Partner功能完全兼容

### 命令行处理
```python
# 多个Partner处理逻辑
target_partners = None
if args.partner:
    target_partners = [p.strip() for p in args.partner.split(',') if p.strip()]
    if len(target_partners) == 1:
        target_partners = target_partners[0]  # 单个Partner保持字符串格式
```

## 测试验证

功能已通过以下测试：
- ✅ 单个Partner处理
- ✅ 多个Partner处理
- ✅ 无效Partner处理
- ✅ 命令行参数解析
- ✅ 配置函数正确性
- ✅ 向后兼容性 