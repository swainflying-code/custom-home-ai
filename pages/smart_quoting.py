"""
智能报价页面
流程：选门店 → 绑定客户(可选) → 按空间添加产品+部件 → 汇总报价单 → 导出PDF
"""
import streamlit as st
import uuid
from datetime import datetime, date
from core.database import db


# ──────────────────────────────────────────────────────────────
# Session state 初始化
# ──────────────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "quote_store_id": None,
        "quote_customer_id": None,
        "quote_customer_name": "",
        "quote_customer_phone": "",
        "quote_designer": "",
        "quote_house_area": "",
        "quote_house_type": "",
        "quote_remark": "",
        "quote_discount": 1.0,
        "quote_items": [],       # list of dict
        "quote_saved_id": None,  # 已保存的 quote id
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _reset_quote():
    keys = [k for k in st.session_state if k.startswith("quote_")]
    for k in keys:
        del st.session_state[k]
    _init_state()


# ──────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────

def _load_stores():
    try:
        return db.select("stores", filters={"is_active": True}, order_by="store_code")
    except Exception:
        return []

def _load_spaces():
    try:
        return db.select("product_spaces", filters={"is_active": True}, order_by="sort_order")
    except Exception:
        return []

def _load_products(store_id, space_id):
    try:
        return db.select("products",
                         filters={"store_id": store_id, "space_id": space_id, "is_active": True},
                         order_by="sort_order")
    except Exception:
        return []

def _load_parts(product_id):
    try:
        return db.select("product_parts",
                         filters={"product_id": product_id, "is_active": True},
                         order_by="sort_order")
    except Exception:
        return []

def _load_customers():
    try:
        rows = db.select("customers", order_by="created_at.desc", limit=200)
        return rows
    except Exception:
        return []

def _gen_quote_no():
    today = datetime.now().strftime("%Y%m%d")
    rand = str(uuid.uuid4().int)[:5]
    return f"Q{today}{rand}"

def _calc_totals():
    subtotal = sum(item["line_total"] for item in st.session_state.quote_items)
    discount = st.session_state.quote_discount
    discount_amount = subtotal * (1 - discount)
    total = subtotal * discount
    return subtotal, discount_amount, total


# ──────────────────────────────────────────────────────────────
# 主页面
# ──────────────────────────────────────────────────────────────

def show_smart_quoting_page():
    _init_state()

    st.title("💰 智能报价")

    # 顶部工具栏
    col_title, col_new = st.columns([4, 1])
    with col_new:
        if st.button("🗑️ 清空重填", use_container_width=True):
            _reset_quote()
            st.rerun()

    tab_build, tab_list = st.tabs(["📝 新建报价单", "📋 报价单记录"])

    with tab_build:
        _section_header()
        st.markdown("---")
        _section_add_items()
        st.markdown("---")
        _section_summary()

    with tab_list:
        _section_quote_list()


# ──────────────────────────────────────────────────────────────
# Section 1：报价头部信息
# ──────────────────────────────────────────────────────────────

