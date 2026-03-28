"""
智能报价页面 v3
逻辑：选客户 → 按空间添加项目 → 每项选产品类型+材质+尺寸 → 自动计算 → 汇总导出
"""
import streamlit as st
import uuid
import json
from datetime import datetime, date
from core.database import db


# ──────────────────────────────────────────────────────────────
# 数据加载（带缓存）
# ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def _load_product_types():
    try:
        return db.select("product_types", filters={"is_active": True}, order_by="sort_order")
    except Exception:
        return []

@st.cache_data(ttl=60)
def _load_surface_materials(category: str):
    try:
        return db.select("surface_materials",
                         filters={"category": category, "is_active": True},
                         order_by="sort_order")
    except Exception:
        return []

@st.cache_data(ttl=60)
def _load_countertop_extras():
    try:
        return db.select("countertop_extras", filters={"is_active": True}, order_by="sort_order")
    except Exception:
        return []

@st.cache_data(ttl=60)
def _load_hardware_options():
    try:
        return db.select("hardware_options", filters={"is_active": True}, order_by="sort_order")
    except Exception:
        return []

@st.cache_data(ttl=60)
def _load_cabinet_body_prices(product_type_id: str):
    try:
        return db.select("cabinet_body_prices",
                         filters={"product_type_id": product_type_id, "is_active": True},
                         order_by="sort_order")
    except Exception:
        return []

def _load_stores():
    try:
        return db.select("stores", filters={"is_active": True}, order_by="store_code")
    except Exception:
        return []

def _load_customers():
    try:
        return db.select("customers", order_by="created_at.desc", limit=200)
    except Exception:
        return []


# ──────────────────────────────────────────────────────────────
# Session state 初始化
# ──────────────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "qv3_store_id": None,
        "qv3_customer_id": None,
        "qv3_customer_name": "",
        "qv3_customer_phone": "",
        "qv3_designer": "",
        "qv3_house_area": "",
        "qv3_house_type": "",
        "qv3_remark": "",
        "qv3_discount": 100,   # 整数百分比，如 85 = 八五折
        "qv3_items": [],       # 已加入的报价项列表
        "qv3_saved_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _reset_quote():
    keys = [k for k in st.session_state if k.startswith("qv3_")]
    for k in keys:
        del st.session_state[k]
    # 清缓存让材质价格也刷新
    _load_product_types.clear()
    _load_surface_materials.clear()
    _load_countertop_extras.clear()
    _load_hardware_options.clear()
    _load_cabinet_body_prices.clear()
    _init_state()

def _gen_quote_no():
    today = datetime.now().strftime("%Y%m%d")
    rand = str(uuid.uuid4().int)[:5]
    return f"Q{today}{rand}"


# ──────────────────────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────────────────────

def show_smart_quoting_page():
    _init_state()
    st.title("💰 智能报价")

    col_title, col_new = st.columns([4, 1])
    with col_new:
        if st.button("🗑️ 清空重填", use_container_width=True):
            _reset_quote()
            st.rerun()

    tab_build, tab_list = st.tabs(["📝 新建报价单", "📋 历史记录"])

    with tab_build:
        _section_header()
        st.markdown("---")
        _section_add_item()
        st.markdown("---")
        _section_summary()

    with tab_list:
        _section_quote_list()


# ──────────────────────────────────────────────────────────────
# Section 1：基本信息
# ──────────────────────────────────────────────────────────────

def _section_header():
    st.subheader("① 基本信息")

    stores = _load_stores()
    if not stores:
        st.error("⚠️ 尚未配置门店，请前往「后台管理 → 门店管理」创建门店")
        return

    store_opts = {f"{s['store_name']} ({s['store_code']})": s["id"] for s in stores}

    c1, c2, c3 = st.columns(3)
    with c1:
        sel_store = st.selectbox("门店 *", list(store_opts.keys()), key="hdr_store")
        st.session_state.qv3_store_id = store_opts[sel_store]
        designer = st.text_input("设计师姓名", value=st.session_state.qv3_designer, key="hdr_designer")
        st.session_state.qv3_designer = designer

    with c2:
        customers = _load_customers()
        cust_opts = {"── 不绑定客户 ──": None}
        for c in customers:
            label = f"{c.get('name','未知')} {c.get('contact_info','')}"
            cust_opts[label] = c["id"]

        sel_cust_label = st.selectbox("关联客户（可选）", list(cust_opts.keys()), key="hdr_cust")
        sel_cust_id = cust_opts[sel_cust_label]
        st.session_state.qv3_customer_id = sel_cust_id

        if sel_cust_id:
            cust_data = next((c for c in customers if c["id"] == sel_cust_id), None)
            if cust_data:
                st.session_state.qv3_customer_name = cust_data.get("name", "")
                st.session_state.qv3_customer_phone = cust_data.get("contact_info", "")
        else:
            name = st.text_input("客户姓名", value=st.session_state.qv3_customer_name, key="hdr_cname")
            st.session_state.qv3_customer_name = name

    with c3:
        phone = st.text_input("客户电话", value=st.session_state.qv3_customer_phone, key="hdr_phone")
        st.session_state.qv3_customer_phone = phone
        area = st.text_input("房屋面积（㎡）", value=st.session_state.qv3_house_area, key="hdr_area")
        st.session_state.qv3_house_area = area
        htype = st.text_input("户型", value=st.session_state.qv3_house_type,
                               placeholder="如 三室两厅", key="hdr_htype")
        st.session_state.qv3_house_type = htype


