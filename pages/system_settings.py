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

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏪 门店管理",
        "📦 产品目录",
        "🔩 部件价格",
        "🗂️ 空间管理",
        "💎 报价配置",
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
        _tab_quoting_config()
    with tab6:
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
                                # 1. 把该门店下的报价单迁移到 DEFAULT 门店
                                default_stores = db.select("stores", filters={"store_code": "DEFAULT"})
                                if default_stores:
                                    default_id = default_stores[0]["id"]
                                    # 迁移 quotes
                                    try:
                                        db.supabase.table("quotes").update(
                                            {"store_id": default_id}
                                        ).eq("store_id", s["id"]).execute()
                                    except Exception:
                                        pass
                                    # 迁移 products（产品目录）
                                    try:
                                        db.supabase.table("products").update(
                                            {"store_id": default_id}
                                        ).eq("store_id", s["id"]).execute()
                                    except Exception:
                                        pass
                                # 2. 删除门店
                                db.delete("stores", s["id"])
                                st.success("✅ 门店已删除，关联报价单已迁移至默认门店")
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

# ──────────────────────────────────────────────────────────────
# Tab 5：报价配置（新系统）
# ──────────────────────────────────────────────────────────────

def _tab_quoting_config():
    st.subheader("💎 报价配置")
    st.caption("管理产品大类、材质单价、台面加项、五金选项——全部动态配置，无需改代码")

    sub1, sub2, sub3, sub4, sub5 = st.tabs([
        "🏷️ 产品大类",
        "🗄️ 柜体材质",
        "🎨 门板/台面材质",
        "🔧 台面工艺加项",
        "🔩 五金选项",
    ])
    with sub1:
        _qc_product_types()
    with sub2:
        _qc_cabinet_body()
    with sub3:
        _qc_surface_materials()
    with sub4:
        _qc_countertop_extras()
    with sub5:
        _qc_hardware_options()


