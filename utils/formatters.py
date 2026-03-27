"""
数据格式化工具模块
提供各种数据格式化和转换功能
"""

import re
from typing import Any, Optional, Dict, List, Union
from datetime import datetime


class TextFormatter:
    """文本格式化器"""
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """格式化手机号"""
        if not phone:
            return ""
        
        phone = re.sub(r'\D', '', phone)
        if len(phone) == 11:
            return f"{phone[:3]} {phone[3:7]} {phone[7:]}"
        return phone
    
    @staticmethod
    def format_budget(budget: Union[int, float, str]) -> str:
        """格式化预算显示"""
        if not budget:
            return "未设置"
        
        try:
            budget_num = float(budget)
            if budget_num >= 10000:
                return f"{budget_num / 10000:.1f}万元"
            else:
                return f"{budget_num:.0f}元"
        except (ValueError, TypeError):
            return str(budget)
    
    @staticmethod
    def format_house_area(area: Union[int, float, str]) -> str:
        """格式化房屋面积"""
        if not area:
            return "未设置"
        
        try:
            area_num = float(area)
            return f"{area_num:.0f}㎡"
        except (ValueError, TypeError):
            return str(area)
    
    @staticmethod
    def format_date(date_value: Union[str, datetime], format_str: str = '%Y-%m-%d') -> str:
        """格式化日期"""
        if not date_value:
            return "未设置"
        
        try:
            if isinstance(date_value, str):
                # 解析日期字符串
                date_obj = datetime.strptime(date_value, '%Y-%m-%d')
            elif isinstance(date_value, datetime):
                date_obj = date_value
            else:
                return str(date_value)
            
            return date_obj.strftime(format_str)
        except (ValueError, TypeError):
            return str(date_value)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
        """截断文本"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length].rsplit(' ', 1)[0] + suffix
    
    @staticmethod
    def highlight_keywords(text: str, keywords: List[str], 
                          highlight_tag: str = '**') -> str:
        """高亮关键词"""
        if not text or not keywords:
            return text
        
        result = text
        for keyword in keywords:
            if keyword:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                result = pattern.sub(
                    f"{highlight_tag}{keyword}{highlight_tag}",
                    result
                )
        
        return result


class CustomerFormatter:
    """客户数据格式化器"""
    
    @staticmethod
    def format_customer_display(customer: Dict[str, Any]) -> Dict[str, Any]:
        """格式化客户数据显示"""
        if not customer:
            return {}
        
        formatted = customer.copy()
        
        # 格式化手机号
        if 'phone' in formatted:
            formatted['phone_display'] = TextFormatter.format_phone(formatted['phone'])
        
        # 格式化预算
        if 'budget' in formatted:
            formatted['budget_display'] = TextFormatter.format_budget(formatted['budget'])
        
        # 格式化房屋面积
        if 'house_area' in formatted:
            formatted['house_area_display'] = TextFormatter.format_house_area(formatted['house_area'])
        
        # 格式化日期
        if 'created_at' in formatted:
            formatted['created_at_display'] = TextFormatter.format_date(
                formatted['created_at'],
                '%Y年%m月%d日'
            )
        
        if 'updated_at' in formatted:
            formatted['updated_at_display'] = TextFormatter.format_date(
                formatted['updated_at'],
                '%Y年%m月%d日 %H:%M'
            )
        
        # 状态显示
        status_map = {
            'new': '新客户',
            'contacted': '已联系',
            'quoted': '已报价',
            'negotiating': '洽谈中',
            'closed': '已成交',
            'lost': '流失'
        }
        if 'status' in formatted:
            formatted['status_display'] = status_map.get(
                formatted['status'],
                formatted['status']
            )
        
        # 装修类型显示
        decoration_type_map = {
            'full': '全屋定制',
            'partial': '局部改造',
            'furniture': '家具定制',
            'soft': '软装设计'
        }
        if 'decoration_type' in formatted:
            formatted['decoration_type_display'] = decoration_type_map.get(
                formatted['decoration_type'],
                formatted['decoration_type']
            )
        
        return formatted
    
    @staticmethod
    def format_customer_list(customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化客户列表"""
        if not customers:
            return []
        
        return [
            CustomerFormatter.format_customer_display(customer)
            for customer in customers
        ]