# ──────────────────────────────────────────────────────────────
# Section 2：添加空间项目（核心报价逻辑）
# ──────────────────────────────────────────────────────────────

DOOR_TYPES = ["平开门", "推拉门", "无门（开放）"]

def _section_add_item():
    st.subheader("② 添加空间项目")

    product_types = _load_product_types()
    if not product_types:
        st.warning("⚠️ 尚未配置产品大类，请前往「后台管理 → 报价配置」添加")
        return

    pt_opts = {pt["name"]: pt for pt in product_types}

    # ── 选产品类型 + 空间备注 ──
    c1, c2 = st.columns(2)
    with c1:
        sel_pt_name = st.selectbox("选择产品类型", list(pt_opts.keys()), key="item_pt")
    with c2:
        space_label = st.text_input("空间/位置备注", placeholder="如 厨房、主卧、入户", key="item_space")

    sel_pt = pt_opts[sel_pt_name]
    is_A = sel_pt["category"] == "A"
    has_countertop = sel_pt.get("has_countertop", False)
    has_upper = sel_pt.get("has_upper_cabinet", False)

    st.markdown("---")

    # ── 加载数据 ──
    body_prices = _load_cabinet_body_prices(sel_pt["id"])
    door_materials = _load_surface_materials("门板")
    countertop_materials = _load_surface_materials("台面")
    ct_extras = _load_countertop_extras()
    hw_options = _load_hardware_options()

    # 柜体材质选项
    body_mat_opts = {bp["material"]: bp for bp in body_prices} if body_prices else {}
    door_mat_opts = {dm["name"]: dm for dm in door_materials} if door_materials else {}
    ct_mat_opts   = {cm["name"]: cm for cm in countertop_materials} if countertop_materials else {}

    # ── A类橱柜 ──
    if is_A:
        _render_kitchen_form(sel_pt, space_label, body_mat_opts, has_upper,
                             door_mat_opts, ct_mat_opts, ct_extras, hw_options)
    else:
        _render_cabinet_form(sel_pt, space_label, body_mat_opts,
                             door_mat_opts, has_countertop, ct_mat_opts, ct_extras, hw_options)


