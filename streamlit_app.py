"""
Streamlit Cloud 入口文件

Streamlit Cloud 默认寻找根目录的 streamlit_app.py。
此文件设置好路径后，直接把 app/main.py 的代码在当前全局作用域中执行，
避免 import 导致的 __file__ 路径偏移问题。
"""

import os
import sys

# 项目根目录（即本文件所在目录）
project_root = os.path.dirname(os.path.abspath(__file__))

# 确保 core / utils / pages 等包都可以被正确 import
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 直接执行 app/main.py，__file__ 指向 main.py 自身，路径计算完全正确
_main_path = os.path.join(project_root, "app", "main.py")
with open(_main_path, "r", encoding="utf-8") as _f:
    exec(compile(_f.read(), _main_path, "exec"))  # noqa: S102
