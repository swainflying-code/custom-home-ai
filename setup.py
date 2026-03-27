#!/usr/bin/env python3
"""
全屋定制客户服务AI助手 - 快速开始脚本
自动化完成项目初始化和配置
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse
import json
import time


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}{Colors.END}\n")


def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_warning(text: str):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text: str):
    """打印信息"""
    print(f"ℹ️  {text}")


def check_python_version():
    """检查Python版本"""
    print_info("检查Python版本...")
    
    if sys.version_info < (3, 8):
        print_error("需要Python 3.8或更高版本")
        sys.exit(1)
    
    print_success(f"Python版本符合要求: {sys.version}")


def check_command(cmd: str, description: str) -> bool:
    """检查命令是否可用"""
    print_info(f"检查 {description}...")
    
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        print_success(f"{description} 可用")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error(f"{description} 未找到")
        return False


def install_dependencies():
    """安装依赖"""
    print_header("安装Python依赖")
    
    if not os.path.exists("requirements.txt"):
        print_error("requirements.txt 文件不存在")
        sys.exit(1)
    
    print_info("开始安装依赖，这可能需要几分钟...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("依赖安装成功")
        else:
            print_error("依赖安装失败")
            print(result.stderr)
            sys.exit(1)
    except Exception as e:
        print_error(f"安装过程出错: {e}")
        sys.exit(1)


def check_environment_file():
    """检查环境变量文件"""
    print_header("检查环境配置")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_success("发现 .env 文件")
        
        # 检查关键配置
        with open(env_file) as f:
            content = f.read()
            
        required_vars = [
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "MIMO_API_KEY"
        ]
        
        missing = []
        for var in required_vars:
            if var not in content or f"{var}=" in content or f"{var} =" in content:
                missing.append(var)
        
        if missing:
            print_warning(f"以下配置需要填写: {', '.join(missing)}")
        else:
            print_success("所有必要配置都已填写")
        
        return True
    else:
        print_warning("未找到 .env 文件")
        
        if env_example.exists():
            print_info("从 .env.example 创建 .env...")
            shutil.copy(env_example, env_file)
            print_success("已创建 .env 文件，请编辑填写配置")
            print_warning("请先编辑 .env 文件，填写必要的配置信息")
            return False
        else:
            print_error("未找到 .env.example 文件")
            return False


def test_database_connection():
    """测试数据库连接"""
    print_header("测试数据库连接")
    
    try:
        # 延迟导入，确保依赖已安装
        from core.config import config
        from core.database import DatabaseManager
        
        db = DatabaseManager()
        
        # 尝试简单查询
        result = db.count("customers")
        print_success(f"数据库连接成功 (当前有 {result} 条客户记录)")
        return True
    except Exception as e:
        print_error(f"数据库连接失败: {e}")
        print_info("请检查 SUPABASE_URL 和 SUPABASE_KEY 配置")
        return False


def test_ai_connection():
    """测试AI服务连接"""
    print_header("测试AI服务连接")
    
    try:
        from core.ai_service import ai_service
        
        # 简单测试
        test_data = {
            "customer_name": "测试客户",
            "gender": "男",
            "age_group": "26-35岁"
        }
        
        print_info("正在测试AI服务（这可能需要几秒）...")
        
        # 使用小数据测试
        result = ai_service.analyze_customer(test_data)
        
        if "error" not in result:
            print_success("AI服务连接成功")
            return True
        else:
            print_error(f"AI服务测试失败: {result.get('error')}")
            print_info("请检查 MIMO_API_KEY 配置")
            return False
    except Exception as e:
        print_error(f"AI服务测试失败: {e}")
        return False


def create_directories():
    """创建必要目录"""
    print_header("创建项目目录")
    
    directories = [
        "logs",
        "temp",
        "uploads",
        "exports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print_success(f"创建目录: {directory}")


def show_configuration_help():
    """显示配置帮助"""
    print_header("配置帮助")
    
    print("""
请先完成以下配置：

1. **Supabase配置**
   - 访问 https://supabase.com
   - 创建新项目
   - 获取项目URL和API密钥
   - 填入 .env 文件的 SUPABASE_URL 和 SUPABASE_KEY

2. **MIMO大模型配置**
   - 访问 https://xiaomimimo.com
   - 注册并获取API密钥
   - 填入 .env 文件的 MIMO_API_KEY

3. **应用配置**
   - 生成SECRET_KEY（可选）
   - 配置其他参数（可选）

配置完成后，重新运行此脚本。
""")


def show_usage_examples():
    """显示使用示例"""
    print_header("使用示例")
    
    print("""
启动应用:
    streamlit run app/main.py

访问地址:
    http://localhost:8501

默认登录信息:
    用户名: admin
    密码: admin123

其他命令:
    # 测试数据库连接
    python -c "from core.database import db; print('OK' if db.client else 'FAIL')"

    # 测试AI服务
    python -c "from core.ai_service import ai_service; print('OK' if ai_service.client else 'FAIL')"
""")


def run_full_setup():
    """运行完整设置流程"""
    print_header("全屋定制客户服务AI助手 - 快速开始")
    print("版本: V2.0\n")
    
    # 检查Python版本
    check_python_version()
    
    # 检查必要命令
    all_good = True
    all_good &= check_command("pip", "pip包管理器")
    
    # 安装依赖
    install_dependencies()
    
    # 创建目录
    create_directories()
    
    # 检查环境文件
    if not check_environment_file():
        show_configuration_help()
        print_warning("请编辑 .env 文件后重新运行此脚本")
        return False
    
    # 测试连接
    db_ok = test_database_connection()
    ai_ok = test_ai_connection()
    
    if db_ok and ai_ok:
        print_success("所有测试通过！系统已准备就绪")
    else:
        print_warning("部分测试未通过，请检查配置")
    
    # 显示使用示例
    show_usage_examples()
    
    return db_ok and ai_ok


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="全屋定制客户服务AI助手 - 快速开始脚本")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="仅检查环境，不执行安装"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="跳过连接测试"
    )
    
    args = parser.parse_args()
    
    try:
        if args.check_only:
            print_header("环境检查模式")
            check_python_version()
            check_command("pip", "pip包管理器")
            check_environment_file()
        else:
            run_full_setup()
    
    except KeyboardInterrupt:
        print("\n" + Colors.YELLOW + "操作已取消" + Colors.END)
        sys.exit(0)
    except Exception as e:
        print_error(f"发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
