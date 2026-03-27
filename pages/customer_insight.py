"""
客户洞察页面
重构版本 V2.0 - 修复版
将原本模块级执行的代码全部封装进函数，避免 import 时触发 NameError
"""

import json
import random
import streamlit as st
import pandas as pd
from datetime import datetime, time
from typing import Any, Dict, Optional

# logger 在模块顶层定义，避免 except 块 NameError
try:
    from utils.logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    import logging
    logger = logging.getLogger(__name__)

# 可选依赖降级处理
try:
    from core.database import db
except Exception as _e:
    logger.warning(f"database 模块加载失败: {_e}")
    db = None

try:
    from core.ai_service import ai_service
except Exception as _e:
    logger.warning(f"ai_service 模块加载失败: {_e}")
    ai_service = None


# ============================================================
# 辅助函数
# ============================================================

def get_safe_appointment_value(saved_appt):
    """获取安全的预约时间值（避免过去时间导致错误）"""
    if saved_appt is None:
        return datetime.now()
    try:
        if isinstance(saved_appt, str):
            dt = datetime.fromisoformat(saved_appt)
            return dt if dt > datetime.now() else datetime.now()
        return saved_appt
    except Exception:
        return datetime.now()


def get_all_customers():
    """获取所有客户"""
    try:
        if db is None:
            return []
        return db.select("customers", order_by="created_at.desc") or []
    except Exception as e:
        logger.error(f"获取客户列表失败: {e}")
        return []


def delete_customer(customer_id: str) -> bool:
    """删除客户"""
    try:
        if db is None:
            return False
        db.delete("customers", customer_id)
        return True
    except Exception as e:
        logger.error(f"删除客户失败: {e}")
        return False


def save_customer(data: Dict[str, Any]) -> Optional[str]:
    """保存客户到数据库"""
    try:
        if db is None:
            st.error("数据库未连接")
            return None
        return db.insert("customers", data)
    except Exception as e:
        logger.error(f"保存客户失败: {e}")
        st.error(f"保存失败: {e}")
        return None


def mimo_analysis(customer_data: Dict[str, Any]) -> Dict[str, Any]:
    """调用 MIMO 大模型分析客户"""
    try:
        if ai_service is None:
            return {"error": "AI服务未初始化"}
        return ai_service.analyze_customer(customer_data)
    except Exception as e:
        logger.error(f"AI分析失败: {e}")
        return {"error": str(e)}


# ============================================================
# 主入口函数 — 由 main.py 调用
# ============================================================

def show_customer_insight_page():
    """显示客户洞察页面（由 main.py 路由调用）"""
    show_customer_insight()


def show_customer_insight():
    """客户洞察系统主体"""

    st.header("🎯 客户洞察系统")
    st.markdown("---")

    # 初始化 session_state
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "📝 填写客户调研"
    if "current_step" not in st.session_state:
        st.session_state.current_step = 0
    if "customer_data" not in st.session_state:
        st.session_state.customer_data = {}
    if "ai_analysis_result" not in st.session_state:
        st.session_state.ai_analysis_result = None

    current_view_mode = st.session_state.view_mode

    view_mode = st.radio(
        "操作模式",
        ["📝 填写客户调研", "📊 客户统计面板"],
        horizontal=True,
        index=0 if current_view_mode == "📝 填写客户调研" else 1
    )

    if view_mode != current_view_mode:
        st.session_state.view_mode = view_mode
        st.rerun()

    if view_mode == "📊 客户统计面板":
        _show_statistics_panel()
    else:
        _show_survey_form()


# ============================================================
# 统计面板
# ============================================================

