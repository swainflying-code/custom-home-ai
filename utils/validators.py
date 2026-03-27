"""
数据验证工具模块
提供各种数据验证和清洗功能
"""

import re
from typing import Any, Optional, List, Dict
from datetime import datetime


class DataValidator:
    """数据验证器基类"""
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证手机号格式"""
        if not phone:
            return False
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone.strip()))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    @staticmethod
    def validate_required(value: Any, field_name: str = "字段") -> Optional[str]:
        """验证必填字段"""
        if value is None or value == "":
            return f"{field_name}不能为空"
        return None
    
    @staticmethod
    def validate_length(value: str, min_len: int = 0, max_len: Optional[int] = None, field_name: str = "字段") -> Optional[str]:
        """验证字符串长度"""
        if not value:
            return None
        
        value_str = str(value)
        if len(value_str) < min_len:
            return f"{field_name}至少需要{min_len}个字符"
        
        if max_len and len(value_str) > max_len:
            return f"{field_name}不能超过{max_len}个字符"
        
        return None
    
    @staticmethod
    def validate_budget(budget_str: str) -> Optional[int]:
        """验证并解析预算字符串"""
        if not budget_str:
            return None
        
        try:
            # 移除中文单位和逗号
            budget_clean = budget_str.replace('万', '0000').replace('元', '').replace(',', '')
            budget_clean = re.sub(r'[^0-9]', '', budget_clean)
            
            if not budget_clean:
                return None
            
            budget = int(budget_clean)
            
            # 合理范围检查（1万 - 1000万）
            if 10000 <= budget <= 10000000:
                return budget
            
            return None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def validate_house_area(area_str: str) -> Optional[int]:
        """验证并解析房屋面积"""
        if not area_str:
            return None
        
        try:
            # 移除单位
            area_clean = area_str.replace('㎡', '').replace('平方米', '').replace('平', '')
            area_clean = re.sub(r'[^0-9.]', '', area_clean)
            
            if not area_clean:
                return None
            
            area = float(area_clean)
            
            # 合理范围检查（20 - 1000平米）
            if 20 <= area <= 1000:
                return int(area)
            
            return None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def validate_date(date_str: str) -> Optional[str]:
        """验证日期格式"""
        if not date_str:
            return None
        
        try:
            # 支持多种格式
            formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日', '%m/%d/%Y']
            
            for fmt in formats:
                try:
                    datetime.strptime(date_str, fmt)
                    return date_str
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None


class CustomerValidator:
    """客户数据验证器"""
    
    @staticmethod
    def validate_customer_data(data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证客户数据"""
        errors = []
        
        # 验证客户姓名
        name_error = DataValidator.validate_required(data.get('name'), '客户姓名')
        if name_error:
            errors.append(name_error)
        
        # 验证联系方式（手机或邮箱至少一个）
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        
        if phone and not DataValidator.validate_phone(phone):
            errors.append('手机号格式不正确')
        
        if email and not DataValidator.validate_email(email):
            errors.append('邮箱格式不正确')
        
        if not phone and not email:
            errors.append('手机号或邮箱至少填写一个')
        
        # 验证房屋面积
        house_area = data.get('house_area', '')
        if house_area and not DataValidator.validate_house_area(house_area):
            errors.append('房屋面积格式不正确，应为数字')
        
        # 验证预算
        budget = data.get('budget', '')
        if budget and not DataValidator.validate_budget(budget):
            errors.append('预算格式不正确')
        
        return len(errors) == 0, errors


class DesignValidator:
    """设计需求验证器"""
    
    @staticmethod
    def validate_design_data(data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证设计需求数据"""
        errors = []
        
        # 验证客户ID
        if not data.get('customer_id'):
            errors.append('客户ID不能为空')
        
        # 验证需求描述
        desc_error = DataValidator.validate_required(
            data.get('requirement_text'), 
            '需求描述'
        )
        if desc_error:
            errors.append(desc_error)
        
        # 验证需求描述长度
        length_error = DataValidator.validate_length(
            data.get('requirement_text', ''), 
            min_len=10,
            max_len=2000,
            field_name='需求描述'
        )
        if length_error:
            errors.append(length_error)
        
        # 验证房间类型
        valid_room_types = ['客厅', '卧室', '厨房', '卫生间', '书房', '阳台', '餐厅', '玄关', '儿童房', '老人房']
        room_type = data.get('room_type', '')
        if room_type and room_type not in valid_room_types:
            errors.append(f'房间类型应为: {", ".join(valid_room_types)}')
        
        return len(errors) == 0, errors


class SecurityValidator:
    """安全验证器"""
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """清理用户输入，防止XSS"""
        if not text:
            return ""
        
        # 移除危险的HTML标签
        dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<link']
        for tag in dangerous_tags:
            text = text.replace(tag, '')
        
        # 转义特殊字符
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace('"', '&quot;').replace("'", '&#x27;')
        
        return text
    
    @staticmethod
    def check_sql_injection(text: str) -> bool:
        """检查SQL注入风险"""
        if not text:
            return False
        
        dangerous_patterns = [
            r'(union|select|insert|update|delete|drop|create|alter)\s+',
            r'\-\-',
            r'\/\*',
            r';.*(drop|delete|truncate)',
        ]
        
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False


# 便捷函数
validate_phone = DataValidator.validate_phone
validate_email = DataValidator.validate_email
validate_required = DataValidator.validate_required
validate_length = DataValidator.validate_length
validate_customer_data = CustomerValidator.validate_customer_data
validate_design_data = DesignValidator.validate_design_data
sanitize_input = SecurityValidator.sanitize_input
