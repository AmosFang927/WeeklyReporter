#!/usr/bin/env python3
"""
PostBack + Vertex AI 完整查询系统
支持自然语言查询您的PostBack Google Cloud SQL数据
"""

import asyncio
import asyncpg
import json
import sys
from datetime import datetime, timedelta

# 尝试导入Vertex AI，如果失败则使用基础版本
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    HAS_VERTEX_AI = True
except ImportError:
    HAS_VERTEX_AI = False
    print("⚠️  Vertex AI未安装，使用基础查询模式")

# PostBack 数据库配置
POSTBACK_DB_CONFIG = {
    "host": "34.124.206.16",
    "port": 5432,
    "database": "postback_db",
    "user": "postback_admin",
    "password": "ByteC2024PostBack_CloudSQL_20250708"
}

# Vertex AI 配置
VERTEX_AI_CONFIG = {
    "project_id": "solar-idea-463423-h8",
    "location": "asia-southeast1",
    "model_name": "gemini-1.5-pro"
}

class PostbackAIQuery:
    def __init__(self):
        self.db_conn = None
        self.ai_model = None
        self.has_ai = HAS_VERTEX_AI
        
        if self.has_ai:
            self.setup_vertex_ai()
    
    def setup_vertex_ai(self):
        """初始化Vertex AI"""
        try:
            vertexai.init(
                project=VERTEX_AI_CONFIG["project_id"],
                location=VERTEX_AI_CONFIG["location"]
            )
            self.ai_model = GenerativeModel(VERTEX_AI_CONFIG["model_name"])
            print("✅ Vertex AI 初始化成功")
        except Exception as e:
            print(f"⚠️  Vertex AI 初始化失败: {e}")
            print("💡 使用基础查询模式")
            self.has_ai = False
    
    async def connect_database(self):
        """连接到postback数据库"""
        try:
            connection_string = f"postgresql://{POSTBACK_DB_CONFIG['user']}:{POSTBACK_DB_CONFIG['password']}@{POSTBACK_DB_CONFIG['host']}:{POSTBACK_DB_CONFIG['port']}/{POSTBACK_DB_CONFIG['database']}"
            self.db_conn = await asyncpg.connect(connection_string)
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    async def get_database_schema(self):
        """获取数据库表结构"""
        schema_info = """
PostBack数据库表结构：

1. conversions (基础转化表)
   - conversion_id: 转化ID
   - offer_name: 广告活动名称
   - usd_payout: 美元收益
   - usd_sale_amount: 美元销售金额
   - created_at: 创建时间
   - aff_sub: 联盟子ID

2. partner_conversions (合作伙伴转化表)
   - conversion_id: 转化ID
   - offer_name: 广告活动名称
   - usd_earning: 美元收益
   - usd_sale_amount: 美元销售金额
   - created_at: 创建时间
   - media_id: 媒体ID
   - sub_id: 子ID

3. postback_conversions (PostBack转化表)
   - conversion_id: 转化ID
   - offer_name: 广告活动名称
   - usd_payout: 美元收益
   - usd_sale_amount: 美元销售金额
   - created_at: 创建时间
   - status: 状态

4. postback_conversions_rector (Rector转化表)
   - conversion_id: 转化ID
   - offer_name: 广告活动名称
   - usd_earning: 美元收益
   - created_at: 创建时间
   - status: 状态
        """
        return schema_info
    
    def natural_language_to_sql(self, question):
        """将自然语言转换为SQL查询"""
        if not self.has_ai:
            return self.basic_query_mapping(question)
        
        try:
            schema = self.get_database_schema()
            
            prompt = f"""
你是一个PostgreSQL专家。基于PostBack转化数据库，将自然语言问题转换为SQL查询。

{schema}

重要规则：
1. 只返回SQL查询，不要解释
2. 使用PostgreSQL语法
3. 时间查询使用 DATE(created_at) = CURRENT_DATE 表示今天
4. 使用 created_at >= CURRENT_DATE - INTERVAL '7 days' 表示最近7天
5. 主要查询conversions表（基础转化数据）
6. 收入字段使用usd_payout
7. 只允许SELECT查询

用户问题：{question}

SQL查询：
"""
            
            response = self.ai_model.generate_content(prompt)
            sql_query = response.text.strip()
            
            # 清理SQL查询
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
        except Exception as e:
            print(f"❌ AI查询生成失败: {e}")
            return self.basic_query_mapping(question)
    
    def basic_query_mapping(self, question):
        """基础查询映射（无AI时使用）"""
        question_lower = question.lower()
        
        if "今天" in question and "转化" in question:
            return "SELECT COUNT(*) as total_conversions FROM conversions WHERE DATE(created_at) = CURRENT_DATE"
        
        elif "今天" in question and "收入" in question:
            return "SELECT SUM(usd_payout) as total_revenue FROM conversions WHERE DATE(created_at) = CURRENT_DATE"
        
        elif "offer" in question_lower and "最多" in question:
            return """
            SELECT offer_name, COUNT(*) as count, SUM(usd_payout) as revenue
            FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY offer_name
            ORDER BY count DESC
            LIMIT 10
            """
        
        elif "最近" in question and "天" in question:
            return """
            SELECT DATE(created_at) as date, COUNT(*) as conversions, SUM(usd_payout) as revenue
            FROM conversions 
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date
            """
        
        elif "小时" in question:
            return """
            SELECT EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as conversions, SUM(usd_payout) as revenue
            FROM conversions 
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
            """
        
        else:
            return "SELECT COUNT(*) as total_conversions, SUM(usd_payout) as total_revenue FROM conversions WHERE DATE(created_at) = CURRENT_DATE"
    
    async def execute_query(self, sql_query):
        """执行SQL查询"""
        try:
            # 安全检查
            if not sql_query.strip().upper().startswith('SELECT'):
                return {"error": "只允许SELECT查询"}
            
            result = await self.db_conn.fetch(sql_query)
            return [dict(row) for row in result]
        except Exception as e:
            return {"error": f"查询执行失败: {e}"}
    
    def analyze_result(self, result, question):
        """分析查询结果"""
        if not result or isinstance(result, dict):
            return "❌ 查询结果为空或出错"
        
        if self.has_ai:
            return self.ai_analyze_result(result, question)
        else:
            return self.basic_analyze_result(result, question)
    
    def ai_analyze_result(self, result, question):
        """使用AI分析结果"""
        try:
            prompt = f"""
基于以下PostBack转化数据查询结果，用中文简洁回答用户问题。

用户问题：{question}

查询结果：
{json.dumps(result, indent=2, ensure_ascii=False)}

请提供：
1. 直接回答问题
2. 关键数据洞察
3. 如果有趋势，简要分析
"""
            
            response = self.ai_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return self.basic_analyze_result(result, question)
    
    def basic_analyze_result(self, result, question):
        """基础结果分析"""
        if len(result) == 0:
            return "📊 没有找到相关数据"
        
        if len(result) == 1:
            row = result[0]
            if 'total_conversions' in row:
                return f"📈 今日总转化数: {row['total_conversions']}"
            elif 'total_revenue' in row:
                return f"💰 今日总收入: ${row['total_revenue']:.2f}"
        
        # 多行结果
        if 'offer_name' in result[0]:
            analysis = "🎯 Top Offers:\n"
            for i, row in enumerate(result[:5], 1):
                analysis += f"  {i}. {row['offer_name']}: {row.get('count', 0)} 转化, ${row.get('revenue', 0):.2f}\n"
            return analysis
        
        elif 'date' in result[0]:
            analysis = "📅 趋势分析:\n"
            for row in result:
                analysis += f"  {row['date']}: {row.get('conversions', 0)} 转化, ${row.get('revenue', 0):.2f}\n"
            return analysis
        
        return f"📊 查询结果：{len(result)} 条记录"
    
    async def ask_question(self, question):
        """完整的问答流程"""
        print(f"\n🤔 问题: {question}")
        print("-" * 50)
        
        # 生成SQL查询
        sql_query = self.natural_language_to_sql(question)
        print(f"🔍 SQL查询: {sql_query}")
        
        # 执行查询
        result = await self.execute_query(sql_query)
        
        if isinstance(result, dict) and 'error' in result:
            print(f"❌ {result['error']}")
            return
        
        # 分析结果
        analysis = self.analyze_result(result, question)
        print(f"📊 分析结果:\n{analysis}")
        
        return result
    
    async def interactive_mode(self):
        """交互式问答模式"""
        print("\n🎯 进入交互式查询模式")
        print("💡 您可以用自然语言询问PostBack数据")
        print("📝 示例问题:")
        print("  - 今天有多少转化？")
        print("  - 今天的总收入是多少？")
        print("  - 哪个offer转化最多？")
        print("  - 最近7天的趋势如何？")
        print("  - 今天各小时的转化情况？")
        print("输入 'exit' 退出\n")
        
        while True:
            try:
                question = input("🔍 请输入问题: ").strip()
                
                if question.lower() in ['exit', 'quit', '退出']:
                    print("👋 再见！")
                    break
                
                if not question:
                    continue
                
                await self.ask_question(question)
                
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 处理问题时出错: {e}")
    
    async def demo_queries(self):
        """演示查询"""
        demo_questions = [
            "今天有多少转化？",
            "今天的总收入是多少？",
            "哪个offer转化最多？",
            "最近7天的趋势如何？",
            "今天各小时的转化情况？"
        ]
        
        print("\n🎯 演示查询:")
        print("="*50)
        
        for question in demo_questions:
            await self.ask_question(question)
            print()
    
    async def close(self):
        """关闭连接"""
        if self.db_conn:
            await self.db_conn.close()
            print("✅ 数据库连接已关闭")

async def main():
    """主函数"""
    print("🚀 PostBack + Vertex AI 查询系统")
    print("=" * 50)
    
    # 检查系统状态
    if HAS_VERTEX_AI:
        print("🤖 AI模式: 支持自然语言查询")
    else:
        print("📊 基础模式: 支持预定义查询")
    
    system = PostbackAIQuery()
    
    # 连接数据库
    if not await system.connect_database():
        print("❌ 无法连接数据库，程序退出")
        return
    
    try:
        # 检查命令行参数
        if len(sys.argv) > 1:
            if sys.argv[1] == "--demo":
                await system.demo_queries()
            elif sys.argv[1] == "--interactive":
                await system.interactive_mode()
            else:
                # 直接查询
                question = " ".join(sys.argv[1:])
                await system.ask_question(question)
        else:
            # 默认交互模式
            await system.interactive_mode()
    
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
    finally:
        await system.close()

if __name__ == "__main__":
    asyncio.run(main()) 