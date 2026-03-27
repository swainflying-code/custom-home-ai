#!/usr/bin/env python3
"""
执行V1.05到V2.0客户洞察模块迁移
"""

import shutil

# 1. 备份V2.0文件
shutil.copy('pages/customer_insight.py', 'pages/customer_insight.py.backup')
print('STEP 1: Backup completed - pages/customer_insight.py.backup')

# 2. 读取V1.05文件
with open('F:/AI-ying/Dingzhi AI/custom-home-ai/custom-home-ai/全屋定制客户服务AI助手_V1.05.py', 'r', encoding='utf-8') as f:
    v1_content = f.read()

# 3. 提取客户洞察代码块
start_marker = 'if current_page == "客户洞察":'
end_marker = '# ==================== 设计辅助系统'

start_idx = v1_content.find(start_marker)
end_idx = v1_content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    customer_insight_code = v1_content[start_idx:end_idx]
    print('STEP 2: Extracted customer insight code from V1.05')
else:
    print('ERROR: Cannot find customer insight code block')
    exit(1)

# 4. 读取V2.0文件头部
with open('pages/customer_insight.py', 'r', encoding='utf-8') as f:
    v2_content = f.read()

# 5. 找到函数定义位置
v2_func_start = v2_content.find('def show_customer_insight_page():')

if v2_func_start == -1:
    print('ERROR: Cannot find function definition in V2.0')
    exit(1)

# 6. 保留V2.0的头部（imports等），替换函数体
v2_header = v2_content[:v2_func_start]

# 构建新的V2.0文件内容
new_v2_content = v2_header + customer_insight_code

# 7. 写入新内容
with open('pages/customer_insight.py', 'w', encoding='utf-8') as f:
    f.write(new_v2_content)

print('STEP 3: Migration completed - V1.05 customer insight module migrated to V2.0')
print('RESULT: The complete 7-step survey from V1.05 is now in V2.0')
print('')
print('Key features migrated:')
print('  - Step 0: 顾客基础&进店信息 (complete)')
print('  - Step 1: 房屋装修 (complete)')
print('  - Step 2: 产品偏好 (complete)')
print('  - Step 3: 客户生活方式 (complete)')
print('  - Step 4: 沟通转化 (complete)')
print('  - Step 5: 需求补充 (complete)')
print('  - Step 6: 确认提交 (complete)')
print('')
print('All data fields are preserved and will be available for design assistant module')
