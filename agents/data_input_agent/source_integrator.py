#!/usr/bin/env python3
"""
数据源集成器
统一处理来自不同源的数据：postback、API拉取等
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """数据源类型枚举"""
    POSTBACK = "postback"
    API_PULL = "api_pull"
    MANUAL_IMPORT = "manual_import"
    BATCH_UPLOAD = "batch_upload"


class DataSourceIntegrator:
    """数据源集成器"""
    
    def __init__(self):
        self.supported_sources = {
            DataSourceType.POSTBACK: self._process_postback_data,
            DataSourceType.API_PULL: self._process_api_data,
            DataSourceType.MANUAL_IMPORT: self._process_manual_data,
            DataSourceType.BATCH_UPLOAD: self._process_batch_data
        }
    
    def integrate_data(self, data: Dict[str, Any], source_type: DataSourceType) -> Dict[str, Any]:
        """
        集成数据的主要方法
        
        Args:
            data: 原始数据
            source_type: 数据源类型
            
        Returns:
            标准化后的数据
        """
        try:
            if source_type not in self.supported_sources:
                raise ValueError(f"Unsupported source type: {source_type}")
            
            # 调用对应的处理方法
            processor = self.supported_sources[source_type]
            standardized_data = processor(data)
            
            # 添加元数据
            standardized_data['_metadata'] = {
                'source_type': source_type.value,
                'processed_at': datetime.now().isoformat(),
                'processor_version': '1.0.0'
            }
            
            return standardized_data
            
        except Exception as e:
            logger.error(f"数据集成失败: {str(e)}")
            raise
    
    def _process_postback_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理postback数据"""
        logger.info("Processing postback data")
        
        # 标准化postback数据结构
        standardized = {
            'conversion_id': data.get('conversion_id'),
            'offer_id': data.get('offer_id'),
            'offer_name': data.get('offer_name'),
            'partner_name': self._extract_partner_from_postback(data),
            'conversion_time': data.get('datetime_conversion'),
            'order_id': data.get('order_id'),
            'amounts': {
                'local': data.get('sale_amount_local'),
                'usd': data.get('usd_sale_amount'),
                'myr': data.get('myr_sale_amount')
            },
            'payouts': {
                'local': data.get('payout_local'),
                'usd': data.get('usd_payout'),
                'myr': data.get('myr_payout')
            },
            'currency': data.get('conversion_currency'),
            'status': data.get('status'),
            'raw_data': data
        }
        
        return standardized
    
    def _process_api_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理API拉取数据"""
        logger.info("Processing API data")
        
        # 标准化API数据结构
        conversions = []
        if 'data' in data and 'conversions' in data['data']:
            for conv in data['data']['conversions']:
                standardized_conv = {
                    'conversion_id': conv.get('id'),
                    'offer_id': conv.get('offer_id'),
                    'offer_name': conv.get('offer_name'),
                    'partner_name': self._extract_partner_from_api(conv),
                    'conversion_time': conv.get('datetime_conversion'),
                    'order_id': conv.get('order_id'),
                    'amounts': {
                        'local': conv.get('sale_amount_local'),
                        'usd': conv.get('usd_sale_amount'),
                        'myr': conv.get('myr_sale_amount')
                    },
                    'payouts': {
                        'local': conv.get('payout_local'),
                        'usd': conv.get('usd_payout'),
                        'myr': conv.get('myr_payout')
                    },
                    'currency': conv.get('conversion_currency'),
                    'status': conv.get('status'),
                    'raw_data': conv
                }
                conversions.append(standardized_conv)
        
        return {
            'conversions': conversions,
            'total_count': len(conversions),
            'metadata': data.get('metadata', {})
        }
    
    def _process_manual_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理手动导入数据"""
        logger.info("Processing manual import data")
        
        # 基本的手动数据处理
        return {
            'data': data,
            'processed': True,
            'manual_import': True
        }
    
    def _process_batch_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理批量上传数据"""
        logger.info("Processing batch upload data")
        
        # 批量数据处理
        return {
            'batch_data': data,
            'processed': True,
            'batch_size': len(data) if isinstance(data, list) else 1
        }
    
    def _extract_partner_from_postback(self, data: Dict[str, Any]) -> str:
        """从postback数据中提取partner信息"""
        # 优先使用aff_sub2，如果没有则使用offer_name
        if data.get('aff_sub2'):
            return data['aff_sub2']
        elif data.get('offer_name'):
            # 从offer_name解析partner
            offer_name = data['offer_name'].lower()
            if 'rampup' in offer_name:
                return 'RAMPUP'
            elif 'deepleaper' in offer_name:
                return 'DeepLeaper'
            elif 'bytec' in offer_name:
                return 'ByteC'
        
        return 'UNKNOWN'
    
    def _extract_partner_from_api(self, data: Dict[str, Any]) -> str:
        """从API数据中提取partner信息"""
        # 类似的逻辑，但适应API数据结构
        return self._extract_partner_from_postback(data)
    
    def get_supported_sources(self) -> List[str]:
        """获取支持的数据源类型"""
        return [source.value for source in DataSourceType]
    
    def validate_data_structure(self, data: Dict[str, Any], source_type: DataSourceType) -> bool:
        """验证数据结构是否符合要求"""
        if source_type == DataSourceType.POSTBACK:
            required_fields = ['conversion_id']
            return all(field in data for field in required_fields)
        elif source_type == DataSourceType.API_PULL:
            return 'data' in data or 'conversions' in data
        else:
            return isinstance(data, dict) 