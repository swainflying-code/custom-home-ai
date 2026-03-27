# 🚀 Streamlit Cloud 部署快速指南

## 📋 5分钟部署清单

### 步骤1: 准备GitHub仓库（1分钟）

#### 需要上传的文件
```
✅ app/main.py                    # 主入口
✅ app/pages/customer_insight.py  # 客户洞察页面
✅ core/config.py                 # 配置管理
✅ core/database.py               # 数据库抽象层
✅ core/ai_service.py             # AI服务层
✅ utils/validators.py            # 验证器
✅ utils/formatters.py            # 格式化工具
✅ requirements.txt               # 依赖管理
✅ .gitignore                     # Git忽略文件
```

#### 删除的旧文件
```
❌ 全屋定制客户服务AI助手_V1.05.py   # 原始单体文件
❌ 需求文档.md                        # 临时文件
❌ unpacked_doc/                      # 临时解压目录
❌ ~$快速开始指南.md                  # 临时文件
```

**操作命令**:
```bash
cd c:/Users/flying/WorkBuddy/20260327090749

# 删除旧文件
rm -f 全屋定制客户服务AI助手_V1.05.py
rm -f 需求文档.md
rm -rf unpacked_doc/
rm -f ~$快速开始指南.md

# 确保__init__.py存在
touch core/__init__.py
touch utils/__init__.py
touch app/__init__.py

# 提交到GitHub
git add app/ core/ utils/ requirements.txt .gitignore
git add *.md
git commit -m "deploy: 准备V2.0部署"
git push origin main
```

---

### 步骤2: 配置Supabase（2分钟）

#### 1. 创建项目
- 访问 https://supabase.com
- 登录账号
- 点击 "New Project"
- 填写项目名称和密码
- 等待创建完成（约1分钟）

#### 2. 执行SQL脚本
- 进入 "SQL Editor"
- 复制 [supabase_schema.sql](./supabase_schema.sql) 的全部内容
- 粘贴到SQL Editor
- 点击 "Run" 执行

**验证**: 执行以下查询确认表已创建
```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
```

应该看到：`customers`, `design_requests`, `users`, `logs` 等表

#### 3. 获取连接信息
- 进入 "Project Settings"
- 选择 "API"
- 复制以下内容备用：
  - **Project URL** (例如: https://xxxxx.supabase.co)
  - **anon public key** (以eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9开头的长字符串)

---

### 步骤3: 部署到Streamlit Cloud（1分钟）

#### 1. 连接GitHub
- 访问 https://share.streamlit.io
- 点击 "Sign in with GitHub"
- 授权Streamlit访问你的GitHub仓库

#### 2. 创建新应用
- 点击 "New app"
- 选择你的GitHub仓库
- 分支: `main`
- 主文件路径: `app/main.py`
- 点击 "Deploy!"

**等待**: 部署大约需要 2-5 分钟

---

### 步骤4: 配置Secrets（1分钟）

部署完成后，立即配置环境变量：

1. 进入App Dashboard
2. 点击 "Settings"
3. 选择 "Secrets"
4. 粘贴以下内容（替换为你的实际值）:

```toml
# Supabase配置
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-public-key"

# MIMO大模型配置
MIMO_API_KEY = "your-mimo-api-key"
MIMO_BASE_URL = "https://api.xiaomimimo.com/v1"
MIMO_MODEL = "mimo-v2-pro"

# 应用配置
SECRET_KEY = "your-secret-key-here-change-this"
DEBUG = "false"
```

5. 点击 "Save"
6. 点击 "Reboot app" 重启应用

---

### 步骤5: 验证部署（1分钟）

访问你的应用URL（例如: https://your-app.streamlit.app）

#### 验证功能
- [ ] 登录页面正常显示
- [ ] 使用默认账号登录: admin/admin123
- [ ] 创建测试客户
- [ ] AI分析功能正常工作
- [ ] 数据成功保存到Supabase

---

## 🔑 获取配置参数

### Supabase配置
1. 登录 https://supabase.com
2. 选择你的项目
3. 进入 "Project Settings" → "API"
4. 复制:
   - Project URL → `SUPABASE_URL`
   - anon public key → `SUPABASE_KEY`

### MIMO大模型配置
1. 登录 https://xiaomimimo.com
2. 进入 "API管理"
3. 复制 API Key → `MIMO_API_KEY`

### 密钥生成（可选）
```bash
# Linux/Mac
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Windows (PowerShell)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📊 部署验证清单

- [ ] GitHub仓库包含必要文件
- [ ] 旧文件已删除
- [ ] Supabase数据库表已创建
- [ ] Streamlit Secrets已配置
- [ ] 应用可以正常访问
- [ ] 登录功能正常
- [ ] 客户创建功能正常
- [ ] AI分析功能正常

---

## 🆘 常见问题

### Q1: 部署失败，提示ModuleNotFoundError
**原因**: Python路径问题

**解决**: 确保 `app/main.py` 开头有：
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Q2: 数据库连接失败
**原因**: Secrets配置错误

**解决**:
1. 检查Secrets格式（必须是TOML格式）
2. 确认SUPABASE_URL和SUPABASE_KEY正确
3. 重启应用

### Q3: AI分析失败
**原因**: MIMO_API_KEY无效

**解决**:
1. 检查MIMO_API_KEY是否正确
2. 确认账户余额充足
3. 查看Streamlit Cloud日志

### Q4: 图片上传失败
**原因**: Supabase Storage未配置

**解决**:
1. 登录Supabase控制台
2. 进入 "Storage"
3. 创建存储桶: customer-avatars, design-references

---

## 📁 文件状态检查

运行此脚本检查文件完整性：

```bash
#!/bin/bash

echo "=== 部署前文件检查 ==="

# 检查必要文件
files=(
    "app/main.py"
    "app/pages/customer_insight.py"
    "core/config.py"
    "core/database.py"
    "core/ai_service.py"
    "utils/validators.py"
    "utils/formatters.py"
    "requirements.txt"
    ".gitignore"
)

echo "✅ 检查必要文件..."
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (缺失)"
    fi
done

echo ""
echo "⚠️  检查旧文件（应删除）..."

old_files=(
    "全屋定制客户服务AI助手_V1.05.py"
    "需求文档.md"
    "unpacked_doc/"
)

for file in "${old_files[@]}"; do
    if [ -e "$file" ]; then
        echo "  ⚠  $file (建议删除)"
    else
        echo "  ✓ $file (已删除)"
    fi
done

echo ""
echo "=== 检查完成 ==="
```

---

## 🎉 部署成功！

部署成功后，你会获得：
- 🌐 在线访问URL
- 🔒 自动HTTPS加密
- 🔄 持续部署（GitHub更新自动部署）
- 📊 应用监控面板
- 📝 日志查看

---

## 🔧 高级配置

### 自定义域名（可选）
1. 在Streamlit Cloud Settings中
2. 选择 "Custom subdomain"
3. 输入你想要的子域名

### 环境变量（可选）
```toml
# 性能配置
CACHE_TTL = "3600"
AI_TIMEOUT = "60"
MAX_UPLOAD_SIZE = "10485760"

# 功能开关
ENABLE_AI_ANALYSIS = "true"
ENABLE_IMAGE_UPLOAD = "true"
```

---

**🚀 现在就开始部署吧！**

预计总时间：5-10分钟
难度等级：⭐☆☆☆☆（非常简单）

如有问题，查看详细指南：[DEPLOY_CHECKLIST.md](./DEPLOY_CHECKLIST.md)
