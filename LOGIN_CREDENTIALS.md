# 登录凭证说明

## 默认管理员账号

### 账号信息
- **用户名**: `admin`
- **密码**: `admin123`
- **邮箱**: `admin@bink.com`
- **角色**: 系统管理员

### 测试用户账号
- **用户名**: `user`
- **密码**: `user123`
- **邮箱**: `user@bink.com`
- **角色**: 普通用户

## 首次使用前准备

### 步骤1：在Supabase中执行SQL脚本

1. 登录 [Supabase](https://supabase.com)
2. 进入你的项目
3. 点击左侧菜单的 **"SQL Editor"**
4. 点击 **"New query"**
5. 将下面的SQL代码复制粘贴到编辑器中：

```sql
-- 更新默认管理员用户密码（密码：admin123）
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
```

6. 点击 **"Run"** 执行SQL

### 步骤2：登录应用

1. 打开应用URL
2. 在登录页面输入：
   - **用户名**: `admin`
   - **密码**: `admin123`
3. 点击 **"登录系统"**

## 安全建议

⚠️ **重要提示**：
- 首次登录后，请立即修改默认密码
- 建议删除或禁用测试用户账号（user/user123）
- 生产环境请使用强密码策略

## 创建新用户

登录后，可以在 **"系统设置"** → **"用户管理"** 中创建新用户。

## 密码加密说明

本系统使用PBKDF2算法（SHA-256，100,000次迭代）加密密码，格式为：`salt:hash`。

如果需要生成新的密码哈希，可以使用：

```bash
python generate_password.py <你的密码>
```

## 常见问题

### Q: 登录时显示"用户名不存在"
**A**: 请确保已在Supabase中执行了SQL脚本创建用户

### Q: 登录时显示"用户名或密码错误"
**A**: 
- 确认用户名和密码正确（区分大小写）
- 确认已在Supabase中执行SQL脚本
- 检查Supabase的users表是否有数据

### Q: 如何重置密码？
**A**: 
1. 使用generate_password.py生成新密码的哈希
2. 在Supabase中更新users表的password_hash字段

```sql
UPDATE users 
SET password_hash = '新哈希值'
WHERE username = '要重置的用户名';
```

### Q: 如何添加更多默认用户？
**A**: 
1. 使用generate_password.py生成密码哈希
2. 在setup_default_user.sql中添加新的INSERT语句
3. 在Supabase中执行更新后的SQL

## 需要帮助？

如果仍然无法登录，请检查：
1. Supabase数据库连接是否正常
2. users表是否已创建
3. 应用日志中的错误信息