def _render_kitchen_form(pt, space_label, body_mat_opts, has_upper,
                         door_mat_opts, ct_mat_opts, ct_extras, hw_options):
    """A类橱柜报价表单"""
    st.markdown("#### 🍳 橱柜配置")

    # 延米
    length = st.number_input("操作台长度（米）", min_value=0.5, max_value=20.0,
                              value=3.0, step=0.1, key="kt_length",
                              help="沿墙操作台的总延米数")

    col1, col2 = st.columns(2)

    # ── 下柜 ──
    with col1:
        st.markdown("**下柜**")
        if body_mat_opts:
            # 分离出下柜选项
            lower_opts = {m: bp for m, bp in body_mat_opts.items()
                          if "上柜" not in bp.get("position", "")}
            if lower_opts:
                lower_mat = st.selectbox("下柜材质", list(lower_opts.keys()), key="kt_lower_mat")
                lower_price = float(lower_opts[lower_mat]["price"])
                lower_unit = lower_opts[lower_mat].get("unit", "元/m")
                lower_sub = round(length * lower_price, 2)
                st.caption(f"{length}m × ¥{lower_price:,.0f}/{lower_unit[2:]} = **¥{lower_sub:,.0f}**")
            else:
                lower_mat = st.selectbox("下柜材质", list(body_mat_opts.keys()), key="kt_lower_mat2")
                lower_price = float(body_mat_opts[lower_mat]["price"])
                lower_sub = round(length * lower_price, 2)
                lower_unit = "元/m"
                st.caption(f"¥{lower_sub:,.0f}")
        else:
            lower_mat = st.text_input("下柜材质", key="kt_lower_mat_txt")
            lower_price = st.number_input("下柜单价(元/m)", min_value=0.0, value=1500.0, key="kt_lower_p")
            lower_sub = round(length * lower_price, 2)
            lower_unit = "元/m"

    # ── 上柜 ──
    with col2:
        st.markdown("**上柜**")
        has_upper_sel = st.checkbox("含上柜", value=True, key="kt_has_upper")
        upper_mat = ""
        upper_price = 0.0
        upper_sub = 0.0
        if has_upper_sel:
            if body_mat_opts:
                upper_opts = {m: bp for m, bp in body_mat_opts.items()
                              if "上柜" in bp.get("position", "") or "上" in bp.get("position", "")}
                if not upper_opts:
                    upper_opts = body_mat_opts  # 没有单独配置上柜就复用下柜选项
                upper_mat = st.selectbox("上柜材质", list(upper_opts.keys()), key="kt_upper_mat")
                upper_price = float(upper_opts[upper_mat]["price"])
                upper_unit = upper_opts[upper_mat].get("unit", "元/m")
                upper_sub = round(length * upper_price, 2)
                st.caption(f"{length}m × ¥{upper_price:,.0f}/{upper_unit[2:]} = **¥{upper_sub:,.0f}**")
            else:
                upper_mat = st.text_input("上柜材质", key="kt_upper_mat_txt")
                upper_price = st.number_input("上柜单价(元/m)", min_value=0.0, value=1000.0, key="kt_upper_p")
                upper_sub = round(length * upper_price, 2)

    st.markdown("---")

    # ── 门板 ──
    st.markdown("**门板**")
    c1, c2, c3 = st.columns(3)
    with c1:
        door_type = st.selectbox("开门方式", DOOR_TYPES, key="kt_door_type")
    with c2:
        if door_mat_opts:
            door_mat = st.selectbox("门板材质", list(door_mat_opts.keys()), key="kt_door_mat")
            door_unit_price = float(door_mat_opts[door_mat]["price"])
        else:
            door_mat = st.text_input("门板材质", key="kt_door_mat_txt")
            door_unit_price = st.number_input("门板单价(元/m²)", min_value=0.0, value=580.0, key="kt_door_p")
    with c3:
        # 橱柜默认门高参数
        door_height = st.number_input("门板高度（m）", min_value=0.1, max_value=3.0,
                                       value=0.72, step=0.01, key="kt_door_h",
                                       help="下柜门高约0.72m，上柜门高约0.35m，此处填合计估算高度")

    if door_type == "无门（开放）":
        door_area = 0.0
        door_sub = 0.0
        st.caption("开放柜，无门板费用")
    else:
        door_area = round(length * door_height, 3)
        door_sub = round(door_area * door_unit_price, 2)
        st.caption(f"{length}m × {door_height}m = {door_area}m²  × ¥{door_unit_price:,.0f}/m² = **¥{door_sub:,.0f}**")

    st.markdown("---")

    # ── 台面 ──
    st.markdown("**台面**")
    c1, c2 = st.columns(2)
    with c1:
        if ct_mat_opts:
            ct_mat = st.selectbox("台面材质", list(ct_mat_opts.keys()), key="kt_ct_mat")
            ct_unit_price = float(ct_mat_opts[ct_mat]["price"])
        else:
            ct_mat = st.text_input("台面材质", key="kt_ct_mat_txt")
            ct_unit_price = st.number_input("台面单价(元/m)", min_value=0.0, value=480.0, key="kt_ct_p")
        ct_base = round(length * ct_unit_price, 2)
        st.caption(f"{length}m × ¥{ct_unit_price:,.0f}/m = ¥{ct_base:,.0f}")
    with c2:
        st.markdown("工艺加项")
        ct_extra_total = 0.0
        ct_extras_selected = []
        for ex in ct_extras:
            default_val = ex.get("is_default", False)
            label = f"{'[默认含]' if default_val else ''} {ex['name']}  ¥{float(ex['price']):,.0f}/{ex['unit'][2:]}"
            checked = st.checkbox(label, value=default_val, key=f"kt_ex_{ex['id']}")
            if checked and float(ex["price"]) > 0:
                sub = round(length * float(ex["price"]), 2)
                ct_extra_total += sub
                ct_extras_selected.append({"name": ex["name"], "price": float(ex["price"]),
                                            "unit": ex["unit"], "subtotal": sub})
            elif checked:
                ct_extras_selected.append({"name": ex["name"], "price": 0, "unit": ex["unit"], "subtotal": 0})

    ct_sub = round(ct_base + ct_extra_total, 2)
    st.caption(f"台面合计：¥{ct_base:,.0f} + 加项¥{ct_extra_total:,.0f} = **¥{ct_sub:,.0f}**")

    st.markdown("---")

    # ── 五金 ──
    hw_total, hw_items = _render_hardware(hw_options, "kt", applicable=["通用", "橱柜"])

    # ── 预览小计 ──
    body_total = lower_sub + upper_sub
    line_sub = round(body_total + door_sub + ct_sub + hw_total, 2)
    _show_preview(body_total, door_sub, ct_sub, hw_total, line_sub)

    # ── 加入报价单 ──
    if st.button("➕ 加入报价单", type="primary", key="kt_add", use_container_width=True):
        space = space_label.strip() or pt["name"]
        item = {
            "_id": str(uuid.uuid4())[:8],
            "space_name": space,
            "product_type_name": pt["name"],
            "product_type_id": pt["id"],
            "category": "A",
            # 尺寸
            "length_m": length,
            "width_m": None,
            "height_m": None,
            # 柜体
            "body_material": lower_mat,
            "body_unit_price": lower_price,
            "body_subtotal": lower_sub,
            # 上柜
            "has_upper_cabinet": has_upper_sel,
            "upper_material": upper_mat if has_upper_sel else "",
            "upper_unit_price": upper_price,
            "upper_subtotal": upper_sub,
            # 门板
            "door_type": door_type,
            "door_material": door_mat,
            "door_area_m2": door_area,
            "door_unit_price": door_unit_price,
            "door_subtotal": door_sub,
            # 台面
            "countertop_material": ct_mat,
            "countertop_length_m": length,
            "countertop_unit_price": ct_unit_price,
            "countertop_extras_json": ct_extras_selected,
            "countertop_subtotal": ct_sub,
            # 五金
            "hardware_items_json": hw_items,
            "hardware_subtotal": hw_total,
            # 合计
            "line_subtotal": line_sub,
        }
        _add_item(item)


