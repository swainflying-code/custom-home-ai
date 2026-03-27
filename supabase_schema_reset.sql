-- 删除现有表（警告：会丢失所有数据！）
drop table if exists notifications cascade;
drop table if exists file_metadata cascade;
drop table if exists logs cascade;
drop table if exists design_requests cascade;
drop table if exists system_settings cascade;
drop table if exists users cascade;
drop table if exists customers cascade;

-- 然后重新创建所有表
create table customers (
    id uuid primary key default gen_random_uuid(),
    customer_code text unique not null,
    name text,
    gender text,
    age_group text,
    visit_times text,
    entry_time text,
    leave_time text,
    stay_duration text,
    companion_count text,
    companion_type text[],
    decision_maker_present text,
    customer_source text,
    house_type text,
    renovation_type text,
    renovation_progress text,
    house_area text,
    custom_budget text,
    custom_spaces text[],
    material_preference text,
    color_preference text[],
    style_preference text[],
    custom_style text,
    focus_points text[],
    has_competitor text,
    competitor_info text,
    life_style text,
    family_members text[],
    dining_count text,
    design_focus text[],
    storage_preference text,
    material_combination text,
    ideal_home text,
    quote_type text,
    quote_attitude text,
    has_contact text,
    contact_type text,
    contact_info text,
    intent_level text,
    has_appointment text,
    appointment_time text,
    objection text,
    leave_status text,
    special_needs text,
    ai_analysis_result jsonb,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create index idx_customers_code on customers(customer_code);
create index idx_customers_name on customers(name);

create table design_requests (
    id uuid primary key default gen_random_uuid(),
    customer_id uuid not null references customers(id) on delete cascade,
    customer_name text,
    customer_phone text,
    style_preference text[],
    material_preference text[],
    color_preference text[],
    design_scope text[],
    design_budget text,
    additional_notes text,
    ai_design_suggestion text,
    prompt_keywords text,
    reference_images_count integer default 0,
    reference_images text[],
    status text default 'pending',
    priority text default 'normal',
    assigned_to text,
    assigned_at timestamptz,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create index idx_design_requests_customer on design_requests(customer_id);

create table users (
    id uuid primary key default gen_random_uuid(),
    username text unique not null,
    email text unique,
    password_hash text not null,
    full_name text,
    role text default 'staff',
    can_view_customers boolean default true,
    can_edit_customers boolean default true,
    can_delete_customers boolean default false,
    can_view_reports boolean default true,
    can_manage_settings boolean default false,
    can_manage_designs boolean default true,
    is_active boolean default true,
    is_verified boolean default false,
    last_login timestamptz,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create index idx_users_username on users(username);

insert into users (username, email, password_hash, full_name, role, is_active, is_verified) 
values 
    ('admin', 'admin@bink.com', '$2b$12$LQv3Hej2s2tV3sXbQv3Hej2s2tV3sXb', '系统管理员', 'admin', true, true)
on conflict (username) do nothing;

create table logs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references users(id) on delete set null,
    username text,
    action text not null,
    resource_type text,
    resource_id text,
    ip_address inet,
    user_agent text,
    request_data jsonb,
    response_data jsonb,
    status text,
    error_message text,
    error_stack text,
    execution_time_ms integer,
    created_at timestamptz default now()
);

create index idx_logs_user on logs(user_id);

create table system_settings (
    id uuid primary key default gen_random_uuid(),
    setting_key text unique not null,
    setting_value text,
    setting_type text default 'string',
    category text,
    description text,
    is_sensitive boolean default false,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create index idx_settings_key on system_settings(setting_key);

insert into system_settings (setting_key, setting_value, setting_type, category, description) values
    ('app_name', 'BINK不锈钢定制AI助手', 'string', 'general', '应用名称'),
    ('app_version', '2.0.0', 'string', 'general', '应用版本'),
    ('enable_ai_analysis', 'true', 'boolean', 'ai', '启用AI分析功能'),
    ('ai_timeout', '60', 'number', 'ai', 'AI请求超时时间（秒）')
on conflict (setting_key) do nothing;

create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language 'plpgsql';

create trigger update_customers_updated_at before update on customers for each row execute function update_updated_at_column();
create trigger update_design_requests_updated_at before update on design_requests for each row execute function update_updated_at_column();
create trigger update_users_updated_at before update on users for each row execute function update_updated_at_column();
create trigger update_system_settings_updated_at before update on system_settings for each row execute function update_updated_at_column();
