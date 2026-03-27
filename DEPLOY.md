# 全屋定制客户服务AI助手 - 部署指南

## 📦 项目结构

```
全屋定制AI助手/
├── app/
│   ├── main.py                  # 主应用入口
│   ├── pages/                   # 页面模块
│   │   ├── customer_insight.py  # 客户洞察 ✅
│   │   ├── design_assistant.py  # 设计辅助
│   │   ├── smart_quoting.py     # 智能报价
│   │   ├── customer_service.py  # 客户服务
│   │   ├── statistics.py        # 数据统计
│   │   └── system_settings.py   # 系统设置
│   └── components/              # UI组件
│       ├── navigation.py        # 导航组件
│       └── loading.py           # 加载组件
├── core/                        # 核心模块 ✅
│   ├── __init__.py
│   ├── config.py                # 配置管理
│   ├── database.py              # 数据库抽象层
│   ├── ai_service.py            # AI服务层
│   ├── auth.py                  # 认证授权
│   ├── cache.py                 # 缓存管理
│   └── exceptions.py            # 异常定义
├── models/                      # 数据模型
│   ├── __init__.py
│   ├── customer.py              # 客户模型
│   ├── design.py                # 设计模型
│   └── user.py                  # 用户模型
├── utils/                       # 工具函数 ✅
│   ├── __init__.py
│   ├── validators.py            # 验证器
│   ├── formatters.py            # 格式化工具
│   ├── helpers.py               # 通用辅助
│   ├── form_state.py            # 表单状态管理
│   └── logger.py                # 日志配置
├── assets/                      # 静态资源
│   └── styles.css               # 样式文件
├── tests/                       # 测试文件
├── docs/                        # 文档
├── .env.example                 # 环境变量示例
├── requirements.txt             # 依赖管理
├── DEPLOY.md                    # 部署指南
└── README.md                    # 项目说明
```

## 🔧 环境准备

### 1. 系统要求
- Python 3.8+
- pip (Python包管理器)
- Git

### 2. 创建虚拟环境（推荐）

```bash
# 克隆项目
git clone <your-repo-url>
cd custom-home-ai

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制示例文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
# Supabase配置
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_api_key

# MIMO大模型配置
MIMO_API_KEY=your_mimo_api_key
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2-pro

# 应用配置
SECRET_KEY=your_secret_key_here_change_in_production
DEBUG=false
MAX_UPLOAD_SIZE=10485760
```

## 🚀 部署方式

### 方式一：本地运行（开发）

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 运行应用
streamlit run app/main.py
```

访问：http://localhost:8501

### 方式二：Streamlit Cloud部署（推荐）

1. **准备代码**
   - 确保项目已推送到GitHub
   - 根目录包含 `requirements.txt`

2. **部署步骤**
   - 访问 [Streamlit Cloud](https://share.streamlit.io)
   - 使用GitHub账号登录
   - 点击 "New app"
   - 选择仓库和分支
   - 主文件路径填写: `app/main.py`
   - 点击 "Deploy!"

3. **配置Secrets**
   - 在App Dashboard中点击 "Settings"
   - 选择 "Secrets"
   - 添加以下配置：
     ```toml
     SUPABASE_URL = "your_supabase_url"
     SUPABASE_KEY = "your_supabase_key"
     MIMO_API_KEY = "your_mimo_api_key"
     SECRET_KEY = "your_secret_key"
     ```
   - 点击 "Save"
   - 重新部署应用

### 方式三：Docker部署

创建 `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8501

# 运行应用
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

构建和运行：
```bash
# 构建镜像
docker build -t custom-home-ai .

# 运行容器
docker run -p 8501:8501 \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_KEY=your_key \
  -e MIMO_API_KEY=your_key \
  -e SECRET_KEY=your_secret \
  custom-home-ai
```

### 方式四：云服务器部署（Linux）

1. **安装系统依赖**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和pip
sudo apt install python3 python3-pip python3-venv git -y

# 安装Nginx（反向代理）
sudo apt install nginx -y
```

2. **部署应用**
```bash
# 创建应用目录
mkdir -p /opt/custom-home-ai
cd /opt/custom-home-ai

# 克隆代码
git clone <your-repo-url> .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 测试运行
streamlit run app/main.py --server.port 8501
```

3. **配置Systemd服务**

创建服务文件 `/etc/systemd/system/custom-home-ai.service`:
```ini
[Unit]
Description=Custom Home AI Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/custom-home-ai
Environment=PATH=/opt/custom-home-ai/venv/bin
Environment=PYTHONPATH=/opt/custom-home-ai
ExecStart=/opt/custom-home-ai/venv/bin/streamlit run app/main.py --server.port 8501 --server.address 127.0.0.1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用和启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable custom-home-ai
sudo systemctl start custom-home-ai
sudo systemctl status custom-home-ai
```

4. **配置Nginx反向代理**

创建配置文件 `/etc/nginx/sites-available/custom-home-ai`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        proxy_pass http://127.0.0.1:8501;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/custom-home-ai /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl reload nginx
```

5. **配置HTTPS（推荐）**

使用Certbot配置SSL：
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo systemctl enable certbot.timer
```

## 🔐 安全配置

### 1. 环境变量保护
- 不要将 `.env` 文件提交到Git
- 在 `.gitignore` 中添加：
```
.env
*.env
.venv/
venv/
```

### 2. 密码安全
- 使用强密码策略（至少8位，包含大小写字母、数字、符号）
- 定期更换密码
- 使用 `secrets` 模块生成密钥：
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. 数据库安全
- 使用Supabase的Row Level Security (RLS)限制数据访问
- 为不同用户创建不同权限的API密钥
- 定期备份数据

### 4. 网络安全
- 配置防火墙（UFW）：
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

- 配置Fail2ban防止暴力破解：
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

## 📊 性能优化

### 1. Streamlit配置优化
在 `.streamlit/config.toml` 中：
```toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 10

[browser]
serverAddress = "0.0.0.0"
serverPort = 8501

[runner]
fastReruns = true
```

### 2. 数据库优化
- 为常用查询字段创建索引
- 使用数据库连接池
- 启用查询缓存

### 3. 前端优化
- 压缩静态资源
- 启用CDN加速
- 使用图片懒加载

## 🔄 持续部署（CI/CD）

### GitHub Actions配置

创建 `.github/workflows/deploy.yml`：
```yaml
name: Deploy to Streamlit Cloud

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v
    
    - name: Deploy to Streamlit Cloud
      run: |
        echo "部署完成"
```

## 📈 监控和日志

### 1. 应用监控
在 `core/config.py` 中配置日志：
```python
import logging
import structlog

def setup_logger(name: str):
    """设置日志"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger(name)
```

### 2. 错误追踪
集成Sentry：
```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)
```

## 🔧 故障排查

### 常见问题

1. **数据库连接失败**
```bash
# 检查网络
ping your-supabase-url

# 检查配置
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

2. **AI服务调用失败**
- 检查API密钥余额
- 验证API端点可访问性
- 查看错误日志

3. **内存不足**
```bash
# 监控内存使用
free -h
top

# 增加交换空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 日志查看
```bash
# 查看应用日志
sudo journalctl -u custom-home-ai -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 📞 技术支持

如遇到问题，请检查：
1. 环境变量配置正确
2. 依赖版本匹配
3. 网络连接正常
4. 查看错误日志

---

**最后更新**: 2025-03-27  
**版本**: v2.0  
**维护者**: 技术团队