def _render_cabinet_form(pt, space_label, body_mat_opts,
                         door_mat_opts, has_countertop, ct_mat_opts, ct_extras, hw_options):
    """B类通用柜报价表单"""
    st.markdown(f"#### 🗄️ {pt['name']} 配置")

    # 投影面积
    c1, c2, c3 = st.columns(3)
    with c1:
        width = st.number_input("宽度（米）", min_value=0.1, max_value=20.0,
                                 value=2.4, step=0.1, key="cab_w")
    with c2:
        height = st.number_input("高度（米）", min_value=0.1, max_value=5.0,
                                  value=2.4, step=0.1, key="cab_h")
    with c3:
        proj_area = round(width * height, 3)
        st.metric("投影面积", f"{proj_area} m²")

    st.markdown("---")

    # ── 柜体 ──
    st.markdown("**柜体**")
    if body_mat_opts:
        body_mat = st.selectbox("柜体材质", list(body_mat_opts.keys()), key="cab_body_mat")
        body_price = float(body_mat_opts[body_mat]["price"])
        body_unit = body_mat_opts[body_mat].get("unit", "元/m²")
        body_sub = round(proj_area * body_price, 2)
        st.caption(f"{proj_area}m² × ¥{body_price:,.0f}/{body_unit[2:]} = **¥{body_sub:,.0f}**")
    else:
        body_mat = st.text_input("柜体材质", key="cab_body_mat_txt")
        body_price = st.number_input("柜体单价(元/m²)", min_value=0.0, value=320.0, key="cab_body_p")
        body_sub = round(proj_area * body_price, 2)

    st.markdown("---")

    # ── 门板 ──
    st.markdown("**门板**")
    c1, c2, c3 = st.columns(3)
    with c1:
        door_type = st.selectbox("开门方式", DOOR_TYPES, key="cab_door_type")
    with c2:
        if door_mat_opts:
            door_mat = st.selectbox("门板材质", list(door_mat_opts.keys()), key="cab_door_mat")
            door_unit_price = float(door_mat_opts[door_mat]["price"])
        else:
            door_mat = st.text_input("门板材质", key="cab_door_mat_txt")
            door_unit_price = st.number_input("门板单价(元/m²)", min_value=0.0, value=580.0, key="cab_door_p")

    if door_type == "无门（开放）":
        door_area = 0.0
        door_sub = 0.0
        with c3:
            st.caption("开放柜，无门板")
    elif door_type == "推拉门":
        # 推拉门：宽×高（整面）
        door_area = round(width * height, 3)
        door_sub = round(door_area * door_unit_price, 2)
        with c3:
            st.caption(f"推拉门 {width}m×{height}m = {door_area}m²  **¥{door_sub:,.0f}**")
    else:
        # 平开门：输入实际门面积
        with c3:
            door_area = st.number_input("实际门板面积(m²)", min_value=0.0,
                                         value=round(proj_area * 0.85, 2),
                                         step=0.1, key="cab_door_area",
                                         help="默认按投影面积×0.85估算，可手动调整")
        door_sub = round(door_area * door_unit_price, 2)
        st.caption(f"{door_area}m² × ¥{door_unit_price:,.0f}/m² = **¥{door_sub:,.0f}**")

    st.markdown("---")

    # ── 台面（有台面的产品） ──
    ct_mat = ""
    ct_unit_price = 0.0
    ct_sub = 0.0
    ct_extras_selected = []

    if has_countertop:
        st.markdown("**台面**")
        c1, c2 = st.columns(2)
        with c1:
            ct_length = st.number_input("台面长度（米）", min_value=0.0, value=width,
                                         step=0.1, key="cab_ct_len")
            if ct_mat_opts:
                ct_mat = st.selectbox("台面材质", list(ct_mat_opts.keys()), key="cab_ct_mat")
                ct_unit_price = float(ct_mat_opts[ct_mat]["price"])
            else:
                ct_mat = st.text_input("台面材质", key="cab_ct_mat_txt")
                ct_unit_price = st.number_input("台面单价(元/m)", min_value=0.0, value=480.0, key="cab_ct_p")
            ct_base = round(ct_length * ct_unit_price, 2)
            st.caption(f"¥{ct_base:,.0f}")
        with c2:
            st.markdown("工艺加项")
            ct_extra_total = 0.0
            for ex in ct_extras:
                default_val = ex.get("is_default", False)
                label = f"{'[默认]' if default_val else ''} {ex['name']}  ¥{float(ex['price']):,.0f}/{ex['unit'][2:]}"
                checked = st.checkbox(label, value=default_val, key=f"cab_ex_{ex['id']}")
                if checked and float(ex["price"]) > 0:
                    sub = round(ct_length * float(ex["price"]), 2)
                    ct_extra_total += sub
                    ct_extras_selected.append({"name": ex["name"], "price": float(ex["price"]),
                                                "unit": ex["unit"], "subtotal": sub})
                elif checked:
                    ct_extras_selected.append({"name": ex["name"], "price": 0, "unit": ex["unit"], "subtotal": 0})
        ct_sub = round(ct_base + ct_extra_total, 2)
        st.caption(f"台面合计：**¥{ct_sub:,.0f}**")
        st.markdown("---")
    else:
        ct_length = 0.0
        ct_base = 0.0

    # ── 五金 ──
    hw_total, hw_items = _render_hardware(hw_options, "cab", applicable=["通用", pt["name"]])

    # ── 预览 ──
    line_sub = round(body_sub + door_sub + ct_sub + hw_total, 2)
    _show_preview(body_sub, door_sub, ct_sub, hw_total, line_sub)

    # ── 加入报价单 ──
    if st.button("➕ 加入报价单", type="primary", key="cab_add", use_container_width=True):
        space = space_label.strip() or pt["name"]
        item = {
            "_id": str(uuid.uuid4())[:8],
            "space_name": space,
            "product_type_name": pt["name"],
            "product_type_id": pt["id"],
            "category": "B",
            # 尺寸
            "length_m": None,
            "width_m": width,
            "height_m": height,
            # 柜体
            "body_material": body_mat,
            "body_unit_price": body_price,
            "body_subtotal": body_sub,
            # 上柜
            "has_upper_cabinet": False,
            "upper_material": "",
            "upper_unit_price": 0,
            "upper_subtotal": 0,
            # 门板
            "door_type": door_type,
            "door_material": door_mat if door_type != "无门（开放）" else "无门",
            "door_area_m2": door_area,
            "door_unit_price": door_unit_price,
            "door_subtotal": door_sub,
            # 台面
            "countertop_material": ct_mat,
            "countertop_length_m": ct_length if has_countertop else 0,
            "countertop_unit_price": ct_unit_price,
            "countertop_extras_json": ct_extras_selected,
            "countertop_subtotal": ct_sub,
            # 五金
            "hardware_items_json": hw_items,
            "hardware_subtotal": hw_total,
            # 合计
            "line_subtotal": line_sub,
        }
        _add_item(item)


