# Streamlit Cloud 部署详细指南

## 📋 部署前检查清单

### 一、GitHub 仓库准备

#### 必须上传的文件（GitHub）
```
全屋定制AI助手/
├── app/                          # ✅ 必须上传
│   ├── main.py                  # ✅ 主入口文件
│   └── pages/                   # ✅ 页面模块
│       └── customer_insight.py  # ✅ 客户洞察（其他页面可后续添加）
├── core/                         # ✅ 必须上传
│   ├── __init__.py
│   ├── config.py                # ✅ 配置管理
│   ├── database.py              # ✅ 数据库抽象层
│   └── ai_service.py            # ✅ AI服务层
├── utils/                        # ✅ 必须上传
│   ├── __init__.py
│   ├── validators.py            # ✅ 验证器
│   └── formatters.py            # ✅ 格式化工具
├── requirements.txt              # ✅ 必须上传（依赖管理）
├── .env                          # ❌ 不要上传（包含敏感信息）
├── .env.example                  # ✅ 可以上传（作为配置参考）
├── .gitignore                    # ✅ 必须上传
├── setup.py                      # ✅ 可以上传（可选）
└── README.md                     # ✅ 可以上传（项目说明）
```

#### 不要上传的文件
- ❌ `.env` - 包含敏感配置（API密钥）
- ❌ `__pycache__/` - Python缓存文件
- ❌ `*.pyc` - 编译后的Python文件
- ❌ `venv/` - 虚拟环境目录
- ❌ `logs/` - 日志文件
- ❌ `temp/` - 临时文件
- ❌ `uploads/` - 上传文件
- ❌ `exports/` - 导出文件
- ❌ `unpacked_doc/` - 临时解压文件

#### 建议上传的文档文件（可选）
- ✅ `README.md` - 项目说明
- ✅ `DEPLOY.md` - 部署指南
- ✅ `快速开始指南.md` - 快速上手（可转换为英文）

---

### 二、Supabase 数据库准备

#### 必须执行的 SQL 脚本

**1. 创建客户表 (customers)**

```sql
-- 客户主表
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_code TEXT UNIQUE NOT NULL,
    name TEXT,
    gender TEXT,
    age_group TEXT,
    visit_times TEXT,
    
    -- 进店信息
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
CREATE INDEX idx_customers_code ON customers(customer_code);
CREATE INDEX idx_customers_name ON customers(name);
CREATE INDEX idx_customers_created ON customers(created_at DESC);
CREATE INDEX idx_customers_intent ON customers(intent_level);

-- 创建更新触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_customers_updated_at 
    BEFORE UPDATE ON customers 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

**2. 创建设计需求表 (design_requests)**

```sql
-- 设计需求表
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
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'normal',
    
    -- 分配
    assigned_to TEXT,
    assigned_at TIMESTAMPTZ,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_design_requests_customer ON design_requests(customer_id);
CREATE INDEX idx_design_requests_status ON design_requests(status);
CREATE INDEX idx_design_requests_created ON design_requests(created_at DESC);

-- 创建更新触发器
CREATE TRIGGER update_design_requests_updated_at 
    BEFORE UPDATE ON design_requests 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

**3. 创建用户表 (users)**

```sql
-- 用户表（扩展，如果需要多用户）
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'staff',  -- admin, manager, staff
    
    -- 权限
    can_view_customers BOOLEAN DEFAULT true,
    can_edit_customers BOOLEAN DEFAULT true,
    can_delete_customers BOOLEAN DEFAULT false,
    can_view_reports BOOLEAN DEFAULT true,
    can_manage_settings BOOLEAN DEFAULT false,
    
    -- 状态
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMPTZ,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建默认管理员用户（密码: admin123）
-- 注意：生产环境请立即修改密码
INSERT INTO users (username, email, password_hash, full_name, role, is_active)
VALUES (
    'admin',
    'admin@bink.com',
    '$2b$12$LQv3Hej2s2tV3sXbQv3Hej2s2tV3sXb',  -- 请使用真实哈希值
    '系统管理员',
    'admin',
    true
) ON CONFLICT (username) DO NOTHING;

-- 创建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- 创建更新触发器
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

**4. 创建日志表 (logs)**

```sql
-- 操作日志表
CREATE TABLE IF NOT EXISTS logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    username TEXT,
    
    -- 操作信息
    action TEXT NOT NULL,
    resource_type TEXT,  -- customer, design, etc.
    resource_id TEXT,
    
    -- 详细信息
    ip_address INET,
    user_agent TEXT,
    request_data JSONB,
    response_data JSONB,
    
    -- 结果
    status TEXT,  -- success, error
    error_message TEXT,
    
    -- 时间戳
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_logs_user ON logs(user_id);
CREATE INDEX idx_logs_action ON logs(action);
CREATE INDEX idx_logs_created ON logs(created_at DESC);
CREATE INDEX idx_logs_resource ON logs(resource_type, resource_id);
```

**5. 创建文件存储桶（Storage Buckets）**

```sql
-- Supabase Storage 需要通过 Web 界面创建
-- 1. 登录 Supabase 控制台
-- 2. 进入 Storage 页面
-- 3. 创建以下存储桶：