def _section_header():
    st.subheader("① 基本信息")

    stores = _load_stores()
    if not stores:
        st.error("⚠️ 尚未配置门店，请前往「后台管理 → 门店管理」创建门店后再使用报价功能")
        return

    store_opts = {f"{s['store_name']} ({s['store_code']})": s["id"] for s in stores}

    c1, c2, c3 = st.columns(3)
    with c1:
        sel_store = st.selectbox("门店 *", list(store_opts.keys()), key="hdr_store")
        st.session_state.quote_store_id = store_opts[sel_store]
        designer = st.text_input("设计师姓名", value=st.session_state.quote_designer, key="hdr_designer")
        st.session_state.quote_designer = designer

    with c2:
        # 客户绑定
        customers = _load_customers()
        cust_opts = {"── 不绑定客户 ──": None}
        for c in customers:
            label = f"{c.get('name','未知')} {c.get('contact_info','')}"
            cust_opts[label] = c["id"]

        sel_cust_label = st.selectbox("关联客户（可选）", list(cust_opts.keys()), key="hdr_cust")
        sel_cust_id = cust_opts[sel_cust_label]
        st.session_state.quote_customer_id = sel_cust_id

        if sel_cust_id:
            cust_data = next((c for c in customers if c["id"] == sel_cust_id), None)
            if cust_data:
                st.session_state.quote_customer_name = cust_data.get("name", "")
                st.session_state.quote_customer_phone = cust_data.get("contact_info", "")
        else:
            name = st.text_input("客户姓名", value=st.session_state.quote_customer_name, key="hdr_cname")
            st.session_state.quote_customer_name = name

    with c3:
        phone = st.text_input("客户电话", value=st.session_state.quote_customer_phone, key="hdr_phone")
        st.session_state.quote_customer_phone = phone
        area = st.text_input("房屋面积（㎡）", value=st.session_state.quote_house_area, key="hdr_area")
        st.session_state.quote_house_area = area
        htype = st.text_input("户型", value=st.session_state.quote_house_type,
                               placeholder="如 三室两厅", key="hdr_htype")
        st.session_state.quote_house_type = htype


# ──────────────────────────────────────────────────────────────
# 规格参数解析工具
# ──────────────────────────────────────────────────────────────

def _parse_options(raw) -> list:
    """解析逗号分隔的规格选项字符串，返回数字列表，如 '680,700,720' → [680,700,720]"""
    if not raw:
        return []
    import re
    parts = re.split(r"[,，\s]+", str(raw).strip())
    result = []
    for p in parts:
        p = p.strip()
        if p:
            try:
                result.append(int(float(p)))
            except ValueError:
                result.append(p)
    return result


def _calc_part_price(part: dict, height: float, width: float) -> tuple[float, str]:
    """
    根据 price_type 计算部件单价和描述。
    返回 (line_total, price_desc)
    price_type:
      fixed    → 固定价格，直接取 part['price']
      included → 已包含，价格为 0
      area     → 面积计价，height(mm)/1000 * width(mm)/1000 * price/㎡
                 或 height * width 均以毫米传入时换算成米
    """
    price_type = part.get("price_type") or "fixed"
    unit_price  = float(part.get("price") or 0)

    if price_type == "included":
        return 0.0, "已包含"
    elif price_type == "area":
        # 高度/宽度单位为 mm，转换为 m 再算面积
        h_m = height / 1000.0
        w_m = width  / 1000.0
        area = h_m * w_m
        total = round(area * unit_price, 2)
        return total, f"{h_m:.3f}m × {w_m:.3f}m × ¥{unit_price:,.0f}/㎡ = ¥{total:,.0f}"
    else:  # fixed
        return unit_price, f"¥{unit_price:,.0f} / {part.get('price_unit','个')}"


# ──────────────────────────────────────────────────────────────
# Section 2：添加产品+部件
# ──────────────────────────────────────────────────────────────