def _render_hardware(hw_options, prefix, applicable):
    """渲染五金选项，返回 (total, items_list)"""
    st.markdown("**五金配件**")
    total = 0.0
    items = []

    if not hw_options:
        st.caption("暂无五金配置，请在「后台管理 → 报价配置」中添加")
        return 0.0, []

    # 筛选适用的五金
    relevant = [h for h in hw_options
                if h.get("applicable_to", "通用") in applicable
                or h.get("applicable_to", "通用") == "通用"]

    cols_per_row = 2
    rows = [relevant[i:i+cols_per_row] for i in range(0, len(relevant), cols_per_row)]

    for row in rows:
        cols = st.columns(cols_per_row)
        for idx, hw in enumerate(row):
            with cols[idx]:
                default_val = hw.get("is_default", False)
                checked = st.checkbox(
                    f"{'✅' if default_val else '○'} {hw['name']}  ¥{float(hw['price']):,.0f}/{hw['unit'][2:]}",
                    value=default_val,
                    key=f"{prefix}_hw_{hw['id']}"
                )
                if checked:
                    qty = st.number_input(
                        f"数量({hw['unit'][2:]})", min_value=0.0, value=1.0, step=1.0,
                        key=f"{prefix}_hw_qty_{hw['id']}",
                        label_visibility="collapsed"
                    )
                    sub = round(float(hw["price"]) * qty, 2)
                    total += sub
                    items.append({
                        "name": hw["name"],
                        "unit": hw["unit"],
                        "qty": qty,
                        "price": float(hw["price"]),
                        "subtotal": sub
                    })
                    if sub > 0:
                        st.caption(f"¥{sub:,.0f}")

    if total > 0:
        st.caption(f"五金合计：**¥{total:,.0f}**")
    return round(total, 2), items


def _show_preview(body_sub, door_sub, ct_sub, hw_total, line_sub):
    """显示当前项目小计预览"""
    st.markdown("---")
    st.markdown("**💡 当前项目小计预览**")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("柜体", f"¥{body_sub:,.0f}")
    c2.metric("门板", f"¥{door_sub:,.0f}")
    c3.metric("台面", f"¥{ct_sub:,.0f}")
    c4.metric("五金", f"¥{hw_total:,.0f}")
    c5.metric("🏷️ 小计", f"¥{line_sub:,.0f}")


def _add_item(item: dict):
    st.session_state.qv3_items.append(item)
    st.success(f"✅ 已加入：{item['space_name']} · {item['product_type_name']}  ¥{item['line_subtotal']:,.0f}")
    st.rerun()


# ──────────────────────────────────────────────────────────────
# Section 3：报价汇总
# ──────────────────────────────────────────────────────────────

