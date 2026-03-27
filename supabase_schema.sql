-- 全屋定制客户服务AI助手 - Supabase数据库架构
-- 版本: V2.0
-- 生成时间: 2025-03-27

-- ==========================================
-- 1. 客户表 (customers)
-- ==========================================

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_code TEXT UNIQUE NOT NULL,
    name TEXT,
    gender TEXT,
    age_group TEXT,
    
    -- 进店信息
    visit_times TEXT,
    entry_time TEXT,
    leave_time TEXT,
    stay_duration TEXT,
    companion_count TEXT,
    companion_type TEXT[],
    decision_maker_present TEXT,
    customer_source TEXT,
    
    -- 房屋信息
    house_type TEXT,
    renovation_type TEXT,
    renovation_progress TEXT,
    house_area TEXT,
    custom_budget TEXT,
    custom_spaces TEXT[],
    
    -- 产品偏好
    material_preference TEXT,
    color_preference TEXT[],
    style_preference TEXT[],
    custom_style TEXT,
    focus_points TEXT[],
    has_competitor TEXT,
    competitor_info TEXT,
    
    -- 生活方式
    life_style TEXT,
    family_members TEXT[],
    dining_count TEXT,
    design_focus TEXT[],
    storage_preference TEXT,
    material_combination TEXT,
    ideal_home TEXT,
    
    -- 沟通转化
    quote_type TEXT,
    quote_attitude TEXT,
    has_contact TEXT,
    contact_type TEXT,
    contact_info TEXT,
    intent_level TEXT,
    has_appointment TEXT,
    appointment_time TEXT,
    objection TEXT,
    leave_status TEXT,
    
    -- 需求补充
    special_needs TEXT,
    
    -- AI分析结果
    ai_analysis_result JSONB,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code);
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
CREATE INDEX IF NOT EXISTS idx_customers_created ON customers(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_customers_intent ON customers(intent_level);
CREATE INDEX IF NOT EXISTS idx_customers_gender ON customers(gender);
CREATE INDEX IF NOT EXISTS idx_customers_age_group ON customers(age_group);

-- ==========================================
-- 2. 设计需求表 (design_requests)
-- ==========================================

CREATE TABLE IF NOT EXISTS design_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    -- 客户信息
    customer_name TEXT,
    customer_phone TEXT,
    
    -- 设计要求
    style_preference TEXT[],
    material_preference TEXT[],
    color_preference TEXT[],
    design_scope TEXT[],
    design_budget TEXT,
    
    -- 设计师调整
    additional_notes TEXT,
    
    -- AI生成内容
    ai_design_suggestion TEXT,
    prompt_keywords TEXT,
    
    -- 参考图
    reference_images_count INTEGER DEFAULT 0,
    reference_images TEXT[],
    
    -- 状态管理
    status TEXT DEFAULT 'pending',  -- pending, designing, completed
    priority TEXT DEFAULT 'normal',  -- low, normal, high, urgent
    
    -- 分配
    assigned_to TEXT,
    assigned_at TIMESTAMPTZ,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_design_requests_customer ON design_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_design_requests_status ON design_requests(status);
CREATE INDEX IF NOT EXISTS idx_design_requests_priority ON design_requests(priority);
CREATE INDEX IF NOT EXISTS idx_design_requests_created ON design_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_design_requests_assigned ON design_requests(assigned_to);

-- ==========================================
-- 3. 用户表 (users)
-- ==========================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'staff',  -- admin, manager, designer, staff
    
    -- 权限
    can_view_customers BOOLEAN DEFAULT true,
    can_edit_customers BOOLEAN DEFAULT true,
    can_delete_customers BOOLEAN DEFAULT false,
    can_view_reports BOOLEAN DEFAULT true,
    can_manage_settings BOOLEAN DEFAULT false,
    can_manage_designs BOOLEAN DEFAULT true,
    
    -- 状态
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMPTZ,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- 创建默认用户（生产环境请修改密码）
-- 密码: admin123（请使用bcrypt哈希）
INSERT INTO users (username, email, password_hash, full_name, role, is_active, is_verified) 
VALUES 
    ('admin', 'admin@bink.com', '$2b$12$LQv3Hej2s2tV3sXbQv3Hej2s2tV3sXb', '系统管理员', 'admin', true, true)
ON CONFLICT (username) DO NOTHING;

-- ==========================================
-- 4. 操作日志表 (logs)
-- ==========================================

CREATE TABLE IF NOT EXISTS logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    username TEXT,
    
    -- 操作信息
    action TEXT NOT NULL,  -- login, create_customer, update_customer, delete_customer, ai_analyze, generate_design
    resource_type TEXT,  -- customer, design_request, user
    resource_id TEXT,
    
    -- 详细信息
    ip_address INET,
    user_agent TEXT,
    request_data JSONB,
    response_data JSONB,
    
    -- 结果
    status TEXT,  -- success, error, warning
    error_message TEXT,
    error_stack TEXT,
    
    -- 性能
    execution_time_ms INTEGER,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_action ON logs(action);
CREATE INDEX IF NOT EXISTS idx_logs_created ON logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_resource ON logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_logs_status ON logs(status);

-- ==========================================
-- 5. 系统配置表 (system_settings)
-- ==========================================

CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type TEXT DEFAULT 'string',  -- string, number, boolean, json
    category TEXT,  -- general, ai, database, security
    description TEXT,
    is_sensitive BOOLEAN DEFAULT false,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_settings_key ON system_settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_settings_category ON system_settings(category);

-- 插入默认配置
INSERT INTO system_settings (setting_key, setting_value, setting_type, category, description) VALUES
    ('app_name', 'BINK不锈钢定制AI助手', 'string', 'general', '应用名称'),
    ('app_version', '2.0.0', 'string', 'general', '应用版本'),
    ('max_upload_size', '10485760', 'number', 'general', '最大上传文件大小（字节）'),
    ('default_currency', 'CNY', 'string', 'general', '默认货币'),
    ('enable_ai_analysis', 'true', 'boolean', 'ai', '启用AI分析功能'),
    ('ai_timeout', '60', 'number', 'ai', 'AI请求超时时间（秒）'),
    ('cache_ttl', '3600', 'number', 'general', '缓存过期时间（秒）'),
    ('rate_limit_per_minute', '60', 'number', 'security', '每分钟请求限制')
ON CONFLICT (setting_key) DO NOTHING;

-- ==========================================
-- 6. 文件存储元数据表 (file_metadata)
-- ==========================================

CREATE TABLE IF NOT EXISTS file_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name TEXT NOT NULL,
    original_name TEXT,
    file_size INTEGER,
    file_type TEXT,
    mime_type TEXT,
    
    -- 关联信息
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    design_request_id UUID REFERENCES design_requests(id) ON DELETE CASCADE,
    
    -- 存储信息
    storage_bucket TEXT,
    storage_path TEXT,
    storage_url TEXT,
    
    -- 元数据
    metadata JSONB,
    is_public BOOLEAN DEFAULT false,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_files_uploaded_by ON file_metadata(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_files_customer ON file_metadata(customer_id);
CREATE INDEX IF NOT EXISTS idx_files_created ON file_metadata(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_files_bucket ON file_metadata(storage_bucket, storage_path);

-- ==========================================
-- 7. 通知表 (notifications)
-- ==========================================

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 通知内容
    title TEXT NOT NULL,
    message TEXT,
    notification_type TEXT,  -- info, success, warning, error
    
    -- 关联资源
    resource_type TEXT,
    resource_id TEXT,
    
    -- 状态
    is_read BOOLEAN DEFAULT false,
    is_important BOOLEAN DEFAULT false,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_important ON notifications(is_important, is_read) WHERE is_important = true AND is_read = false;

-- ==========================================
-- 8. 通用更新触发器函数
-- ==========================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有表创建更新触发器
CREATE TRIGGER update_customers_updated_at 
    BEFORE UPDATE ON customers 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_design_requests_updated_at 
    BEFORE UPDATE ON design_requests 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_logs_updated_at 
    BEFORE UPDATE ON logs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at 
    BEFORE UPDATE ON system_settings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_file_metadata_updated_at 
    BEFORE UPDATE ON file_metadata 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notifications_updated_at 
    BEFORE UPDATE ON notifications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- 9. Row Level Security (RLS) 策略
-- ==========================================

-- 为客户表启用RLS
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE design_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- 创建策略：用户只能查看自己的记录（示例，可根据需要调整）
-- CREATE POLICY "Users can view own customers" ON customers
--     FOR SELECT USING (auth.uid()::text = (metadata->>'owner_id')::text);

-- CREATE POLICY "Users can insert own customers" ON customers
--     FOR INSERT WITH CHECK (auth.uid()::text = (metadata->>'owner_id')::text);

-- CREATE POLICY "Users can update own customers" ON customers
--     FOR UPDATE USING (auth.uid()::text = (metadata->>'owner_id')::text);

-- ==========================================
-- 10. 创建视图（可选）
-- ==========================================

-- 客户统计视图
CREATE OR REPLACE VIEW customer_statistics AS
SELECT 
    COUNT(*) as total_customers,
    COUNT(CASE WHEN intent_level LIKE '%高意向%' THEN 1 END) as high_intent_count,
    COUNT(CASE WHEN ai_analysis_result IS NOT NULL THEN 1 END) as ai_analyzed_count,
    COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as today_new_count,
    COUNT(CASE WHEN has_appointment = '预约上门测量' THEN 1 END) as appointment_count
FROM customers;

-- 设计需求统计视图
CREATE OR REPLACE VIEW design_request_statistics AS
SELECT 
    status,
    priority,
    COUNT(*) as count,
    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_count
FROM design_requests
GROUP BY status, priority;

-- 用户活动视图
CREATE OR REPLACE VIEW user_activity AS
SELECT 
    u.username,
    u.full_name,
    u.role,
    COUNT(l.id) as total_actions,
    COUNT(CASE WHEN l.status = 'success' THEN 1 END) as success_actions,
    COUNT(CASE WHEN l.created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_actions
FROM users u
LEFT JOIN logs l ON u.id = l.user_id
WHERE u.is_active = true
GROUP BY u.id, u.username, u.full_name, u.role;

-- ==========================================
-- 11. 创建函数（可选）
-- ==========================================

-- 自动创建客户编号的函数
CREATE OR REPLACE FUNCTION generate_customer_code()
RETURNS TEXT AS $$
BEGIN
    RETURN 'BINK-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || SUBSTRING(MD5(RANDOM()::TEXT) FROM 1 FOR 6);
END;
$$ LANGUAGE plpgsql;

-- 创建客户时自动设置编号（示例）
-- CREATE TRIGGER set_customer_code_trigger
--     BEFORE INSERT ON customers
--     FOR EACH ROW
--     WHEN (NEW.customer_code IS NULL)
--     EXECUTE FUNCTION set_customer_code();

-- ==========================================
-- 12. 初始化数据
-- ==========================================

-- 插入默认系统配置
INSERT INTO system_settings (setting_key, setting_value, setting_type, category, description) VALUES
    ('app_name', 'BINK不锈钢定制AI助手', 'string', 'general', '应用名称'),
    ('app_version', '2.0.0', 'string', 'general', '应用版本'),
    ('max_upload_size', '10485760', 'number', 'general', '最大上传文件大小（字节）'),
    ('default_currency', 'CNY', 'string', 'general', '默认货币'),
    ('enable_ai_analysis', 'true', 'boolean', 'ai', '启用AI分析功能'),
    ('ai_timeout', '60', 'number', 'ai', 'AI请求超时时间（秒）'),
    ('cache_ttl', '3600', 'number', 'general', '缓存过期时间（秒）'),
    ('rate_limit_per_minute', '60', 'number', 'security', '每分钟请求限制')
ON CONFLICT (setting_key) DO NOTHING;

-- ==========================================
-- 13. 注释说明
-- ==========================================

COMMENT ON TABLE customers IS '客户主表 - 存储客户基本信息、房屋信息、产品偏好、生活方式等';
COMMENT ON TABLE design_requests IS '设计需求表 - 存储客户的设计需求和AI生成的设计建议';
COMMENT ON TABLE users IS '用户表 - 存储系统用户信息（管理员、设计师、销售等）';
COMMENT ON TABLE logs IS '操作日志表 - 记录用户操作日志，用于审计和监控';
COMMENT ON TABLE system_settings IS '系统配置表 - 存储系统参数配置';
COMMENT ON TABLE file_metadata IS '文件元数据表 - 存储上传文件的元数据信息';
COMMENT ON TABLE notifications IS '通知表 - 存储用户通知消息';

-- ==========================================
-- 14. 权限设置（重要）
-- ==========================================

-- 启用实时订阅（如果需要）
-- ALTER TABLE customers REPLICA IDENTITY FULL;
-- ALTER TABLE design_requests REPLICA IDENTITY FULL;
-- ALTER TABLE users REPLICA IDENTITY FULL;

-- ==========================================
-- 15. 完成提示
-- ==========================================

-- 查看创建的表
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- 查看表统计
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 祝贺！数据库初始化完成
-- 请记得：
-- 1. 在Supabase Storage中创建存储桶（customer-avatars, design-references, exports）
-- 2. 配置Row Level Security (RLS)策略（如果需要）
-- 3. 测试数据库连接
-- 4. 备份数据库结构
