"""
表单状态管理模块
提供表单状态的保存、恢复和验证功能
"""

from typing import Any, Dict, Optional, List
import json
import time


class FormStateManager:
    """表单状态管理器"""
    
    def __init__(self, form_name: str, session_state: Dict[str, Any]):
        """
        初始化表单状态管理器
        
        Args:
            form_name: 表单名称
            session_state: Streamlit session_state对象
        """
        self.form_name = form_name
        self.session_state = session_state
        self._initialize_state()
    
    def _initialize_state(self) -> None:
        """初始化状态存储"""
        state_key = f"_form_state_{self.form_name}"
        if state_key not in self.session_state:
            self.session_state[state_key] = {
                'data': {},
                'errors': {},
                'touched': set(),
                'is_valid': False,
                'last_updated': None
            }
    
    @property
    def state(self) -> Dict[str, Any]:
        """获取完整状态"""
        state_key = f"_form_state_{self.form_name}"
        return self.session_state[state_key]
    
    @property
    def data(self) -> Dict[str, Any]:
        """获取表单数据"""
        return self.state['data']
    
    @data.setter
    def data(self, value: Dict[str, Any]) -> None:
        """设置表单数据"""
        self.state['data'] = value
        self.state['last_updated'] = time.time()
    
    @property
    def errors(self) -> Dict[str, List[str]]:
        """获取错误信息"""
        return self.state['errors']
    
    @errors.setter
    def errors(self, value: Dict[str, List[str]]) -> None:
        """设置错误信息"""
        self.state['errors'] = value
    
    @property
    def touched(self) -> set:
        """获取已触摸的字段"""
        return self.state['touched']
    
    def set_touched(self, field: str) -> None:
        """标记字段为已触摸"""
        self.state['touched'].add(field)
    
    def is_touched(self, field: str) -> bool:
        """检查字段是否已触摸"""
        return field in self.state['touched']
    
    @property
    def is_valid(self) -> bool:
        """获取表单验证状态"""
        return self.state['is_valid']
    
    @is_valid.setter
    def is_valid(self, value: bool) -> None:
        """设置表单验证状态"""
        self.state['is_valid'] = value
    
    def get(self, field: str, default: Any = None) -> Any:
        """
        获取字段值
        
        Args:
            field: 字段名
            default: 默认值
        
        Returns:
            Any: 字段值或默认值
        """
        return self.data.get(field, default)
    
    def set(self, field: str, value: Any, mark_as_touched: bool = True) -> None:
        """
        设置字段值
        
        Args:
            field: 字段名
            value: 字段值
            mark_as_touched: 是否标记为已触摸
        """
        self.data[field] = value
        if mark_as_touched:
            self.set_touched(field)
        self.state['last_updated'] = time.time()
    
    def update(self, data: Dict[str, Any], mark_as_touched: bool = True) -> None:
        """
        批量更新字段值
        
        Args:
            data: 字段数据字典
            mark_as_touched: 是否标记为已触摸
        """
        self.data.update(data)
        if mark_as_touched:
            for field in data.keys():
                self.set_touched(field)
        self.state['last_updated'] = time.time()
    
    def clear_field(self, field: str) -> None:
        """清空字段值"""
        if field in self.data:
            del self.data[field]
        if field in self.errors:
            del self.errors[field]
        self.state['touched'].discard(field)
    
    def clear_all(self) -> None:
        """清空所有数据"""
        self.data.clear()
        self.errors.clear()
        self.state['touched'].clear()
        self.is_valid = False
        self.state['last_updated'] = time.time()
    
    def set_error(self, field: str, error: str) -> None:
        """
        设置字段错误信息
        
        Args:
            field: 字段名
            error: 错误信息
        """
        if field not in self.errors:
            self.errors[field] = []
        
        if error not in self.errors[field]:
            self.errors[field].append(error)
    
    def set_errors(self, errors: Dict[str, List[str]]) -> None:
        """
        批量设置错误信息
        
        Args:
            errors: 错误信息字典
        """
        self.errors.update(errors)
    
    def get_errors(self, field: str) -> List[str]:
        """
        获取字段错误信息
        
        Args:
            field: 字段名
        
        Returns:
            List[str]: 错误信息列表
        """
        return self.errors.get(field, [])
    
    def clear_errors(self, field: Optional[str] = None) -> None:
        """
        清空错误信息
        
        Args:
            field: 字段名，如果为None则清空所有错误
        """
        if field is None:
            self.errors.clear()
        else:
            self.errors.pop(field, None)
    
    def has_error(self, field: str) -> bool:
        """
        检查字段是否有错误
        
        Args:
            field: 字段名
        
        Returns:
            bool: 是否有错误
        """
        return field in self.errors and len(self.errors[field]) > 0
    
    @property
    def has_errors(self) -> bool:
        """检查表单是否有错误"""
        return len(self.errors) > 0
    
    def validate(self, validators: Dict[str, callable]) -> bool:
        """
        验证表单数据
        
        Args:
            validators: 验证函数字典 {field: validator_func}
        
        Returns:
            bool: 是否验证通过
        """
        self.clear_errors()
        
        for field, validator in validators.items():
            value = self.get(field)
            is_valid, errors = validator(value)
            
            if not is_valid:
                if isinstance(errors, list):
                    for error in errors:
                        self.set_error(field, error)
                else:
                    self.set_error(field, errors)
        
        self.is_valid = not self.has_errors
        return self.is_valid
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'form_name': self.form_name,
            'data': self.data.copy(),
            'errors': self.errors.copy(),
            'touched': list(self.touched),
            'is_valid': self.is_valid,
            'last_updated': self.state['last_updated']
        }
    
    def save_to_session(self, session_key: str) -> None:
        """
        保存到session_state
        
        Args:
            session_key: session_state中的键
        """
        try:
            import streamlit as st
            st.session_state[session_key] = self.to_dict()
        except ImportError:
            pass
    
    def load_from_session(self, session_key: str) -> bool:
        """
        从session_state加载
        
        Args:
            session_key: session_state中的键
        
        Returns:
            bool: 是否成功加载
        """
        try:
            import streamlit as st
            
            if session_key in st.session_state:
                data = st.session_state[session_key]
                self.data = data.get('data', {})
                self.errors = data.get('errors', {})
                self.state['touched'] = set(data.get('touched', []))
                self.is_valid = data.get('is_valid', False)
                self.state['last_updated'] = data.get('last_updated')
                return True
        except ImportError:
            pass
        
        return False