def _section_summary():
    st.subheader("③ 报价汇总")

    items = st.session_state.qv3_items
    if not items:
        st.info("尚未添加任何项目，请在上方配置后点击「加入报价单」")
        return

    # ── 明细表 ──
    st.markdown("**已选明细：**")
    to_delete = []

    for item in items:
        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.5, 1, 1, 1.2, 0.5])
            c1.markdown(f"**{item['space_name']}**")
            c2.markdown(f"{item['product_type_name']}")

            # 尺寸说明
            if item["category"] == "A":
                c3.markdown(f"延米 {item['length_m']}m")
            else:
                c3.markdown(f"{item['width_m']}m × {item['height_m']}m")

            # 材质组合
            mats = []
            if item.get("body_material"):
                mats.append(f"柜:{item['body_material']}")
            if item.get("door_material") and item.get("door_type") != "无门（开放）":
                mats.append(f"门:{item['door_material']}")
            if item.get("countertop_material"):
                mats.append(f"台:{item['countertop_material']}")
            c4.caption(" / ".join(mats))

            c5.markdown(f"**¥{item['line_subtotal']:,.0f}**")
            if c6.button("✕", key=f"del_{item['_id']}", help="移除"):
                to_delete.append(item["_id"])

    if to_delete:
        st.session_state.qv3_items = [i for i in items if i["_id"] not in to_delete]
        st.rerun()

    st.markdown("---")

    # ── 折扣 & 备注 ──
    c_disc, c_remark = st.columns(2)
    with c_disc:
        discount_pct = st.slider(
            "整单折扣",
            min_value=50, max_value=100, step=5,
            value=st.session_state.qv3_discount,
            format="%d%%",
            help="100% = 不打折，85% = 八五折"
        )
        st.session_state.qv3_discount = discount_pct
        discount = discount_pct / 100.0
    with c_remark:
        remark = st.text_area("报价备注", value=st.session_state.qv3_remark,
                               height=68, placeholder="如：含安装费、含基础五金...")
        st.session_state.qv3_remark = remark

    # ── 合计 ──
    subtotal = sum(i["line_subtotal"] for i in items)
    discount_amount = round(subtotal * (1 - discount), 2)
    total = round(subtotal * discount, 2)

    col_m = st.columns(4)
    col_m[0].metric("小计", f"¥{subtotal:,.0f}")
    col_m[1].metric("折扣", f"{discount_pct}折" if discount_pct < 100 else "无折扣",
                    f"-¥{discount_amount:,.0f}" if discount_amount > 0 else "")
    col_m[2].metric("📌 最终报价", f"¥{total:,.0f}")
    col_m[3].metric("项目数", f"{len(items)} 项")

    st.markdown("---")

    # ── 保存 & 导出 ──
    c_save, c_pdf = st.columns(2)
    with c_save:
        if st.button("💾 保存报价单", type="primary", use_container_width=True):
            _save_quote(subtotal, discount_amount, total, items)
    with c_pdf:
        if st.button("📄 导出 PDF", use_container_width=True):
            _export_pdf(subtotal, discount_amount, total, items)


# ──────────────────────────────────────────────────────────────
# 保存报价单
# ──────────────────────────────────────────────────────────────

def _uuid_or_none(v):
    if not v:
        return None
    s = str(v).strip()
    return s if s else None

def _save_quote(subtotal, discount_amount, total, items):
    if not st.session_state.qv3_store_id:
        st.error("请先在基本信息中选择门店")
        return

    quote_no = _gen_quote_no()
    discount = st.session_state.qv3_discount / 100.0

    try:
        qid = db.insert("quotes", {
            "quote_no": quote_no,
            "store_id": _uuid_or_none(st.session_state.qv3_store_id),
            "customer_id": _uuid_or_none(st.session_state.qv3_customer_id),
            "customer_name": st.session_state.qv3_customer_name,
            "customer_phone": st.session_state.qv3_customer_phone,
            "designer_name": st.session_state.qv3_designer,
            "house_area": st.session_state.qv3_house_area,
            "house_type": st.session_state.qv3_house_type,
            "quote_date": date.today().isoformat(),
            "subtotal": subtotal,
            "discount_rate": discount,
            "discount_amount": discount_amount,
            "total_amount": total,
            "remark": st.session_state.qv3_remark,
            "status": "draft",
        })

        for idx, item in enumerate(items):
            db.insert("quote_items_v2", {
                "quote_id": _uuid_or_none(qid),
                "sort_order": idx,
                "space_name": item.get("space_name"),
                "product_type_id": _uuid_or_none(item.get("product_type_id")),
                "product_type_name": item.get("product_type_name"),
                "length_m": item.get("length_m"),
                "width_m": item.get("width_m"),
                "height_m": item.get("height_m"),
                "body_material": item.get("body_material"),
                "body_unit_price": item.get("body_unit_price"),
                "body_subtotal": item.get("body_subtotal"),
                "has_upper_cabinet": item.get("has_upper_cabinet", False),
                "upper_material": item.get("upper_material"),
                "upper_unit_price": item.get("upper_unit_price"),
                "upper_subtotal": item.get("upper_subtotal"),
                "door_type": item.get("door_type"),
                "door_material": item.get("door_material"),
                "door_area_m2": item.get("door_area_m2"),
                "door_unit_price": item.get("door_unit_price"),
                "door_subtotal": item.get("door_subtotal"),
                "countertop_material": item.get("countertop_material"),
                "countertop_length_m": item.get("countertop_length_m"),
                "countertop_unit_price": item.get("countertop_unit_price"),
                "countertop_extras_json": json.dumps(item.get("countertop_extras_json") or [], ensure_ascii=False),
                "countertop_subtotal": item.get("countertop_subtotal"),
                "hardware_items_json": json.dumps(item.get("hardware_items_json") or [], ensure_ascii=False),
                "hardware_subtotal": item.get("hardware_subtotal"),
                "line_subtotal": item.get("line_subtotal"),
            })

        st.session_state.qv3_saved_id = qid
        st.success(f"✅ 已保存！单号：**{quote_no}**  总价：¥{total:,.0f}")

    except Exception as e:
        st.error(f"保存失败: {e}")


# ──────────────────────────────────────────────────────────────
# 导出 PDF
# ──────────────────────────────────────────────────────────────