def _section_add_items():
    st.subheader("② 按空间添加产品和部件")

    store_id = st.session_state.quote_store_id
    if not store_id:
        st.warning("请先在基本信息中选择门店")
        return

    spaces = _load_spaces()
    if not spaces:
        st.warning("暂无空间数据，请前往「后台管理 → 空间管理」配置")
        return

    space_opts = {f"{s['space_icon']} {s['space_name']}": s for s in spaces}

    col_sp, col_prod = st.columns(2)
    with col_sp:
        sel_space_label = st.selectbox("选择空间", list(space_opts.keys()), key="item_space")
    sel_space = space_opts[sel_space_label]

    products = _load_products(store_id=store_id, space_id=sel_space["id"])
    if not products:
        st.info(f"「{sel_space_label}」下暂无产品，请前往「后台管理 → 产品目录」添加")
        return

    prod_opts = {p["product_name"]: p for p in products}
    with col_prod:
        sel_prod_label = st.selectbox("选择产品系列", list(prod_opts.keys()), key="item_prod")
    sel_prod = prod_opts[sel_prod_label]

    # 显示产品简介
    if sel_prod.get("description"):
        st.caption(f"📌 {sel_prod['description']}")

    # ── 规格参数选择（高度 / 宽度）──
    height_opts = _parse_options(sel_prod.get("height_options"))
    width_opts  = _parse_options(sel_prod.get("width_options"))

    sel_height = None
    sel_width  = None
    has_params = bool(height_opts or width_opts)

    if has_params:
        st.markdown("**📐 选择产品规格尺寸：**")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            if height_opts:
                h_labels = [f"{v} mm" for v in height_opts]
                h_idx = st.selectbox("高度", h_labels, key="item_height")
                sel_height = height_opts[h_labels.index(h_idx)]
            else:
                sel_height = st.number_input("高度 (mm)", min_value=100, value=720, step=10, key="item_height_num")
        with pc2:
            if width_opts:
                w_labels = [f"{v} mm" for v in width_opts]
                w_idx = st.selectbox("宽度", w_labels, key="item_width")
                sel_width = width_opts[w_labels.index(w_idx)]
            else:
                sel_width = st.number_input("宽度 (mm)", min_value=100, value=800, step=50, key="item_width_num")
        with pc3:
            if sel_height and sel_width:
                area = (sel_height / 1000) * (sel_width / 1000)
                st.metric("展开面积", f"{area:.3f} ㎡")

    # 加载部件
    parts = _load_parts(product_id=sel_prod["id"])

    if not parts:
        st.info("该产品暂无部件配置，请前往「后台管理 → 部件价格」添加")
        base_price = float(sel_prod.get("base_price") or 0)
        if base_price > 0:
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                st.info(f"基础起步价：¥{base_price:,.0f} / {sel_prod.get('unit','套')}")
            with c2:
                qty = st.number_input("数量", min_value=0.1, value=1.0, step=0.5, key="item_base_qty")
            with c3:
                if st.button("➕ 加入报价", key="btn_add_base", type="primary", use_container_width=True):
                    _add_item({
                        "space_name": sel_space["space_name"],
                        "product_name": sel_prod["product_name"],
                        "product_id": sel_prod["id"],
                        "part_id": None,
                        "part_name": "基础套餐",
                        "spec_name": sel_prod.get("series") or "",
                        "unit_price": base_price,
                        "price_unit": sel_prod.get("unit", "套"),
                        "quantity": qty,
                        "line_total": base_price * qty,
                        "remark": "",
                    })
        return

    # ── 按分类展示部件 ──
    parts_sorted = sorted(parts, key=lambda x: (x.get("part_category") or "其他", x.get("sort_order") or 0))

    st.markdown("**选择部件规格，确认后加入报价单：**")

    # 没有尺寸参数时默认 0，不影响 fixed/included 计价
    h = float(sel_height or 0)
    w = float(sel_width or 0)

    cat_map = {}
    for part in parts_sorted:
        cat = part.get("part_category") or "其他"
        cat_map.setdefault(cat, []).append(part)

    for cat, cat_parts in cat_map.items():
        st.markdown(f"**{cat}**")
        for part in cat_parts:
            price_type = part.get("price_type") or "fixed"
            req = " 🔴" if part.get("is_required") else ""
            line_total, price_desc = _calc_part_price(part, h, w)
            unit_price = float(part.get("price") or 0)

            c1, c2, c3, c4 = st.columns([3.5, 1.2, 1.2, 0.8])
            with c1:
                label = f"{part['part_name']} · {part['spec_name']}{req}"
                if part.get("remark"):
                    label += f"  _{part['remark']}_"
                st.markdown(f"&nbsp;&nbsp;{label}", unsafe_allow_html=False)
                # 计价说明
                if price_type == "included":
                    st.caption("✅ 已包含，不另计费")
                elif price_type == "area":
                    st.caption(f"📐 面积计价：{price_desc}" if (h and w) else f"📐 面积计价：¥{unit_price:,.0f}/㎡（请先选择尺寸）")
                else:
                    st.caption(f"¥{unit_price:,.0f} / {part.get('price_unit','个')}")

            with c2:
                # included 类型不需要填数量
                if price_type == "included":
                    qty = 1.0
                    st.markdown("——")
                elif price_type == "area":
                    # 面积已由尺寸决定，数量默认1（可改为延米/套数）
                    qty = st.number_input(
                        "套数", min_value=1.0, value=1.0, step=1.0,
                        key=f"qty_{part['id']}", label_visibility="collapsed"
                    )
                else:
                    qty = st.number_input(
                        "数量", min_value=0.0,
                        value=float(part.get("min_qty") or 1),
                        step=0.5,
                        key=f"qty_{part['id']}",
                        label_visibility="collapsed"
                    )

            with c3:
                actual_total = line_total * qty if price_type != "area" else line_total * qty
                if price_type == "included":
                    st.markdown("**已含**")
                else:
                    st.markdown(f"**¥{actual_total:,.0f}**")

            with c4:
                if price_type == "included":
                    # included 直接一键加入，不需要用户操作
                    if st.button("含✓", key=f"add_{part['id']}", help="已包含项，点击加入记录",
                                 use_container_width=True, disabled=False):
                        _add_item({
                            "space_name": sel_space["space_name"],
                            "product_name": sel_prod["product_name"],
                            "product_id": sel_prod["id"],
                            "part_id": part["id"],
                            "part_name": part["part_name"],
                            "spec_name": part["spec_name"],
                            "unit_price": 0.0,
                            "price_unit": "已含",
                            "quantity": 1,
                            "line_total": 0.0,
                            "remark": "已包含",
                        })
                else:
                    if st.button("➕", key=f"add_{part['id']}", help="加入报价单", use_container_width=True):
                        if price_type != "area" and qty <= 0:
                            st.warning("数量必须大于0")
                        elif price_type == "area" and not (h and w):
                            st.warning("请先选择高度和宽度")
                        else:
                            spec_label = part["spec_name"]
                            if has_params and (h or w):
                                spec_label += f"（{int(h)}×{int(w)}mm）"
                            _add_item({
                                "space_name": sel_space["space_name"],
                                "product_name": sel_prod["product_name"],
                                "product_id": sel_prod["id"],
                                "part_id": part["id"],
                                "part_name": part["part_name"],
                                "spec_name": spec_label,
                                "unit_price": unit_price,
                                "price_unit": part.get("price_unit", "元"),
                                "quantity": qty,
                                "line_total": actual_total,
                                "remark": part.get("remark", ""),
                            })


