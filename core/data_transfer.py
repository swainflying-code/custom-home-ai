"""
数据传递模块 - 客户洞察到设计辅助
确保两个模块之间的数据无缝传递
"""

from typing import Dict, Any, Optional
from core.database import db
import streamlit as st

class DataTransferManager:
    """数据传递管理器"""
    
    @staticmethod
    def get_customer_insight_data(customer_id: str) -> Optional[Dict[str, Any]]:
        """
        从客户洞察模块获取客户数据
        
        Args:
            customer_id: 客户ID
            
        Returns:
            dict: 客户洞察数据，包含7大栏目所有信息
        """
        try:
            customers = db.find("customers", {"id": customer_id})
            if customers and len(customers) > 0:
                return customers[0]
            return None
        except Exception as e:
            print(f"获取客户洞察数据失败: {e}")
            return None
    
    @staticmethod
    def prepare_data_for_design_assistant(customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将客户洞察数据整理为设计辅助模块可用的格式
        
        Args:
            customer_data: 原始客户数据
            
        Returns:
            dict: 整理后的数据，包含设计辅助所需的关键信息
        """
        if not customer_data:
            return {}
        
        # 提取关键信息，按设计辅助模块需求组织
        prepared_data = {
            # 基础信息
            "customer_id": customer_data.get("id"),
            "customer_name": customer_data.get("name", customer_data.get("customer_code", "未知客户")),
            "customer_code": customer_data.get("customer_code"),
            
            # 房屋信息（用于空间设计）
            "house_type": customer_data.get("house_type", ""),
            "renovation_type": customer_data.get("renovation_type", ""),
            "renovation_progress": customer_data.get("renovation_progress", ""),
            "house_area": customer_data.get("house_area", ""),
            "custom_budget": customer_data.get("custom_budget", ""),
            "custom_spaces": customer_data.get("custom_spaces", []),
            
            # 产品偏好（用于材质和风格推荐）
            "material_preference": customer_data.get("material_preference", ""),
            "color_preference": customer_data.get("color_preference", []),
            "style_preference": customer_data.get("style_preference", []),
            "custom_style": customer_data.get("custom_style", ""),
            "focus_points": customer_data.get("focus_points", []),
            
            # 生活方式（用于个性化设计）
            "life_style": customer_data.get("life_style", ""),
            "family_members": customer_data.get("family_members", []),
            "dining_count": customer_data.get("dining_count", ""),
            "design_focus": customer_data.get("design_focus", []),
            "storage_preference": customer_data.get("storage_preference", ""),
            "material_combination": customer_data.get("material_combination", ""),
            "ideal_home": customer_data.get("ideal_home", ""),
            
            # 竞品信息（用于差异化设计）
            "has_competitor": customer_data.get("has_competitor", "否"),
            "competitor_info": customer_data.get("competitor_info", ""),
            
            # 沟通转化信息（用于方案优化）
            "quote_type": customer_data.get("quote_type", ""),
            "quote_attitude": customer_data.get("quote_attitude", ""),
            
            # 需求补充（将在设计辅助中完善）
            "additional_notes": customer_data.get("additional_notes", ""),
            "special_requirements": customer_data.get("special_requirements", ""),
        }
        
        return prepared_data
    
    @staticmethod
    def save_design_assistant_data(customer_id: str, design_data: Dict[str, Any]) -> bool:
        """
        保存设计辅助模块的数据
        
        Args:
            customer_id: 客户ID
            design_data: 设计辅助数据
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 准备数据
            data = {
                "customer_id": customer_id,
                "design_preferences": design_data.get("design_preferences", {}),
                "space_requirements": design_data.get("space_requirements", {}),
                "material_selections": design_data.get("material_selections", {}),
                "created_at": "now()",
                "updated_at": "now()"
            }
            
            # 插入或更新设计需求表
            result = db.upsert("design_requests", data, {"customer_id": customer_id})
            return result is not None
        except Exception as e:
            print(f"保存设计辅助数据失败: {e}")
            return False
    
    @staticmethod
    def get_design_assistant_data(customer_id: str) -> Optional[Dict[str, Any]]:
        """
        获取设计辅助模块的数据
        
        Args:
            customer_id: 客户ID
            
        Returns:
            dict: 设计辅助数据
        """
        try:
            designs = db.find("design_requests", {"customer_id": customer_id})
            if designs and len(designs) > 0:
                return designs[0]
            return None
        except Exception as e:
            print(f"获取设计辅助数据失败: {e}")
            return None

# 全局实例
data_transfer_manager = DataTransferManager()

def transfer_customer_to_design(customer_id: str) -> bool:
    """
    将客户洞察数据传递到设计辅助模块
    
    这是主接口函数，在设计辅助模块中调用
    
    Args:
        customer_id: 客户ID
        
    Returns:
        bool: 是否成功传递
    """
    # 1. 获取客户洞察数据
    customer_data = data_transfer_manager.get_customer_insight_data(customer_id)
    if not customer_data:
        print(f"未找到客户ID: {customer_id}")
        return False
    
    # 2. 准备数据
    design_data = data_transfer_manager.prepare_data_for_design_assistant(customer_data)
    
    # 3. 保存到设计辅助表
    success = data_transfer_manager.save_design_assistant_data(customer_id, design_data)
    
    if success:
        print(f"成功将客户 {customer_id} 的数据传递到设计辅助模块")
    else:
        print(f"传递客户 {customer_id} 数据失败")
    
    return success