def _show_statistics_panel():
    st.subheader("📊 客户统计面板")
    st.markdown("---")

    customers = get_all_customers()

    if not customers:
        st.info("暂无客户记录，您可以填写客户调研后提交")
        return

    # ── 顶部汇总指标 ──────────────────────────────────────────
    total = len(customers)
    high_intent = sum(1 for c in customers if "高意向" in (c.get("intent_level") or ""))
    has_contact = sum(1 for c in customers if c.get("has_contact") == "是")
    has_appt = sum(1 for c in customers if c.get("has_appointment") not in (None, "无预约", ""))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📋 客户总数", total)
    m2.metric("🔥 高意向客户", high_intent)
    m3.metric("📞 留联系方式", has_contact)
    m4.metric("📅 已预约", has_appt)

    st.markdown("---")

    # ── 客户列表（关键字段） ───────────────────────────────────
    st.subheader("📋 客户记录列表")

    # 构建展示用 DataFrame（只取关键列，避免信息过多）
    rows = []
    for c in customers:
        ai_score = ""
        raw_ai = c.get("ai_analysis_result")
        if raw_ai:
            try:
                ai_data = json.loads(raw_ai) if isinstance(raw_ai, str) else raw_ai
                score = ai_data.get("综合评分", {})
                if score:
                    ai_score = f"{score.get('总分', '')}分"
            except Exception:
                pass

        rows.append({
            "编号": c.get("customer_code", ""),
            "姓名": c.get("name", ""),
            "性别": c.get("gender", ""),
            "年龄段": c.get("age_group", ""),
            "来源": c.get("customer_source", ""),
            "意向等级": c.get("intent_level", ""),
            "报价态度": c.get("quote_attitude", ""),
            "已留联系": c.get("has_contact", ""),
            "预约状态": c.get("has_appointment", ""),
            "AI评分": ai_score,
            "登记时间": (c.get("created_at") or "")[:16],
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, height=400)

    # ── 刚保存的客户高亮提示 ──────────────────────────────────
    new_id = st.session_state.get("selected_customer_id")
    if new_id:
        matched = next((c for c in customers if c.get("id") == new_id), None)
        if matched:
            st.success(f"✅ 最新保存：{matched.get('name', '未填姓名')} | {matched.get('customer_code', '')} | 意向：{matched.get('intent_level', '—')}")
            raw_ai = matched.get("ai_analysis_result")
            if raw_ai:
                try:
                    ai_data = json.loads(raw_ai) if isinstance(raw_ai, str) else raw_ai
                    if "综合评分" in ai_data:
                        score = ai_data["综合评分"]
                        st.info(f"🧠 AI综合评分：**{score.get('总分', '')}分** — {score.get('评分说明', '')}")
                    if "客户画像标签" in ai_data:
                        tags = ai_data["客户画像标签"]
                        st.write("🏷️ 客户标签：" + "  |  ".join(tags))
                except Exception:
                    pass

    st.markdown("---")

    # ── 删除客户 ──────────────────────────────────────────────
    st.subheader("🗑️ 删除客户记录")
    col1, col2 = st.columns(2)
    with col1:
        customer_options = {
            f"{c.get('name', '未知')} ({c.get('customer_code', c.get('id', ''))[:12]})": c["id"]
            for c in customers
        }
        selected_label = st.selectbox("选择要删除的客户", options=list(customer_options.keys()))
        customer_id_to_delete = customer_options[selected_label]
    with col2:
        st.write("")
        st.write("")
        if st.button("确认删除", type="primary", help="删除后无法恢复，请谨慎操作！"):
            if delete_customer(customer_id_to_delete):
                st.success("✅ 删除成功！")
                st.rerun()
            else:
                st.error("❌ 删除失败")


# ============================================================
# 调研表单（7 步骤）
# ============================================================

def _show_survey_form():
    steps = ["顾客基础&进店信息", "房屋装修", "产品偏好", "客户生活方式", "沟通转化", "确认提交"]
    current_step = st.session_state.current_step

    progress = current_step / (len(steps) - 1)
    st.progress(progress)

    cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        with cols[i]:
            if i == current_step:
                st.markdown(f'<span style="background:#d4af37;color:#fff;padding:2px 8px;border-radius:50%">{i+1}</span> **{step}**', unsafe_allow_html=True)
            elif i < current_step:
                st.markdown(f'<span style="background:#4caf50;color:#fff;padding:2px 8px;border-radius:50%">✓</span> {step}', unsafe_allow_html=True)
            else:
                st.markdown(f'<span style="background:#ccc;color:#fff;padding:2px 8px;border-radius:50%">{i+1}</span> {step}', unsafe_allow_html=True)

    st.markdown("---")

    if current_step == 0:
        _step0_basic_info()
    elif current_step == 1:
        _step1_house_info()
    elif current_step == 2:
        _step2_product_preference()
    elif current_step == 3:
        _step3_lifestyle()
    elif current_step == 4:
        _step4_communication()
    elif current_step == 5:
        _step5_confirm_submit()


# ──────────────────────────────────────────────────────────────
# 步骤 0：顾客基础 & 进店信息
# ──────────────────────────────────────────────────────────────
def _step0_basic_info():
    st.subheader("顾客基础 & 进店信息")
    st.info("💡 提示：进店和离店时间请选择 8:00-22:00 之间的时间")

    today = datetime.now().strftime("%Y%m%d")
    default_code = f"BINK-{today}-{random.randint(100, 999)}"

    customer_name = st.text_input(
        "客户姓名 *",
        value=st.session_state.customer_data.get("name", ""),
        help="请输入客户姓名，此字段为必填项"
    )

    customer_code = st.text_input(
        "顾客编号",
        value=st.session_state.customer_data.get("customer_code", default_code)
    )

    visit_options = ["第1次", "第2次", "第3次"]
    visit_times = st.radio(
        "客户进店第几次", visit_options,
        index=visit_options.index(st.session_state.customer_data.get("visit_times", "第1次"))
              if st.session_state.customer_data.get("visit_times") in visit_options else 0,
        horizontal=True
    )

    gender_options = ["男", "女"]
    gender = st.radio(
        "顾客性别", gender_options,
        index=gender_options.index(st.session_state.customer_data.get("gender", "男"))
              if st.session_state.customer_data.get("gender") in gender_options else 0,
        horizontal=True
    )

    age_options = ["18-25岁", "26-35岁", "36-45岁", "46-55岁", "56岁以上", "未询问"]
    age_group = st.radio(
        "顾客年龄段", age_options,
        index=age_options.index(st.session_state.customer_data.get("age_group", "26-35岁"))
              if st.session_state.customer_data.get("age_group") in age_options else 1,
        horizontal=True
    )

    col1, col2 = st.columns(2)
    with col1:
        entry_time = st.time_input(
            "进店时间 *",
            value=st.session_state.customer_data.get("entry_time", time(9, 0))
        )
    with col2:
        leave_time = st.time_input(
            "离店时间 *",
            value=st.session_state.customer_data.get("leave_time", time(10, 0))
        )

    stay_duration = "请填写进店和离店时间"
    if entry_time and leave_time:
        entry_dt = datetime.combine(datetime.today(), entry_time)
        leave_dt = datetime.combine(datetime.today(), leave_time)
        delta = leave_dt - entry_dt
        if delta.total_seconds() > 0:
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            stay_duration = f"{hours}小时{minutes}分钟"
        else:
            stay_duration = "请填写正确的时间"

    st.text_input("在店时长", value=stay_duration, disabled=True)

    companion_options = ["0", "1", "2", "3人及以上"]
    companion_count = st.radio(
        "同行人数 *", companion_options,
        index=companion_options.index(st.session_state.customer_data.get("companion_count", "1"))
              if st.session_state.customer_data.get("companion_count") in companion_options else 1,
        horizontal=True
    )

    st.markdown("#### 同行人员类型 (多选)")
    companion_type_options = ["配偶", "朋友", "父母", "孩子", "设计师", "同购者", "装修师傅", "其他"]
    companion_type = st.multiselect(
        "", companion_type_options,
        default=st.session_state.customer_data.get("companion_type", []),
        label_visibility="collapsed"
    )

    decision_options = ["是", "否", "不确定"]
    decision_maker_present = st.radio(
        "决策人是否同行", decision_options,
        index=decision_options.index(st.session_state.customer_data.get("decision_maker_present", "是"))
              if st.session_state.customer_data.get("decision_maker_present") in decision_options else 0,
        horizontal=True
    )

    source_options = ["自然到店", "老客介绍", "线上推广 (抖音/小红书等)", "小区拓客", "装修公司推荐", "其他"]
    customer_source = st.radio(
        "顾客来源", source_options,
        index=source_options.index(st.session_state.customer_data.get("customer_source", "自然到店"))
              if st.session_state.customer_data.get("customer_source") in source_options else 0,
        horizontal=True
    )

    col1, col2, col3 = st.columns([1, 1, 2])
    with col3:
        if st.button("下一步 →", type="primary", use_container_width=True):
            if entry_time < time(8, 0) or entry_time > time(22, 0):
                st.error("❌ 进店时间必须在 8:00-22:00 之间")
            elif leave_time < time(8, 0) or leave_time > time(22, 0):
                st.error("❌ 离店时间必须在 8:00-22:00 之间")
            else:
                companion_type_list = companion_type if isinstance(companion_type, list) else ([companion_type] if companion_type else [])
                st.session_state.customer_data.update({
                    "name": customer_name,
                    "customer_code": customer_code,
                    "visit_times": visit_times,
                    "gender": gender,
                    "age_group": age_group,
                    "entry_time": entry_time,
                    "leave_time": leave_time,
                    "stay_duration": stay_duration,
                    "companion_count": companion_count,
                    "companion_type": companion_type_list,
                    "decision_maker_present": decision_maker_present,
                    "customer_source": customer_source,
                })
                st.session_state.current_step = 1
                st.rerun()


# ──────────────────────────────────────────────────────────────
# 步骤 1：房屋装修
# ──────────────────────────────────────────────────────────────
def _step1_house_info():
    st.subheader("房屋 & 装修信息")

    house_type_options = ["别墅", "大平层", "普通住宅 (两居)", "普通住宅 (三居)", "普通住宅 (四居+)", "自建房", "公寓", "商住两用", "未告知"]
    house_type = st.radio("房屋户型", house_type_options,
        index=house_type_options.index(st.session_state.customer_data.get("house_type", "普通住宅 (三居)"))
              if st.session_state.customer_data.get("house_type") in house_type_options else 3,
        horizontal=True)

    renovation_type_options = ["全新装", "翻新装 (全屋)", "局部装 (厨房)", "局部装 (阳台)", "局部装 (卧室等)", "已装修 (仅换柜)", "未装修 (计划)", "未告知"]
    renovation_type = st.radio("装修类型", renovation_type_options,
        index=renovation_type_options.index(st.session_state.customer_data.get("renovation_type", "全新装"))
              if st.session_state.customer_data.get("renovation_type") in renovation_type_options else 0,
        horizontal=True)

    renovation_progress_options = ["刚动工", "水电阶段", "木工阶段", "收尾阶段", "已完工", "未开始", "未告知"]
    renovation_progress = st.radio("装修进度", renovation_progress_options,
        index=renovation_progress_options.index(st.session_state.customer_data.get("renovation_progress", "未开始"))
              if st.session_state.customer_data.get("renovation_progress") in renovation_progress_options else 5,
        horizontal=True)

    house_area = st.text_input("房屋所在区域",
        value=st.session_state.customer_data.get("house_area", ""),
        placeholder="如: XX小区 / XX街道")

    budget_options = ["5万以内", "5-10万", "10-20万", "20-30万", "30万以上", "未告知"]
    custom_budget = st.radio("装修预算 (定制柜部分)", budget_options,
        index=budget_options.index(st.session_state.customer_data.get("custom_budget", "10-20万"))
              if st.session_state.customer_data.get("custom_budget") in budget_options else 2,
        horizontal=True)

    st.markdown("#### 计划定制空间 (多选)")
    space_options = ["橱柜", "厅柜", "餐边柜", "家政柜", "阳台柜", "浴室柜", "鞋柜", "衣柜", "酒柜", "门墙柜一体", "其他"]
    custom_spaces = st.multiselect("", space_options,
        default=st.session_state.customer_data.get("custom_spaces", ["橱柜", "衣柜"]),
        label_visibility="collapsed")

    custom_spaces_list = custom_spaces if isinstance(custom_spaces, list) else ([custom_spaces] if custom_spaces else [])
    st.session_state.customer_data.update({
        "house_type": house_type, "renovation_type": renovation_type,
        "renovation_progress": renovation_progress, "house_area": house_area,
        "custom_budget": custom_budget, "custom_spaces": custom_spaces_list,
    })

    col1, _, _, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("← 上一步", use_container_width=True):
            st.session_state.current_step = 0
            st.rerun()
    with col4:
        if st.button("下一步 →", type="primary", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()


# ──────────────────────────────────────────────────────────────
# 步骤 2：产品偏好
# ──────────────────────────────────────────────────────────────
def _step2_product_preference():
    st.subheader("产品偏好信息")

    st.markdown("#### 偏好材质")
    material_options = ["不锈钢原色", "肤感烤漆", "哑光烤漆", "金属烤漆", "木纹色（浅）", "木纹色（深）", "大理石纹", "岩板", "玻璃"]
    material_preference = st.radio("", material_options,
        index=material_options.index(st.session_state.customer_data.get("material_preference", "不锈钢原色"))
              if st.session_state.customer_data.get("material_preference") in material_options else 0,
        horizontal=True, label_visibility="collapsed")

    st.markdown("#### 偏好色彩")
    color_options = ["亮白色", "浅暖色", "中灰色", "深灰色", "米兰迪色", "深暖色"]
    color_preference = st.radio("", color_options,
        index=color_options.index(st.session_state.customer_data.get("color_preference", "亮白色"))
              if st.session_state.customer_data.get("color_preference") in color_options else 0,
        horizontal=True, label_visibility="collapsed")

    st.markdown("#### 偏好风格")
    style_options = ["现代简约", "轻奢", "新中式", "北欧", "工业风", "日式", "其他"]
    style_preference = st.radio("", style_options,
        index=style_options.index(st.session_state.customer_data.get("style_preference", "现代简约"))
              if st.session_state.customer_data.get("style_preference") in style_options else 0,
        horizontal=True, label_visibility="collapsed")

    custom_style = st.text_input("自定义风格",
        value=st.session_state.customer_data.get("custom_style", ""))

    st.markdown("#### 关注重点")
    focus_options = ["价格", "材质环保性", "耐用性", "设计美观度", "售后保障", "收纳方便", "储藏量大", "电动智能", "容易打理"]
    focus_points = st.multiselect("", focus_options,
        default=st.session_state.customer_data.get("focus_points", []),
        label_visibility="collapsed")

    st.markdown("#### 是否对比竞品")
    competitor_options = ["是", "否"]
    has_competitor = st.radio("", competitor_options,
        index=competitor_options.index(st.session_state.customer_data.get("has_competitor", "否"))
              if st.session_state.customer_data.get("has_competitor") in competitor_options else 1,
        horizontal=True, label_visibility="collapsed")

    competitor_info = ""
    if has_competitor == "是":
        competitor_info = st.text_area("竞品情况说明",
            value=st.session_state.customer_data.get("competitor_info", ""),
            placeholder="请描述客户对比的竞品情况",
            height=100)

    st.session_state.customer_data.update({
        "material_preference": material_preference,
        "color_preference": [color_preference] if color_preference else [],
        "style_preference": [style_preference] if style_preference else [],
        "custom_style": custom_style,
        "focus_points": focus_points if isinstance(focus_points, list) else ([focus_points] if focus_points else []),
        "has_competitor": has_competitor,
        "competitor_info": competitor_info,
    })

    col1, _, _, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("← 上一步", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()
    with col4:
        if st.button("下一步 →", type="primary", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()


# ──────────────────────────────────────────────────────────────
# 步骤 3：客户生活方式
# ──────────────────────────────────────────────────────────────
def _step3_lifestyle():
    st.subheader("客户生活方式")
    st.markdown("---")

    st.markdown("### 1. 您的生活方式更接近哪种类型?")
    life_style_options = [
        "忙碌的专业人士 - 工作繁忙，追求高效便捷，易洁材质、智能收纳",
        "热爱家庭的社交达人 - 经常聚会招待朋友家人，大容量储物、多功能空间",
        "健康生活追求者 - 注重环保和健康生活方式，环保材料、有机食材存储",
        "科技产品爱好者 - 喜欢尝试最新的智能科技，智能控制系统、集成电器",
        "艺术审美追求者 - 重视美学和设计感，定制化设计、艺术元素",
    ]
    life_style = st.radio("", life_style_options,
        index=life_style_options.index(st.session_state.customer_data.get("life_style", life_style_options[0]))
              if st.session_state.customer_data.get("life_style") in life_style_options else 0,
        label_visibility="collapsed")
    st.markdown("---")

    st.markdown("### 2. 家庭情况")
    family_options = [
        "老人 - 免弯腰拉篮、电动升降",
        "5岁以下儿童 - R角圆弧防撞工艺、防指纹涂层",
        "青少年 - 学习区域设计、收纳系统",
        "经常下厨的人 - 人体工学设计、高效收纳系统",
    ]
    family_members = st.multiselect("家庭成员 (多选)", family_options,
        default=st.session_state.customer_data.get("family_members", []),
        label_visibility="collapsed")

    dining_options = [
        "1-2人 - 紧凑型餐桌、折叠餐桌",
        "3-4人 - 标准餐桌、扩展餐桌",
        "5-6人 - 大型餐桌、圆形餐桌",
        "7人以上 - 超大型餐桌、分餐设计",
    ]
    dining_count = st.radio("家里一般几位成员一起就餐?", dining_options,
        index=dining_options.index(st.session_state.customer_data.get("dining_count", dining_options[0]))
              if st.session_state.customer_data.get("dining_count") in dining_options else 0,
        label_visibility="collapsed")
    st.markdown("---")

    st.markdown("### 3. 您希望家居设计重点突出哪些方面? (多选)")
    design_focus_options = [
        "舒适体验 - 符合人体工学的舒适使用体验",
        "美观设计 - 注重视觉效果和设计美感",
        "实用功能 - 强调实用性和高效功能布局",
        "耐用品质 - 选择耐用材质和精良工艺",
        "创新科技 - 融入智能科技和创新设计",
        "环保健康 - 使用环保材料，关注健康生活",
        "收纳整理 - 完善的收纳系统和整理方案",
    ]
    design_focus = st.multiselect("", design_focus_options,
        default=st.session_state.customer_data.get("design_focus", []),
        label_visibility="collapsed")
    st.markdown("---")

    st.markdown("### 4. 储物功能上，您更倾向于:")
    storage_options = [
        '最大化储物空间，"有藏有露"，外观整洁 - 隐藏式收纳设计、分层储物系统',
        "侧重便捷性，常用物品要触手可及 - 开放式置物架、易取设计",
        "需要精细分区 (如: 餐具分隔、调料拉篮、锅具专用位) - 专业分隔系统、定制化隔板",
        "需要融入智能储物 (如: 升降柜、转角拉篮) - 智能升降系统、转角拉篮",
    ]
    storage_preference = st.radio("", storage_options,
        index=storage_options.index(st.session_state.customer_data.get("storage_preference", storage_options[0]))
              if st.session_state.customer_data.get("storage_preference") in storage_options else 0,
        label_visibility="collapsed")
    st.markdown("---")

    st.markdown("### 5. 您更偏爱哪种材质组合:")
    material_combination_options = [
        "不锈钢 + 温润木纹 (营造冷暖平衡) - 不锈钢主体、木质装饰",
        "不锈钢 + 纯净玻璃 (增强通透感) - 不锈钢框架、玻璃面板",
        "不锈钢 + 岩板/石英石 (打造高端质感) - 不锈钢结构、岩板台面",
        "不锈钢 + 烤漆面板 (色彩更丰富) - 不锈钢基材、烤漆装饰",
    ]
    material_combination = st.radio("", material_combination_options,
        index=material_combination_options.index(st.session_state.customer_data.get("material_combination", material_combination_options[0]))
              if st.session_state.customer_data.get("material_combination") in material_combination_options else 0,
        label_visibility="collapsed")
    st.markdown("---")

    st.markdown("### 6. 您最理想的家是:")
    ideal_options = [
        "更智能 - 全屋语音控制、自动化场景、智能安防",
        "更温馨 - 充满阳光、舒适的角落、家人共处的开放空间",
        "更健康 - 良好的通风、阳光照射、环保材料、绿植点缀",
        "更个性 - 能体现个人收藏和爱好、独特的色彩搭配",
        "更便捷 - 家务动线合理、一站式收纳、无死角清洁设计",
        "更灵活 - 空间可变化、家具可移动重组、适应未来家庭结构",
        "更贴近自然 - 拥有阳台花园、大量室内植物、使用天然材质",
    ]
    ideal_home = st.radio("", ideal_options,
        index=ideal_options.index(st.session_state.customer_data.get("ideal_home", ideal_options[0]))
              if st.session_state.customer_data.get("ideal_home") in ideal_options else 0,
        label_visibility="collapsed")

    st.session_state.customer_data.update({
        "life_style": life_style,
        "family_members": family_members if isinstance(family_members, list) else ([family_members] if family_members else []),
        "dining_count": dining_count,
        "design_focus": design_focus if isinstance(design_focus, list) else ([design_focus] if design_focus else []),
        "storage_preference": storage_preference,
        "material_combination": material_combination,
        "ideal_home": ideal_home,
    })

    col1, _, _, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("← 上一步", use_container_width=True):
            st.session_state.current_step = 2
            st.rerun()
    with col4:
        if st.button("下一步 →", type="primary", use_container_width=True):
            st.session_state.current_step = 4
            st.rerun()


# ──────────────────────────────────────────────────────────────
# 步骤 4：沟通转化
# ──────────────────────────────────────────────────────────────
def _step4_communication():
    st.subheader("沟通 & 转化信息")

    quote_options = ["顾客主动问价", "销售主动报价", "未提及报价"]
    quote_type = st.radio("报价相关 *", quote_options,
        index=quote_options.index(st.session_state.customer_data.get("quote_type", "销售主动报价"))
              if st.session_state.customer_data.get("quote_type") in quote_options else 1,
        horizontal=True)

    attitude_options = ["接受", "偏高 (可谈)", "过高 (不考虑)", "无明确态度"]
    quote_attitude = st.radio("对报价态度 *", attitude_options,
        index=attitude_options.index(st.session_state.customer_data.get("quote_attitude", "偏高 (可谈)"))
              if st.session_state.customer_data.get("quote_attitude") in attitude_options else 1,
        horizontal=True)

    contact_options = ["是", "否"]
    has_contact = st.radio("是否留联系方式 *", contact_options,
        index=contact_options.index(st.session_state.customer_data.get("has_contact", "是"))
              if st.session_state.customer_data.get("has_contact") in contact_options else 0,
        horizontal=True)

    contact_type = ""
    contact_info = ""
    if has_contact == "是":
        contact_type_options = ["电话", "微信", "其他"]
        contact_type = st.radio("联系方式类型", contact_type_options,
            index=contact_type_options.index(st.session_state.customer_data.get("contact_type", "电话"))
                  if st.session_state.customer_data.get("contact_type") in contact_type_options else 0,
            horizontal=True)
        contact_info = st.text_input("联系方式",
            value=st.session_state.customer_data.get("contact_info", ""),
            placeholder="电话号码将自动脱敏显示")

    intent_options = ["高意向 (一周内下单)", "中意向 (需跟进)", "低意向 (仅了解)", "无意向"]
    intent_level = st.radio("顾客意向等级 *", intent_options,
        index=intent_options.index(st.session_state.customer_data.get("intent_level", "高意向 (一周内下单)"))
              if st.session_state.customer_data.get("intent_level") in intent_options else 0,
        horizontal=True)

    appointment_options = ["预约到店", "预约上门测量", "无预约"]
    has_appointment = st.radio("是否预约后续动作 *", appointment_options,
        index=appointment_options.index(st.session_state.customer_data.get("has_appointment", "预约上门测量"))
              if st.session_state.customer_data.get("has_appointment") in appointment_options else 1,
        horizontal=True)

    appointment_time = None
    if has_appointment != "无预约":
        saved_appt = st.session_state.customer_data.get("appointment_time")
        safe_value = get_safe_appointment_value(saved_appt)
        appt_dt = st.date_input("预约日期", value=safe_value.date())
        appt_ti = st.time_input("预约时间", value=safe_value.time())
        appointment_time = datetime.combine(appt_dt, appt_ti).isoformat()

    objection = st.text_area("顾客异议点",
        value=st.session_state.customer_data.get("objection", ""),
        placeholder="如: 价格偏高 / 担心不锈钢质感冷 / 想要更多木纹款式",
        height=80)

    leave_status_options = ["迫切", "高兴", "平静", "犹豫", "不满"]
    leave_status = st.radio("客户离店状态", leave_status_options,
        index=leave_status_options.index(st.session_state.customer_data.get("leave_status", "平静"))
              if st.session_state.customer_data.get("leave_status") in leave_status_options else 2,
        horizontal=True)

    # ── 需求补充（原步骤6，合并至此）────────────────────────────
    st.markdown("---")
    st.markdown("#### 📝 特殊需求补充")
    special_needs = st.text_area("",
        value=st.session_state.customer_data.get("special_needs", ""),
        height=100,
        placeholder="例如：家里有宠物需要特殊设计、有老人需要无障碍设计、特别喜欢某种风格细节...",
        label_visibility="collapsed")

    st.session_state.customer_data.update({
        "quote_type": quote_type, "quote_attitude": quote_attitude,
        "has_contact": has_contact, "contact_type": contact_type,
        "contact_info": contact_info, "intent_level": intent_level,
        "has_appointment": has_appointment, "appointment_time": appointment_time,
        "objection": objection, "leave_status": leave_status,
        "special_needs": special_needs,
    })

    col1, _, _, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("← 上一步", use_container_width=True):
            st.session_state.current_step = 3
            st.rerun()
    with col4:
        if st.button("下一步 →", type="primary", use_container_width=True):
            st.session_state.current_step = 5
            st.rerun()


# ──────────────────────────────────────────────────────────────
# 步骤 5：确认提交 + AI分析（原步骤6，序号调整）
# ──────────────────────────────────────────────────────────────
def _step5_confirm_submit():
    st.subheader("✅ 确认提交")

    st.markdown("### 客户信息汇总")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**进店信息**")
        st.write(f"📋 顾客编号：{st.session_state.customer_data.get('customer_code', '未提供')}")
        st.write(f"🔄 进店次数：{st.session_state.customer_data.get('visit_times', '未提供')}")
        st.write(f"👤 性别：{st.session_state.customer_data.get('gender', '未提供')}")
        st.write(f"🎂 年龄段：{st.session_state.customer_data.get('age_group', '未提供')}")
        st.write(f"📍 来源：{st.session_state.customer_data.get('customer_source', '未提供')}")
        st.write(f"⏱️ 在店时长：{st.session_state.customer_data.get('stay_duration', '未提供')}")
        companions = st.session_state.customer_data.get('companion_type', [])
        st.write(f"👥 同行人员：{', '.join(companions) if companions else '无'}")
    with col2:
        st.info("**房屋装修**")
        st.write(f"🏠 房屋户型：{st.session_state.customer_data.get('house_type', '未提供')}")
        st.write(f"🔨 装修类型：{st.session_state.customer_data.get('renovation_type', '未提供')}")
        st.write(f"📊 装修进度：{st.session_state.customer_data.get('renovation_progress', '未提供')}")
        st.write(f"📍 所在区域：{st.session_state.customer_data.get('house_area', '未提供')}")
        st.write(f"💰 定制预算：{st.session_state.customer_data.get('custom_budget', '未提供')}")
        spaces = st.session_state.customer_data.get('custom_spaces', [])
        st.write(f"📦 定制空间：{', '.join(spaces) if spaces else '未提供'}")

    st.markdown("---")
    st.subheader("🧠 大师级AI深度客户分析")

    if st.session_state.ai_analysis_result:
        result = st.session_state.ai_analysis_result
        if "error" not in result:
            st.success("✅ AI分析完成！")
            if isinstance(result, dict):
                if "综合评分" in result:
                    summary = result["综合评分"]
                    st.metric("综合评分", f"{summary.get('总分', 0)}分", summary.get("评分说明", ""))
                if "客户画像标签" in result:
                    st.markdown("**客户画像标签:** " + "  |  ".join(result["客户画像标签"]))
                if "可成交预期" in result:
                    deal = result["可成交预期"]
                    st.metric("成交预期", f"{deal.get('预期分数', 0)}分", deal.get("建议成交周期", ""))
                if "详细分析" in result:
                    st.markdown("### 📋 AI详细分析建议")
                    for dimension, content in result["详细分析"].items():
                        with st.expander(f"📊 {dimension}", expanded=False):
                            if isinstance(content, dict):
                                for key, value in content.items():
                                    if key == "具体建议" and isinstance(value, list):
                                        st.write(f"**{key}:**")
                                        for item in value:
                                            st.write(f"  • {item}")
                                    else:
                                        st.write(f"**{key}:** {value}")
                            else:
                                st.write(content)
            else:
                st.markdown(result)
        else:
            st.error(f"❌ {result['error']}")

    if st.button("🤖 开始AI分析", type="primary"):
        with st.spinner("融合全球顶尖大师方法论，正在深度分析客户信息..."):
            analysis_result = mimo_analysis(st.session_state.customer_data)
            st.session_state.ai_analysis_result = analysis_result
            st.rerun()

    st.markdown("---")
    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
    with col2:
        if st.button("← 上一步", use_container_width=True):
            st.session_state.ai_analysis_result = None
            st.session_state.current_step = 4
            st.rerun()

    with col3:
        if st.button("✅ 提交客户信息", type="primary", use_container_width=True):
            data = st.session_state.customer_data.copy()

            # 时间字段序列化
            if data.get("entry_time") and not isinstance(data["entry_time"], str):
                data["entry_time"] = data["entry_time"].isoformat()
            if data.get("leave_time") and not isinstance(data["leave_time"], str):
                data["leave_time"] = data["leave_time"].isoformat()

            # 确保数组字段类型正确
            for arr_field in ["style_preference", "color_preference", "focus_points",
                               "family_members", "design_focus", "custom_spaces",
                               "companion_type"]:
                val = data.get(arr_field)
                if val is None:
                    data[arr_field] = []
                elif isinstance(val, str):
                    data[arr_field] = [val]

            data["created_at"] = datetime.now().isoformat()
            data["updated_at"] = datetime.now().isoformat()

            if st.session_state.ai_analysis_result and "error" not in st.session_state.ai_analysis_result:
                data["ai_analysis_result"] = json.dumps(
                    st.session_state.ai_analysis_result, ensure_ascii=False)

            customer_id = save_customer(data)
            if customer_id:
                st.balloons()
                st.success(f"✅ 客户信息保存成功！客户ID：{customer_id}")
                # 重置表单状态
                st.session_state.selected_customer_id = customer_id
                st.session_state.current_step = 0
                st.session_state.customer_data = {}
                st.session_state.ai_analysis_result = None
                # 自动跳转到统计面板查看结果
                st.session_state.view_mode = "📊 客户统计面板"
                st.rerun()
            else:
                st.error("❌ 保存失败，请检查数据库连接")