def _add_item(item: dict):
    items = st.session_state.quote_items
    item["_id"] = str(uuid.uuid4())[:8]
    items.append(item)
    st.session_state.quote_items = items
    st.success(f"✅ 已加入：{item['part_name']} · {item['spec_name']}  ¥{item['line_total']:,.0f}")
    st.rerun()


# ──────────────────────────────────────────────────────────────
# Section 3：报价汇总 & 保存 & 导出
# ──────────────────────────────────────────────────────────────

def _section_summary():
    st.subheader("③ 报价汇总")

    items = st.session_state.quote_items

    if not items:
        st.info("尚未加入任何产品部件，请在上方「按空间添加产品和部件」中选择")
        return

    # ── 已选明细表 ──
    st.markdown("**已选明细：**")

    # 按空间分组展示
    space_groups = {}
    for item in items:
        sp = item.get("space_name", "未分类")
        space_groups.setdefault(sp, []).append(item)

    to_delete = []
    for space, sp_items in space_groups.items():
        st.markdown(f"**🏠 {space}**")
        for item in sp_items:
            c1, c2, c3, c4, c5 = st.columns([2.5, 2, 1, 1.2, 0.5])
            with c1:
                st.markdown(f"{item['product_name']}")
            with c2:
                st.markdown(f"{item['part_name']} · {item['spec_name']}")
            with c3:
                st.markdown(f"{item['quantity']} {item.get('price_unit','')}")
            with c4:
                st.markdown(f"**¥{item['line_total']:,.0f}**")
            with c5:
                if st.button("✕", key=f"del_{item['_id']}", help="移除此项"):
                    to_delete.append(item["_id"])

    if to_delete:
        st.session_state.quote_items = [i for i in items if i["_id"] not in to_delete]
        st.rerun()

    st.markdown("---")

    # ── 折扣 & 合计 ──
    c_disc, c_remark = st.columns(2)
    with c_disc:
        # 用整数百分比 50-100 操作，避免 format="%.0f%%" 把 0.95 显示成 1%
        discount_pct = st.slider(
            "整单折扣",
            min_value=50, max_value=100, step=5,
            value=int(round(st.session_state.quote_discount * 100)),
            format="%d%%",
            help="100% = 不打折，90% = 九折，50% = 五折"
        )
        discount = discount_pct / 100.0
        st.session_state.quote_discount = discount
    with c_remark:
        remark = st.text_area("报价备注", value=st.session_state.quote_remark,
                               height=68, placeholder="如：含安装费、含五金配件...")
        st.session_state.quote_remark = remark

    subtotal, discount_amount, total = _calc_totals()

    col_m = st.columns(4)
    col_m[0].metric("小计", f"¥{subtotal:,.0f}")
    col_m[1].metric("折扣", f"{discount*100:.0f}折", f"-¥{discount_amount:,.0f}")
    col_m[2].metric("📌 最终报价", f"¥{total:,.0f}")
    col_m[3].metric("明细项数", f"{len(items)} 项")

    st.markdown("---")

    # ── 保存 & 导出 ──
    c_save, c_pdf = st.columns(2)
    with c_save:
        if st.button("💾 保存报价单", type="primary", use_container_width=True):
            _save_quote(subtotal, discount_amount, total)
    with c_pdf:
        if st.button("📄 导出 PDF", use_container_width=True):
            _export_pdf(subtotal, discount_amount, total)