def _export_pdf(subtotal, discount_amount, total, items):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import io, os

        font_paths = [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/msyh.ttc",
        ]
        font_registered = False
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    pdfmetrics.registerFont(TTFont("CJK", fp))
                    font_registered = True
                    break
                except Exception:
                    continue
        cn = "CJK" if font_registered else "Helvetica"

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                 leftMargin=2*cm, rightMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)

        def P(text, size=9, bold=False, align=0, color=colors.black):
            return Paragraph(text, ParagraphStyle("s", fontName=cn, fontSize=size,
                                                   spaceAfter=3, alignment=align,
                                                   textColor=color))

        story = []
        story.append(P("全屋定制 · 估价单", 18, align=1))
        story.append(Spacer(1, 0.3*cm))

        # 客户信息
        info = [
            ["客户", st.session_state.qv3_customer_name or "—",
             "电话", st.session_state.qv3_customer_phone or "—"],
            ["设计师", st.session_state.qv3_designer or "—",
             "日期", date.today().strftime("%Y年%m月%d日")],
            ["面积", f"{st.session_state.qv3_house_area or '—'} ㎡",
             "户型", st.session_state.qv3_house_type or "—"],
        ]
        t = Table(info, colWidths=[2.5*cm, 5*cm, 2.5*cm, 5*cm])
        t.setStyle(TableStyle([
            ("FONTNAME", (0,0),(-1,-1), cn), ("FONTSIZE",(0,0),(-1,-1),9),
            ("BACKGROUND",(0,0),(0,-1), colors.HexColor("#F0F0F0")),
            ("BACKGROUND",(2,0),(2,-1), colors.HexColor("#F0F0F0")),
            ("GRID",(0,0),(-1,-1),0.4, colors.grey),
            ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))

        # 明细
        story.append(P("估价明细", 11))
        header = ["空间", "产品类型", "规格/材质", "柜体", "门板", "台面", "五金", "小计"]
        cw = [2*cm, 2.5*cm, 4*cm, 2*cm, 2*cm, 2*cm, 1.8*cm, 2.2*cm]
        rows = [header]
        for item in items:
            mats = []
            if item.get("body_material"):
                mats.append(f"柜:{item['body_material']}")
            if item.get("door_material") and item.get("door_type") != "无门（开放）":
                mats.append(f"门:{item['door_material']}")
            if item.get("countertop_material"):
                mats.append(f"台:{item['countertop_material']}")
            if item["category"] == "A":
                spec = f"延米{item['length_m']}m"
            else:
                spec = f"{item['width_m']}m×{item['height_m']}m"

            rows.append([
                item.get("space_name",""),
                item.get("product_type_name",""),
                f"{spec}\n{' '.join(mats)}",
                f"¥{item.get('body_subtotal',0):,.0f}",
                f"¥{item.get('door_subtotal',0):,.0f}",
                f"¥{item.get('countertop_subtotal',0):,.0f}",
                f"¥{item.get('hardware_subtotal',0):,.0f}",
                f"¥{item.get('line_subtotal',0):,.0f}",
            ])

        dt = Table(rows, colWidths=cw, repeatRows=1)
        dt.setStyle(TableStyle([
            ("FONTNAME",(0,0),(-1,-1),cn), ("FONTSIZE",(0,0),(-1,-1),8),
            ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#2C2C2C")),
            ("TEXTCOLOR",(0,0),(-1,0), colors.white),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#FAFAFA")]),
            ("GRID",(0,0),(-1,-1),0.4, colors.HexColor("#DDDDDD")),
            ("ALIGN",(3,0),(-1,-1),"RIGHT"),
            ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ]))
        story.append(dt)
        story.append(Spacer(1, 0.4*cm))

        # 合计
        discount = st.session_state.qv3_discount
        sum_rows = [
            ["","","","","","","合计", f"¥{subtotal:,.0f}"],
            ["","","","","","",f"折扣({discount}折)", f"-¥{discount_amount:,.0f}"],
            ["","","","","","","最终估价", f"¥{total:,.0f}"],
        ]
        st_t = Table(sum_rows, colWidths=cw)
        st_t.setStyle(TableStyle([
            ("FONTNAME",(0,0),(-1,-1),cn), ("FONTSIZE",(0,0),(-1,-1),9),
            ("FONTSIZE",(6,2),(7,2),12),
            ("TEXTCOLOR",(6,2),(7,2), colors.HexColor("#C0392B")),
            ("ALIGN",(6,0),(-1,-1),"RIGHT"),
        ]))
        story.append(st_t)

        if st.session_state.qv3_remark:
            story.append(Spacer(1, 0.3*cm))
            story.append(P(f"备注：{st.session_state.qv3_remark}"))

        story.append(Spacer(1, 0.5*cm))
        story.append(P(f"本估价单有效期30天，最终价格以图纸确认后合同为准。  生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        7, align=1, color=colors.grey))

        doc.build(story)
        cname = st.session_state.qv3_customer_name or "guest"
        st.download_button(
            "⬇️ 点击下载 PDF",
            data=buf.getvalue(),
            file_name=f"估价单_{cname}_{date.today()}.pdf",
            mime="application/pdf",
            type="primary"
        )

    except ImportError:
        st.error("需要 reportlab 库，请确认 requirements.txt 中有 `reportlab`")
    except Exception as e:
        st.error(f"PDF生成失败: {e}")


# ──────────────────────────────────────────────────────────────
# Tab 2：历史报价单
# ──────────────────────────────────────────────────────────────

def _section_quote_list():
    st.subheader("📋 历史报价单")

    try:
        quotes = db.select("quotes", order_by="created_at.desc", limit=50)
    except Exception:
        st.error("加载报价单失败")
        return

    if not quotes:
        st.info("暂无报价记录")
        return

    # ── 快捷操作栏 ──
    draft_ids = [q["id"] for q in quotes if q.get("status", "draft") == "draft"]
    c_info, c_btn = st.columns([3, 1])
    with c_info:
        st.caption(f"共 {len(quotes)} 条记录，其中草稿 {len(draft_ids)} 条")
    with c_btn:
        if draft_ids and st.button("🗑️ 清空所有草稿", use_container_width=True, type="secondary"):
            try:
                for qid in draft_ids:
                    try:
                        db.supabase.table("quote_items_v2").delete().eq("quote_id", qid).execute()
                    except Exception:
                        pass
                    try:
                        db.supabase.table("quote_items").delete().eq("quote_id", qid).execute()
                    except Exception:
                        pass
                    db.delete("quotes", qid)
                st.success(f"✅ 已清空 {len(draft_ids)} 条草稿")
                st.rerun()
            except Exception as e:
                st.error(f"清空失败: {e}")
    st.markdown("---")

    STATUS_MAP = {
        "draft":    ("📝 草稿",  "#888888"),
        "sent":     ("📤 已发送","#2196F3"),
        "accepted": ("✅ 已成交","#4CAF50"),
        "rejected": ("❌ 已取消","#F44336"),
    }

    for q in quotes:
        status = q.get("status", "draft")
        status_label, _ = STATUS_MAP.get(status, ("📝", "#888"))
        total = float(q.get("total_amount") or 0)

        with st.expander(
            f"{status_label}  `{q['quote_no']}`  "
            f"{q.get('customer_name','未知客户')}  "
            f"**¥{total:,.0f}**  _{q.get('quote_date','')}_",
            expanded=False
        ):
            # 尝试加载 v2 明细
            try:
                items = db.select("quote_items_v2", filters={"quote_id": q["id"]}, order_by="sort_order")
            except Exception:
                items = []

            if items:
                hdr = st.columns([1.5, 1.5, 1.5, 1, 1, 1, 1, 1.2])
                for h, t in zip(hdr, ["空间","产品","材质","柜体","门板","台面","五金","小计"]):
                    h.markdown(f"**{t}**")

                for it in items:
                    row = st.columns([1.5, 1.5, 1.5, 1, 1, 1, 1, 1.2])
                    row[0].write(it.get("space_name",""))
                    row[1].write(it.get("product_type_name",""))
                    mats = []
                    if it.get("body_material"): mats.append(it["body_material"])
                    if it.get("door_material") and it.get("door_type") != "无门（开放）":
                        mats.append(it["door_material"])
                    if it.get("countertop_material"): mats.append(it["countertop_material"])
                    row[2].write(" / ".join(mats))
                    row[3].write(f"¥{float(it.get('body_subtotal') or 0):,.0f}")
                    row[4].write(f"¥{float(it.get('door_subtotal') or 0):,.0f}")
                    row[5].write(f"¥{float(it.get('countertop_subtotal') or 0):,.0f}")
                    row[6].write(f"¥{float(it.get('hardware_subtotal') or 0):,.0f}")
                    row[7].write(f"¥{float(it.get('line_subtotal') or 0):,.0f}")

            st.markdown("---")
            disc = float(q.get("discount_rate") or 1.0)
            disc_amt = float(q.get("discount_amount") or 0)
            mc = st.columns(4)
            mc[0].metric("小计", f"¥{float(q.get('subtotal') or 0):,.0f}")
            mc[1].metric("折扣", f"{disc*100:.0f}折", f"-¥{disc_amt:,.0f}")
            mc[2].metric("总价", f"¥{total:,.0f}")
            mc[3].metric("状态", status_label)

            if q.get("remark"):
                st.caption(f"备注：{q['remark']}")

            col_upd, col_del = st.columns([3, 1])
            with col_upd:
                new_status = st.selectbox(
                    "更新状态", ["draft","sent","accepted","rejected"],
                    index=["draft","sent","accepted","rejected"].index(status),
                    key=f"status_{q['id']}"
                )
                if st.button("更新状态", key=f"upd_{q['id']}", use_container_width=True):
                    try:
                        db.update("quotes", q["id"], {"status": new_status})
                        st.success("已更新")
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新失败: {e}")
            with col_del:
                st.write("")  # 占位对齐
                st.write("")
                if st.button("🗑️ 删除", key=f"del_{q['id']}", use_container_width=True, type="secondary"):
                    try:
                        # 先删明细，再删主单
                        try:
                            db.supabase.table("quote_items_v2").delete().eq("quote_id", q["id"]).execute()
                        except Exception:
                            pass
                        try:
                            db.supabase.table("quote_items").delete().eq("quote_id", q["id"]).execute()
                        except Exception:
                            pass
                        db.delete("quotes", q["id"])
                        st.success("已删除")
                        st.rerun()
                    except Exception as e:
                        st.error(f"删除失败: {e}")
