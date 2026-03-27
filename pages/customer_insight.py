"""
客户洞察页面
重构版本 V2.0
"""

import streamlit as st
from typing import Dict, Any, Optional
import json
import pandas as pd
from datetime import datetime

from core.database import db
from core.ai_service import ai_service
from utils.form_state import FormStateManager
from utils.validators import validate_customer_data
from utils.formatters import format_customer_display


def show_customer_insight_page():
    """显示客户洞察页面"""
    
    st.markdown("""
    <div class="page-header">
        <h1>🎯 客户洞察系统</h1>
        <p>深度了解客户需求，提供精准服务</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 模式切换
    tab1, tab2 = st.tabs(["📝 客户调研", "📊 客户统计"])
    
    with tab1:
        show_customer_survey_tab()
    
    with tab2:
        show_customer_statistics_tab()


def show_customer_survey_tab():
    """显示客户调研标签页"""
    
    # 步骤指示器
    steps = ["基础信息", "房屋信息", "产品偏好", "生活方式", "沟通转化", "需求补充", "确认提交"]
    
    if 'survey_step' not in st.session_state:
        st.session_state.survey_step = 0
    
    # 显示进度条
    progress = (st.session_state.survey_step + 1) / len(steps)
    st.progress(progress, text=f"步骤 {st.session_state.survey_step + 1} / {len(steps)}")
    
    # 显示步骤指示器
    cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        with cols[i]:
            if i == st.session_state.survey_step:
                st.markdown(f"<div class='step-active'>{i + 1}</div>", unsafe_allow_html=True)
                st.caption(step)
            elif i < st.session_state.survey_step:
                st.markdown(f"<div class='step-completed'>✓</div>", unsafe_allow_html=True)
                st.caption(step)
            else:
                st.markdown(f"<div class='step-pending'>{i + 1}</div>", unsafe_allow_html=True)
                st.caption(step)
    
    st.markdown("---")
    
    # 表单容器
    with st.form("customer_survey_form", clear_on_submit=False):
        
        # 根据当前步骤显示不同表单内容
        step_content = get_step_content(st.session_state.survey_step)
        
        if step_content:
            for field in step_content["fields"]:
                render_form_field(field)
        
        st.markdown("---")
        
        # 按钮区域
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.session_state.survey_step > 0:
                if st.form_submit_button("← 上一步", use_container_width=True):
                    st.session_state.survey_step -= 1
                    st.rerun()
        
        with col3:
            if st.session_state.survey_step < len(steps) - 1:
                if st.form_submit_button("下一步 →", type="primary", use_container_width=True):
                    # 验证当前步骤数据
                    if validate_current_step(st.session_state.survey_step):
                        st.session_state.survey_step += 1
                        st.rerun()
                    else:
                        st.error("请完善当前步骤的信息")
            else:
                # 最后一步 - 提交
                if st.form_submit_button("✅ 提交客户信息", type="primary", use_container_width=True):
                    submit_customer_data()


def get_step_content(step: int) -> Optional[Dict[str, Any]]:
    """获取步骤内容配置"""
    
    step_configs = {
        0: {
            "title": "📝 基础信息",
            "fields": [
                {
                    "type": "text",
                    "key": "customer_name",
                    "label": "客户姓名 *",
                    "required": True
                },
                {
                    "type": "text",
                    "key": "customer_code",
                    "label": "客户编号",
                    "disabled": True,
                    "value": generate_customer_code()
                },
                {
                    "type": "radio",
                    "key": "visit_times",
                    "label": "进店次数",
                    "options": ["第1次", "第2次", "第3次"],
                    "horizontal": True
                },
                {
                    "type": "radio",
                    "key": "gender",
                    "label": "性别",
                    "options": ["男", "女"],
                    "horizontal": True
                },
                {
                    "type": "radio",
                    "key": "age_group",
                    "label": "年龄段",
                    "options": ["18-25岁", "26-35岁", "36-45岁", "46-55岁", "56岁以上"],
                    "horizontal": True
                }
            ]
        },
        1: {
            "title": "🏠 房屋信息",
            "fields": [
                {
                    "type": "radio",
                    "key": "house_type",
                    "label": "房屋户型",
                    "options": ["别墅", "大平层", "普通住宅", "公寓", "自建房"],
                    "horizontal": True
                },
                {
                    "type": "radio",
                    "key": "renovation_type",
                    "label": "装修类型",
                    "options": ["全新装", "翻新装", "局部装", "已装修"],
                    "horizontal": True
                }
            ]
        }
        # 其他步骤配置省略...
    }
    
    return step_configs.get(step)


def render_form_field(field: Dict[str, Any]):
    """渲染表单字段"""
    
    field_type = field.get("type")
    key = field["key"]
    label = field["label"]
    
    # 获取或设置默认值
    if key not in st.session_state:
        st.session_state[key] = field.get("value", "")
    
    # 根据类型渲染
    if field_type == "text":
        st.text_input(
            label=label,
            key=key,
            disabled=field.get("disabled", False),
            help=field.get("help")
        )
    
    elif field_type == "radio":
        st.radio(
            label=label,
            options=field["options"],
            key=key,
            horizontal=field.get("horizontal", False),
            help=field.get("help")
        )
    
    elif field_type == "multiselect":
        st.multiselect(
            label=label,
            options=field["options"],
            key=key,
            help=field.get("help")
        )
    
    elif field_type == "textarea":
        st.text_area(
            label=label,
            key=key,
            height=field.get("height", 100),
            help=field.get("help")
        )


def validate_current_step(step: int) -> bool:
    """验证当前步骤的数据"""
    
    # 基础验证逻辑
    if step == 0:  # 基础信息
        if not st.session_state.get("customer_name", "").strip():
            return False
    
    return True


def generate_customer_code() -> str:
    """生成客户编号"""
    import uuid
    from datetime import datetime
    
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = str(uuid.uuid4())[:8].upper()
    return f"BINK-{date_str}-{random_str}"


def submit_customer_data():
    """提交客户数据"""
    
    with st.spinner("正在保存客户信息..."):
        try:
            # 收集所有表单数据
            customer_data = collect_form_data()
            
            # 数据验证
            validation_result = validate_customer_data(customer_data)
            if not validation_result["valid"]:
                st.error(f"数据验证失败: {validation_result['errors']}")
                return
            
            # 保存到数据库
            customer_id = db.insert("customers", customer_data)
            
            if customer_id:
                st.success(f"✅ 客户信息保存成功！客户ID: {customer_id}")
                
                # 清理表单状态
                cleanup_form_state()
                
                # 显示下一步建议
                st.info("💡 建议进行AI客户分析或进入设计辅助模块")
                
                # 提供快捷操作
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🧠 立即进行AI分析", use_container_width=True):
                        perform_ai_analysis(customer_id)
                with col2:
                    if st.button("🎨 进入设计辅助", use_container_width=True):
                        st.session_state.current_page = "设计辅助"
                        st.rerun()
            else:
                st.error("❌ 保存失败，请稍后重试")
        
        except Exception as e:
            st.error(f"保存失败: {str(e)}")
            import traceback
            st.code(traceback.format_exc())


def collect_form_data() -> Dict[str, Any]:
    """收集表单数据"""
    
    data = {}
    
    # 收集所有session state中的表单数据
    for key, value in st.session_state.items():
        if not key.startswith("_") and key not in ['logged_in', 'current_page', 'user_info']:
            data[key] = value
    
    # 添加时间戳
    from datetime import datetime
    data["created_at"] = datetime.now().isoformat()
    data["updated_at"] = datetime.now().isoformat()
    
    return data


def cleanup_form_state():
    """清理表单状态"""
    
    # 重置步骤
    st.session_state.survey_step = 0
    
    # 清理表单字段
    keys_to_delete = []
    for key in st.session_state.keys():
        if not key.startswith("_") and key not in ['logged_in', 'current_page', 'user_info', 'survey_step']:
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        del st.session_state[key]


def perform_ai_analysis(customer_id: str):
    """执行AI客户分析"""
    
    try:
        # 获取客户数据
        customer_data = db.get_by_id("customers", customer_id)
        
        if not customer_data:
            st.error("客户数据不存在")
            return
        
        # 执行AI分析
        with st.spinner("🤖 AI正在深度分析客户信息..."):
            analysis_result = ai_service.analyze_customer(customer_data)
        
        if analysis_result.get("_success"):
            # 保存分析结果
            db.update("customers", customer_id, {
                "ai_analysis_result": analysis_result
            })
            
            st.success("✅ AI分析完成！")
            
            # 显示分析结果
            display_ai_analysis(analysis_result)
        else:
            st.error(f"AI分析失败: {analysis_result.get('error', '未知错误')}")
    
    except Exception as e:
        st.error(f"分析过程出错: {str(e)}")


def display_ai_analysis(analysis_result: Dict[str, Any]):
    """显示AI分析结果"""
    
    st.markdown("### 📊 AI客户分析结果")
    
    # 综合评分
    if "综合评分" in analysis_result:
        score_info = analysis_result["综合评分"]
        st.metric("综合评分", f"{score_info.get('总分', 0)}分", score_info.get("评分说明", ""))
    
    # 客户画像标签
    if "客户画像标签" in analysis_result:
        tags = analysis_result["客户画像标签"]
        st.markdown("**客户画像标签:**")
        for tag in tags:
            st.markdown(f"<span class='tag'>{tag}</span>", unsafe_allow_html=True)
    
    # 可成交预期
    if "可成交预期" in analysis_result:
        deal_info = analysis_result["可成交预期"]
        st.metric("成交预期", f"{deal_info.get('预期分数', 0)}分", deal_info.get("预期说明", ""))
    
    # 详细分析
    if "详细分析" in analysis_result:
        st.markdown("### 📋 详细分析")
        
        for dimension, content in analysis_result["详细分析"].items():
            with st.expander(f"📊 {dimension}"):
                if isinstance(content, dict):
                    st.write(f"**分析结论:** {content.get('分析结论', '')}")
                    st.write(f"**置信度:** {content.get('置信度', '')}")
                    
                    if "具体建议" in content:
                        st.write("**具体建议:**")
                        for item in content["具体建议"]:
                            st.write(f"• {item}")
                else:
                    st.write(content)


def show_customer_statistics_tab():
    """显示客户统计标签页"""
    
    st.markdown("### 📊 客户数据统计")
    
    try:
        # 获取所有客户
        customers = db.select("customers", order_by="created_at.desc")
        
        if not customers:
            st.info("暂无客户数据")
            return
        
        # 显示统计卡片
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总客户数", len(customers))
        
        with col2:
            high_intent = sum(1 for c in customers if "高意向" in str(c.get("intent_level", "")))
            st.metric("高意向客户", high_intent)
        
        with col3:
            has_ai_analysis = sum(1 for c in customers if c.get("ai_analysis_result"))
            st.metric("AI分析客户", has_ai_analysis)
        
        with col4:
            today = datetime.now().date()
            today_customers = sum(1 for c in customers if 
                                datetime.fromisoformat(c.get("created_at", "")).date() == today)
            st.metric("今日新增", today_customers)
        
        st.markdown("---")
        
        # 显示客户列表
        st.markdown("### 👥 客户列表")
        
        # 转换数据为DataFrame
        df_data = []
        for customer in customers:
            df_data.append({
                "客户编号": customer.get("customer_code", ""),
                "姓名": customer.get("customer_name", customer.get("name", "未命名")),
                "性别": customer.get("gender", ""),
                "年龄段": customer.get("age_group", ""),
                "意向等级": customer.get("intent_level", ""),
                "创建时间": customer.get("created_at", "")
            })
        
        df = pd.DataFrame(df_data)
        
        # 显示可搜索的表格
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "创建时间": st.column_config.DatetimeColumn(
                    format="YYYY-MM-DD HH:mm"
                )
            }
        )
        
        # 导出功能
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("📥 导出数据"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="下载CSV",
                    data=csv,
                    file_name=f"customers_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    except Exception as e:
        st.error(f"加载统计数据失败: {str(e)}")
        logger.error(f"统计页面加载异常: {e}", exc_info=True)