def _uuid_or_none(v):
    """确保 uuid 字段不传空字符串，一律转为 None"""
    if not v:
        return None
    s = str(v).strip()
    return s if s else None


def _save_quote(subtotal, discount_amount, total):
    if not st.session_state.quote_store_id:
        st.error("请先选择门店")
        return

    quote_no = _gen_quote_no()
    try:
        cust_id  = _uuid_or_none(st.session_state.quote_customer_id)
        store_id = _uuid_or_none(st.session_state.quote_store_id)

        qid = db.insert("quotes", {
            "quote_no": quote_no,
            "store_id": store_id,
            "customer_id": cust_id,
            "customer_name": st.session_state.quote_customer_name,
            "customer_phone": st.session_state.quote_customer_phone,
            "designer_name": st.session_state.quote_designer,
            "house_area": st.session_state.quote_house_area,
            "house_type": st.session_state.quote_house_type,
            "quote_date": date.today().isoformat(),
            "subtotal": subtotal,
            "discount_rate": st.session_state.quote_discount,
            "discount_amount": discount_amount,
            "total_amount": total,
            "remark": st.session_state.quote_remark,
            "status": "draft",
        })

        # 保存明细（uuid 字段空字符串统一转 None）
        for idx, item in enumerate(st.session_state.quote_items):
            db.insert("quote_items", {
                "quote_id": _uuid_or_none(qid),
                "space_name": item.get("space_name"),
                "product_name": item.get("product_name"),
                "product_id": _uuid_or_none(item.get("product_id")),
                "part_id": _uuid_or_none(item.get("part_id")),
                "part_name": item.get("part_name"),
                "spec_name": item.get("spec_name"),
                "unit_price": item.get("unit_price"),
                "price_unit": item.get("price_unit"),
                "quantity": item.get("quantity"),
                "line_total": item.get("line_total"),
                "remark": item.get("remark", ""),
                "sort_order": idx,
            })

        st.session_state.quote_saved_id = qid
        st.success(f"✅ 报价单已保存！单号：**{quote_no}**  总金额：¥{total:,.0f}")

    except Exception as e:
        st.error(f"保存失败: {e}")


