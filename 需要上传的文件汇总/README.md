# 全屋定制客户服务AI助手 V2.0

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)](https://streamlit.io/)
[![Supabase](https://img.shields.io/badge/Supabase-2.0+-green.svg)](https://supabase.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于AI大模型的全屋定制客户服务平台，深度整合客户洞察、设计辅助、智能报价、客户服务、数据统计和系统设置六大核心模块。

## 🎯 核心功能

### 1. 客户洞察 (Customer Insight)
- **智能信息采集**: 7步客户调研流程，支持表单状态持久化
- **AI深度分析**: 融合全球顶尖大师方法论的客户画像分析
- **标签化管理**: 自动客户标签生成和分类
- **数据可视化**: 客户数据统计和趋势分析

### 2. 设计辅助 (Design Assistant)
- **AI设计建议**: 基于客户信息生成个性化设计方案
- **文生图提示词**: 自动生成Midjourney/DALL-E专业提示词
- **参考图管理**: 支持多图上传和智能分析
- **设计历史追踪**: 完整的设计版本管理

### 3. 智能报价 (Smart Quoting)
- **规则引擎**: 基于配置规则的自动报价系统
- **报价历史**: 完整的报价记录和追踪
- **PDF导出**: 专业的报价单生成
- **价格分析**: 价格趋势和统计分析

### 4. 客户服务 (Customer Service)
- **跟进记录**: 客户跟进历史管理
- **预约系统**: 集成日历的预约管理
- **工单处理**: 问题和投诉处理流程
- **满意度调查**: 自动化客户满意度收集

### 5. 数据统计 (Statistics)
- **实时仪表板**: 关键指标实时监控
- **自定义报表**: 灵活的数据报表生成
- **趋势预测**: 基于历史数据的趋势分析
- **数据导出**: 支持多种格式的数据导出

### 6. 系统设置 (System Settings)
- **用户管理**: 多用户支持和角色权限管理
- **配置管理**: 系统参数配置和热更新
- **日志审计**: 完整的操作日志记录
- **系统监控**: 系统性能和健康状态监控

## 🏗️ 技术架构

### 技术栈
- **前端框架**: Streamlit 1.32+
- **数据库**: Supabase (PostgreSQL)
- **AI服务**: MIMO大模型 (兼容OpenAI API)
- **配置管理**: python-dotenv
- **数据验证**: Pydantic 2.0+
- **缓存系统**: 多级缓存架构
- **日志系统**: structlog + Python logging

### 系统架构
```
┌─────────────────────────────────────────────────────────────┐
│                         用户界面层                            │
│                    Streamlit + 自定义组件                      │
├─────────────────────────────────────────────────────────────┤
│                         业务逻辑层                            │
│  客户洞察  设计辅助  智能报价  客户服务  数据统计  系统设置  │
├─────────────────────────────────────────────────────────────┤
│                         核心服务层                            │
│  配置管理  数据库抽象  AI服务  认证授权  缓存管理  异常处理  │
├─────────────────────────────────────────────────────────────┤
│                         数据存储层                            │
│                  Supabase PostgreSQL数据库                     │
└─────────────────────────────────────────────────────────────┘
```

### 模块依赖
```
app/main.py (入口)
    └── core/ (核心服务)
        ├── config.py (配置管理)
        ├── database.py (数据库操作)
        ├── ai_service.py (AI服务)
        ├── auth.py (认证授权)
        └── cache.py (缓存管理)
    └── pages/ (业务页面)
    └── components/ (UI组件)
    └── utils/ (工具函数)
        ├── validators.py (数据验证)
        ├── formatters.py (数据格式化)
        └── helpers.py (通用辅助)
```

## 🚀 快速开始

### 前置条件
- Python 3.8+
- Supabase账号
- MIMO大模型API密钥

### 安装部署

1. **克隆项目**
```bash
git clone <repository-url>
cd custom-home-ai
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入配置信息
```

5. **运行应用**
```bash
streamlit run app/main.py
```

访问 http://localhost:8501

### Docker部署

```bash
# 构建镜像
docker build -t custom-home-ai .

# 运行容器
docker run -p 8501:8501 --env-file .env custom-home-ai
```

详细部署指南请参考 [DEPLOY.md](DEPLOY.md)

## 💡 核心特性

### AI智能分析
- **融合大师方法论**: 整合消费心理学、营销管理、设计美学、成交转化等顶尖理论
- **多维度分析**: 心理画像、决策特征、设计需求、预算评估、风险识别等8个维度
- **可执行建议**: 提供具体、可落地的跟进策略和沟通方案

### 数据驱动设计
- **客户画像**: 自动化标签生成和分类
- **偏好分析**: 深度挖掘客户设计偏好和生活方式
- **趋势预测**: 基于历史数据的客户需求预测

### 性能优化
- **多级缓存**: 数据库查询缓存、AI结果缓存、页面缓存
- **异步处理**: 非阻塞的AI调用和图片处理
- **数据分页**: 大数据量分页加载，提升响应速度

### 安全可靠
- **认证授权**: JWT令牌 + RBAC权限模型
- **数据验证**: Pydantic严格类型验证
- **错误处理**: 完善的异常捕获和恢复机制
- **操作审计**: 完整的操作日志记录

## 📊 数据模型

### 客户模型 (Customer)
```python
{
    "id": "uuid",
    "customer_code": "BINK-20250327-XXXX",
    "name": "客户姓名",
    "gender": "男/女",
    "age_group": "26-35岁",
    "house_type": "普通住宅",
    "renovation_type": "全新装",
    "custom_budget": "10-20万",
    "style_preference": ["现代简约", "轻奢"],
    "color_preference": ["亮白色", "浅暖色"],
    "ai_analysis_result": {...},
    "created_at": "2025-03-27T10:00:00",
    "updated_at": "2025-03-27T10:00:00"
}
```

### 设计需求模型 (DesignRequest)
```python
{
    "id": "uuid",
    "customer_id": "customer_uuid",
    "design_scope": ["橱柜", "衣柜"],
    "design_adjustment": "设计师调整说明",
    "ai_design_suggestion": "AI设计建议",
    "prompt_keywords": "文生图提示词",
    "reference_images": ["image_url1", "image_url2"],
    "status": "待处理/设计中/已完成",
    "created_at": "2025-03-27T10:00:00"
}
```

## 🔧 开发指南

### 代码规范
- **类型注解**: 所有函数必须包含类型提示
- **代码格式**: 使用Black进行代码格式化
- **导入排序**: 使用isort进行导入排序
- **静态检查**: 使用mypy进行类型检查

### 提交规范
```bash
# 安装提交钩子
pre-commit install

# 手动运行检查
pre-commit run --all-files
```

### 测试
```bash
# 运行测试
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

## 🎨 UI/UX设计

### 设计原则
- **简洁专业**: 简洁的界面，专业的体验
- **响应式**: 适配桌面和移动端
- **一致性**: 统一的视觉风格和交互模式
- **可访问性**: 符合WCAG 2.1标准

### 色彩系统
- **主色调**: #d4af37（金色）
- **辅助色**: #f0f2f0（浅灰）
- **文本色**: #2d342d（深灰）
- **强调色**: #b8962e（深金）

### 组件库
- **表单组件**: 自定义表单字段和验证
- **数据展示**: 表格、卡片、图表组件
- **反馈组件**: 加载、提示、对话框
- **导航组件**: 侧边栏、面包屑、分页

## 📈 性能指标

### 响应时间
- **页面加载**: < 1.5秒
- **AI分析**: < 5秒
- **数据查询**: < 1秒
- **表单提交**: < 2秒

### 系统容量
- **并发用户**: 50+
- **客户记录**: 10万+
- **图片存储**: 支持S3扩展

### 可用性
- **系统可用性**: 99.5%
- **数据可靠性**: 99.9%
- **备份恢复**: RPO < 1小时

## 🔒 安全特性

### 认证授权
- **JWT令牌**: 无状态认证机制
- **RBAC权限**: 基于角色的访问控制
- **密码策略**: 强密码要求和加密存储
- **会话管理**: 自动过期和续期

### 数据安全
- **传输加密**: HTTPS/TLS 1.3
- **存储加密**: 数据库静态加密
- **敏感数据**: 联系方式脱敏显示
- **访问日志**: 完整的操作审计

### 应用安全
- **输入验证**: 严格的输入验证和过滤
- **XSS防护**: 内容安全策略(CSP)
- **CSRF防护**: 跨站请求伪造保护
- **速率限制**: API调用频率限制

## 🤝 贡献指南

1. **Fork项目**
2. **创建分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **创建Pull Request**

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- **MIMO大模型**: 提供AI分析能力
- **Supabase**: 提供数据库服务
- **Streamlit**: 提供Web框架
- **开源社区**: 所有贡献者和用户

## 📞 联系方式

- **项目地址**: [GitHub Repository](https://github.com/your-org/custom-home-ai)
- **问题反馈**: [Issues](https://github.com/your-org/custom-home-ai/issues)
- **功能建议**: [Discussions](https://github.com/your-org/custom-home-ai/discussions)

## 🔄 更新日志

### v2.0 (2025-03-27)
- ✅ 重构为模块化架构
- ✅ 添加类型注解和Pydantic验证
- ✅ 实现多级缓存机制
- ✅ 增强错误处理和日志记录
- ✅ 优化数据库操作层
- ✅ 改进UI/UX设计
- ✅ 添加完整的部署文档
- ✅ 实现表单状态持久化

### v1.05 (2025-03-20)
- 初始版本，单体架构
- 基础客户调研功能
- AI分析功能
- 设计辅助功能

---

**项目状态**: 🚀 活跃开发中  
**最后更新**: 2025-03-27  
**版本**: v2.0  
**作者**: BINK不锈钢定制技术团队