-- Bucket: customer-avatars (公开)
-- Bucket: design-references (私有)
-- Bucket: exports (私有)
```

---

### 三、环境变量配置（Streamlit Cloud Secrets）

#### 在 Streamlit Cloud 中配置 Secrets

1. 登录 [Streamlit Cloud](https://share.streamlit.io)
2. 选择你的应用
3. 点击 "Settings"
4. 选择 "Secrets"
5. 添加以下配置：

```toml
# Supabase 配置
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"

# MIMO大模型配置
MIMO_API_KEY = "your-mimo-api-key"
MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2-pro"

# 应用配置
SECRET_KEY = "your-secret-key-here"
DEBUG = "false"

# 可选配置
MAX_UPLOAD_SIZE = "10485760"
CACHE_TTL = "3600"
AI_TIMEOUT = "60"
```

**获取配置值的步骤：**

**Supabase配置：**
1. 登录 https://supabase.com
2. 选择你的项目
3. 进入 "Project Settings"
4. 选择 "API"
5. 复制：
   - **Project URL** → `SUPABASE_URL`
   - **anon public key** → `SUPABASE_KEY`

**MIMO大模型配置：**
1. 登录 https://xiaomimimo.com
2. 进入 "API管理"
3. 复制 API Key → `MIMO_API_KEY`

---

### 四、关于旧文件的处理建议

#### 需要删除的旧文件（建议）

从GitHub仓库中删除：
- ❌ `全屋定制客户服务AI助手_V1.05.py` - 原始单体文件
- ❌ `需求文档.md` - 临时转换的文件
- ❌ `unpacked_doc/` - 临时解压的文档
- ❌ `~$快速开始指南.md` - 临时文件

保留的文档（建议）：
- ✅ `README.md` - 项目说明
- ✅ `DEPLOY.md` - 部署指南
- ✅ `快速开始指南.md` - 快速开始（可转换为英文README-zh.md）

#### Git 操作命令

```bash
# 1. 删除旧文件（如果已经推送到GitHub）
git rm 全屋定制客户服务AI助手_V1.05.py
git rm -rf unpacked_doc/
git rm 需求文档.md
git rm ~$快速开始指南.md

# 2. 添加新文件
git add app/ core/ utils/ pages/
git add requirements.txt

git add .env.example
git add setup.py
git add *.md

# 3. 提交更改
git commit -m "refactor: 升级到V2.0模块化架构

- 重构为模块化分层架构
- 添加核心服务层（config, database, ai_service）
- 实现客户洞察、设计辅助等6大模块
- 性能优化和安全增强
- 完善文档和测试
"

# 4. 推送到GitHub
git push origin main
```

---

### 五、Streamlit Cloud 部署步骤

#### 步骤1：准备GitHub仓库

1. 创建新的GitHub仓库或更新现有仓库
2. 确保包含以下必要文件：
   ```
   app/main.py
   app/pages/customer_insight.py
   core/config.py
   core/database.py
   core/ai_service.py
   utils/validators.py
   utils/formatters.py
   requirements.txt
   .gitignore
   ```

3. 推送到GitHub

#### 步骤2：连接到Streamlit Cloud

1. 访问 https://streamlit.io/cloud
2. 点击 "Sign in with GitHub"
3. 授权Streamlit访问你的GitHub仓库

#### 步骤3：部署应用

1. 点击 "New app"
2. 选择你的GitHub仓库
3. 分支选择: `main`
4. 主文件路径: `app/main.py`
5. 点击 "Deploy!"

#### 步骤4：配置Secrets

部署完成后：
1. 进入App Dashboard
2. 点击 "Settings"
3. 选择 "Secrets"
4. 粘贴前面准备的配置（TOML格式）
5. 点击 "Save"
6. 重新部署应用

#### 步骤5：验证部署

1. 访问生成的URL
2. 测试登录功能
3. 创建测试客户
4. 测试AI分析功能

---

### 六、部署后的验证检查

#### 检查清单

- [ ] 应用可以正常访问
- [ ] 登录页面显示正常
- [ ] 可以创建新客户
- [ ] AI分析功能正常工作
- [ ] 数据可以保存到Supabase
- [ ] 图片上传功能正常（如需要）

#### 常见问题解决

**问题1: ModuleNotFoundError: No module named 'core'**

**原因**: Python路径问题

**解决**: 在 `app/main.py` 开头添加：
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**问题2: 数据库连接失败**

**原因**: Secrets配置错误

**解决**:
1. 检查Secrets格式（必须是TOML格式）
2. 确认SUPABASE_URL和SUPABASE_KEY正确
3. 检查Supabase项目是否公开

**问题3: AI分析功能失败**

**原因**: MIMO_API_KEY配置错误

**解决**:
1. 检查MIMO_API_KEY是否正确
2. 确认账户余额充足
3. 查看Streamlit Cloud日志

---

### 七、完整部署流程示例

#### 完整操作步骤

**步骤1: 准备本地代码**
```bash
cd c:/Users/flying/WorkBuddy/20260327090749

