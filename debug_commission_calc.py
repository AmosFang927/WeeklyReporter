import json
import pandas as pd
import config
from modules.bytec_report_generator import ByteCReportGenerator

def debug_commission_calculation():
    """调试佣金计算过程"""
    print("🔍 开始调试佣金计算过程...")
    
    # 读取原始数据
    with open('output/conversions_20250626_203038.json', 'r') as f:
        raw_data = json.load(f)
    
    # 创建ByteC报表生成器
    generator = ByteCReportGenerator()
    
    # 预处理数据
    df = generator._prepare_data(raw_data)
    print(f"预处理后数据量: {len(df)} 条记录")
    
    # 专门查看RAMPUP + Shopee ID的记录
    rampup_shopee_records = df[(df['offer_name'] == 'Shopee ID (Media Buyers) - CPS') & (df['aff_sub1'] == 'RAMPUP')]
    print(f"\nRAMPUP + Shopee ID记录数: {len(rampup_shopee_records)}")
    
    if len(rampup_shopee_records) > 0:
        print("前几条记录的详细信息:")
        for idx, (_, record) in enumerate(rampup_shopee_records.head(3).iterrows()):
            print(f"\n记录 {idx+1}:")
            print(f"  Sale Amount: {record.get('sale_amount', 'N/A')}")
            print(f"  Payout: {record.get('payout', 'N/A')}")
            print(f"  Platform: {record.get('api_source', 'N/A')}")
            print(f"  Source: {record.get('aff_sub1', 'N/A')}")
        
        # 计算这个组合的汇总数据
        sales_amount = rampup_shopee_records['sale_amount'].sum()
        estimated_earning = rampup_shopee_records['payout'].sum()
        conversions = len(rampup_shopee_records)
        
        print(f"\n汇总数据:")
        print(f"  总销售额: ${sales_amount:.2f}")
        print(f"  总收益: ${estimated_earning:.2f}")
        print(f"  转换数: {conversions}")
        
        # 计算平均佣金率
        avg_commission_rate = 0.0
        if sales_amount > 0:
            avg_commission_rate = (estimated_earning / sales_amount) * 100
        print(f"  计算的平均佣金率: {avg_commission_rate:.2f}%")
        
        # 获取平台名称
        platform_name = rampup_shopee_records['api_source'].iloc[0] if 'api_source' in rampup_shopee_records.columns else 'Unknown'
        print(f"  平台名称: {platform_name}")
        
        # 获取广告主佣金率
        adv_commission_rate = config.get_adv_commission_rate(platform_name, avg_commission_rate)
        print(f"  广告主佣金率: {adv_commission_rate:.2f}%")
        
        # 获取发布商佣金率
        pub_commission_rate = config.get_pub_commission_rate('RAMPUP', 'Shopee ID (Media Buyers) - CPS')
        print(f"  发布商佣金率: {pub_commission_rate:.2f}%")
        
        # 计算各种佣金
        adv_commission = sales_amount * (adv_commission_rate / 100.0)
        pub_commission = sales_amount * (pub_commission_rate / 100.0)
        bytec_commission = sales_amount * ((adv_commission_rate - pub_commission_rate) / 100.0)
        
        print(f"  广告主佣金: ${adv_commission:.2f}")
        print(f"  发布商佣金: ${pub_commission:.2f}")
        print(f"  ByteC佣金: ${bytec_commission:.2f}")
        
        # 计算ROI
        bytec_roi = 0.0
        if pub_commission > 0:
            bytec_roi = (1 + (adv_commission - pub_commission) / pub_commission) * 100
        print(f"  ByteC ROI: {bytec_roi:.2f}%")

    # 查看Shopee PH的记录
    print("\n" + "="*60)
    shopee_ph_records = df[(df['offer_name'] == 'Shopee PH - CPS') & (df['aff_sub1'] == 'OEM2')]
    print(f"OEM2 + Shopee PH记录数: {len(shopee_ph_records)}")
    
    if len(shopee_ph_records) > 0:
        sales_amount = shopee_ph_records['sale_amount'].sum()
        estimated_earning = shopee_ph_records['payout'].sum()
        conversions = len(shopee_ph_records)
        
        print(f"\n汇总数据:")
        print(f"  总销售额: ${sales_amount:.2f}")
        print(f"  总收益: ${estimated_earning:.2f}")
        print(f"  转换数: {conversions}")
        
        avg_commission_rate = 0.0
        if sales_amount > 0:
            avg_commission_rate = (estimated_earning / sales_amount) * 100
        print(f"  计算的平均佣金率: {avg_commission_rate:.2f}%")
        
        # 获取平台名称
        platform_name = shopee_ph_records['api_source'].iloc[0] if 'api_source' in shopee_ph_records.columns else 'Unknown'
        print(f"  平台名称: {platform_name}")
        
        # 获取广告主佣金率
        adv_commission_rate = config.get_adv_commission_rate(platform_name, avg_commission_rate)
        print(f"  广告主佣金率: {adv_commission_rate:.2f}%")
        
        # 获取发布商佣金率 (YueMeng + Shopee PH)
        pub_commission_rate = config.get_pub_commission_rate('YueMeng', 'Shopee PH - CPS')
        print(f"  发布商佣金率: {pub_commission_rate:.2f}%")

    # 查看YRAC的记录
    print("\n" + "="*60)
    yrac_records = df[(df['offer_name'] == 'Shopee ID (Media Buyers) - CPS') & (df['aff_sub1'] == 'YRAC')]
    print(f"YRAC + Shopee ID记录数: {len(yrac_records)}")
    
    if len(yrac_records) > 0:
        sales_amount = yrac_records['sale_amount'].sum()
        estimated_earning = yrac_records['payout'].sum()
        conversions = len(yrac_records)
        
        print(f"\n汇总数据:")
        print(f"  总销售额: ${sales_amount:.2f}")
        print(f"  总收益: ${estimated_earning:.2f}")
        print(f"  转换数: {conversions}")
        
        avg_commission_rate = 0.0
        if sales_amount > 0:
            avg_commission_rate = (estimated_earning / sales_amount) * 100
        print(f"  计算的平均佣金率: {avg_commission_rate:.2f}%")
        
        # 获取平台名称
        platform_name = yrac_records['api_source'].iloc[0] if 'api_source' in yrac_records.columns else 'Unknown'
        print(f"  平台名称: {platform_name}")
        
        # 获取广告主佣金率
        adv_commission_rate = config.get_adv_commission_rate(platform_name, avg_commission_rate)
        print(f"  广告主佣金率: {adv_commission_rate:.2f}%")
        
        # 获取发布商佣金率 (YRAC + Shopee ID)
        pub_commission_rate = config.get_pub_commission_rate('YRAC', 'Shopee ID (Media Buyers) - CPS')
        print(f"  发布商佣金率: {pub_commission_rate:.2f}%")

def test_excel_generation():
    """测试Excel生成过程"""
    print("\n🔍 测试Excel生成过程...")
    
    # 读取原始数据
    with open('output/conversions_20250626_203038.json', 'r') as f:
        raw_data = json.load(f)
    
    # 创建ByteC报表生成器
    generator = ByteCReportGenerator()
    
    # 预处理数据
    df = generator._prepare_data(raw_data)
    
    # 创建汇总数据
    summary_data = generator._create_offer_summary(df)
    
    print("生成的汇总数据:")
    for idx, row in summary_data.iterrows():
        if 'RAMPUP' in str(row['Partner']) or 'Shopee PH' in str(row['Offer Name']) or 'YRAC' in str(row['Partner']):
            print(f"\nOffer: {row['Offer Name']}")
            print(f"Partner: {row['Partner']}")
            print(f"Platform: {row['Platform']}")
            print(f"Avg Commission Rate: {row['Avg. Commission Rate']}%")
            print(f"Adv Commission Rate: {row['Adv Commission Rate']}%")
            print(f"Pub Commission Rate: {row['Pub Commission Rate']}%")

if __name__ == "__main__":
    debug_commission_calculation()
    test_excel_generation() 