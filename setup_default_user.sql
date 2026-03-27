-- 更新默认管理员用户密码（密码：admin123）
-- 如果用户不存在则创建
INSERT INTO users (username, email, password_hash, full_name, role, is_active, is_verified) 
VALUES 
    ('admin', 'admin@bink.com', '2bc923d4803375ae9f42d67e4ae62970:ac7a03883381478d54757fb65e1a50e7364c5c9223a33ded00bd4f37a49d3cae', '系统管理员', 'admin', true, true)
ON CONFLICT (username) DO UPDATE 
SET password_hash = EXCLUDED.password_hash,
    updated_at = NOW();

-- 创建测试用户（密码：user123）  
INSERT INTO users (username, email, password_hash, full_name, role, is_active, is_verified)
VALUES
    ('user', 'user@bink.com', '5b17a8bee9a6b7d9dfa22b52c865d32b:ea9b83dab629e0b489e214d96d03673c58dcc75c42d2db5ae6ddb8d3a596ebfb', '测试用户', 'user', true, true)
ON CONFLICT (username) DO NOTHING;

-- 查询所有用户
SELECT username, email, full_name, role, is_active FROM users;