class DesignFormatter:
    """设计需求格式化器"""
    
    @staticmethod
    def format_design_display(design: Dict[str, Any]) -> Dict[str, Any]:
        """格式化设计需求显示"""
        if not design:
            return {}
        
        formatted = design.copy()
        
        # 格式化日期
        if 'created_at' in formatted:
            formatted['created_at_display'] = TextFormatter.format_date(
                formatted['created_at'],
                '%Y年%m月%d日 %H:%M'
            )
        
        if 'updated_at' in formatted:
            formatted['updated_at_display'] = TextFormatter.format_date(
                formatted['updated_at'],
                '%Y年%m月%d日 %H:%M'
            )
        
        # 优先级显示
        priority_map = {
            'low': '低',
            'medium': '中',
            'high': '高',
            'urgent': '紧急'
        }
        if 'priority' in formatted:
            formatted['priority_display'] = priority_map.get(
                formatted['priority'],
                formatted['priority']
            )
        
        # 状态显示
        status_map = {
            'pending': '待处理',
            'analyzing': '分析中',
            'designing': '设计中',
            'reviewing': '审核中',
            'completed': '已完成',
            'cancelled': '已取消'
        }
        if 'status' in formatted:
            formatted['status_display'] = status_map.get(
                formatted['status'],
                formatted['status']
            )
        
        # 截断需求描述
        if 'requirement_text' in formatted:
            formatted['requirement_summary'] = TextFormatter.truncate_text(
                formatted['requirement_text'],
                max_length=100
            )
        
        return formatted


class AIResponseFormatter:
    """AI响应格式化器"""
    
    @staticmethod
    def format_ai_analysis(analysis_text: str) -> str:
        """格式化AI分析结果"""
        if not analysis_text:
            return ""
        
        # 添加Markdown格式优化
        formatted = analysis_text
        
        # 确保标题正确格式
        formatted = re.sub(r'^##\s+(.+)$', r'**\1**', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^###\s+(.+)$', r'**\1**', formatted, flags=re.MULTILINE)
        
        # 优化列表显示
        formatted = re.sub(r'^\*\s+(.+)$', r'• \1', formatted, flags=re.MULTILINE)
        
        return formatted
    
    @staticmethod
    def extract_key_points(analysis_text: str) -> List[str]:
        """从AI分析中提取关键点"""
        if not analysis_text:
            return []
        
        key_points = []
        
        # 匹配常见关键词后面的内容
        patterns = [
            r'需求分析[:：]\s*(.+)',
            r'风格偏好[:：]\s*(.+)',
            r'功能需求[:：]\s*(.+)',
            r'预算范围[:：]\s*(.+)',
            r'重点[:：]\s*(.+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, analysis_text)
            key_points.extend(matches)
        
        # 清理和去重
        key_points = [point.strip() for point in key_points if point.strip()]
        
        return list(set(key_points))


class ExportFormatter:
    """导出格式化器"""
    
    @staticmethod
    def format_for_export(data: Dict[str, Any], format_type: str = 'csv') -> Dict[str, Any]:
        """格式化为导出格式"""
        if format_type == 'csv':
            return ExportFormatter._format_for_csv(data)
        elif format_type == 'json':
            return ExportFormatter._format_for_json(data)
        else:
            return data
    
    @staticmethod
    def _format_for_csv(data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化为CSV友好的格式"""
        formatted = {}
        
        for key, value in data.items():
            if isinstance(value, list):
                # 列表转为逗号分隔字符串
                formatted[key] = ', '.join(map(str, value))
            elif isinstance(value, dict):
                # 字典转为JSON字符串
                import json
                formatted[key] = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, bool):
                # 布尔值转为中文
                formatted[key] = '是' if value else '否'
            else:
                formatted[key] = value if value is not None else ''
        
        return formatted
    
    @staticmethod
    def _format_for_json(data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化为JSON友好的格式"""
        formatted = {}
        
        for key, value in data.items():
            if isinstance(value, datetime):
                # 日期转为ISO格式
                formatted[key] = value.isoformat()
            else:
                formatted[key] = value
        
        return formatted


# 便捷函数
format_phone = TextFormatter.format_phone
format_budget = TextFormatter.format_budget
format_house_area = TextFormatter.format_house_area
format_date = TextFormatter.format_date
truncate_text = TextFormatter.truncate_text
format_customer_display = CustomerFormatter.format_customer_display
format_customer_list = CustomerFormatter.format_customer_list
format_design_display = DesignFormatter.format_design_display
format_ai_analysis = AIResponseFormatter.format_ai_analysis
