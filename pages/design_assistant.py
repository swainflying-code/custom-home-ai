"""
设计辅助页面 V2.0
功能：
  1. 接收客户洞察系统传导的设计信息
  2. 设计修正栏（设计师自主调整）
  3. 参考著名设计师多选
  4. 参考著名品牌多选
  5. 参考图上传（≤2张，≤1680×1680 或 ≤2MB）
  6. AI设计建议分析（消耗10积分）
  7. 文生图提示词展示（一键复制）
  8. AI生图（Nano Banana API）
"""

import io
import json
import base64
import logging
import requests
import streamlit as st
from datetime import datetime
from typing import Any, Dict, List, Optional

# ── logger ──────────────────────────────────────────────────────
try:
    from utils.logger import setup_logger
    logger = setup_logger(__name__)
except Exception:
    logger = logging.getLogger(__name__)

# ── 可选依赖 ────────────────────────────────────────────────────
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

try:
    from core.config import config
except Exception as _e:
    logger.warning(f"config 模块加载失败: {_e}")
    config = None

# PIL 用于图片尺寸校验（可选）
try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

# ── 常量 ────────────────────────────────────────────────────────
DESIGNERS = [
    "梁志天", "傅厚民", "吴滨", "唐忠汉", "邱德光",
    "Kelly Hoppen", "Kelly Wearstler", "Axel Vervoordt",
    "Peter Marino",
]

BRANDS = [
    "M77", "威法", "木里木外", "Poliform", "Rimadesio",
    "Molteni&C", "Bulthaup", "Liaigre",
]

MAX_IMAGE_SIDE = 1680          # 单边最大像素
MAX_IMAGE_SIZE_MB = 2          # 文件大小上限
DESIGN_ANALYSIS_COST = 10      # 消耗积分

# ── 积分简单管理（session级，生产可持久化）──────────────────────
def _get_credits() -> int:
    if "design_credits" not in st.session_state:
        st.session_state.design_credits = 100   # 默认给100积分
    return st.session_state.design_credits


def _deduct_credits(amount: int) -> bool:
    credits = _get_credits()
    if credits < amount:
        return False
    st.session_state.design_credits -= amount
    return True


# ── 图片校验 ────────────────────────────────────────────────────
def _validate_image(uploaded_file) -> tuple[bool, str]:
    """返回 (ok, error_msg)"""
    size_bytes = uploaded_file.size
    if size_bytes > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        return False, f"文件大小 {size_bytes/1024/1024:.1f}MB 超过 {MAX_IMAGE_SIZE_MB}MB 限制"

    if _PIL_AVAILABLE:
        try:
            img = Image.open(uploaded_file)
            w, h = img.size
            if w > MAX_IMAGE_SIDE or h > MAX_IMAGE_SIDE:
                return False, f"图片尺寸 {w}×{h} 超过 {MAX_IMAGE_SIDE}×{MAX_IMAGE_SIDE} 限制，请压缩后重新上传"
            uploaded_file.seek(0)
        except Exception as e:
            return False, f"图片读取失败: {e}"
    else:
        uploaded_file.seek(0)

    return True, ""


def _image_to_base64(uploaded_file) -> str:
    uploaded_file.seek(0)
    return base64.b64encode(uploaded_file.read()).decode("utf-8")


# ── 从客户洞察传导信息 ──────────────────────────────────────────
def _get_customer_context() -> Optional[Dict[str, Any]]:
    """
    优先从 session_state 读取刚保存的客户；
    否则从数据库读取最近一条高意向客户。
    """
    # 1. session 中有刚选定的客户ID
    cid = st.session_state.get("selected_customer_id")
    if cid and db:
        try:
            res = db.client.table("customers").select("*").eq("id", cid).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.warning(f"按ID查客户失败: {e}")

    # 2. 从数据库拉最近一条
    if db:
        try:
            res = db.client.table("customers").select("*")\
                .order("created_at", desc=True).limit(1).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.warning(f"拉取最近客户失败: {e}")

    return None


