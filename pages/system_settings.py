"""
系统设置 / 后台管理页
包含：门店配置、产品目录管理、部件价格管理
"""
import streamlit as st
import uuid
from datetime import datetime
from core.database import db


# ──────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────

def _load_stores():
    try:
        return db.select("stores", order_by="store_code")
    except Exception:
        return []

def _load_spaces():
    try:
        return db.select("product_spaces", order_by="sort_order")
    except Exception:
        return []

def _load_products(store_id=None, space_id=None):
    try:
        filters = {}
        if store_id:
            filters["store_id"] = store_id
        if space_id:
            filters["space_id"] = space_id
        return db.select("products", filters=filters, order_by="sort_order")
    except Exception:
        return []

def _load_parts(product_id=None):
    try:
        filters = {"product_id": product_id} if product_id else {}
        return db.select("product_parts", filters=filters, order_by="sort_order")
    except Exception:
        return []


def _store_options(stores):
    """返回 {name: id} 字典"""
    return {f"{s['store_name']} ({s['store_code']})": s["id"] for s in stores}


def _space_options(spaces):
    return {f"{s['space_icon']} {s['space_name']}": s["id"] for s in spaces}


# ──────────────────────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────────────────────

def show_system_settings_page():
    st.title("⚙️ 后台管理")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏪 门店管理",
        "📦 产品目录",
        "🔩 部件价格",
        "🗂️ 空间管理",
        "🔍 数据诊断",
    ])

    with tab1:
        _tab_stores()
    with tab2:
        _tab_products()
    with tab3:
        _tab_parts()
    with tab4:
        _tab_spaces()
    with tab5:
        _tab_diagnostics()


# ──────────────────────────────────────────────────────────────
# Tab 1：门店管理
# ──────────────────────────────────────────────────────────────

def _tab_stores():
    st.subheader("门店 / 经销商管理")
    st.caption("每个门店拥有独立的产品目录和价格体系")

    stores = _load_stores()

    # ── 新增门店 ──
    with st.expander("➕ 新增门店", expanded=False):
        with st.form("form_add_store"):
            c1, c2 = st.columns(2)
            with c1:
                code = st.text_input("门店编号 *", placeholder="如 BK001")
                name = st.text_input("门店名称 *", placeholder="如 北京旗舰店")
            with c2:
                city = st.text_input("城市")
                contact = st.text_input("联系人")
                phone = st.text_input("联系电话")
            submitted = st.form_submit_button("保存门店", type="primary")
            if submitted:
                if not code.strip() or not name.strip():
                    st.error("门店编号和名称不能为空")
                else:
                    try:
                        db.insert("stores", {
                            "store_code": code.strip().upper(),
                            "store_name": name.strip(),
                            "city": city, "contact_person": contact,
                            "contact_phone": phone, "is_active": True
                        })
                        st.success(f"✅ 门店「{name}」已创建")
                        st.rerun()
                    except Exception as e:
                        st.error(f"创建失败: {e}")

    # ── 门店列表 ──
    st.markdown("---")
    if not stores:
        st.info("暂无门店数据，请先新增")
        return

    for s in stores:
        with st.expander(
            f"{'🟢' if s.get('is_active') else '🔴'} {s['store_name']}  `{s['store_code']}`  {s.get('city','') or ''}",
            expanded=False
        ):
            with st.form(f"form_edit_store_{s['id']}"):
                c1, c2 = st.columns(2)
                with c1:
                    new_name = st.text_input("门店名称", value=s.get("store_name", ""))
                    new_city = st.text_input("城市", value=s.get("city", "") or "")
                with c2:
                    new_contact = st.text_input("联系人", value=s.get("contact_person", "") or "")
                    new_phone = st.text_input("联系电话", value=s.get("contact_phone", "") or "")
                new_active = st.checkbox("启用", value=s.get("is_active", True))

                c_save, c_del = st.columns(2)
                with c_save:
                    if st.form_submit_button("💾 保存修改", use_container_width=True):
                        try:
                            db.update("stores", s["id"], {
                                "store_name": new_name, "city": new_city,
                                "contact_person": new_contact, "contact_phone": new_phone,
                                "is_active": new_active
                            })
                            st.success("已更新")
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新失败: {e}")
                with c_del:
                    if s.get("store_code") != "DEFAULT":
                        if st.form_submit_button("🗑️ 删除门店", use_container_width=True):
                            try:
                                db.delete("stores", s["id"])
                                st.success("已删除")
                                st.rerun()
                            except Exception as e:
                                st.error(f"删除失败: {e}")


