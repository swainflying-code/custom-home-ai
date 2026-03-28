-- ============================================================================
-- BINK 智能报价模块 - 数据库架构
-- 在 Supabase SQL Editor 中执行此文件
-- ============================================================================

-- 1. 门店配置表（每个门店/经销商独立的产品目录和价格体系）
create table if not exists stores (
    id uuid primary key default gen_random_uuid(),
    store_code text unique not null,       -- 门店编号，如 BK001
    store_name text not null,              -- 门店名称
    city text,                             -- 城市
    contact_person text,                   -- 联系人
    contact_phone text,
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_stores_code on stores(store_code);

-- 插入默认门店
insert into stores (store_code, store_name, city) values
    ('DEFAULT', '默认门店', '总部')
on conflict (store_code) do nothing;


-- 2. 产品空间表（厨房、衣帽间、书房…）
create table if not exists product_spaces (
    id uuid primary key default gen_random_uuid(),
    space_name text not null,              -- 空间名称
    space_icon text default '🏠',          -- 图标 emoji
    sort_order integer default 0,          -- 排序
    is_active boolean default true,
    created_at timestamptz default now()
);
create index if not exists idx_spaces_sort on product_spaces(sort_order);

insert into product_spaces (space_name, space_icon, sort_order) values
    ('厨房', '🍳', 1),
    ('主卧衣帽间', '👔', 2),
    ('次卧衣柜', '👗', 3),
    ('书房书柜', '📚', 4),
    ('客厅电视柜', '📺', 5),
    ('卫生间浴室柜', '🚿', 6),
    ('玄关鞋柜', '🚪', 7),
    ('其他定制', '📦', 8)
on conflict do nothing;


-- 3. 产品系列表（每个空间下的产品线，与门店关联实现差异化目录）
create table if not exists products (
    id uuid primary key default gen_random_uuid(),
    store_id uuid references stores(id) on delete cascade,
    space_id uuid references product_spaces(id) on delete cascade,
    product_name text not null,            -- 产品系列名，如「轻奢岛台款」
    product_code text,                     -- 产品编号
    series text,                           -- 所属系列，如「经典系列」「高定系列」
    description text,                      -- 产品描述
    cover_image text,                      -- 封面图URL
    base_price numeric(10,2) default 0,    -- 基础起步价（含安装）
    unit text default '套',               -- 计价单位
    sort_order integer default 0,
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_products_store on products(store_id);
create index if not exists idx_products_space on products(space_id);
create index if not exists idx_products_sort on products(sort_order);


-- 4. 产品部件表（每个产品下的部件/配置项，可单独计价）
create table if not exists product_parts (
    id uuid primary key default gen_random_uuid(),
    product_id uuid references products(id) on delete cascade,
    part_name text not null,               -- 部件名称，如「门板」「拉手」「铰链」
    part_category text,                    -- 部件分类，如「柜体」「五金」「台面」「电器」
    spec_name text not null,               -- 规格名称，如「哑光钢灰 / 平板门」
    spec_code text,                        -- 规格编号
    price numeric(10,2) default 0,         -- 单价
    price_unit text default '元/延米',     -- 价格单位，如 元/延米、元/个、元/㎡
    min_qty numeric(6,2) default 1,        -- 最小数量
    is_required boolean default false,     -- 是否必选
    is_active boolean default true,
    sort_order integer default 0,
    remark text,                           -- 备注说明
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_parts_product on product_parts(product_id);
create index if not exists idx_parts_category on product_parts(part_category);


-- 5. 报价单主表
create table if not exists quotes (
    id uuid primary key default gen_random_uuid(),
    quote_no text unique not null,         -- 报价单号，如 Q2026032800001
    store_id uuid references stores(id),
    customer_id uuid references customers(id) on delete set null,
    customer_name text,
    customer_phone text,
    designer_name text,                    -- 设计师姓名
    house_area text,                       -- 房屋面积
    house_type text,                       -- 户型
    quote_date date default current_date,
    valid_days integer default 30,         -- 报价有效天数
    subtotal numeric(12,2) default 0,      -- 小计
    discount_rate numeric(4,2) default 1.0,-- 折扣率，如 0.9 = 九折
    discount_amount numeric(12,2) default 0,-- 折扣金额
    total_amount numeric(12,2) default 0,  -- 最终总价
    status text default 'draft',           -- draft/sent/accepted/rejected
    remark text,                           -- 备注
    created_by text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);
create index if not exists idx_quotes_no on quotes(quote_no);
create index if not exists idx_quotes_customer on quotes(customer_id);
create index if not exists idx_quotes_status on quotes(status);
create index if not exists idx_quotes_date on quotes(quote_date desc);


-- 6. 报价单明细表
create table if not exists quote_items (
    id uuid primary key default gen_random_uuid(),
    quote_id uuid references quotes(id) on delete cascade,
    space_name text,                       -- 空间名称（冗余，方便查询）
    product_name text,                     -- 产品名称（冗余）
    product_id uuid references products(id) on delete set null,
    part_id uuid references product_parts(id) on delete set null,
    part_name text,                        -- 部件名称（冗余）
    spec_name text,                        -- 规格名称（冗余）
    unit_price numeric(10,2) default 0,    -- 单价（下单时锁定）
    price_unit text,                       -- 价格单位
    quantity numeric(8,2) default 1,       -- 数量/尺寸
    line_total numeric(12,2) default 0,    -- 行小计
    remark text,
    sort_order integer default 0,
    created_at timestamptz default now()
);
create index if not exists idx_quote_items_quote on quote_items(quote_id);


-- 自动更新 updated_at 触发器
create trigger update_stores_updated_at
    before update on stores for each row execute function update_updated_at_column();

create trigger update_products_updated_at
    before update on products for each row execute function update_updated_at_column();

create trigger update_parts_updated_at
    before update on product_parts for each row execute function update_updated_at_column();

create trigger update_quotes_updated_at
    before update on quotes for each row execute function update_updated_at_column();

-- ============================================================================
-- 查看创建结果
select tablename from pg_tables where schemaname = 'public' order by tablename;