def _qc_product_types():
    """产品大类管理"""
    st.markdown("##### 产品大类")
    st.caption("定义产品类型（如衣柜、橱柜），并指定其计价特性")

    try:
        pts = db.select("product_types", order_by="sort_order")
    except Exception:
        pts = []

    # 新增
    with st.expander("➕ 新增产品大类", expanded=False):
        with st.form("form_add_pt"):
            c1, c2 = st.columns(2)
            with c1:
                pt_name = st.text_input("产品名称 *", placeholder="如 衣柜")
                pt_cat = st.selectbox("类型", ["B - 通用柜（投影面积计价）", "A - 橱柜（延米计价）"])
            with c2:
                pt_has_ct = st.checkbox("有台面（如餐边柜、浴室柜）")
                pt_has_upper = st.checkbox("有上柜（仅橱柜）")
                pt_sort = st.number_input("排序", value=len(pts)+1, step=1)
            if st.form_submit_button("保存", type="primary"):
                if not pt_name.strip():
                    st.error("名称不能为空")
                else:
                    try:
                        cat = "A" if pt_cat.startswith("A") else "B"
                        db.insert("product_types", {
                            "name": pt_name.strip(),
                            "category": cat,
                            "has_countertop": pt_has_ct,
                            "has_upper_cabinet": pt_has_upper,
                            "sort_order": pt_sort,
                            "is_active": True
                        })
                        st.success(f"✅ 已添加：{pt_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"失败: {e}")

    st.markdown("---")
    if not pts:
        st.info("暂无产品大类，请先新增")
        return

    for pt in pts:
        cat_label = "A-橱柜" if pt.get("category") == "A" else "B-通用柜"
        tags = []
        if pt.get("has_countertop"): tags.append("有台面")
        if pt.get("has_upper_cabinet"): tags.append("有上柜")
        tag_str = "  ".join(f"`{t}`" for t in tags) if tags else ""

        with st.expander(
            f"{'🟢' if pt.get('is_active') else '🔴'} {pt['name']}  "
            f"[{cat_label}]  {tag_str}",
            expanded=False
        ):
            with st.form(f"form_edit_pt_{pt['id']}"):
                c1, c2 = st.columns(2)
                with c1:
                    n_name = st.text_input("名称", value=pt.get("name",""))
                    n_cat_opts = ["B - 通用柜（投影面积计价）", "A - 橱柜（延米计价）"]
                    cur_cat_idx = 1 if pt.get("category") == "A" else 0
                    n_cat = st.selectbox("类型", n_cat_opts, index=cur_cat_idx)
                with c2:
                    n_has_ct = st.checkbox("有台面", value=pt.get("has_countertop", False))
                    n_has_upper = st.checkbox("有上柜", value=pt.get("has_upper_cabinet", False))
                    n_sort = st.number_input("排序", value=int(pt.get("sort_order") or 0), step=1)
                n_active = st.checkbox("启用", value=pt.get("is_active", True))

                c_s, c_d = st.columns(2)
                with c_s:
                    if st.form_submit_button("💾 保存", use_container_width=True):
                        try:
                            db.update("product_types", pt["id"], {
                                "name": n_name,
                                "category": "A" if n_cat.startswith("A") else "B",
                                "has_countertop": n_has_ct,
                                "has_upper_cabinet": n_has_upper,
                                "sort_order": n_sort,
                                "is_active": n_active
                            })
                            st.success("已更新")
                            st.rerun()
                        except Exception as e:
                            st.error(f"失败: {e}")
                with c_d:
                    if st.form_submit_button("🗑️ 删除", use_container_width=True):
                        try:
                            db.delete("product_types", pt["id"])
                            st.success("已删除")
                            st.rerun()
                        except Exception as e:
                            st.error(f"失败: {e}")


def _qc_cabinet_body():
    """柜体材质单价管理"""
    st.markdown("##### 柜体材质单价")
    st.caption("为每个产品大类配置柜体材质和单价。A类橱柜单位：元/m；B类通用柜单位：元/m²")

    try:
        pts = db.select("product_types", filters={"is_active": True}, order_by="sort_order")
        prices = db.select("cabinet_body_prices", order_by="sort_order")
    except Exception as e:
        st.error(f"加载失败: {e}")
        return

    pt_opts = {pt["name"]: pt for pt in pts} if pts else {}

    with st.expander("➕ 新增柜体材质", expanded=False):
        with st.form("form_add_body"):
            c1, c2, c3 = st.columns(3)
            with c1:
                if pt_opts:
                    sel_pt = st.selectbox("产品大类 *", list(pt_opts.keys()))
                    sel_pt_id = pt_opts[sel_pt]["id"]
                    sel_pt_cat = pt_opts[sel_pt]["category"]
                else:
                    st.warning("请先添加产品大类")
                    sel_pt_id = None
                    sel_pt_cat = "B"
            with c2:
                b_mat = st.text_input("材质名称 *", placeholder="如 多层实木板")
                b_pos = st.text_input("位置", value="柜体", placeholder="下柜/上柜/柜体")
            with c3:
                default_unit = "元/m" if sel_pt_cat == "A" else "元/m²"
                b_unit = st.text_input("单位", value=default_unit)
                b_price = st.number_input("单价 *", min_value=0.0, value=0.0, step=50.0)
                b_sort = st.number_input("排序", value=0, step=1)
            if st.form_submit_button("保存", type="primary"):
                if not b_mat.strip() or not sel_pt_id:
                    st.error("材质名称和产品大类不能为空")
                else:
                    try:
                        db.insert("cabinet_body_prices", {
                            "product_type_id": sel_pt_id,
                            "position": b_pos.strip() or "柜体",
                            "material": b_mat.strip(),
                            "unit": b_unit.strip(),
                            "price": b_price,
                            "sort_order": b_sort,
                            "is_active": True
                        })
                        st.success(f"✅ 已添加：{b_mat}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"失败: {e}")

    st.markdown("---")

    # 按产品大类分组展示
    pt_map = {pt["id"]: pt["name"] for pt in pts}
    from itertools import groupby
    prices_sorted = sorted(prices, key=lambda x: (pt_map.get(x.get("product_type_id",""), ""), x.get("sort_order") or 0))

    current_group = None
    for bp in prices_sorted:
        group = pt_map.get(bp.get("product_type_id",""), "未分类")
        if group != current_group:
            st.markdown(f"**── {group} ──**")
            current_group = group

        with st.expander(
            f"{'🟢' if bp.get('is_active') else '🔴'} [{bp.get('position','柜体')}] "
            f"{bp['material']}  ¥{float(bp.get('price',0)):,.0f}/{bp.get('unit','')}",
            expanded=False
        ):
            with st.form(f"form_edit_body_{bp['id']}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    n_mat = st.text_input("材质", value=bp.get("material",""))
                    n_pos = st.text_input("位置", value=bp.get("position","柜体"))
                with c2:
                    n_unit = st.text_input("单位", value=bp.get("unit","元/m²"))
                    n_price = st.number_input("单价", value=float(bp.get("price") or 0), step=50.0)
                with c3:
                    n_sort = st.number_input("排序", value=int(bp.get("sort_order") or 0), step=1)
                    n_active = st.checkbox("启用", value=bp.get("is_active", True))
                c_s, c_d = st.columns(2)
                with c_s:
                    if st.form_submit_button("💾 保存", use_container_width=True):
                        try:
                            db.update("cabinet_body_prices", bp["id"], {
                                "material": n_mat, "position": n_pos,
                                "unit": n_unit, "price": n_price,
                                "sort_order": n_sort, "is_active": n_active
                            })
                            st.success("已更新")
                            st.rerun()
                        except Exception as e:
                            st.error(f"失败: {e}")
                with c_d:
                    if st.form_submit_button("🗑️ 删除", use_container_width=True):
                        try:
                            db.delete("cabinet_body_prices", bp["id"])
                            st.success("已删除")
                            st.rerun()
                        except Exception as e:
                            st.error(f"失败: {e}")


def _qc_surface_materials():
    """门板 + 台面材质管理（合并一页）"""
    st.markdown("##### 门板 & 台面材质")
    st.caption("门板单位：元/m²；台面单位：元/m（延米）。随时增删，立即生效")

    try:
        materials = db.select("surface_materials", order_by="sort_order")
    except Exception as e:
        st.error(f"加载失败: {e}")
        return

    door_mats = [m for m in materials if m.get("category") == "门板"]
    ct_mats   = [m for m in materials if m.get("category") == "台面"]

    # 新增
    with st.expander("➕ 新增材质", expanded=False):
        with st.form("form_add_surface"):
            c1, c2, c3 = st.columns(3)
            with c1:
                sm_cat = st.selectbox("类别 *", ["门板", "台面"])
                sm_name = st.text_input("材质名称 *", placeholder="如 肤感烤漆 / 岩板20mm")
            with c2:
                default_unit = "元/m²" if sm_cat == "门板" else "元/m"
                sm_unit = st.text_input("单位", value=default_unit)
                sm_price = st.number_input("单价 *", min_value=0.0, value=0.0, step=10.0)
            with c3:
                sm_sort = st.number_input("排序", value=len(materials)+1, step=1)
            if st.form_submit_button("保存", type="primary"):
                if not sm_name.strip():
                    st.error("材质名称不能为空")
                else:
                    try:
                        db.insert("surface_materials", {
                            "category": sm_cat,
                            "name": sm_name.strip(),
                            "unit": sm_unit.strip(),
                            "price": sm_price,
                            "sort_order": sm_sort,
                            "is_active": True
                        })
                        st.success(f"✅ 已添加：{sm_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"失败: {e}")

    st.markdown("---")

    def _render_material_list(mat_list, label):
        st.markdown(f"**{label}**（共{len(mat_list)}项）")
        for m in mat_list:
            with st.expander(
                f"{'🟢' if m.get('is_active') else '🔴'} {m['name']}  "
                f"¥{float(m.get('price',0)):,.0f}/{m.get('unit','')}",
                expanded=False
            ):
                with st.form(f"form_edit_sm_{m['id']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        n_name = st.text_input("名称", value=m.get("name",""))
                        n_unit = st.text_input("单位", value=m.get("unit",""))
                    with c2:
                        n_price = st.number_input("单价", value=float(m.get("price") or 0), step=10.0)
                        n_sort = st.number_input("排序", value=int(m.get("sort_order") or 0), step=1)
                    n_active = st.checkbox("启用", value=m.get("is_active", True))
                    c_s, c_d = st.columns(2)
                    with c_s:
                        if st.form_submit_button("💾 保存", use_container_width=True):
                            try:
                                db.update("surface_materials", m["id"], {
                                    "name": n_name, "unit": n_unit,
                                    "price": n_price, "sort_order": n_sort,
                                    "is_active": n_active
                                })
                                st.success("已更新")
                                st.rerun()
                            except Exception as e:
                                st.error(f"失败: {e}")
                    with c_d:
                        if st.form_submit_button("🗑️ 删除", use_container_width=True):
                            try:
                                db.delete("surface_materials", m["id"])
                                st.success("已删除")
                                st.rerun()
                            except Exception as e:
                                st.error(f"失败: {e}")

    col_a, col_b = st.columns(2)
    with col_a:
        _render_material_list(door_mats, "🎨 门板材质")
    with col_b:
        _render_material_list(ct_mats, "🪨 台面材质")


def _qc_countertop_extras():
    """台面工艺加项管理"""
    st.markdown("##### 台面工艺加项")
    st.caption("可勾选的台面加工选项，如前挡水、圆弧边等。is_default=true 表示默认含在台面基础价里")

    try:
        extras = db.select("countertop_extras", order_by="sort_order")
    except Exception as e:
        st.error(f"加载失败: {e}")
        return

    with st.expander("➕ 新增加项", expanded=False):
        with st.form("form_add_ct_extra"):
            c1, c2, c3 = st.columns(3)
            with c1:
                ex_name = st.text_input("加项名称 *", placeholder="如 前挡水")
            with c2:
                ex_unit = st.text_input("单位", value="元/m")
                ex_price = st.number_input("单价", min_value=0.0, value=0.0, step=5.0)
            with c3:
                ex_default = st.checkbox("默认含（价格填0）")
                ex_sort = st.number_input("排序", value=len(extras)+1, step=1)
            if st.form_submit_button("保存", type="primary"):
                if not ex_name.strip():
                    st.error("名称不能为空")
                else:
                    try:
                        db.insert("countertop_extras", {
                            "name": ex_name.strip(),
                            "unit": ex_unit.strip(),
                            "price": ex_price,
                            "is_default": ex_default,
                            "sort_order": ex_sort,
                            "is_active": True
                        })
                        st.success(f"✅ 已添加：{ex_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"失败: {e}")

    st.markdown("---")
    for ex in extras:
        default_tag = " `默认含`" if ex.get("is_default") else ""
        with st.expander(
            f"{'🟢' if ex.get('is_active') else '🔴'} {ex['name']}"
            f"{default_tag}  ¥{float(ex.get('price',0)):,.0f}/{ex.get('unit','')}",
            expanded=False
        ):
            with st.form(f"form_edit_ct_ex_{ex['id']}"):
                c1, c2 = st.columns(2)
                with c1:
                    n_name = st.text_input("名称", value=ex.get("name",""))
                    n_unit = st.text_input("单位", value=ex.get("unit","元/m"))
                with c2:
                    n_price = st.number_input("单价", value=float(ex.get("price") or 0), step=5.0)
                    n_sort = st.number_input("排序", value=int(ex.get("sort_order") or 0), step=1)
                n_default = st.checkbox("默认含", value=ex.get("is_default", False))
                n_active = st.checkbox("启用", value=ex.get("is_active", True))
                c_s, c_d = st.columns(2)
                with c_s:
                    if st.form_submit_button("💾 保存", use_container_width=True):
                        try:
                            db.update("countertop_extras", ex["id"], {
                                "name": n_name, "unit": n_unit,
                                "price": n_price, "sort_order": n_sort,
                                "is_default": n_default, "is_active": n_active
                            })
                            st.success("已更新")
                            st.rerun()
                        except Exception as e:
                            st.error(f"失败: {e}")
                with c_d:
                    if st.form_submit_button("🗑️ 删除", use_container_width=True):
                        try:
                            db.delete("countertop_extras", ex["id"])
                            st.success("已删除")
                            st.rerun()
                        except Exception as e:
                            st.error(f"失败: {e}")


def _qc_hardware_options():
    """五金选项管理"""
    st.markdown("##### 五金选项")
    st.caption("管理可选五金配件，is_default=true 会在报价页面默认勾选。applicable_to 控制显示范围")

    try:
        hws = db.select("hardware_options", order_by="sort_order")
    except Exception as e:
        st.error(f"加载失败: {e}")
        return

    with st.expander("➕ 新增五金", expanded=False):
        with st.form("form_add_hw"):
            c1, c2, c3 = st.columns(3)
            with c1:
                hw_name = st.text_input("五金名称 *", placeholder="如 抽屉（普通）")
                hw_applicable = st.text_input("适用范围", value="通用",
                                               placeholder="通用 / 橱柜 / 衣柜")
            with c2:
                hw_unit = st.text_input("单位", value="元/个")
                hw_price = st.number_input("单价", min_value=0.0, value=0.0, step=5.0)
            with c3:
                hw_default = st.checkbox("默认勾选")
                hw_sort = st.number_input("排序", value=len(hws)+1, step=1)
            if st.form_submit_button("保存", type="primary"):
                if not hw_name.strip():
                    st.error("名称不能为空")
                else:
                    try:
                        db.insert("hardware_options", {
                            "name": hw_name.strip(),
                            "unit": hw_unit.strip(),
                            "price": hw_price,
                            "is_default": hw_default,
                            "applicable_to": hw_applicable.strip() or "通用",
                            "sort_order": hw_sort,
                            "is_active": True
                        })
                        st.success(f"✅ 已添加：{hw_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"失败: {e}")

    st.markdown("---")
    for hw in hws:
        default_tag = " `默认`" if hw.get("is_default") else ""
        with st.expander(
            f"{'🟢' if hw.get('is_active') else '🔴'} {hw['name']}"
            f"{default_tag}  [{hw.get('applicable_to','通用')}]  "
            f"¥{float(hw.get('price',0)):,.0f}/{hw.get('unit','')}",
            expanded=False
        ):
            with st.form(f"form_edit_hw_{hw['id']}"):
                c1, c2 = st.columns(2)
                with c1:
                    n_name = st.text_input("名称", value=hw.get("name",""))
                    n_unit = st.text_input("单位", value=hw.get("unit","元/个"))
                    n_applicable = st.text_input("适用范围", value=hw.get("applicable_to","通用"))
                with c2:
                    n_price = st.number_input("单价", value=float(hw.get("price") or 0), step=5.0)
                    n_sort = st.number_input("排序", value=int(hw.get("sort_order") or 0), step=1)
                n_default = st.checkbox("默认勾选", value=hw.get("is_default", False))
                n_active = st.checkbox("启用", value=hw.get("is_active", True))
                c_s, c_d = st.columns(2)
                with c_s:
                    if st.form_submit_button("💾 保存", use_container_width=True):
                        try:
                            db.update("hardware_options", hw["id"], {
                                "name": n_name, "unit": n_unit,
                                "price": n_price, "applicable_to": n_applicable,
                                "sort_order": n_sort, "is_default": n_default,
                                "is_active": n_active
                            })
                            st.success("已更新")
                            st.rerun()
                        except Exception as e:
                            st.error(f"失败: {e}")
                with c_d:
                    if st.form_submit_button("🗑️ 删除", use_container_width=True):
                        try:
                            db.delete("hardware_options", hw["id"])
                            st.success("已删除")
                            st.rerun()
                        except Exception as e:
                            st.error(f"失败: {e}")


# ──────────────────────────────────────────────────────────────
# Tab 6：数据诊断（原Tab 5）
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