# ──────────────────────────────────────────────────────────────
# Tab 2：产品目录
# ──────────────────────────────────────────────────────────────

def _tab_products():
    st.subheader("产品目录管理")
    st.caption("为每个门店配置各空间下的产品系列")

    stores = _load_stores()
    spaces = _load_spaces()

    if not stores:
        st.warning("请先在「门店管理」中创建至少一个门店")
        return

    # 筛选栏
    col_s, col_sp = st.columns(2)
    store_opts = _store_options(stores)
    space_opts = _space_options(spaces)

    with col_s:
        sel_store_label = st.selectbox("选择门店", list(store_opts.keys()), key="prod_store_sel")
    with col_sp:
        sel_space_label = st.selectbox("筛选空间（可选）", ["全部空间"] + list(space_opts.keys()), key="prod_space_sel")

    sel_store_id = store_opts[sel_store_label]
    sel_space_id = space_opts[sel_space_label] if sel_space_label != "全部空间" else None

    # ── 新增产品 ──
    with st.expander("➕ 新增产品系列", expanded=False):
        with st.form("form_add_product"):
            c1, c2 = st.columns(2)
            with c1:
                p_space = st.selectbox("所属空间 *", list(space_opts.keys()), key="add_p_space")
                p_name = st.text_input("产品名称 *", placeholder="如 水槽柜")
                p_code = st.text_input("产品编号", placeholder="如 KT-SC-01")
            with c2:
                p_series = st.text_input("所属系列", placeholder="如 高定系列")
                p_base_price = st.number_input("基础起步价（元）", min_value=0.0, value=0.0, step=100.0)
                p_unit = st.text_input("计价单位", value="套")
            p_desc = st.text_area("产品描述", height=60)
            st.markdown("**📐 规格参数配置**（用逗号分隔，留空表示不限）")
            pc1, pc2 = st.columns(2)
            with pc1:
                p_height_opts = st.text_input("高度选项 (mm)", placeholder="如 680,700,720",
                                               help="报价时显示为下拉选项，影响面积计价部件的价格")
            with pc2:
                p_width_opts = st.text_input("宽度选项 (mm)", placeholder="如 800,850,900,1000")

            if st.form_submit_button("保存产品", type="primary"):
                if not p_name.strip():
                    st.error("产品名称不能为空")
                else:
                    try:
                        db.insert("products", {
                            "store_id": sel_store_id,
                            "space_id": space_opts[p_space],
                            "product_name": p_name.strip(),
                            "product_code": p_code.strip(),
                            "series": p_series.strip(),
                            "description": p_desc.strip(),
                            "base_price": p_base_price,
                            "unit": p_unit,
                            "height_options": p_height_opts.strip() or None,
                            "width_options": p_width_opts.strip() or None,
                            "is_active": True,
                            "sort_order": 0
                        })
                        st.success(f"✅ 产品「{p_name}」已添加")
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加失败: {e}")

    # ── 产品列表 ──
    st.markdown("---")
    products = _load_products(store_id=sel_store_id, space_id=sel_space_id)

    if not products:
        st.info("该门店暂无产品，请先新增")
        return

    # 按空间分组展示
    space_map = {s["id"]: f"{s['space_icon']} {s['space_name']}" for s in spaces}
    from itertools import groupby
    products_sorted = sorted(products, key=lambda x: x.get("space_id") or "")

    current_space = None
    for p in products_sorted:
        sp_label = space_map.get(p.get("space_id"), "未分类")
        if sp_label != current_space:
            st.markdown(f"#### {sp_label}")
            current_space = sp_label

        with st.expander(
            f"{'🟢' if p.get('is_active') else '🔴'} {p['product_name']}  "
            f"{'`' + p['series'] + '`' if p.get('series') else ''}  "
            f"¥{p.get('base_price', 0):,.0f}起/{p.get('unit','套')}",
            expanded=False
        ):
            with st.form(f"form_edit_prod_{p['id']}"):
                c1, c2 = st.columns(2)
                with c1:
                    new_pname = st.text_input("产品名称", value=p.get("product_name", ""))
                    new_pcode = st.text_input("产品编号", value=p.get("product_code", "") or "")
                    new_series = st.text_input("所属系列", value=p.get("series", "") or "")
                with c2:
                    new_price = st.number_input("基础起步价", value=float(p.get("base_price") or 0), step=100.0)
                    new_unit = st.text_input("计价单位", value=p.get("unit", "套"))
                    new_sort = st.number_input("排序", value=int(p.get("sort_order") or 0), step=1)
                new_desc = st.text_area("描述", value=p.get("description", "") or "", height=60)
                st.markdown("**📐 规格参数**（逗号分隔，留空表示不限）")
                ec1, ec2 = st.columns(2)
                with ec1:
                    new_height_opts = st.text_input("高度选项 (mm)",
                        value=p.get("height_options", "") or "",
                        placeholder="如 680,700,720")
                with ec2:
                    new_width_opts = st.text_input("宽度选项 (mm)",
                        value=p.get("width_options", "") or "",
                        placeholder="如 800,850,900,1000")
                new_active = st.checkbox("启用", value=p.get("is_active", True))

                c_save, c_del = st.columns(2)
                with c_save:
                    if st.form_submit_button("💾 保存", use_container_width=True):
                        try:
                            db.update("products", p["id"], {
                                "product_name": new_pname, "product_code": new_pcode,
                                "series": new_series, "description": new_desc,
                                "base_price": new_price, "unit": new_unit,
                                "sort_order": new_sort, "is_active": new_active,
                                "height_options": new_height_opts.strip() or None,
                                "width_options": new_width_opts.strip() or None,
                            })
                            st.success("已更新")
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新失败: {e}")
                with c_del:
                    if st.form_submit_button("🗑️ 删除", use_container_width=True):
                        try:
                            db.delete("products", p["id"])
                            st.success("已删除")
                            st.rerun()
                        except Exception as e:
                            st.error(f"删除失败: {e}")