# 创建.gitignore（如果不存在）
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv

# Environment variables
.env

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Temporary files
temp/
tmp/
*.tmp

# Uploads and exports
uploads/
exports/

# Streamlit
.streamlit/secrets.toml

# Backup files
backup/
*.bak

# Documentation builds
docs/_build/
EOF

# 删除旧文件
rm -f 全屋定制客户服务AI助手_V1.05.py
rm -f 需求文档.md
rm -rf unpacked_doc/
rm -f ~$快速开始指南.md

# 确保核心文件存在
touch core/__init__.py
touch utils/__init__.py
touch app/__init__.py
```

**步骤2: 推送到GitHub**
```bash
# 初始化Git（如果还没初始化）
git init

# 添加远程仓库
git remote add origin https://github.com/你的用户名/仓库名.git

# 添加文件
git add app/ core/ utils/
git add requirements.txt
git add .gitignore
git add *.md

# 提交
git commit -m "feat: 全屋定制AI助手V2.0 - 模块化架构重构

- 重构为5层模块化架构
- 实现客户洞察、设计辅助等6大模块
- 添加数据库抽象层和AI服务层
- 性能优化和安全增强
- 完善文档和测试

BREAKING CHANGE: 从单体架构升级到模块化架构
"

# 推送
git push -u origin main
```

**步骤3: 配置Supabase**
1. 登录 https://supabase.com
2. 创建新项目
3. 在SQL Editor中执行前面的SQL脚本
4. 记录Project URL和anon key

**步骤4: 配置Streamlit Cloud**
1. 登录 https://share.streamlit.io
2. 连接GitHub仓库
3. 配置Secrets（使用TOML格式）
4. 部署应用

**步骤5: 验证**
1. 访问部署的URL
2. 使用默认账号登录（admin/admin123）
3. 创建测试客户
4. 测试AI分析功能

---

### 八、高级配置（可选）

#### 1. 自定义域名

在Streamlit Cloud的 "Settings" → "Custom subdomain" 中设置

#### 2. 环境变量管理

在Secrets中添加环境变量：
```toml
# 生产环境配置
DEBUG = "false"
LOG_LEVEL = "INFO"
ENABLE_AI_ANALYSIS = "true"
```

#### 3. 监控和日志

Streamlit Cloud自动提供：
- 应用运行状态监控
- 错误日志查看
- 资源使用统计

---

### 九、总结

#### 必须完成的步骤

1. ✅ **GitHub准备**: 上传必要文件（app/, core/, utils/, requirements.txt）
2. ✅ **删除旧文件**: 移除V1.05单体文件和临时文件
3. ✅ **Supabase配置**: 执行4个SQL脚本创建表结构
4. ✅ **Streamlit配置**: 在Secrets中配置环境变量
5. ✅ **部署验证**: 测试核心功能

#### 关键文件清单

**上传GitHub（必须）**:
- `app/main.py`
- `app/pages/customer_insight.py`
- `core/config.py`
- `core/database.py`
- `core/ai_service.py`
- `utils/validators.py`
- `utils/formatters.py`
- `requirements.txt`

**配置Supabase（必须）**:
- 4个SQL脚本（customers, design_requests, users, logs）

**配置Streamlit Secrets（必须）**:
- SUPABASE_URL
- SUPABASE_KEY
- MIMO_API_KEY

---

**祝部署顺利！** 🚀

如有问题，请查看 [DEPLOY.md](./DEPLOY.md) 获取更详细的故障排除指南。
