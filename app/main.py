"""
全屋定制客户服务AI助手 - 主应用入口
重构版本 V2.0
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import streamlit as st
from streamlit_option_menu import option_menu
from core.config import config
from core.auth import AuthManager
from core.database import db
from utils.logger import setup_logger

# 设置日志
logger = setup_logger(__name__)

# 初始化认证管理器
auth_manager = AuthManager()

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
        'logged_in': False,
        'current_page': '客户洞察',
        'user_info': None,
        'customer_form_state': {},
        'ai_analysis_cache': {}
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

# 登录页面
def show_login_page():
    """显示登录页面"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <h1 class="app-title">🏡 BINK不锈钢定制</h1>
            <p class="app-subtitle">AI客户服务助手 V2.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submitted = st.form_submit_button("登录系统", type="primary", use_container_width=True)
            
            if submitted:
                try:
                    success, user_info = auth_manager.authenticate(username, password)
                    if success and user_info:
                        st.session_state.logged_in = True
                        st.session_state.user_info = user_info
                        logger.info(f"用户登录成功: {username}")
                        st.success("✅ 登录成功！正在跳转...")
                        st.rerun()
                    else:
                        st.error("❌ 用户名或密码错误")
                        logger.warning(f"登录失败: {username}")
                except Exception as e:
                    st.error(f"登录异常: {str(e)}")
                    logger.error(f"登录异常: {e}")

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
        
        st.markdown("---")
        
        # 退出按钮
        if st.button("🚪 退出登录", use_container_width=True):
            auth_manager.logout()
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.session_state.customer_form_state = {}
            st.session_state.ai_analysis_cache = {}
            logger.info("用户退出登录")
            st.rerun()
    
    # 主内容区
    try:
        # 根据选择的页面加载对应模块
        if selected_page == "客户洞察":
            from pages.customer_insight import show_customer_insight_page
            show_customer_insight_page()
        
        elif selected_page == "设计辅助":
            from pages.design_assistant import show_design_assistant_page
            show_design_assistant_page()
        
        elif selected_page == "智能报价":
            from pages.smart_quoting import show_smart_quoting_page
            show_smart_quoting_page()
        
        elif selected_page == "客户服务":
            from pages.customer_service import show_customer_service_page
            show_customer_service_page()
        
        elif selected_page == "数据统计":
            from pages.statistics import show_statistics_page
            show_statistics_page()
        
        elif selected_page == "系统设置":
            from pages.system_settings import show_system_settings_page
            show_system_settings_page()
        
        else:
            st.error(f"未知的页面: {selected_page}")
            logger.error(f"尝试访问未知页面: {selected_page}")
    
    except Exception as e:
        st.error(f"页面加载失败: {str(e)}")
        logger.error(f"页面 {selected_page} 加载异常: {e}", exc_info=True)
        
        # 显示错误详情（调试用）
        with st.expander("查看错误详情"):
            import traceback
            st.code(traceback.format_exc())

# 主流程
if __name__ == "__main__":
    try:
        # 检查配置（绕过 auth_manager.check_config()，直接检查）
        if not config.is_valid():
            missing = config.get_missing_configs()
            st.error("⚠️ 配置检查失败")
            st.markdown(f"缺少以下必要配置：\n\n{'\n'.join([f'- **{item}**' for item in missing])}")
            
            with st.expander("查看配置说明"):
                st.markdown("""
                ### 配置 Streamlit Secrets
                
                请在 Streamlit Cloud 的 Secrets 中添加以下配置：
                
                ```toml
                SUPABASE_URL = "https://your-project.supabase.co"
                SUPABASE_KEY = "your-anon-key"
                SUPABASE_JWT_SECRET = "your-jwt-secret"
                MIMO_API_KEY = "your-mimo-key"
                MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
                MIMO_MODEL = "mimo-v2-pro"
                SECRET_KEY = "your-secret-key"
                ```
                
                ### 获取配置
                
                1. **Supabase**: [https://supabase.com](https://supabase.com)
                2. **MIMO大模型**: [https://xiaomimimo.com](https://xiaomimimo.com)
                """)
            st.stop()
        
        # 显示登录页面或主应用
        if not st.session_state.logged_in:
            show_login_page()
        else:
            show_main_app()
    
    except Exception as e:
        st.error(f"应用启动失败: {str(e)}")
        logger.critical(f"应用启动异常: {e}", exc_info=True)
        # 显示错误详情（调试用）
        with st.expander("查看错误详情"):
            import traceback
            st.code(traceback.format_exc())