# ──────────────────────────────────────────────────────────────
# Tab 3：部件价格
# ──────────────────────────────────────────────────────────────

PART_CATEGORIES = ["柜体", "门板", "台面", "五金", "电器", "灯光", "其他"]
PRICE_UNITS = ["元/延米", "元/㎡", "元/个", "元/组", "元/套", "元/扇", "元/米"]
PRICE_TYPES = {
    "fixed":    "💰 固定单价（数量 × 单价）",
    "area":     "📐 面积计价（高度 × 宽度 × 单价/㎡）",
    "included": "✅ 已包含（不另计费）",
}

def _tab_parts():
    st.subheader("部件 & 价格管理")
    st.caption("为每个产品配置可选部件和规格价格，报价时按需组合")

    stores = _load_stores()
    spaces = _load_spaces()

    if not stores:
        st.warning("请先在「门店管理」中创建门店")
        return

    store_opts = _store_options(stores)
    space_opts = _space_options(spaces)

    col1, col2, col3 = st.columns(3)
    with col1:
        sel_store_label = st.selectbox("门店", list(store_opts.keys()), key="parts_store")
    with col2:
        sel_space_label = st.selectbox("空间", ["全部空间"] + list(space_opts.keys()), key="parts_space")
    with col3:
        sel_space_id = space_opts.get(sel_space_label) if sel_space_label != "全部空间" else None
        products = _load_products(
            store_id=store_opts[sel_store_label],
            space_id=sel_space_id
        )
        prod_opts = {p["product_name"]: p["id"] for p in products}
        if not prod_opts:
            st.selectbox("产品", ["暂无产品"], key="parts_prod_empty")
            st.info("请先在「产品目录」中添加产品")
            return
        sel_prod_label = st.selectbox("产品", list(prod_opts.keys()), key="parts_prod")

    sel_prod_id = prod_opts[sel_prod_label]

    # ── 批量导入提示 ──
    st.markdown("---")

    # ── 新增部件 ──
    with st.expander("➕ 新增部件规格", expanded=False):
        with st.form("form_add_part"):
            c1, c2, c3 = st.columns(3)
            with c1:
                part_name = st.text_input("部件名称 *", placeholder="如 门板")
                part_cat = st.selectbox("部件分类", PART_CATEGORIES)
                is_required = st.checkbox("是否必选")
            with c2:
                spec_name = st.text_input("规格名称 *", placeholder="如 哑光钢灰平板门")
                spec_code = st.text_input("规格编号", placeholder="如 MP-AG-01")
                price_type_label = st.selectbox("计价方式", list(PRICE_TYPES.values()))
            with c3:
                price = st.number_input("单价 *", min_value=0.0, value=0.0, step=10.0,
                                        help="fixed=每个单价；area=每㎡单价；included=填0")
                price_unit = st.selectbox("价格单位", PRICE_UNITS)
                min_qty = st.number_input("最小数量", min_value=0.1, value=1.0, step=0.5)
            remark = st.text_input("备注说明", placeholder="如 需额外3个工作日")
            sort_order = st.number_input("排序", value=0, step=1)

            if st.form_submit_button("保存部件", type="primary"):
                # 反查 price_type key
                pt_key = next(k for k, v in PRICE_TYPES.items() if v == price_type_label)
                if not part_name.strip() or not spec_name.strip():
                    st.error("部件名称和规格名称不能为空")
                elif price <= 0 and pt_key != "included":
                    st.warning("⚠️ 单价为0，请确认是否正确")
                    _save_part(sel_prod_id, part_name, part_cat, spec_name, spec_code,
                               price, price_unit, min_qty, is_required, sort_order, remark, pt_key)
                else:
                    _save_part(sel_prod_id, part_name, part_cat, spec_name, spec_code,
                               price, price_unit, min_qty, is_required, sort_order, remark, pt_key)

    # ── 部件列表 ──
    st.markdown("---")
    parts = _load_parts(product_id=sel_prod_id)

    if not parts:
        st.info(f"「{sel_prod_label}」暂无部件，请新增")
        return

    st.markdown(f"**{sel_prod_label}** 共 {len(parts)} 个部件规格")

    # 按分类分组
    from itertools import groupby
    parts_sorted = sorted(parts, key=lambda x: (x.get("part_category") or "其他", x.get("sort_order") or 0))

    current_cat = None
    for part in parts_sorted:
        cat = part.get("part_category") or "其他"
        if cat != current_cat:
            st.markdown(f"**── {cat} ──**")
            current_cat = cat

        req_badge = " 🔴必选" if part.get("is_required") else ""
        pt = part.get("price_type") or "fixed"
        pt_icon = "📐" if pt == "area" else "✅" if pt == "included" else "💰"
        with st.expander(
            f"{'🔩' if cat=='五金' else '🪵' if cat in ('柜体','门板','台面') else '⚡' if cat=='电器' else '📌'} "
            f"{part['part_name']} · {part['spec_name']}  "
            f"{pt_icon} ¥{part.get('price',0):,.0f}/{part.get('price_unit','元')}{req_badge}",
            expanded=False
        ):
            with st.form(f"form_edit_part_{part['id']}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    n_pname = st.text_input("部件名称", value=part.get("part_name", ""))
                    n_cat = st.selectbox("分类", PART_CATEGORIES,
                                         index=PART_CATEGORIES.index(part.get("part_category", "其他"))
                                         if part.get("part_category") in PART_CATEGORIES else 0)
                    n_req = st.checkbox("必选", value=part.get("is_required", False))
                with c2:
                    n_spec = st.text_input("规格名称", value=part.get("spec_name", ""))
                    n_code = st.text_input("规格编号", value=part.get("spec_code", "") or "")
                    pt_labels = list(PRICE_TYPES.values())
                    pt_keys   = list(PRICE_TYPES.keys())
                    cur_pt_idx = pt_keys.index(pt) if pt in pt_keys else 0
                    n_pt_label = st.selectbox("计价方式", pt_labels, index=cur_pt_idx)
                with c3:
                    n_price = st.number_input("单价", value=float(part.get("price") or 0), step=10.0)
                    n_punit = st.selectbox("价格单位", PRICE_UNITS,
                                           index=PRICE_UNITS.index(part.get("price_unit", "元/延米"))
                                           if part.get("price_unit") in PRICE_UNITS else 0)
                    n_minqty = st.number_input("最小数量", value=float(part.get("min_qty") or 1), step=0.5)
                n_remark = st.text_input("备注", value=part.get("remark", "") or "")
                n_sort = st.number_input("排序", value=int(part.get("sort_order") or 0), step=1)
                n_active = st.checkbox("启用", value=part.get("is_active", True))

                c_save, c_del = st.columns(2)
                with c_save:
                    if st.form_submit_button("💾 保存", use_container_width=True):
                        n_pt_key = pt_keys[pt_labels.index(n_pt_label)]
                        try:
                            db.update("product_parts", part["id"], {
                                "part_name": n_pname, "part_category": n_cat,
                                "spec_name": n_spec, "spec_code": n_code,
                                "price": n_price, "price_unit": n_punit,
                                "price_type": n_pt_key,
                                "min_qty": n_minqty, "is_required": n_req,
                                "sort_order": n_sort, "remark": n_remark,
                                "is_active": n_active
                            })
                            st.success("已更新")
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新失败: {e}")
                with c_del:
                    if st.form_submit_button("🗑️ 删除", use_container_width=True):
                        try:
                            db.delete("product_parts", part["id"])
                            st.success("已删除")
                            st.rerun()
                        except Exception as e:
                            st.error(f"删除失败: {e}")


def _save_part(prod_id, part_name, part_cat, spec_name, spec_code,
               price, price_unit, min_qty, is_required, sort_order, remark,
               price_type="fixed"):
    try:
        db.insert("product_parts", {
            "product_id": prod_id,
            "part_name": part_name.strip(),
            "part_category": part_cat,
            "spec_name": spec_name.strip(),
            "spec_code": spec_code.strip(),
            "price": price,
            "price_unit": price_unit,
            "price_type": price_type,
            "min_qty": min_qty,
            "is_required": is_required,
            "sort_order": sort_order,
            "remark": remark.strip(),
            "is_active": True
        })
        st.success(f"✅ 部件「{part_name} · {spec_name}」已保存")
        st.rerun()
    except Exception as e:
        st.error(f"保存失败: {e}")


# ──────────────────────────────────────────────────────────────
# Tab 4：空间管理
# ──────────────────────────────────────────────────────────────

def _tab_spaces():
    st.subheader("空间类型管理")
    st.caption("管理产品归属的空间分类（如厨房、衣帽间等）")

    spaces = _load_spaces()

    with st.expander("➕ 新增空间", expanded=False):
        with st.form("form_add_space"):
            c1, c2, c3 = st.columns(3)
            with c1:
                sp_name = st.text_input("空间名称 *", placeholder="如 阳台柜")
            with c2:
                sp_icon = st.text_input("图标 emoji", value="🏠", placeholder="一个 emoji")
            with c3:
                sp_sort = st.number_input("排序", value=len(spaces) + 1, step=1)
            if st.form_submit_button("保存空间", type="primary"):
                if not sp_name.strip():
                    st.error("空间名称不能为空")
                else:
                    try:
                        db.insert("product_spaces", {
                            "space_name": sp_name.strip(),
                            "space_icon": sp_icon.strip() or "🏠",
                            "sort_order": sp_sort,
                            "is_active": True
                        })
                        st.success(f"✅ 空间「{sp_name}」已添加")
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加失败: {e}")

    st.markdown("---")
    for sp in spaces:
        with st.expander(
            f"{sp.get('space_icon','🏠')} {sp['space_name']}  排序:{sp.get('sort_order',0)}",
            expanded=False
        ):
            with st.form(f"form_edit_space_{sp['id']}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    n_name = st.text_input("名称", value=sp.get("space_name", ""))
                with c2:
                    n_icon = st.text_input("图标", value=sp.get("space_icon", "🏠"))
                with c3:
                    n_sort = st.number_input("排序", value=int(sp.get("sort_order") or 0), step=1)
                n_active = st.checkbox("启用", value=sp.get("is_active", True))

                c_save, c_del = st.columns(2)
                with c_save:
                    if st.form_submit_button("💾 保存", use_container_width=True):
                        try:
                            db.update("product_spaces", sp["id"], {
                                "space_name": n_name, "space_icon": n_icon,
                                "sort_order": n_sort, "is_active": n_active
                            })
                            st.success("已更新")
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新失败: {e}")
                with c_del:
                    if st.form_submit_button("🗑️ 删除", use_container_width=True):
                        try:
                            db.delete("product_spaces", sp["id"])
                            st.success("已删除")
                            st.rerun()
                        except Exception as e:
                            st.error(f"删除失败: {e}")


# ──────────────────────────────────────────────────────────────
# Tab 5：数据诊断
# ──────────────────────────────────────────────────────────────

def _tab_diagnostics():
    st.subheader("🔍 数据诊断")
    st.caption("检查产品与部件的关联关系，排查「无部件配置」问题")

    stores = _load_stores()
    spaces = _load_spaces()

    if not stores:
        st.warning("暂无门店数据")
        return

    store_opts = _store_options(stores)
    sel_store_label = st.selectbox("选择门店", list(store_opts.keys()), key="diag_store")
    sel_store_id = store_opts[sel_store_label]

    # 加载该门店所有产品
    try:
        all_products = db.select("products", filters={"store_id": sel_store_id}, order_by="space_id")
    except Exception as e:
        st.error(f"加载产品失败: {e}")
        return

    if not all_products:
        st.info("该门店暂无产品")
        return

    # 构建空间名称映射
    space_map = {s["id"]: s["space_name"] for s in spaces}

    st.markdown(f"**共 {len(all_products)} 个产品**")
    st.markdown("---")

    for prod in all_products:
        pid = prod["id"]
        pname = prod.get("product_name", "未知")
        space_name = space_map.get(prod.get("space_id", ""), "未知空间")

        # 查该产品的部件数量
        try:
            parts = db.select("product_parts", filters={"product_id": pid})
            part_count = len(parts) if parts else 0
        except Exception:
            part_count = -1

        status_icon = "✅" if part_count > 0 else "❌"
        with st.expander(f"{status_icon} [{space_name}] {pname} — {part_count} 个部件", expanded=(part_count == 0)):
            st.code(f"product_id = {pid}", language="text")
            col_a, col_b = st.columns(2)
            col_a.write(f"**门店**：{sel_store_label}")
            col_b.write(f"**空间**：{space_name}")
            if part_count == 0:
                st.warning("⚠️ 该产品没有部件！请在「部件价格」Tab 里选中此产品并添加部件。")
                st.caption(f"提示：在「部件价格」Tab 中，选择门店「{sel_store_label}」→ 空间「{space_name}」→ 产品「{pname}」，然后新增部件规格。")
            else:
                for p in parts:
                    st.markdown(f"- `{p.get('part_name','')}` · {p.get('spec_name','')} · ¥{p.get('price',0)}/{p.get('price_unit','元')}")
