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
from utils.logger import setup_logger

# 设置日志
logger = setup_logger(__name__)


# 客户洞察系统主函数
def show_customer_insight():
    st.header("🎯 客户洞察系统")
    st.markdown("---")
    
    # 操作模式切换 - 强制使用session_state保存状态
    # 使用query_params而不是直接修改session_state来避免循环渲染
    current_view_mode = st.session_state.view_mode
    
    view_mode = st.radio(
        "操作模式",
        ["📝 填写客户调研", "📊 客户统计面板"],
        horizontal=True,
        index=0 if current_view_mode == "📝 填写客户调研" else 1
    )
    
    # 只有当view_mode真正改变时才更新session_state
    if view_mode != current_view_mode:
        st.session_state.view_mode = view_mode
        st.rerun()
    
    if view_mode == "📊 客户统计面板":
        # 统计面板模式
        st.subheader("📊 客户统计面板")
        st.markdown("---")
        
        # 获取所有客户
        customers = get_all_customers()
        
        if customers:
            st.success(f"共查询到 {len(customers)} 条客户记录，所有提交的客户信息（包括生活方式调查表）都已保存到这里！")
            
            # 转换成DataFrame
            df = pd.DataFrame(customers)
            
            # 显示表格
            st.dataframe(df, use_container_width=True)
            
            # 删除功能
            st.markdown("---")
            st.subheader("🗑️ 删除客户记录")
            col1, col2 = st.columns(2)
            with col1:
                # 选择要删除的客户
                customer_options = {f"{c.get('customer_code', c.get('id', ''))}": c['id'] for c in customers}
                selected_id = st.selectbox("选择要删除的客户", options=list(customer_options.keys()))
                customer_id_to_delete = customer_options[selected_id]
            
            with col2:
                if st.button("确认删除", type="primary", help="删除后无法恢复，请谨慎操作！"):
                    if delete_customer(customer_id_to_delete):
                        st.success("✅ 删除成功！")
                        st.rerun()
                    else:
                        st.error("❌ 删除失败")
        else:
            st.info("暂无客户记录，您可以填写客户调研后提交，信息就会保存到这里了")
            
    else:
        # 填写调研模式
        # 步骤指示器 - 新的步骤列表
        steps = ["顾客基础&进店信息", "房屋装修", "产品偏好", "客户生活方式", "沟通转化", "需求补充", "确认提交"]
        
        current_step = st.session_state.current_step
        
        # 进度条
        progress = current_step / (len(steps) - 1)
        st.progress(progress)
        
        cols = st.columns(len(steps))
        for i, step in enumerate(steps):
            with cols[i]:
                if i == current_step:
                    st.markdown(f'<span class="step-indicator step-active">{i+1}</span> {step}', unsafe_allow_html=True)
                elif i < current_step:
                    st.markdown(f'<span class="step-indicator step-completed">✓</span> {step}', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="step-indicator step-pending">{i+1}</span> {step}', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 步骤0：顾客基础&进店信息
        if current_step == 0:
            st.subheader("顾客基础 & 进店信息")
            st.info("💡 提示：进店和离店时间请选择 8:00-22:00 之间的时间")

            # 自动生成顾客编号
            today = datetime.now().strftime("%Y%m%d")
            default_code = f"BINK-{today}-{random.randint(100, 999)}"

            # 客户姓名（必填）
            customer_name = st.text_input(
                "客户姓名 *",
                value=st.session_state.customer_data.get("name", ""),
                help="请输入客户姓名，此字段为必填项"
            )

            customer_code = st.text_input(
                "顾客编号",
                value=st.session_state.customer_data.get("customer_code", default_code)
            )
            
            # 进店次数
            visit_options = ["第1次", "第2次", "第3次"]
            visit_times = st.radio(
                "客户进店第几次",
                visit_options,
                index=visit_options.index(st.session_state.customer_data.get("visit_times", "第1次")) if st.session_state.customer_data.get("visit_times") in visit_options else 0,
                horizontal=True
            )
            
            # 性别
            gender_options = ["男", "女"]
            gender = st.radio(
                "顾客性别",
                gender_options,
                index=gender_options.index(st.session_state.customer_data.get("gender", "男")) if st.session_state.customer_data.get("gender") in gender_options else 0,
                horizontal=True
            )
            
            # 年龄段
            age_options = ["18-25岁", "26-35岁", "36-45岁", "46-55岁", "56岁以上", "未询问"]
            age_group = st.radio(
                "顾客年龄段",
                age_options,
                index=age_options.index(st.session_state.customer_data.get("age_group", "26-35岁")) if st.session_state.customer_data.get("age_group") in age_options else 1,
                horizontal=True
            )
            
            # 时间 - 兼容旧版本Streamlit
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
            
            # 自动计算在店时长
            stay_duration = st.session_state.customer_data.get("stay_duration", "请填写进店和离店时间")
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
            
            stay_duration = st.text_input(
                "在店时长",
                value=stay_duration,
                disabled=True
            )
            
            # 同行人数
            companion_options = ["0", "1", "2", "3人及以上"]
            companion_count = st.radio(
                "同行人数 *",
                companion_options,
                index=companion_options.index(st.session_state.customer_data.get("companion_count", "1")) if st.session_state.customer_data.get("companion_count") in companion_options else 1,
                horizontal=True
            )
            
            # 同行人员类型 - 按钮式多选，完全按照您的要求
            st.markdown("#### 同行人员类型 (多选，直接点击选择)")
            companion_type_options = ["配偶", "朋友", "父母", "孩子", "设计师", "同购者", "装修师傅", "其他"]
            companion_type = st.multiselect(
                "",
                companion_type_options,
                default=st.session_state.customer_data.get("companion_type", []),
                label_visibility="collapsed"
            )
            
            # 决策人是否同行
            decision_options = ["是", "否", "不确定"]
            decision_maker_present = st.radio(
                "决策人是否同行",
                decision_options,
                index=decision_options.index(st.session_state.customer_data.get("decision_maker_present", "是")) if st.session_state.customer_data.get("decision_maker_present") in decision_options else 0,
                horizontal=True
            )
            
            # 顾客来源
            source_options = ["自然到店", "老客介绍", "线上推广 (抖音/小红书等)", "小区拓客", "装修公司推荐", "其他"]
            customer_source = st.radio(
                "顾客来源",
                source_options,
                index=source_options.index(st.session_state.customer_data.get("customer_source", "自然到店")) if st.session_state.customer_data.get("customer_source") in source_options else 0,
                horizontal=True
            )
            
            # 下一步按钮
            col1, col2, col3 = st.columns([1, 1, 2])
            with col3:
                if st.button("下一步 →", type="primary", use_container_width=True):
                    # 验证时间
                    if entry_time < time(8, 0) or entry_time > time(22, 0):
                        st.error("❌ 进店时间必须在 8:00-22:00 之间，请重新选择")
                    elif leave_time < time(8, 0) or leave_time > time(22, 0):
                        st.error("❌ 离店时间必须在 8:00-22:00 之间，请重新选择")
                    elif not entry_time or not leave_time:
                        st.error("请填写进店时间和离店时间")
                    else:
                        # 保存数据 - 确保数组类型字段正确转换
                        # companion_type 是多选,需要确保是列表
                        companion_type_list = companion_type if isinstance(companion_type, list) else [companion_type] if companion_type else []

                        st.session_state.customer_data.update({
                            "name": customer_name,  # 添加客户姓名
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
                            "customer_source": customer_source
                        })
                        st.session_state.current_step = 1
                        st.rerun()
        
        # 步骤1：房屋装修
        elif current_step == 1:
            st.subheader("房屋 & 装修信息")
            
            # 房屋户型
            house_type_options = ["别墅", "大平层", "普通住宅 (两居)", "普通住宅 (三居)", "普通住宅 (四居+)", "自建房", "公寓", "商住两用", "未告知"]
            house_type = st.radio(
                "房屋户型",
                house_type_options,
                index=house_type_options.index(st.session_state.customer_data.get("house_type", "普通住宅 (三居)")) if st.session_state.customer_data.get("house_type") in house_type_options else 3,
                horizontal=True
            )
            
            # 装修类型
            renovation_type_options = ["全新装", "翻新装 (全屋)", "局部装 (厨房)", "局部装 (阳台)", "局部装 (卧室等)", "已装修 (仅换柜)", "未装修 (计划)", "未告知"]
            renovation_type = st.radio(
                "装修类型",
                renovation_type_options,
                index=renovation_type_options.index(st.session_state.customer_data.get("renovation_type", "全新装")) if st.session_state.customer_data.get("renovation_type") in renovation_type_options else 0,
                horizontal=True
            )
            
            # 装修进度
            renovation_progress_options = ["刚动工", "水电阶段", "木工阶段", "收尾阶段", "已完工", "未开始", "未告知"]
            renovation_progress = st.radio(
                "装修进度",
                renovation_progress_options,
                index=renovation_progress_options.index(st.session_state.customer_data.get("renovation_progress", "未开始")) if st.session_state.customer_data.get("renovation_progress") in renovation_progress_options else 5,
                horizontal=True
            )
            
            # 房屋所在区域
            house_area = st.text_input(
                "房屋所在区域",
                value=st.session_state.customer_data.get("house_area", ""),
                placeholder="如: XX小区 / XX街道"
            )
            
            # 装修预算（定制柜部分）
            budget_options = ["5万以内", "5-10万", "10-20万", "20-30万", "30万以上", "未告知"]
            custom_budget = st.radio(
                "装修预算 (定制柜部分)",
                budget_options,
                index=budget_options.index(st.session_state.customer_data.get("custom_budget", "10-20万")) if st.session_state.customer_data.get("custom_budget") in budget_options else 2,
                horizontal=True
            )
            
            # 计划定制空间 - 按钮式多选，完全按照您的要求
            st.markdown("#### 计划定制空间 (多选，直接点击选择)")
            space_options = ["橱柜", "厅柜", "餐边柜", "家政柜", "阳台柜", "浴室柜", "鞋柜", "衣柜", "酒柜", "门墙柜一体", "其他"]
            custom_spaces = st.multiselect(
                "",
                space_options,
                default=st.session_state.customer_data.get("custom_spaces", ["橱柜", "衣柜"]),
                label_visibility="collapsed"
            )
            
            # 保存数据 - 确保数组类型字段正确转换
            # custom_spaces 是多选,需要确保是列表
            custom_spaces_list = custom_spaces if isinstance(custom_spaces, list) else [custom_spaces] if custom_spaces else []
            
            st.session_state.customer_data.update({
                "house_type": house_type,
                "renovation_type": renovation_type,
                "renovation_progress": renovation_progress,
                "house_area": house_area,
                "custom_budget": custom_budget,
                "custom_spaces": custom_spaces_list
            })
            
            # 按钮
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if st.button("← 上一步", use_container_width=True):
                    st.session_state.current_step = 0
                    st.rerun()
            with col4:
                if st.button("下一步 →", type="primary", use_container_width=True):
                    st.session_state.current_step = 2
                    st.rerun()
        
        # 步骤2：产品偏好
        elif current_step == 2:
            st.subheader("产品偏好信息")
            
            # 偏好材质 - 按钮式选择
            st.markdown("#### 偏好材质")
            material_options = ["不锈钢原色", "肤感烤漆", "哑光烤漆", "金属烤漆", "木纹色（浅）", "木纹色（深）", "大理石纹", "岩板", "玻璃"]
            material_preference = st.radio(
                "",
                material_options,
                index=material_options.index(st.session_state.customer_data.get("material_preference", "不锈钢原色")) if st.session_state.customer_data.get("material_preference") in material_options else 0,
                horizontal=True,
                label_visibility="collapsed"
            )
            
            # 偏好颜色 - 按钮式选择
            st.markdown("#### 偏好色彩")
            color_options = ["亮白色", "浅暖色", "中灰色", "深灰色", "米兰迪色", "深暖色"]
            color_preference = st.radio(
                "",
                color_options,
                index=color_options.index(st.session_state.customer_data.get("color_preference", "亮白色")) if st.session_state.customer_data.get("color_preference") in color_options else 0,
                horizontal=True,
                label_visibility="collapsed"
            )
            
            # 偏好风格
            st.markdown("#### 偏好风格")
            style_options = ["现代简约", "轻奢", "新中式", "北欧", "工业风", "日式", "其他"]
            style_preference = st.radio(
                "",
                style_options,
                index=style_options.index(st.session_state.customer_data.get("style_preference", "现代简约")) if st.session_state.customer_data.get("style_preference") in style_options else 0,
                horizontal=True,
                label_visibility="collapsed"
            )
            
            custom_style = st.text_input(
                "自定义风格",
                value=st.session_state.customer_data.get("custom_style", "")
            )
            
            # 关注重点
            st.markdown("#### 关注重点")
            focus_options = ["价格", "材质环保性", "耐用性", "设计美观度", "售后保障", "收纳方便", "储藏量大", "电动智能", "容易打理"]
            focus_points = st.multiselect(
                "",
                focus_options,
                default=st.session_state.customer_data.get("focus_points", []),
                label_visibility="collapsed"
            )
            
            # 是否对比竞品
            st.markdown("#### 是否对比竞品")
            competitor_options = ["是", "否"]
            has_competitor = st.radio(
                "",
                competitor_options,
                index=competitor_options.index(st.session_state.customer_data.get("has_competitor", "否")) if st.session_state.customer_data.get("has_competitor") in competitor_options else 1,
                horizontal=True,
                label_visibility="collapsed"
            )
            
            # 如果选择是，显示竞品情况
            competitor_info = ""
            if has_competitor == "是":
                competitor_info = st.text_area(
                    "竞品情况说明",
                    value=st.session_state.customer_data.get("competitor_info", ""),
                    placeholder="请描述客户对比的竞品情况，如品牌、价格、产品特点等",
                    height=100
                )

            # 保存数据 - 确保数组类型字段正确转换
            # 注意：style_preference 和 color_preference 虽然是单选,但如果数据库是 TEXT[] 类型,需要转换为数组
            style_preference_array = [style_preference] if style_preference else []
            color_preference_array = [color_preference] if color_preference else []

            st.session_state.customer_data.update({
                "material_preference": material_preference,
                "color_preference": color_preference_array,  # 转换为数组
                "style_preference": style_preference_array,  # 转换为数组
                "custom_style": custom_style,
                "focus_points": focus_points if isinstance(focus_points, list) else [focus_points] if focus_points else [],
                "has_competitor": has_competitor,
                "competitor_info": competitor_info
            })
            
            # 按钮
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if st.button("← 上一步", use_container_width=True):
                    st.session_state.current_step = 1
                    st.rerun()
            with col4:
                if st.button("下一步 →", type="primary", use_container_width=True):
                    st.session_state.current_step = 3
                    st.rerun()
        
        # 步骤3：客户生活方式
        elif current_step == 3:
            st.subheader("客户生活方式")
            st.markdown("请您填写以下信息，帮助我们为您定制最适合的家居方案")
            st.markdown("---")
            
            # 1. 生活方式
            st.markdown("### 1. 您的生活方式更接近哪种类型?")
            life_style_options = [
                "忙碌的专业人士 - 工作繁忙，追求高效便捷，易洁材质、智能收纳",
                "热爱家庭的社交达人 - 经常聚会招待朋友家人，大容量储物、多功能空间",
                "健康生活追求者 - 注重环保和健康生活方式，环保材料、有机食材存储",
                "科技产品爱好者 - 喜欢尝试最新的智能科技，智能控制系统、集成电器",
                "艺术审美追求者 - 重视美学和设计感，定制化设计、艺术元素"
            ]
            life_style = st.radio(
                "",
                life_style_options,
                index=0 if st.session_state.customer_data.get("life_style") is None else life_style_options.index(st.session_state.customer_data.get("life_style")),
                label_visibility="collapsed"
            )
            st.markdown("---")
            
            # 2. 家庭成员&就餐人数（整合）
            st.markdown("### 2. 家庭情况")
            family_options = [
                "老人 - 免弯腰拉篮、电动升降",
                "5岁以下儿童 - R角圆弧防撞工艺、防指纹涂层",
                "青少年 - 学习区域设计、收纳系统",
                "经常下厨的人 - 人体工学设计、高效收纳系统"
            ]
            family_members = st.multiselect(
                "家庭成员 (多选)",
                family_options,
                default=st.session_state.customer_data.get("family_members", []),
                label_visibility="collapsed"
            )
            
            # 就餐人数
            dining_options = [
                "1-2人 - 紧凑型餐桌、折叠餐桌",
                "3-4人 - 标准餐桌、扩展餐桌",
                "5-6人 - 大型餐桌、圆形餐桌",
                "7人以上 - 超大型餐桌、分餐设计"
            ]
            dining_count = st.radio(
                "家里一般几位成员一起就餐?",
                dining_options,
                index=0 if st.session_state.customer_data.get("dining_count") is None else dining_options.index(st.session_state.customer_data.get("dining_count")),
                label_visibility="collapsed"
            )
            st.markdown("---")
            
            # 3. 设计重点 - 按钮式多选
            st.markdown("### 3. 您希望家居设计重点突出哪些方面? (多选)")
            focus_options = [
                "舒适体验 - 符合人体工学的舒适使用体验",
                "美观设计 - 注重视觉效果和设计美感",
                "实用功能 - 强调实用性和高效功能布局",
                "耐用品质 - 选择耐用材质和精良工艺",
                "创新科技 - 融入智能科技和创新设计",
                "环保健康 - 使用环保材料，关注健康生活",
                "收纳整理 - 完善的收纳系统和整理方案"
            ]
            design_focus = st.multiselect(
                "",
                focus_options,
                default=st.session_state.customer_data.get("design_focus", []),
                label_visibility="collapsed"
            )
            st.markdown("---")
            
            # 4. 储物功能
            st.markdown("### 4. 储物功能上，您更倾向于:")
            storage_options = [
                '最大化储物空间，"有藏有露"，外观整洁 - 隐藏式收纳设计、分层储物系统',
                "侧重便捷性，常用物品要触手可及 - 开放式置物架、易取设计",
                "需要精细分区 (如: 餐具分隔、调料拉篮、锅具专用位) - 专业分隔系统、定制化隔板",
                "需要融入智能储物 (如: 升降柜、转角拉篮) - 智能升降系统、转角拉篮"
            ]
            storage_preference = st.radio(
                "",
                storage_options,
                index=0 if st.session_state.customer_data.get("storage_preference") is None else storage_options.index(st.session_state.customer_data.get("storage_preference")),
                label_visibility="collapsed"
            )
            st.markdown("---")
            
            # 5. 材质组合
            st.markdown("### 5. 您更偏爱哪种材质组合:")
            material_options = [
                "不锈钢 + 温润木纹 (营造冷暖平衡) - 不锈钢主体、木质装饰",
                "不锈钢 + 纯净玻璃 (增强通透感) - 不锈钢框架、玻璃面板",
                "不锈钢 + 岩板/石英石 (打造高端质感) - 不锈钢结构、岩板台面",
                "不锈钢 + 烤漆面板 (色彩更丰富) - 不锈钢基材、烤漆装饰"
            ]
            material_combination = st.radio(
                "",
                material_options,
                index=0 if st.session_state.customer_data.get("material_combination") is None else material_options.index(st.session_state.customer_data.get("material_combination")),
                label_visibility="collapsed"
            )
            st.markdown("---")
            
            # 6. 理想的家
            st.markdown("### 6. 您最理想的家是:")
            ideal_options = [
                "更智能 - 全屋语音控制、自动化场景、智能安防",
                "更温馨 - 充满阳光、舒适的角落、家人共处的开放空间",
                "更健康 - 良好的通风、阳光照射、环保材料、绿植点缀",
                "更个性 - 能体现个人收藏和爱好、独特的色彩搭配",
                "更便捷 - 家务动线合理、一站式收纳、无死角清洁设计",
                "更灵活 - 空间可变化、家具可移动重组、适应未来家庭结构",
                "更贴近自然 - 拥有阳台花园、大量室内植物、使用天然材质"
            ]
            ideal_home = st.radio(
                "",
                ideal_options,
                index=0 if st.session_state.customer_data.get("ideal_home") is None else ideal_options.index(st.session_state.customer_data.get("ideal_home")),
                label_visibility="collapsed"
            )
            
            # 保存数据 - 确保数组类型字段正确转换
            # family_members 和 design_focus 是多选,需要确保是列表
            family_members_list = family_members if isinstance(family_members, list) else [family_members] if family_members else []
            design_focus_list = design_focus if isinstance(design_focus, list) else [design_focus] if design_focus else []
            
            st.session_state.customer_data.update({
                "life_style": life_style,
                "family_members": family_members_list,
                "dining_count": dining_count,
                "design_focus": design_focus_list,
                "storage_preference": storage_preference,
                "material_combination": material_combination,
                "ideal_home": ideal_home
            })
            
            # 按钮
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if st.button("← 上一步", use_container_width=True):
                    st.session_state.current_step = 2
                    st.rerun()
            with col4:
                if st.button("下一步 →", type="primary", use_container_width=True):
                    st.session_state.current_step = 4
                    st.rerun()
        
        # 步骤4：沟通转化
        elif current_step == 4:
            st.subheader("沟通 & 转化信息")
            
            # 报价相关
            quote_options = ["顾客主动问价", "销售主动报价", "未提及报价"]
            quote_type = st.radio(
                "报价相关 *",
                quote_options,
                index=quote_options.index(st.session_state.customer_data.get("quote_type", "销售主动报价")) if st.session_state.customer_data.get("quote_type") in quote_options else 1,
                horizontal=True
            )
            
            # 对报价态度
            attitude_options = ["接受", "偏高 (可谈)", "过高 (不考虑)", "无明确态度"]
            quote_attitude = st.radio(
                "对报价态度 *",
                attitude_options,
                index=attitude_options.index(st.session_state.customer_data.get("quote_attitude", "偏高 (可谈)")) if st.session_state.customer_data.get("quote_attitude") in attitude_options else 1,
                horizontal=True
            )
            
            # 是否留联系方式
            contact_options = ["是", "否"]
            has_contact = st.radio(
                "是否留联系方式 *",
                contact_options,
                index=contact_options.index(st.session_state.customer_data.get("has_contact", "是")) if st.session_state.customer_data.get("has_contact") in contact_options else 0,
                horizontal=True
            )
            
            contact_type = ""
            contact_info = ""
            if has_contact == "是":
                # 联系方式类型
                contact_type_options = ["电话", "微信", "其他"]
                contact_type = st.radio(
                    "联系方式类型",
                    contact_type_options,
                    index=contact_type_options.index(st.session_state.customer_data.get("contact_type", "电话")) if st.session_state.customer_data.get("contact_type") in contact_type_options else 0,
                    horizontal=True
                )
                
                # 联系方式
                contact_info = st.text_input(
                    "联系方式",
                    value=st.session_state.customer_data.get("contact_info", ""),
                    placeholder="请填写联系方式，电话号码将自动脱敏显示"
                )
            
            # 顾客意向等级
            intent_options = ["高意向 (一周内下单)", "中意向 (需跟进)", "低意向 (仅了解)", "无意向"]
            intent_level = st.radio(
                "顾客意向等级 *",
                intent_options,
                index=intent_options.index(st.session_state.customer_data.get("intent_level", "高意向 (一周内下单)")) if st.session_state.customer_data.get("intent_level") in intent_options else 0,
                horizontal=True
            )
            
            # 是否预约后续动作
            appointment_options = ["预约到店", "预约上门测量", "无预约"]
            has_appointment = st.radio(
                "是否预约后续动作 *",
                appointment_options,
                index=appointment_options.index(st.session_state.customer_data.get("has_appointment", "预约上门测量")) if st.session_state.customer_data.get("has_appointment") in appointment_options else 1,
                horizontal=True
            )
            
            appointment_time = None
            if has_appointment != "无预约":
                # 安全的获取预约时间，避免过去的时间导致错误
                saved_appt = st.session_state.customer_data.get("appointment_time")
                safe_value = get_safe_appointment_value(saved_appt)
                
                appointment_time = st.datetime_input(
                    "预约时间",
                    value=safe_value,
                    min_value=datetime.now()
                )
                # 转换为字符串
                if appointment_time:
                    appointment_time = appointment_time.isoformat()
            
            # 顾客异议点
            objection = st.text_area(
                "顾客异议点",
                value=st.session_state.customer_data.get("objection", ""),
                placeholder="如: 价格偏高 / 担心不锈钢质感冷 / 想要更多木纹款式",
                height=80
            )
            
            # 客户离店状态
            leave_status_options = ["迫切", "高兴", "平静", "犹豫", "不满"]
            leave_status = st.radio(
                "客户离店状态",
                leave_status_options,
                index=leave_status_options.index(st.session_state.customer_data.get("leave_status", "平静")) if st.session_state.customer_data.get("leave_status") in leave_status_options else 2,
                horizontal=True
            )
            
            # 保存数据
            st.session_state.customer_data.update({
                "quote_type": quote_type,
                "quote_attitude": quote_attitude,
                "has_contact": has_contact,
                "contact_type": contact_type,
                "contact_info": contact_info,
                "intent_level": intent_level,
                "has_appointment": has_appointment,
                "appointment_time": appointment_time,
                "objection": objection,
                "leave_status": leave_status
            })
            
            # 按钮
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if st.button("← 上一步", use_container_width=True):
                    st.session_state.current_step = 3
                    st.rerun()
            with col4:
                if st.button("下一步 →", type="primary", use_container_width=True):
                    st.session_state.current_step = 5
                    st.rerun()
        
        # 步骤5：需求补充
        elif current_step == 5:
            st.subheader("需求补充")
            
            special_needs = st.text_area(
                "特殊需求补充",
                value=st.session_state.customer_data.get("special_needs", ""),
                height=200,
                placeholder="例如：家里有宠物需要特殊设计、有老人需要无障碍设计、有幼童需要防护、或者其他特殊需求..."
            )
            
            # 保存数据
            st.session_state.customer_data.update({
                "special_needs": special_needs
            })
            
            # 按钮
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if st.button("← 上一步", use_container_width=True):
                    st.session_state.current_step = 4
                    st.rerun()
            with col4:
                if st.button("下一步 →", type="primary", use_container_width=True):
                    st.session_state.current_step = 6
                    st.rerun()
        
        # 步骤6：确认提交
        elif current_step == 6:
            st.subheader("✅ 确认提交")
            
            # 显示汇总信息
            st.markdown("### 客户信息汇总")
            
            col1, col2 = st.columns(2)
            with col1:
                with st.container():
                    st.info("**进店信息**")
                    st.write(f"📋 顾客编号：{st.session_state.customer_data.get('customer_code', '未提供')}")
                    st.write(f"🔄 进店次数：{st.session_state.customer_data.get('visit_times', '未提供')}")
                    st.write(f"👤 性别：{st.session_state.customer_data.get('gender', '未提供')}")
                    st.write(f"🎂 年龄段：{st.session_state.customer_data.get('age_group', '未提供')}")
                    st.write(f"📍 来源：{st.session_state.customer_data.get('customer_source', '未提供')}")
                    st.write(f"⏱️ 在店时长：{st.session_state.customer_data.get('stay_duration', '未提供')}")
                    st.write(f"👥 同行人员：{', '.join(st.session_state.customer_data.get('companion_type', []))}")
            
            with col2:
                with st.container():
                    st.info("**房屋装修**")
                    st.write(f"🏠 房屋户型：{st.session_state.customer_data.get('house_type', '未提供')}")
                    st.write(f"🔨 装修类型：{st.session_state.customer_data.get('renovation_type', '未提供')}")
                    st.write(f"📊 装修进度：{st.session_state.customer_data.get('renovation_progress', '未提供')}")
                    st.write(f"📍 所在区域：{st.session_state.customer_data.get('house_area', '未提供')}")
                    st.write(f"💰 定制预算：{st.session_state.customer_data.get('custom_budget', '未提供')}")
                    st.write(f"📦 定制空间：{', '.join(st.session_state.customer_data.get('custom_spaces', []))}")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                with st.container():
                    st.info("**产品偏好**")
                    st.write(f"🪵 偏好材质：{st.session_state.customer_data.get('material_preference', '未提供')}")
                    st.write(f"🎨 偏好颜色：{st.session_state.customer_data.get('color_preference', '未提供')}")
                    st.write(f"✨ 偏好风格：{st.session_state.customer_data.get('style_preference', '未提供')}")
                    st.write(f"🎯 关注重点：{', '.join(st.session_state.customer_data.get('focus_points', []))}")
                    if st.session_state.customer_data.get('has_competitor') == "是":
                        st.write(f"⚔️ 竞品情况：{st.session_state.customer_data.get('competitor_info', '未提供')}")
            
            with col2:
                with st.container():
                    st.info("**生活方式**")
                    st.write(f"👤 生活方式：{st.session_state.customer_data.get('life_style', '未提供')}")
                    st.write(f"👨‍👩‍👧‍👦 家庭成员：{', '.join(st.session_state.customer_data.get('family_members', []))}")
                    st.write(f"🍽️ 就餐人数：{st.session_state.customer_data.get('dining_count', '未提供')}")
                    st.write(f"🎯 设计重点：{', '.join(st.session_state.customer_data.get('design_focus', []))}")
                    st.write(f"📦 储物偏好：{st.session_state.customer_data.get('storage_preference', '未提供')}")
                    st.write(f"🪨 材质组合：{st.session_state.customer_data.get('material_combination', '未提供')}")
                    st.write(f"🏡 理想的家：{st.session_state.customer_data.get('ideal_home', '未提供')}")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                with st.container():
                    st.info("**沟通转化**")
                    st.write(f"💬 报价情况：{st.session_state.customer_data.get('quote_type', '未提供')}")
                    st.write(f"💹 报价态度：{st.session_state.customer_data.get('quote_attitude', '未提供')}")
                    st.write(f"⭐ 意向等级：{st.session_state.customer_data.get('intent_level', '未提供')}")
                    st.write(f"😊 离店状态：{st.session_state.customer_data.get('leave_status', '未提供')}")
                    if st.session_state.customer_data.get('has_contact') == "是":
                        st.write(f"📱 联系方式：{st.session_state.customer_data.get('contact_info', '未提供')}")
            
            with col2:
                with st.container():
                    st.info("**需求补充**")
                    st.write(st.session_state.customer_data.get('special_needs', '无特殊需求'))
            
            st.markdown("---")
            
            # MIMO大模型分析
            st.subheader("🧠 大师级AI深度客户分析")
            
            # 显示已有的分析结果
            if st.session_state.ai_analysis_result:
                result = st.session_state.ai_analysis_result
                if "error" not in result:
                    st.success("✅ AI分析完成！")
                    
                    # 新的分析结果展示方式：先显示综合信息，再显示详细分析
                    if isinstance(result, dict):
                        # 第一部分：综合评分
                        if "综合评分" in result:
                            st.markdown("### 📊 综合评分")
                            summary = result["综合评分"]
                            total_score = summary.get("总分", 0)
                            score_desc = summary.get("评分说明", "")
                            
                            st.markdown(f"""
                            <div class="ai-summary-card">
                                <div class="score-display">{total_score}分</div>
                                <p style="text-align: center; color: #2d342d; margin-bottom: 16px;">{score_desc}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # 第二部分：客户画像标签
                        if "客户画像标签" in result:
                            st.markdown("### 🏷️ 客户画像标签")
                            tags = result["客户画像标签"]
                            tags_html = " ".join([f'<span class="customer-tag">{tag}</span>' for tag in tags])
                            st.markdown(f"""
                            <div class="customer-tags">
                                {tags_html}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # 第三部分：可成交预期
                        if "可成交预期" in result:
                            st.markdown("### 💰 可成交预期")
                            deal = result["可成交预期"]
                            prob_score = deal.get("预期分数", 0)
                            prob_desc = deal.get("预期说明", "")
                            deal_cycle = deal.get("建议成交周期", "")
                            
                            st.markdown(f"""
                            <div class="deal-probability">
                                <div class="probability-value">{prob_score}分</div>
                                <p><strong>预期说明：</strong>{prob_desc}</p>
                                <p><strong>建议成交周期：</strong>{deal_cycle}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # 第四部分：详细分析（分块展示）
                        if "详细分析" in result:
                            st.markdown("---")
                            st.markdown("### 📋 AI详细分析建议")
                            detailed = result["详细分析"]
                            
                            for dimension, content in detailed.items():
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
                            # 兼容旧版本格式
                            for dimension, content in result.items():
                                if dimension not in ["综合评分", "客户画像标签", "可成交预期", "详细分析"]:
                                    with st.expander(f"📊 {dimension}", expanded=False):
                                        if isinstance(content, dict):
                                            for key, value in content.items():
                                                st.write(f"**{key}:** {value}")
                                        else:
                                            st.write(content)
                    else:
                        # 非dict格式，直接显示
                        st.markdown(result)
                else:
                    st.error(f"❌ {result['error']}")
            
            # 分析按钮
            if st.button("开始AI分析", type="primary"):
                with st.spinner("🤖 融合全球顶尖大师方法论，正在深度分析客户信息..."):
                    analysis_result = mimo_analysis(st.session_state.customer_data)
                    # 保存结果到session_state，避免刷新丢失
                    st.session_state.ai_analysis_result = analysis_result
                    # 刷新页面显示结果，但是current_step不会变！
                    st.rerun()
            
            st.markdown("---")
            
            # 提交按钮
            col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
            with col2:
                if st.button("← 上一步", use_container_width=True):
                    # 重置AI分析结果
                    st.session_state.ai_analysis_result = None
                    st.session_state.current_step = 5
                    st.rerun()
            
            with col3:
                if st.button("✅ 提交客户信息", type="primary", use_container_width=True):
                    # 处理时间类型字段，转换为字符串避免JSON序列化错误
                    data = st.session_state.customer_data.copy()

                    # 调试信息：显示所有字段的类型和值
                    st.write("🔍 完整调试信息（提交前）：")
                    st.write(f"所有字段：")
                    for key, value in data.items():
                        st.write(f"  - {key}: {value} (类型: {type(value).__name__})")

                    # 处理进店/离店时间
                    if data.get("entry_time"):
                        data["entry_time"] = data["entry_time"].isoformat()
                    if data.get("leave_time"):
                        data["leave_time"] = data["leave_time"].isoformat()

                    # 调试信息：检查 style_preference 和 color_preference 的类型和值
                    st.write(f"🔍 调试信息 - style_preference: {data.get('style_preference')}, 类型: {type(data.get('style_preference'))}")
                    st.write(f"🔍 调试信息 - color_preference: {data.get('color_preference')}, 类型: {type(data.get('color_preference'))}")

                    # 确保数组类型字段正确转换
                    # 处理 style_preference：如果是字符串，转换为数组
                    style_pref = data.get("style_preference")
                    if style_pref:
                        if isinstance(style_pref, str):
                            data["style_preference"] = [style_pref]
                            st.write(f"✅ 已将字符串 '{style_pref}' 转换为数组")
                        elif isinstance(style_pref, list):
                            st.write(f"✅ style_preference 已经是数组: {style_pref}")
                        else:
                            st.write(f"⚠️ style_preference 类型异常: {type(style_pref)}, 值: {style_pref}")
                            data["style_preference"] = [str(style_pref)]
                    else:
                        data["style_preference"] = []
                        st.write("⚠️ style_preference 为空，设置为空数组")

                    # 处理 color_preference：如果是字符串，转换为数组
                    color_pref = data.get("color_preference")
                    if color_pref:
                        if isinstance(color_pref, str):
                            data["color_preference"] = [color_pref]
                            st.write(f"✅ 已将字符串 '{color_pref}' 转换为数组")
                        elif isinstance(color_pref, list):
                            st.write(f"✅ color_preference 已经是数组: {color_pref}")
                        else:
                            st.write(f"⚠️ color_preference 类型异常: {type(color_pref)}, 值: {color_pref}")
                            data["color_preference"] = [str(color_pref)]
                    else:
                        data["color_preference"] = []
                        st.write("⚠️ color_preference 为空，设置为空数组")

                    # 处理 focus_points：确保是数组
                    if data.get("focus_points") and isinstance(data["focus_points"], str):
                        data["focus_points"] = [data["focus_points"]]
                    elif not data.get("focus_points"):
                        data["focus_points"] = []

                    # 处理 family_members：确保是数组
                    if data.get("family_members") and isinstance(data["family_members"], str):
                        data["family_members"] = [data["family_members"]]
                    elif not data.get("family_members"):
                        data["family_members"] = []

                    # 处理 design_focus：确保是数组
                    if data.get("design_focus") and isinstance(data["design_focus"], str):
                        data["design_focus"] = [data["design_focus"]]
                    elif not data.get("design_focus"):
                        data["design_focus"] = []

                    # 处理 custom_spaces：确保是数组
                    if data.get("custom_spaces") and isinstance(data["custom_spaces"], str):
                        data["custom_spaces"] = [data["custom_spaces"]]
                    elif not data.get("custom_spaces"):
                        data["custom_spaces"] = []

                    # 处理 companion_type：确保是数组
                    if data.get("companion_type") and isinstance(data["companion_type"], str):
                        data["companion_type"] = [data["companion_type"]]
                    elif not data.get("companion_type"):
                        data["companion_type"] = []

                    # 添加时间戳
                    data["created_at"] = datetime.now().isoformat()
                    data["updated_at"] = datetime.now().isoformat()
                    
                    # 保存AI分析结果到数据库（如果有）
                    if st.session_state.ai_analysis_result and "error" not in st.session_state.ai_analysis_result:
                        data["ai_analysis_result"] = json.dumps(st.session_state.ai_analysis_result, ensure_ascii=False)
                    
                    # 保存到Supabase
                    # 调试信息：显示保存前的数据
                    st.write("🔍 调试信息 - 准备保存到数据库的数据（关键数组字段）：")
                    st.write(f"style_preference: {data.get('style_preference')}, 类型: {type(data.get('style_preference'))}")
                    st.write(f"material_preference: {data.get('material_preference')}, 类型: {type(data.get('material_preference'))}")
                    st.write(f"color_preference: {data.get('color_preference')}, 类型: {type(data.get('color_preference'))}")
                    st.write(f"focus_points: {data.get('focus_points')}, 类型: {type(data.get('focus_points'))}")

                    customer_id = save_customer(data)
                    
                    if customer_id:
                        st.success(f"✅ 客户信息保存成功！客户ID：{customer_id}")
                        st.info("📋 所有信息（包括生活方式调查表和AI分析）都已经保存到【客户统计面板】中")
                        st.info("💡 请点击左侧导航栏的【🎨 设计辅助】进入设计系统")
                        # 保存客户ID供后续使用
                        st.session_state.selected_customer_id = customer_id
                        # 重置表单数据
                        st.session_state.current_step = 0
                        st.session_state.customer_data = {}
                        st.session_state.ai_analysis_result = None
                        st.balloons()
                        # 不再自动跳转，让用户手动点击导航
                        # st.session_state.current_page = "设计辅助"
                        # st.rerun()
                    else:
                        st.error("❌ 保存失败，请检查数据库连接")

 
 #   gbL��[7bm�[�Qpe 
 s h o w _ c u s t o m e r _ i n s i g h t ( )  
 