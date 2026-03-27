"""
全屋定制客户服务AI助手 - 免登录版本
重构版本 V2.0 - 临时免认证版本
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import streamlit as st
from streamlit_option_menu import option_menu
from core.config import config
from core.database import db
from utils.logger import setup_logger

# 设置日志
logger = setup_logger(__name__)

# 页面配置
st.set_page_config(
    page_title="BINK不锈钢定制 · AI客户服务助手 V2.0",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 加载自定义CSS
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 初始化session state
def init_session_state():
    """初始化会话状态"""
    defaults = {
        'logged_in': True,  # 临时：默认已登录
        'current_page': '客户洞察',
        'user_info': {  # 临时：默认用户信息
            'username': 'admin',
            'role': 'admin',
            'full_name': '系统管理员'
        },
        'customer_form_state': {},
        'ai_analysis_cache': {}
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

# 主应用页面
def show_main_app():
    """显示主应用"""
    
    # 侧边栏
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <h3>🏡 BINK不锈钢定制</h3>
            <p>AI客户服务助手</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 导航菜单
        selected_page = option_menu(
            menu_title=None,
            options=["客户洞察", "设计辅助", "智能报价", "客户服务", "数据统计", "系统设置"],
            icons=["people", "palette", "calculator", "headset", "graph-up", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"color": "#d4af37", "font-size": "18px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "4px 0",
                    "padding": "12px 16px",
                    "border-radius": "8px",
                    "color": "#2d342d"
                },
                "nav-link-selected": {
                    "background-color": "#d4af37",
                    "color": "#1a1a1a"
                }
            }
        )
        
        st.session_state.current_page = selected_page
        
        st.markdown("---")
        
        # 用户信息
        if st.session_state.user_info:
            st.markdown(f"""
            <div class="user-info">
                <p><strong>当前用户:</strong><br>{st.session_state.user_info.get('username', '未知')}</p>
                <p><strong>角色:</strong><br>{st.session_state.user_info.get('role', '普通用户')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 快速统计
        try:
            total_customers = db.count("customers")
            high_intent = db.count("customers", {"intent_level": "高意向 (一周内下单)"})
            
            st.markdown("### 📊 快速统计")
            st.metric("总客户数", total_customers)
            st.metric("高意向客户", high_intent)
            
        except Exception as e:
            logger.warning(f"统计信息加载失败: {e}")
            st.info("暂无统计数据")
        
        st.markdown("---")
        
        # 退出按钮
        if st.button("🚪 退出系统", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.session_state.current_page = "客户洞察"
            st.rerun()
    
    # 主内容区域
    try:
        if selected_page == "客户洞察":
            from pages.customer_insight import show_customer_insight
            show_customer_insight()
        elif selected_page == "设计辅助":
            from pages.design_assistant import show_design_assistant
            show_design_assistant()
        elif selected_page == "智能报价":
            from pages.quoting_tool import show_quoting_tool
            show_quoting_tool()
        elif selected_page == "客户服务":
            from pages.customer_service import show_customer_service
            show_customer_service()
        elif selected_page == "数据统计":
            from pages.data_analytics import show_data_analytics
            show_data_analytics()
        elif selected_page == "系统设置":
            from pages.system_settings import show_system_settings
            show_system_settings()
    except Exception as e:
        logger.error(f"页面加载失败: {e}", exc_info=True)
        st.error(f"页面加载失败: {str(e)}")
        st.info("请检查日志获取详细信息")

# 主程序入口
if __name__ == "__main__":
    try:
        show_main_app()
    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        st.error("应用启动失败")
        st.exception(e)
