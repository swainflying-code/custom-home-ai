"""
全屋定制客户服务AI助手 - 主应用入口
重构版本 V2.0
"""

import os
import sys
import traceback

# 添加项目根目录到Python路径
# 注意：无论从 streamlit_app.py import 还是直接运行，都能正确定位根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
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

# ============================================================
# 页面配置（必须是第一个 st 调用）
# ============================================================
st.set_page_config(
    page_title="BINK不锈钢定制 · AI客户服务助手 V2.0",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 加载自定义CSS（绝对路径，兼容 Streamlit Cloud）
# ============================================================
try:
    css_path = os.path.join(project_root, "assets", "styles.css")
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    logger.warning("styles.css 未找到，跳过自定义样式加载")
except Exception as e:
    logger.warning(f"CSS 加载失败: {e}")

# ============================================================
# Session State 初始化
# ============================================================
def init_session_state():
    """初始化会话状态 —— 每次页面刷新都会执行，幂等安全"""
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

# 立即初始化，确保所有 session_state 键都存在
init_session_state()

# ============================================================
# 登录页面
# ============================================================
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
                submitted = st.form_submit_button(
                    "登录系统", type="primary", use_container_width=True
                )

            if submitted:
                try:
                    # --------------------------------------------------------
                    # 优先从 Supabase users 表查询用户数据；
                    # 若 Supabase 未配置或查询失败，则使用内置默认账户兜底。
                    # --------------------------------------------------------
                    user_data = None

                    # 1. 尝试从数据库获取用户
                    try:
                        result = db.client.table("users").select("*").eq("username", username).execute()
                        if result.data:
                            user_data = result.data[0]
                    except Exception as db_err:
                        logger.warning(f"数据库查询用户失败（使用默认账户兜底）: {db_err}")

                    # 2. 数据库中没有用户 → 使用内置默认账户
                    if not user_data:
                        # 内置账户：admin / admin123
                        default_users = {
                            "admin": {
                                "username": "admin",
                                "password_hash": auth_manager.generate_password_hash("admin123"),
                                "role": "admin",
                                "display_name": "系统管理员",
                            }
                        }
                        # 每次重启哈希值不同（带随机 salt），需要直接比对明文
                        if username in default_users:
                            # 对默认账户使用明文比对（内置账户密码固定）
                            plain_passwords = {"admin": "admin123"}
                            if plain_passwords.get(username) == password:
                                st.session_state.logged_in = True
                                st.session_state.user_info = {
                                    "username": username,
                                    "role": "admin",
                                    "display_name": "系统管理员",
                                }
                                logger.info(f"用户登录成功（默认账户）: {username}")
                                st.success("✅ 登录成功！正在跳转...")
                                st.rerun()
                            else:
                                st.error("❌ 用户名或密码错误")
                                logger.warning(f"登录失败（默认账户密码错误）: {username}")
                        else:
                            st.error("❌ 用户名或密码错误")
                            logger.warning(f"登录失败（用户不存在）: {username}")
                    else:
                        # 3. 数据库中存在用户 → 走正常哈希验证
                        success, user_info = auth_manager.authenticate(username, password, user_data)
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


# ============================================================
# 主应用页面
# ============================================================
def show_main_app():
    """显示主应用"""

    # ----------------------------------------------------------
    # selected_page 必须在函数作用域顶部先赋默认值，
    # 防止 sidebar 渲染中途出错导致后续代码找不到变量
    # ----------------------------------------------------------
    selected_page = st.session_state.get('current_page', '客户洞察')

    # 侧边栏
    try:
        with st.sidebar:
            st.markdown("""
            <div class="sidebar-header">
                <h3>🏡 BINK不锈钢定制</h3>
                <p>AI客户服务助手</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            # 导航菜单
            page_options = ["客户洞察", "设计辅助", "智能报价", "客户服务", "数据统计", "系统设置"]
            page_icons  = ["people", "palette", "calculator", "headset", "graph-up", "gear"]

            # 保持当前选中项
            current_index = page_options.index(selected_page) if selected_page in page_options else 0

            selected_page = option_menu(
                menu_title=None,
                options=page_options,
                icons=page_icons,
                menu_icon="cast",
                default_index=current_index,
                styles={
                    "container": {"padding": "0", "background-color": "transparent"},
                    "icon": {"color": "#d4af37", "font-size": "18px"},
                    "nav-link": {
                        "font-size": "14px",
                        "text-align": "left",
                        "margin": "4px 0",
                        "padding": "12px 16px",
                        "border-radius": "8px",
                        "color": "#2d342d",
                    },
                    "nav-link-selected": {
                        "background-color": "#d4af37",
                        "color": "#1a1a1a",
                    },
                },
            )

            # 同步到 session_state
            st.session_state.current_page = selected_page

            st.markdown("---")

            # 用户信息
            if st.session_state.get('user_info'):
                st.markdown(f"""
                <div class="user-info">
                    <p><strong>当前用户:</strong><br>
                    {st.session_state.user_info.get('username', '未知')}</p>
                    <p><strong>角色:</strong><br>
                    {st.session_state.user_info.get('role', '普通用户')}</p>
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
                for key in ['logged_in', 'user_info', 'customer_form_state', 'ai_analysis_cache']:
                    st.session_state[key] = False if key == 'logged_in' else (None if key == 'user_info' else {})
                logger.info("用户退出登录")
                st.rerun()

    except Exception as sidebar_err:
        logger.error(f"侧边栏渲染异常: {sidebar_err}", exc_info=True)
        # 侧边栏出错不影响主内容区，selected_page 已有默认值，继续执行

    # ----------------------------------------------------------
    # 主内容区 —— 根据 selected_page 路由到对应模块
    # ----------------------------------------------------------
    try:
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
            st.warning(f"页面 '{selected_page}' 尚未实现")
            logger.warning(f"访问了未实现的页面: {selected_page}")

    except Exception as page_err:
        # 安全地报告错误，不再引用可能未定义的变量
        err_msg = str(page_err)
        st.error(f"页面加载失败: {err_msg}")
        logger.error(f"页面 [{selected_page}] 加载异常: {page_err}", exc_info=True)

        with st.expander("查看错误详情（供开发调试）"):
            st.code(traceback.format_exc())


# ============================================================
# 主流程入口
# 重要：不能用 if __name__ == "__main__" 包裹！
# Streamlit Cloud 以 import 方式运行脚本，__name__ 不是 "__main__"
# 顶层代码必须直接执行。
# ============================================================
try:
    if not config.is_valid():
        missing = config.get_missing_configs()
        st.error("⚠️ 配置检查失败，请在 Streamlit Cloud Secrets 中添加以下配置：")
        for item in missing:
            st.markdown(f"- **{item}**")

        with st.expander("查看完整配置说明"):
            st.markdown("""
            ```toml
            SUPABASE_URL = "https://your-project.supabase.co"
            SUPABASE_KEY = "your-anon-key"
            SUPABASE_JWT_SECRET = "your-jwt-secret"
            MIMO_API_KEY = "your-mimo-key"
            MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
            MIMO_MODEL = "mimo-v2-pro"
            SECRET_KEY = "your-secret-key"
            ```
            """)
        st.stop()

    # 根据登录状态显示对应界面
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_main_app()

except SystemExit:
    # st.stop() 会抛出 SystemExit，正常情况，不处理
    raise
except Exception as e:
    st.error(f"应用启动失败: {str(e)}")
    logger.critical(f"应用启动异常: {e}", exc_info=True)
    with st.expander("查看错误详情"):
        st.code(traceback.format_exc())
