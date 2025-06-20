#!/usr/bin/env python3
"""
Involve Asia API 模块
负责从Involve Asia获取conversion数据
"""

import requests
import json
import time
from utils.logger import print_step
import config

class InvolveAsiaAPI:
    """Involve Asia API客户端"""
    
    def __init__(self, api_secret=None, api_key=None):
        # 使用配置文件中的值或传入的值
        self.api_secret = api_secret or config.INVOLVE_ASIA_API_SECRET
        self.api_key = api_key or config.INVOLVE_ASIA_API_KEY
        
        # API端点
        self.auth_url = config.INVOLVE_ASIA_AUTH_URL
        self.conversions_url = config.INVOLVE_ASIA_CONVERSIONS_URL
        
        # 认证token
        self.token = None
    
    def authenticate(self):
        """执行API认证"""
        print_step("认证步骤", "正在执行API认证...")
        
        headers = {"Accept": "application/json"}
        data = {
            "secret": self.api_secret,
            "key": self.api_key
        }
        
        try:
            response = requests.post(
                self.auth_url, 
                headers=headers, 
                data=data, 
                timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "data" in result and "token" in result["data"]:
                self.token = result["data"]["token"]
                token_preview = self.token[:8] + "..." if len(self.token) > 8 else self.token
                print_step("认证成功", f"获得Token: {token_preview}")
                return True
            else:
                print_step("认证失败", f"响应结构不符合预期: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            print_step("认证失败", f"请求错误: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            print_step("认证失败", f"JSON解析错误: {str(e)}")
            return False
    
    def get_conversions(self, start_date, end_date, currency=None):
        """获取指定日期范围的所有conversion数据"""
        if not self.token:
            print_step("数据获取失败", "没有有效的认证token")
            return None
        
        currency = currency or config.PREFERRED_CURRENCY
        print_step("数据获取", f"正在获取转换数据 ({start_date} 到 {end_date})")
        
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
        all_conversions = []
        page = 1
        total_count = 0
        total_pages = 0
        pages_fetched = 0
        
        while True:
            print(f"\n🔄 正在获取第 {page} 页数据...")
            
            data = {
                "page": str(page),
                "limit": str(config.DEFAULT_PAGE_LIMIT),
                "start_date": start_date,
                "end_date": end_date,
                "filters[preferred_currency]": currency
            }
            
            try:
                response = requests.post(
                    self.conversions_url, 
                    headers=headers, 
                    data=data, 
                    timeout=config.REQUEST_TIMEOUT
                )
                
                # 处理429错误(频率限制)
                if response.status_code == 429:
                    print(f"   ⚠️  遇到频率限制，等待{config.RATE_LIMIT_DELAY}秒后重试...")
                    time.sleep(config.RATE_LIMIT_DELAY)
                    continue  # 重试同一页
                
                response.raise_for_status()
                result = response.json()
                
                if "data" not in result:
                    print_step("数据获取失败", f"响应中没有data字段: {result}")
                    break
                
                data_obj = result["data"]
                
                # 获取分页信息
                if isinstance(data_obj, dict):
                    page_data = data_obj.get("data", [])
                    current_page = data_obj.get("page", page)
                    limit = data_obj.get("limit", config.DEFAULT_PAGE_LIMIT)
                    total_count = data_obj.get("count", 0)
                    next_page = data_obj.get("nextPage")
                    
                    # 计算总页数
                    if total_count > 0:
                        total_pages = (total_count + limit - 1) // limit
                    
                    pages_fetched += 1
                    current_total = len(all_conversions) + len(page_data)
                    
                    print(f"   📊 第 {current_page} 页: 获取到 {len(page_data)} 条记录")
                    print(f"   📈 进度: {current_page}/{total_pages} 页 ({current_total}/{total_count} 条)")
                    
                    # 添加到总数据中
                    all_conversions.extend(page_data)
                    
                    # 检查是否超过记录数限制
                    if config.MAX_RECORDS_LIMIT is not None and len(all_conversions) >= config.MAX_RECORDS_LIMIT:
                        # 截断到指定数量
                        all_conversions = all_conversions[:config.MAX_RECORDS_LIMIT]
                        print(f"⏹️ 已达到记录数限制 ({config.MAX_RECORDS_LIMIT} 条)，停止获取")
                        break
                    
                    # 判断是否还有下一页
                    if not next_page or next_page <= current_page or len(page_data) == 0:
                        print(f"✅ 已获取完所有数据！")
                        break
                    
                    page = next_page
                    
                else:
                    # 旧格式兼容
                    page_data = result["data"] if isinstance(result["data"], list) else []
                    all_conversions.extend(page_data)
                    pages_fetched += 1
                    
                    if len(page_data) < config.DEFAULT_PAGE_LIMIT:
                        break
                    page += 1
                
                # 添加延迟避免请求过快
                time.sleep(config.REQUEST_DELAY)
                
            except requests.exceptions.RequestException as e:
                print_step("数据获取失败", f"第{page}页请求错误: {str(e)}")
                break
            except json.JSONDecodeError as e:
                print_step("数据获取失败", f"第{page}页JSON解析错误: {str(e)}")
                break
        
        if all_conversions:
            # 构造完整结果
            result = {
                "status": "success",
                "message": "Success",
                "data": {
                    "page": 1,
                    "limit": config.DEFAULT_PAGE_LIMIT,
                    "count": total_count,
                    "total_pages": total_pages,
                    "pages_fetched": pages_fetched,
                    "current_page_count": len(all_conversions),
                    "data": all_conversions
                }
            }
            
            print_step("数据获取成功", f"成功获取完整数据: {len(all_conversions)} 条转换记录，共 {pages_fetched} 页")
            return result
        else:
            print_step("数据获取失败", "没有获取到任何数据")
            return None
    
    def get_conversions_default_range(self, currency=None):
        """使用默认日期范围获取数据"""
        start_date, end_date = config.get_default_date_range()
        return self.get_conversions(start_date, end_date, currency)
    
    def save_to_json(self, data, filename=None):
        """保存数据到JSON文件"""
        if not filename:
            filename = config.get_json_filename()
        
        try:
            config.ensure_output_dirs()
            filepath = f"{config.OUTPUT_DIR}/{filename}"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print_step("文件保存", f"数据已保存到: {filepath}")
            return filepath
        except Exception as e:
            print_step("文件保存失败", f"无法保存JSON文件: {str(e)}")
            return None 