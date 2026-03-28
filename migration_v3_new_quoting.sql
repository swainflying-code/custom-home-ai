-- ============================================================
-- 全屋定制智能报价系统 v3 — 新建表结构
-- 请在 Supabase SQL Editor 中完整执行此文件
-- ============================================================

-- ① 产品大类表
CREATE TABLE IF NOT EXISTS product_types (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text NOT NULL,                        -- 如 厨房橱柜、衣柜、鞋柜
    category    text NOT NULL DEFAULT 'B',            -- A=橱柜, B=通用柜
    has_countertop    boolean NOT NULL DEFAULT false, -- 是否有台面
    has_upper_cabinet boolean NOT NULL DEFAULT false, -- 是否有上柜（仅A类）
    sort_order  integer NOT NULL DEFAULT 0,
    is_active   boolean NOT NULL DEFAULT true,
    created_at  timestamptz DEFAULT now(),
    updated_at  timestamptz DEFAULT now()
);

-- ② 柜体材质单价表
CREATE TABLE IF NOT EXISTS cabinet_body_prices (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    product_type_id uuid REFERENCES product_types(id) ON DELETE CASCADE,
    position        text NOT NULL DEFAULT '柜体',     -- 下柜/上柜/柜体
    material        text NOT NULL,                    -- 如 不锈钢304、多层实木板
    unit            text NOT NULL DEFAULT '元/m',     -- A类:元/m, B类:元/m²
    price           numeric(10,2) NOT NULL DEFAULT 0,
    sort_order      integer NOT NULL DEFAULT 0,
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz DEFAULT now(),
    updated_at      timestamptz DEFAULT now()
);

-- ③ 表面材质通用表（门板 + 台面 共用，category区分）
CREATE TABLE IF NOT EXISTS surface_materials (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    category    text NOT NULL,    -- '门板' 或 '台面'
    name        text NOT NULL,    -- 如 肤感烤漆、石英石20mm
    unit        text NOT NULL,    -- 元/m² 或 元/m
    price       numeric(10,2) NOT NULL DEFAULT 0,
    sort_order  integer NOT NULL DEFAULT 0,
    is_active   boolean NOT NULL DEFAULT true,
    created_at  timestamptz DEFAULT now(),
    updated_at  timestamptz DEFAULT now()
);

-- ④ 台面工艺加项表
CREATE TABLE IF NOT EXISTS countertop_extras (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text NOT NULL,         -- 如 前挡水、圆弧边
    unit        text NOT NULL DEFAULT '元/m',
    price       numeric(10,2) NOT NULL DEFAULT 0,
    is_default  boolean NOT NULL DEFAULT false,  -- 默认含=true
    sort_order  integer NOT NULL DEFAULT 0,
    is_active   boolean NOT NULL DEFAULT true,
    created_at  timestamptz DEFAULT now(),
    updated_at  timestamptz DEFAULT now()
);

-- ⑤ 五金选项表
CREATE TABLE IF NOT EXISTS hardware_options (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            text NOT NULL,          -- 如 抽屉、挂衣杆
    unit            text NOT NULL,          -- 元/个、元/条、元/m
    price           numeric(10,2) NOT NULL DEFAULT 0,
    is_default      boolean NOT NULL DEFAULT false,  -- 标配=true
    applicable_to   text DEFAULT '通用',    -- 通用/橱柜/衣柜 等
    sort_order      integer NOT NULL DEFAULT 0,
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz DEFAULT now(),
    updated_at      timestamptz DEFAULT now()
);

-- ⑥ 报价单主表（复用现有 quotes 表，无需重建）
-- 现有 quotes 表字段已满足需求

-- ⑦ 新版报价明细表
CREATE TABLE IF NOT EXISTS quote_items_v2 (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id        uuid REFERENCES quotes(id) ON DELETE CASCADE,
    sort_order      integer NOT NULL DEFAULT 0,

    -- 基本信息
    space_name      text,                   -- 如 厨房、主卧
    product_type_id uuid REFERENCES product_types(id),
    product_type_name text,                 -- 冗余存名称，防止改名后报价单变
    custom_label    text,                   -- 自定义备注，如 岛台区

    -- 尺寸输入
    length_m        numeric(8,3),           -- A类橱柜：操作台延米
    width_m         numeric(8,3),           -- B类：宽度(m)
    height_m        numeric(8,3),           -- B类：高度(m)

    -- 柜体
    body_material       text,
    body_unit_price     numeric(10,2),
    body_subtotal       numeric(10,2),

    -- 上柜（仅A类）
    has_upper_cabinet   boolean DEFAULT false,
    upper_material      text,
    upper_unit_price    numeric(10,2),
    upper_subtotal      numeric(10,2),

    -- 门板
    door_type           text,               -- 平开门/推拉门/无门
    door_material       text,
    door_area_m2        numeric(8,3),       -- 计算出来的门板面积
    door_unit_price     numeric(10,2),
    door_subtotal       numeric(10,2),

    -- 台面（有台面的产品）
    countertop_material     text,
    countertop_length_m     numeric(8,3),
    countertop_unit_price   numeric(10,2),
    countertop_extras_json  jsonb,          -- [{name, price, subtotal}]
    countertop_subtotal     numeric(10,2),

    -- 五金（JSON存选项明细）
    hardware_items_json jsonb,              -- [{name, unit, qty, price, subtotal}]
    hardware_subtotal   numeric(10,2),

    -- 汇总
    line_subtotal   numeric(10,2),
    remark          text,

    created_at  timestamptz DEFAULT now(),
    updated_at  timestamptz DEFAULT now()
);