def _render_customer_info_card(c: Dict[str, Any]):
    """渲染客户洞察传导信息卡片"""
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);
                border:1px solid #d4af37;border-radius:12px;padding:16px 20px;margin-bottom:8px;">
        <p style="color:#d4af37;font-size:13px;margin:0 0 4px 0;font-weight:600;
                   letter-spacing:2px;">📡 客户洞察传导</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("客户", c.get("name") or "—")
    col2.metric("意向", c.get("intent_level") or "—")
    col3.metric("预算", c.get("custom_budget") or "—")
    col4.metric("装修进度", c.get("renovation_progress") or "—")

    with st.expander("📋 展开查看完整客户信息", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**房型**：{c.get('house_type','—')}")
            st.write(f"**装修类型**：{c.get('renovation_type','—')}")
            st.write(f"**定制空间**：{', '.join(c.get('custom_spaces') or []) or '—'}")
            st.write(f"**材质偏好**：{c.get('material_preference','—')}")
            st.write(f"**色彩偏好**：{c.get('color_preference','—')}")
        with c2:
            st.write(f"**风格偏好**：{c.get('style_preference','—')}")
            st.write(f"**材质组合**：{(c.get('material_combination') or '—')[:40]}")
            st.write(f"**生活方式**：{(c.get('life_style') or '—')[:40]}")
            st.write(f"**理想家居**：{(c.get('ideal_home') or '—')[:40]}")
            st.write(f"**特殊需求**：{c.get('special_needs','—') or '—'}")

    # 返回核心设计摘要文本（供AI分析用）
    spaces_str = ", ".join(c.get("custom_spaces") or [])
    summary = (
        f"客户：{c.get('name','匿名')}，{c.get('gender','')}{c.get('age_group','')}，"
        f"房型：{c.get('house_type','未知')}，"
        f"装修类型：{c.get('renovation_type','未知')}，进度：{c.get('renovation_progress','未知')}，"
        f"预算：{c.get('custom_budget','未知')}，"
        f"定制空间：{spaces_str or '未知'}，"
        f"材质偏好：{c.get('material_preference','未知')}，"
        f"色彩偏好：{c.get('color_preference','未知')}，"
        f"风格偏好：{c.get('style_preference','未知')}，"
        f"材质组合：{c.get('material_combination','未知')}，"
        f"生活方式：{(c.get('life_style') or '未知')[:60]}，"
        f"特殊需求：{c.get('special_needs','无') or '无'}"
    )
    return summary


# ── AI设计分析 ──────────────────────────────────────────────────
def _call_design_analysis(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """调用大模型生成设计建议"""
    if ai_service is None:
        return {"error": "AI服务未初始化，请检查API Key配置"}

    system_prompt = """你是一位顶级全屋定制设计顾问，专注于高端不锈钢定制家居领域。
请根据用户提供的客户信息、设计师风格参考、品牌参考，给出专业的设计建议。

输出格式（严格JSON）：
{
  "设计主题": "...",
  "核心风格定义": "...",
  "空间设计建议": {
    "色彩方案": "...",
    "材质搭配": "...",
    "空间布局重点": "...",
    "灯光氛围": "..."
  },
  "设计亮点": ["...", "...", "..."],
  "注意事项": ["...", "..."],
  "文生图提示词": {
    "中文版": "...",
    "英文版": "..."
  }
}"""

    user_msg = f"""客户信息摘要：{prompt_data.get('customer_summary', '未提供')}

设计师修正备注：{prompt_data.get('designer_notes', '无')}

参考设计大师：{', '.join(prompt_data.get('ref_designers', [])) or '未指定'}

参考品牌：{', '.join(prompt_data.get('ref_brands', [])) or '未指定'}

请综合上述信息，给出完整的设计建议，并生成高质量的文生图提示词。"""

    try:
        response = ai_service.client.chat.completions.create(
            model=ai_service.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=2048,
            temperature=0.7,
        )
        raw = response.choices[0].message.content
        # 尝试解析JSON
        cleaned = raw.strip()
        for prefix in ["```json", "```"]:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        # 返回原文
        return {"设计主题": "AI建议（原文）", "raw": raw}
    except Exception as e:
        logger.error(f"AI设计分析失败: {e}")
        return {"error": str(e)}


# ── Nano Banana 生图 ────────────────────────────────────────────
def _call_nano_banana(prompt_en: str) -> Optional[str]:
    """
    调用 Nano Banana API 生图，返回图片URL或base64。
    如未配置 API key，返回 None。
    """
    api_key = None
    if config:
        try:
            from core.config import _get_config_value
            api_key = _get_config_value("NANO_BANANA_API_KEY")
        except Exception:
            pass

    if not api_key:
        return None

    try:
        resp = requests.post(
            "https://api.nanobanna.com/v1/text2image",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"prompt": prompt_en, "width": 1024, "height": 1024, "steps": 30},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        # 兼容多种返回格式
        return data.get("image_url") or data.get("url") or data.get("data", [{}])[0].get("url")
    except Exception as e:
        logger.error(f"Nano Banana 生图失败: {e}")
        return None


# ── 主页面入口 ──────────────────────────────────────────────────
def show_design_assistant_page():
    st.title("🎨 设计辅助")
    st.caption("综合客户洞察信息 · AI驱动设计建议 · 一键生成提示词与效果图")
    st.markdown("---")

    # ── session 初始化 ───────────────────────────────────────────
    for key, default in [
        ("da_designer_notes", ""),
        ("da_ref_designers", []),
        ("da_ref_brands", []),
        ("da_designer_other", ""),
        ("da_brand_other", ""),
        ("da_images", []),
        ("da_analysis_result", None),
        ("da_image_url", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    credits = _get_credits()
    st.sidebar.metric("💎 剩余积分", credits)

    # ════════════════════════════════════════════════════════════
    # 区块 1：客户洞察传导信息
    # ════════════════════════════════════════════════════════════
    st.subheader("① 客户洞察传导信息")
    customer = _get_customer_context()
    customer_summary = ""

    if customer:
        customer_summary = _render_customer_info_card(customer)
    else:
        st.info("📭 暂无客户信息传导。请先在【客户洞察】中完成并提交客户调研，或系统会自动读取最近一条客户记录。")
        customer_summary = "无客户信息，请设计师根据当前情况自行填写设计要求。"

    # ════════════════════════════════════════════════════════════
    # 区块 2：设计修正栏
    # ════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("② 设计修正栏")
    st.caption("设计师可在此补充或调整设计要求，优先级高于客户洞察自动传导内容")
    designer_notes = st.text_area(
        "设计师备注 / 调整要求",
        value=st.session_state.da_designer_notes,
        height=120,
        placeholder="例如：客户现场补充了对厨房的特别要求；希望整体偏冷调；取消阳台柜改为榻榻米...",
        key="da_notes_input",
    )
    st.session_state.da_designer_notes = designer_notes

    # ════════════════════════════════════════════════════════════
    # 区块 3：参考设计师
    # ════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("③ 参考设计师风格（可多选）")
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        ref_designers = st.multiselect(
            "",
            options=DESIGNERS,
            default=[d for d in st.session_state.da_ref_designers if d in DESIGNERS],
            label_visibility="collapsed",
            key="da_designers_select",
        )
    with col_d2:
        designer_other = st.text_input(
            "其他（自填）",
            value=st.session_state.da_designer_other,
            placeholder="如：贝聿铭",
            key="da_designer_other_input",
        )
    st.session_state.da_ref_designers = ref_designers
    st.session_state.da_designer_other = designer_other
    all_designers = ref_designers + ([designer_other.strip()] if designer_other.strip() else [])

    # ════════════════════════════════════════════════════════════
    # 区块 4：参考品牌
    # ════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("④ 参考品牌（可多选）")
    col_b1, col_b2 = st.columns([3, 1])
    with col_b1:
        ref_brands = st.multiselect(
            "",
            options=BRANDS,
            default=[b for b in st.session_state.da_ref_brands if b in BRANDS],
            label_visibility="collapsed",
            key="da_brands_select",
        )
    with col_b2:
        brand_other = st.text_input(
            "其他（自填）",
            value=st.session_state.da_brand_other,
            placeholder="如：De Padova",
            key="da_brand_other_input",
        )
    st.session_state.da_ref_brands = ref_brands
    st.session_state.da_brand_other = brand_other
    all_brands = ref_brands + ([brand_other.strip()] if brand_other.strip() else [])

    # ════════════════════════════════════════════════════════════
    # 区块 5：参考图上传
    # ════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("⑤ 参考图上传（最多2张）")
    st.caption(f"支持 JPG / PNG / WEBP · 单边 ≤ {MAX_IMAGE_SIDE}px · 大小 ≤ {MAX_IMAGE_SIZE_MB}MB")

    uploaded_files = st.file_uploader(
        "",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="da_uploader",
    )

    valid_images = []
    if uploaded_files:
        if len(uploaded_files) > 2:
            st.warning("⚠️ 最多上传2张，已自动截取前2张")
            uploaded_files = list(uploaded_files)[:2]
        for uf in uploaded_files:
            ok, err = _validate_image(uf)
            if ok:
                valid_images.append(uf)
                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(uf, use_container_width=True)
                with cols[1]:
                    st.success(f"✅ {uf.name}  ({uf.size/1024:.0f} KB)")
            else:
                st.error(f"❌ {uf.name}：{err}")

    # ════════════════════════════════════════════════════════════
    # 区块 6：AI设计分析
    # ════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("⑥ AI设计分析")

    col_btn, col_credits = st.columns([2, 1])
    with col_credits:
        st.info(f"本次分析消耗 **{DESIGN_ANALYSIS_COST} 积分**，当前剩余 **{credits} 积分**")
    with col_btn:
        run_analysis = st.button(
            "🤖 开始AI设计分析",
            type="primary",
            use_container_width=True,
            disabled=(credits < DESIGN_ANALYSIS_COST),
        )

    if run_analysis:
        if not _deduct_credits(DESIGN_ANALYSIS_COST):
            st.error("❌ 积分不足，无法分析")
        else:
            with st.spinner("正在融合设计大师风格，生成专业设计建议..."):
                prompt_data = {
                    "customer_summary": customer_summary,
                    "designer_notes": designer_notes or "无",
                    "ref_designers": all_designers,
                    "ref_brands": all_brands,
                }
                result = _call_design_analysis(prompt_data)
                st.session_state.da_analysis_result = result
                st.session_state.da_image_url = None  # 重置生图结果
                st.rerun()

    # 展示分析结果
    result = st.session_state.da_analysis_result
    if result:
        if "error" in result:
            st.error(f"❌ 分析失败：{result['error']}")
        else:
            st.success("✅ AI设计建议生成完毕！")

            theme = result.get("设计主题", "")
            core_style = result.get("核心风格定义", "")
            if theme:
                st.markdown(f"### 🎯 {theme}")
            if core_style:
                st.info(f"**核心风格**：{core_style}")

            space_advice = result.get("空间设计建议", {})
            if space_advice:
                st.markdown("#### 🏠 空间设计建议")
                sa_cols = st.columns(2)
                items = list(space_advice.items())
                for i, (k, v) in enumerate(items):
                    sa_cols[i % 2].markdown(f"**{k}**：{v}")

            highlights = result.get("设计亮点", [])
            if highlights:
                st.markdown("#### ✨ 设计亮点")
                for h in highlights:
                    st.markdown(f"- {h}")

            cautions = result.get("注意事项", [])
            if cautions:
                with st.expander("⚠️ 注意事项"):
                    for c_item in cautions:
                        st.markdown(f"- {c_item}")

            # ── 区块 7：文生图提示词 ─────────────────────────────
            st.markdown("---")
            st.subheader("⑦ 文生图提示词")
            prompts = result.get("文生图提示词", {})
            prompt_cn = prompts.get("中文版", "") if isinstance(prompts, dict) else ""
            prompt_en = prompts.get("英文版", "") if isinstance(prompts, dict) else str(prompts)

            if prompt_cn:
                st.markdown("**中文版**")
                st.code(prompt_cn, language=None)
                st.button(
                    "📋 复制中文提示词",
                    key="copy_cn",
                    on_click=lambda: st.write(""),
                    help="点击后手动 Ctrl+A 全选复制",
                )
                st.caption("💡 点击上方代码框右上角复制按钮，或手动选择复制")

            if prompt_en:
                st.markdown("**英文版**（推荐用于AI生图）")
                st.code(prompt_en, language=None)

            # ════════════════════════════════════════════════════
            # 区块 8：AI生图
            # ════════════════════════════════════════════════════
            st.markdown("---")
            st.subheader("⑧ AI生图")

            api_key_set = False
            if config:
                try:
                    from core.config import _get_config_value
                    api_key_set = bool(_get_config_value("NANO_BANANA_API_KEY"))
                except Exception:
                    pass

            if not api_key_set:
                st.warning(
                    "⚙️ 未配置 Nano Banana API Key，AI生图功能暂不可用。\n\n"
                    "请在 Streamlit Secrets 中添加：`NANO_BANANA_API_KEY = \"your_key\"`"
                )
            else:
                if prompt_en:
                    gen_img_btn = st.button(
                        "🖼️ 快速AI生图",
                        type="primary",
                        key="gen_img_btn",
                        use_container_width=False,
                    )
                    if gen_img_btn:
                        with st.spinner("正在调用 Nano Banana 生图，请稍候（约30-60秒）..."):
                            img_url = _call_nano_banana(prompt_en)
                            if img_url:
                                st.session_state.da_image_url = img_url
                                st.rerun()
                            else:
                                st.error("❌ 生图失败，请检查 API Key 或稍后重试")
                else:
                    st.info("请先完成AI设计分析以获取英文提示词")

            img_url = st.session_state.get("da_image_url")
            if img_url:
                st.success("✅ 生图完成！")
                st.image(img_url, caption="AI生成效果图", use_container_width=True)
                st.markdown(f"[🔗 查看原图]({img_url})", unsafe_allow_html=False)

    # ── 底部：选择其他客户 ───────────────────────────────────────
    st.markdown("---")
    with st.expander("🔄 切换参考客户"):
        if db:
            try:
                all_customers = db.client.table("customers")\
                    .select("id,name,customer_code,intent_level,created_at")\
                    .order("created_at", desc=True).limit(20).execute()
                if all_customers.data:
                    options = {
                        f"{c.get('name','匿名')} ({c.get('customer_code','')}) - {c.get('intent_level','')}": c["id"]
                        for c in all_customers.data
                    }
                    selected = st.selectbox("选择客户", list(options.keys()), key="da_cust_select")
                    if st.button("切换到此客户", key="da_switch_cust"):
                        st.session_state.selected_customer_id = options[selected]
                        st.session_state.da_analysis_result = None
                        st.session_state.da_image_url = None
                        st.rerun()
                else:
                    st.info("暂无客户记录")
            except Exception as e:
                st.error(f"读取客户列表失败: {e}")
        else:
            st.warning("数据库未连接")
