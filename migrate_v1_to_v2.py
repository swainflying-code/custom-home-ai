#!/usr/bin/env python3
"""
V1.05到V2.0客户洞察模块迁移对比工具
"""

import os
import sys

def extract_v1_customer_insight(v1_file_path):
    """从V1.05提取客户洞察7个步骤的完整代码"""
    with open(v1_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找客户洞察代码块
    start_marker = 'if current_page == "客户洞察":'
    end_marker = '# ==================== 设计辅助系统'  # 客户洞察结束位置
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("❌ 无法找到客户洞察代码块")
        return None
    
    customer_insight_code = content[start_idx:end_idx]
    
    # 提取7个步骤的字段定义
    steps_data = []
    
    # 步骤列表
    step_names = [
        "顾客基础&进店信息",  # 步骤0
        "房屋装修",  # 步骤1
        "产品偏好",  # 步骤2
        "客户生活方式",  # 步骤3
        "沟通转化",  # 步骤4
        "需求补充",  # 步骤5
        "确认提交"  # 步骤6
    ]
    
    print("=" * 80)
    print("V1.05 客户洞察7大栏目分析")
    print("=" * 80)
    
    for i, step_name in enumerate(step_names):
        step_marker = f"# 步骤{i}：{step_name}"
        next_step_marker = f"# 步骤{i+1}：" if i < len(step_names) - 1 else "# 按钮"
        
        step_start = content.find(step_marker)
        step_end = content.find(next_step_marker) if next_step_marker else len(content)
        
        if step_start != -1:
            step_code = content[step_start:step_end]
            
            # 提取字段
            import re
            # 查找所有 st.text_input, st.radio, st.multiselect
            fields = []
            
            # text_input
            text_inputs = re.findall(r'st\.text_input\([^)]+\)', step_code)
            for field in text_inputs:
                label_match = re.search(r'["\']([^"\']+)["\']', field)
                if label_match:
                    fields.append(f"文本: {label_match.group(1)}")
            
            # radio
            radios = re.findall(r'st\.radio\([^)]+\)', step_code, re.DOTALL)
            for field in radios:
                label_match = re.search(r'["\']([^"\']+)["\']', field)
                if label_match and label_match.group(1) not in ["", " "]:
                    fields.append(f"单选: {label_match.group(1)}")
            
            # multiselect
            multiselects = re.findall(r'st\.multiselect\([^)]+\)', step_code, re.DOTALL)
            for field in multiselects:
                label_match = re.search(r'["\']([^"\']+)["\']', field)
                if label_match and label_match.group(1):
                    fields.append(f"多选: {label_match.group(1)}")
            
            print(f"\n📋 步骤{i}: {step_name}")
            print(f"   字段数量: {len(fields)}")
            for field in fields[:5]:  # 只显示前5个字段
                print(f"   - {field}")
            if len(fields) > 5:
                print(f"   ... 还有 {len(fields) - 5} 个字段")
            
            steps_data.append({
                "step": i,
                "name": step_name,
                "field_count": len(fields),
                "fields": fields,
                "code": step_code
            })
    
    return steps_data

if __name__ == "__main__":
    v1_file = "F:/AI-ying/Dingzhi AI/custom-home-ai/custom-home-ai/全屋定制客户服务AI助手_V1.05.py"
    
    if os.path.exists(v1_file):
        steps = extract_v1_customer_insight(v1_file)
        
        if steps:
            print(f"\n✅ 成功提取 {len(steps)} 个步骤")
            print("\n下一步：将完整代码迁移到V2.0的 pages/customer_insight.py")
    else:
        print(f"❌ 找不到V1.05文件: {v1_file}")