-- ============================================================
-- 预置基础数据
-- ============================================================

-- 产品大类
INSERT INTO product_types (name, category, has_countertop, has_upper_cabinet, sort_order) VALUES
    ('厨房橱柜', 'A', true,  true,  1),
    ('衣柜',     'B', false, false, 2),
    ('鞋柜',     'B', false, false, 3),
    ('餐边柜',   'B', true,  false, 4),
    ('浴室柜',   'B', true,  false, 5),
    ('阳台柜',   'B', false, false, 6),
    ('家政柜',   'B', false, false, 7),
    ('书柜',     'B', false, false, 8),
    ('酒柜',     'B', false, false, 9),
    ('电视柜',   'B', false, false, 10),
    ('榻榻米',   'B', false, false, 11)
ON CONFLICT DO NOTHING;

-- 门板材质（示例，可在后台自由增删）
INSERT INTO surface_materials (category, name, unit, price, sort_order) VALUES
    ('门板', '普通烤漆',   '元/m²', 380,  1),
    ('门板', '肤感烤漆',   '元/m²', 580,  2),
    ('门板', '不锈钢原色', '元/m²', 720,  3),
    ('门板', '拉丝不锈钢', '元/m²', 850,  4),
    ('门板', '镀色不锈钢', '元/m²', 980,  5),
    ('门板', '实木',       '元/m²', 950,  6),
    ('门板', '无门（开放）','元/m²', 0,   99)
ON CONFLICT DO NOTHING;

-- 台面材质（示例，可在后台自由增删）
INSERT INTO surface_materials (category, name, unit, price, sort_order) VALUES
    ('台面', '石英石15mm',    '元/m', 350, 1),
    ('台面', '石英石20mm',    '元/m', 480, 2),
    ('台面', '岩板12mm',      '元/m', 650, 3),
    ('台面', '岩板20mm',      '元/m', 780, 4),
    ('台面', '不锈钢1.2mm',   '元/m', 580, 5),
    ('台面', '大理石20mm',    '元/m', 800, 6)
ON CONFLICT DO NOTHING;

-- 台面工艺加项
INSERT INTO countertop_extras (name, unit, price, is_default, sort_order) VALUES
    ('后挡水', '元/m',  0,  true,  1),
    ('前挡水', '元/m',  80, false, 2),
    ('圆弧边', '元/m',  50, false, 3),
    ('磨边',   '元/m',  30, false, 4),
    ('开孔',   '元/个', 35, false, 5)
ON CONFLICT DO NOTHING;

-- 五金选项
INSERT INTO hardware_options (name, unit, price, is_default, applicable_to, sort_order) VALUES
    ('铰链',         '元/个', 18,  true,  '通用', 1),
    ('调节脚',       '元/个', 8,   true,  '橱柜', 2),
    ('免拉手铝条',   '元/m',  45,  false, '通用', 3),
    ('明装拉手',     '元/个', 35,  false, '通用', 4),
    ('地脚线',       '元/m',  55,  false, '橱柜', 5),
    ('挂衣杆',       '元/条', 65,  false, '衣柜', 6),
    ('抽屉（普通）', '元/个', 280, false, '通用', 7),
    ('抽屉（隐藏）', '元/个', 450, false, '通用', 8),
    ('裤架',         '元/个', 120, false, '衣柜', 9),
    ('层板',         '元/块', 45,  false, '通用', 10),
    ('转角拉篮',     '元/个', 380, false, '橱柜', 11),
    ('上翻门撑',     '元/个', 85,  false, '通用', 12)
ON CONFLICT DO NOTHING;

-- ============================================================
-- 验证查询（执行后检查数据是否正常）
-- ============================================================
-- SELECT name, category FROM product_types ORDER BY sort_order;
-- SELECT category, name, price FROM surface_materials ORDER BY category, sort_order;
-- SELECT name, price FROM hardware_options ORDER BY sort_order;