def _export_pdf(subtotal, discount_amount, total):
    """生成 PDF 并触发下载"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import io, os

        # 注册中文字体（Streamlit Cloud 有 NotoSansCJK，本地可能无）
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

        cn_font = "CJK" if font_registered else "Helvetica"

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                 leftMargin=2*cm, rightMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("title", fontName=cn_font, fontSize=18,
                                      spaceAfter=6, alignment=1)
        normal_style = ParagraphStyle("normal", fontName=cn_font, fontSize=9,
                                       spaceAfter=4)
        bold_style = ParagraphStyle("bold", fontName=cn_font, fontSize=10,
                                     spaceAfter=4)

        story = []

        # 标题
        story.append(Paragraph("BINK 不锈钢定制 · 报价单", title_style))
        story.append(Spacer(1, 0.3*cm))

        # 基本信息表格
        info_data = [
            ["客户姓名", st.session_state.quote_customer_name or "—",
             "联系电话", st.session_state.quote_customer_phone or "—"],
            ["设计师", st.session_state.quote_designer or "—",
             "报价日期", date.today().strftime("%Y年%m月%d日")],
            ["房屋面积", f"{st.session_state.quote_house_area or '—'} ㎡",
             "户型", st.session_state.quote_house_type or "—"],
        ]
        info_table = Table(info_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), cn_font),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F5F5F5")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F5F5F5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.4*cm))

        # 明细表
        story.append(Paragraph("报价明细", bold_style))
        header = ["空间", "产品", "部件/规格", "用量", "单价", "小计"]
        table_data = [header]

        items = st.session_state.quote_items
        space_groups = {}
        for item in items:
            sp = item.get("space_name", "未分类")
            space_groups.setdefault(sp, []).append(item)

        for space, sp_items in space_groups.items():
            for item in sp_items:
                table_data.append([
                    space,
                    item.get("product_name", ""),
                    f"{item.get('part_name','')} · {item.get('spec_name','')}",
                    f"{item.get('quantity',1)} {item.get('price_unit','')}",
                    f"¥{item.get('unit_price',0):,.0f}",
                    f"¥{item.get('line_total',0):,.0f}",
                ])

        col_widths = [2.5*cm, 3.5*cm, 5*cm, 2.5*cm, 2.5*cm, 2.5*cm]
        detail_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        detail_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), cn_font),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C2C2C")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ]))
        story.append(detail_table)
        story.append(Spacer(1, 0.4*cm))

        # 合计
        discount = st.session_state.quote_discount
        summary_data = [
            ["", "", "", "", "小计", f"¥{subtotal:,.0f}"],
            ["", "", "", "", f"折扣 ({discount*100:.0f}折)", f"-¥{discount_amount:,.0f}"],
            ["", "", "", "", "最终报价", f"¥{total:,.0f}"],
        ]
        sum_table = Table(summary_data, colWidths=col_widths)
        sum_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), cn_font),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTSIZE", (4, 2), (5, 2), 12),
            ("TEXTCOLOR", (4, 2), (5, 2), colors.HexColor("#C0392B")),
            ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
            ("LINEABOVE", (4, 0), (5, 0), 0.5, colors.grey),
            ("LINEBELOW", (4, 2), (5, 2), 1, colors.HexColor("#C0392B")),
        ]))
        story.append(sum_table)
        story.append(Spacer(1, 0.4*cm))

        # 备注
        if st.session_state.quote_remark:
            story.append(Paragraph(f"备注：{st.session_state.quote_remark}", normal_style))

        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(
            f"本报价单有效期 30 天，最终价格以合同签订为准。  "
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ParagraphStyle("footer", fontName=cn_font, fontSize=7,
                           textColor=colors.grey, alignment=1)
        ))

        doc.build(story)
        pdf_bytes = buf.getvalue()

        quote_no = _gen_quote_no()
        st.download_button(
            label="⬇️ 点击下载 PDF",
            data=pdf_bytes,
            file_name=f"BINK报价单_{st.session_state.quote_customer_name or 'guest'}_{quote_no}.pdf",
            mime="application/pdf",
            type="primary",
        )

    except ImportError:
        st.error("导出PDF需要 reportlab 库，请在 requirements.txt 中添加 `reportlab` 后重新部署")
    except Exception as e:
        st.error(f"PDF生成失败: {e}")


# ──────────────────────────────────────────────────────────────
# Tab 2：报价单记录列表
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

    STATUS_MAP = {
        "draft": ("📝 草稿", "#888888"),
        "sent": ("📤 已发送", "#2196F3"),
        "accepted": ("✅ 已成交", "#4CAF50"),
        "rejected": ("❌ 已取消", "#F44336"),
    }

    for q in quotes:
        status = q.get("status", "draft")
        status_label, status_color = STATUS_MAP.get(status, ("📝", "#888"))
        total = q.get("total_amount", 0) or 0

        with st.expander(
            f"{status_label}  `{q['quote_no']}`  "
            f"{q.get('customer_name','未知客户')}  "
            f"**¥{float(total):,.0f}**  "
            f"_{q.get('quote_date','')}_",
            expanded=False
        ):
            # 加载明细
            try:
                items = db.select("quote_items", filters={"quote_id": q["id"]}, order_by="sort_order")
            except Exception:
                items = []

            if items:
                col_headers = st.columns([2, 2.5, 3, 1.5, 1.5, 1.5])
                for h, t in zip(col_headers, ["空间", "产品", "部件/规格", "用量", "单价", "小计"]):
                    h.markdown(f"**{t}**")

                for item in items:
                    c = st.columns([2, 2.5, 3, 1.5, 1.5, 1.5])
                    c[0].write(item.get("space_name", ""))
                    c[1].write(item.get("product_name", ""))
                    c[2].write(f"{item.get('part_name','')} · {item.get('spec_name','')}")
                    c[3].write(f"{item.get('quantity',1)} {item.get('price_unit','')}")
                    c[4].write(f"¥{float(item.get('unit_price',0)):,.0f}")
                    c[5].write(f"¥{float(item.get('line_total',0)):,.0f}")

            st.markdown("---")
            subtotal = float(q.get("subtotal") or 0)
            disc = float(q.get("discount_rate") or 1.0)
            disc_amt = float(q.get("discount_amount") or 0)

            mc = st.columns(4)
            mc[0].metric("小计", f"¥{subtotal:,.0f}")
            mc[1].metric("折扣", f"{disc*100:.0f}折", f"-¥{disc_amt:,.0f}")
            mc[2].metric("总价", f"¥{float(total):,.0f}")
            mc[3].metric("状态", status_label)

            if q.get("remark"):
                st.caption(f"备注：{q['remark']}")

            # 状态更新
            new_status = st.selectbox(
                "更新状态", ["draft", "sent", "accepted", "rejected"],
                index=["draft","sent","accepted","rejected"].index(status),
                key=f"status_{q['id']}"
            )
            if st.button("更新状态", key=f"upd_status_{q['id']}"):
                try:
                    db.update("quotes", q["id"], {"status": new_status})
                    st.success("状态已更新")
                    st.rerun()
                except Exception as e:
                    st.error(f"更新失败: {e}")
