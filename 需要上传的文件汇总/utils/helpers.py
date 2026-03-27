"""
通用辅助函数模块
提供各种通用的工具函数
"""

import uuid
import re
from datetime import datetime
from typing import Any, Optional, Dict, List, Union


def generate_id(prefix: str = "") -> str:
    """
    生成唯一ID
    
    Args:
        prefix: ID前缀
    
    Returns:
        str: 唯一ID
    """
    unique_id = str(uuid.uuid4())
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id


def generate_customer_code() -> str:
    """
    生成客户编号
    
    Returns:
        str: 客户编号格式 BINK-YYYYMMDD-XXXXXX
    """
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = str(uuid.uuid4())[:6].upper()
    return f"BINK-{date_part}-{random_part}"


def get_current_timestamp() -> datetime:
    """
    获取当前时间戳
    
    Returns:
        datetime: 当前时间
    """
    return datetime.now()


def get_current_timestamp_str(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前时间戳字符串
    
    Args:
        format_str: 时间格式
    
    Returns:
        str: 格式化的时间字符串
    """
    return datetime.now().strftime(format_str)


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    安全获取字典值
    
    Args:
        dictionary: 字典
        key: 键
        default: 默认值
    
    Returns:
        Any: 值或默认值
    """
    if dictionary is None:
        return default
    return dictionary.get(key, default)


def safe_get_nested(dictionary: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    安全获取嵌套字典值
    
    Args:
        dictionary: 字典
        keys: 键列表（嵌套路径）
        default: 默认值
    
    Returns:
        Any: 值或默认值
    """
    if dictionary is None:
        return default
    
    current = dictionary
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def clean_text(text: Optional[str]) -> str:
    """
    清理文本
    
    Args:
        text: 文本
    
    Returns:
        str: 清理后的文本
    """
    if text is None:
        return ""
    
    # 移除多余的空白字符
    text = str(text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def truncate_text(text: Optional[str], max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 文本
        max_length: 最大长度
        suffix: 后缀
    
    Returns:
        str: 截断后的文本
    """
    if not text:
        return ""
    
    text = str(text)
    if len(text) <= max_length:
        return text
    
    # 在单词边界截断
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + suffix


def parse_comma_separated(text: Optional[str]) -> List[str]:
    """
    解析逗号分隔的字符串为列表
    
    Args:
        text: 逗号分隔的字符串
    
    Returns:
        List[str]: 列表
    """
    if not text:
        return []
    
    items = str(text).split(',')
    items = [item.strip() for item in items if item.strip()]
    
    return items


def list_to_comma_string(items: Optional[List[Any]]) -> str:
    """
    将列表转换为逗号分隔字符串
    
    Args:
        items: 列表
    
    Returns:
        str: 逗号分隔字符串
    """
    if not items:
        return ""
    
    return ', '.join(str(item) for item in items)


def is_valid_email(email: Optional[str]) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
    
    Returns:
        bool: 是否有效
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, str(email).strip()))


def is_valid_phone(phone: Optional[str]) -> bool:
    """
    验证手机号格式
    
    Args:
        phone: 手机号
    
    Returns:
        bool: 是否有效
    """
    if not phone:
        return False
    
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, str(phone).strip()))


def mask_sensitive_info(text: Optional[str], visible_chars: int = 4) -> str:
    """
    脱敏敏感信息
    
    Args:
        text: 文本
        visible_chars: 可见字符数
    
    Returns:
        str: 脱敏后的文本
    """
    if not text:
        return ""
    
    text = str(text).strip()
    if len(text) <= visible_chars:
        return "*" * len(text)
    
    return text[:visible_chars] + "*" * (len(text) - visible_chars)


class DictDiffer:
    """字典差异比较器"""
    
    @staticmethod
    def diff(old_dict: Dict[str, Any], new_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        比较两个字典的差异
        
        Args:
            old_dict: 旧字典
            new_dict: 新字典
        
        Returns:
            Dict[str, Any]: 差异结果
        """
        if old_dict is None:
            old_dict = {}
        if new_dict is None:
            new_dict = {}
        
        diff_result = {
            'added': {},
            'removed': {},
            'changed': {},
            'unchanged': {}
        }
        
        # 查找新增和变更的键
        for key, new_value in new_dict.items():
            if key not in old_dict:
                diff_result['added'][key] = new_value
            elif old_dict[key] != new_value:
                diff_result['changed'][key] = {
                    'old': old_dict[key],
                    'new': new_value
                }
            else:
                diff_result['unchanged'][key] = new_value
        
        # 查找删除的键
        for key, old_value in old_dict.items():
            if key not in new_dict:
                diff_result['removed'][key] = old_value
        
        return diff_result


class PaginationHelper:
    """分页助手"""
    
    def __init__(self, total_items: int, items_per_page: int = 10, current_page: int = 1):
        self.total_items = total_items
        self.items_per_page = items_per_page
        self.current_page = current_page
    
    @property
    def total_pages(self) -> int:
        """总页数"""
        if self.total_items <= 0:
            return 0
        return (self.total_items + self.items_per_page - 1) // self.items_per_page
    
    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.current_page > 1
    
    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.current_page < self.total_pages
    
    @property
    def start_item(self) -> int:
        """当前页开始项索引（0-based）"""
        return (self.current_page - 1) * self.items_per_page
    
    @property
    def end_item(self) -> int:
        """当前页结束项索引（不包含）"""
        return min(self.current_page * self.items_per_page, self.total_items)
    
    def get_page_items(self, items: List[Any]) -> List[Any]:
        """
        获取当前页的项目
        
        Args:
            items: 所有项目列表
        
        Returns:
            List[Any]: 当前页的项目
        """
        if not items:
            return []
        
        return items[self.start_item:self.end_item]
    
    def get_page_range(self, window: int = 5) -> range:
        """
        获取页码范围（用于显示分页控件）
        
        Args:
            window: 窗口大小
        
        Returns:
            range: 页码范围
        """
        start = max(1, self.current_page - window // 2)
        end = min(self.total_pages, start + window - 1)
        start = max(1, end - window + 1)
        
        return range(start, end + 1)
