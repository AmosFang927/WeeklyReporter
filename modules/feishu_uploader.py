#!/usr/bin/env python3
"""
飞书上传模块
负责将Excel文件上传到飞书Sheet
"""

import requests
import os
import json
from datetime import datetime
from utils.logger import print_step
import config

try:
    import lark_oapi as lark
    from lark_oapi.api.drive.v1 import *
    LARK_SDK_AVAILABLE = True
except ImportError:
    LARK_SDK_AVAILABLE = False
    print("警告: lark_oapi SDK未安装，将使用REST API方式")

class FeishuUploader:
    """飞书文件上传器"""
    
    def __init__(self, access_token=None):
        self.app_id = config.FEISHU_APP_ID
        self.app_secret = config.FEISHU_APP_SECRET
        self.auth_url = config.FEISHU_AUTH_URL
        self.access_token = access_token  # 如果提供了就直接使用
        self.upload_url = config.FEISHU_UPLOAD_URL
        self.parent_node = config.FEISHU_PARENT_NODE
        self.file_type = config.FEISHU_FILE_TYPE
    
    def authenticate(self):
        """
        使用app_id和app_secret获取tenant_access_token
        
        Returns:
            bool: 认证是否成功
        """
        print_step("飞书认证", "正在获取tenant_access_token...")
        
        try:
            headers = {
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            payload = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            response = requests.post(
                self.auth_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    self.access_token = result['tenant_access_token']
                    token_preview = self.access_token[:8] + "..." if len(self.access_token) > 8 else self.access_token
                    print_step("认证成功", f"✅ 获得tenant_access_token: {token_preview}")
                    return True
                else:
                    error_msg = result.get('msg', '未知错误')
                    print_step("认证失败", f"❌ 飞书认证失败: {error_msg}")
                    return False
            else:
                print_step("认证失败", f"❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print_step("认证异常", f"❌ 认证过程发生异常: {str(e)}")
            return False
    
    def upload_files(self, file_paths):
        """
        批量上传文件到飞书
        
        Args:
            file_paths: 文件路径列表或单个文件路径
        
        Returns:
            dict: 上传结果摘要
        """
        print_step("飞书上传开始", "开始批量上传Excel文件到飞书Sheet")
        
        # 步骤1: 自动认证获取access_token
        if not self.access_token or self.access_token == "your_feishu_access_token_here":
            if not self.authenticate():
                return {
                    'success': False,
                    'uploaded_files': [],
                    'failed_files': [],
                    'error': '飞书认证失败'
                }
        
        # 确保file_paths是列表
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        # 过滤存在的文件
        existing_files = [f for f in file_paths if os.path.exists(f)]
        missing_files = [f for f in file_paths if not os.path.exists(f)]
        
        if missing_files:
            print_step("文件检查", f"以下文件不存在，跳过上传: {missing_files}")
        
        if not existing_files:
            print_step("上传错误", "没有可用的文件进行上传")
            return {
                'success': False,
                'uploaded_files': [],
                'failed_files': [],
                'error': '没有可用的文件'
            }
        
        print_step("文件检查", f"准备上传 {len(existing_files)} 个文件")
        
        # 逐个上传文件
        uploaded_files = []
        failed_files = []
        
        for file_path in existing_files:
            result = self._upload_single_file(file_path)
            if result['success']:
                uploaded_files.append(result)
            else:
                failed_files.append({
                    'file': file_path,
                    'error': result['error']
                })
        
        # 生成总结
        summary = {
            'success': len(failed_files) == 0,
            'uploaded_files': uploaded_files,
            'failed_files': failed_files,
            'total_files': len(existing_files),
            'success_count': len(uploaded_files),
            'failed_count': len(failed_files)
        }
        
        self._print_upload_summary(summary)
        return summary
    
    def _upload_single_file(self, file_path):
        """
        上传单个文件到飞书
        
        Args:
            file_path: 文件路径
        
        Returns:
            dict: 单个文件上传结果
        """
        filename = os.path.basename(file_path)
        print_step("文件上传", f"正在上传: {filename}")
        
        try:
            # 准备请求头
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 按照官方curl示例准备multipart表单数据
            with open(file_path, 'rb') as f:
                files = {
                    'file': (filename, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                }
                
                data = {
                    'file_name': filename,
                    'parent_type': 'explorer', 
                    'parent_node': self.parent_node,
                    'size': str(file_size)
                }
                
                # 发送请求
                response = requests.post(
                    self.upload_url,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=60
                )
            
            # 检查响应
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    file_info = result.get('data', {})
                    file_token = file_info.get('file_token', 'N/A')
                    print_step("上传成功", f"✅ {filename} 上传成功，文件ID: {file_token}")
                    return {
                        'success': True,
                        'filename': filename,
                        'file_path': file_path,
                        'file_token': file_token,
                        'file_id': file_token,  # 为了兼容旧代码
                        'url': file_info.get('url'),
                        'response': result
                    }
                else:
                    error_msg = f"API错误 {result.get('code')}: {result.get('msg', '未知错误')}"
                    print_step("上传失败", f"❌ {filename} 上传失败: {error_msg}")
                    return {
                        'success': False,
                        'filename': filename,
                        'file_path': file_path,
                        'error': error_msg,
                        'response': result
                    }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                print_step("上传失败", f"❌ {filename} 上传失败: {error_msg}")
                return {
                    'success': False,
                    'filename': filename,
                    'file_path': file_path,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"上传异常: {str(e)}"
            print_step("上传异常", f"❌ {filename} 上传异常: {error_msg}")
            return {
                'success': False,
                'filename': filename,
                'file_path': file_path,
                'error': error_msg
            }
    
    def _print_upload_summary(self, summary):
        """打印上传结果摘要"""
        print_step("上传摘要", "飞书文件上传结果:")
        
        print(f"📊 上传统计:")
        print(f"   - 总文件数: {summary['total_files']}")
        print(f"   - 成功上传: {summary['success_count']}")
        print(f"   - 上传失败: {summary['failed_count']}")
        print(f"   - 整体状态: {'✅ 全部成功' if summary['success'] else '❌ 部分失败'}")
        
        if summary['uploaded_files']:
            print(f"📄 成功上传的文件:")
            for file_info in summary['uploaded_files']:
                print(f"   ✅ {file_info['filename']}")
                if file_info.get('file_token'):
                    print(f"      - 文件ID: {file_info['file_token']}")
                if file_info.get('url'):
                    print(f"      - 访问链接: {file_info['url']}")
        
        if summary['failed_files']:
            print(f"❌ 上传失败的文件:")
            for file_info in summary['failed_files']:
                print(f"   ❌ {os.path.basename(file_info['file'])}: {file_info['error']}")

    def test_connection(self):
        """测试飞书API连接"""
        print_step("连接测试", "正在测试飞书API连接...")
        
        # 步骤1: 测试认证
        if not self.access_token or self.access_token == "your_feishu_access_token_here":
            print_step("认证测试", "正在测试飞书认证...")
            if not self.authenticate():
                return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # 使用获取文件夹信息的API测试连接
            test_url = "https://open.feishu.cn/open-apis/drive/v1/files"
            response = requests.get(
                test_url,
                headers=headers,
                params={'parent_token': self.parent_node},
                timeout=10
            )
            
            if response.status_code == 200:
                print_step("连接测试", "✅ 飞书API连接正常")
                return True
            else:
                print_step("连接测试", f"❌ 飞书API连接失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print_step("连接测试", f"❌ 飞书API连接异常: {str(e)}")
            return False

# 便捷函数
def upload_to_feishu(file_paths, access_token=None):
    """
    便捷的上传函数
    
    Args:
        file_paths: 文件路径列表或单个文件路径
        access_token: 飞书访问令牌
    
    Returns:
        dict: 上传结果摘要
    """
    uploader = FeishuUploader(access_token)
    return uploader.upload_files(file_paths)

def test_feishu_connection(access_token=None):
    """
    测试飞书连接的便捷函数
    
    Args:
        access_token: 飞书访问令牌
    
    Returns:
        bool: 连接是否成功
    """
    uploader = FeishuUploader(access_token)
    return uploader.test_connection() 