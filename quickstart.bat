@echo off
REM 全屋定制客户服务AI助手 - Windows快速启动脚本
REM 版本: V2.0
REM 生成时间: 2025-03-27

echo ============================================================
echo    全屋定制客户服务AI助手 V2.0 - 快速启动
echo ============================================================
echo.

REM 检查Python版本
echo [1/7] 检查Python版本...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python 3.8+并添加到系统环境变量
    pause
    exit /b 1
)
echo ✅ Python版本检查通过
echo.

REM 检查虚拟环境
echo [2/7] 检查虚拟环境...
if exist "venv\Scripts\activate.bat" (
    echo ✅ 虚拟环境已存在
) else (
    echo ⚠️  虚拟环境不存在，将创建新环境
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)
echo.

REM 激活虚拟环境
echo [3/7] 激活虚拟环境...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)
echo ✅ 虚拟环境激活成功
echo.

REM 安装依赖
echo [4/7] 安装Python依赖...
if exist "requirements.txt" (
    pip install -r requirements.txt >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
) else (
    echo ❌ requirements.txt 文件不存在
    pause
    exit /b 1
)
echo.

REM 检查环境变量文件
echo [5/7] 检查环境变量配置...
if exist ".env" (
    echo ✅ .env 文件已存在
    
    REM 检查关键配置
    findstr "SUPABASE_URL=your" .env >nul 2>&1
    if %errorlevel% equ 0 (
        echo ⚠️  .env 文件包含默认配置，请检查并修改为实际配置
        echo.
        echo 需要配置的项目：
        echo - SUPABASE_URL
        echo - SUPABASE_KEY
        echo - MIMO_API_KEY
        echo.
        set /p "continue=是否继续启动应用？(Y/N): "
        if /i not "%continue%"=="Y" (
            echo.
            echo 请先编辑 .env 文件，填写必要的配置信息
            pause
            exit /b 1
        )
    )
) else (
    if exist ".env.example" (
        echo ⚠️  未发现 .env 文件，将从 .env.example 创建
        copy .env.example .env >nul
        echo.
        echo ✅ 已创建 .env 文件
        echo ⚠️  请编辑 .env 文件，填写必要的配置信息：
        echo - SUPABASE_URL
        echo - SUPABASE_KEY
        echo - MIMO_API_KEY
        echo.
        pause
        exit /b 0
    ) else (
        echo ❌ 未找到 .env.example 文件
        pause
        exit /b 1
    )
)
echo.

REM 创建必要目录
echo [6/7] 创建必要目录...
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp
if not exist "uploads" mkdir uploads
if not exist "exports" mkdir exports
echo ✅ 目录创建完成
echo.

REM 启动应用
echo [7/7] 启动应用...
echo.
echo ============================================================
echo    正在启动全屋定制客户服务AI助手 V2.0
echo ============================================================
echo.
echo 请稍候，应用启动可能需要30-60秒
echo.
echo 启动后请访问: http://localhost:8501
echo.
echo 默认登录信息：
echo   用户名: admin
echo   密码: admin123
echo.
echo 如需修改，请在 app/main.py 中修改
echo ============================================================
echo.

streamlit run app/main.py --server.port 8501 --server.headless true

REM 如果启动失败，显示错误信息
if %errorlevel% neq 0 (
    echo.
    echo ❌ 应用启动失败
    echo.
    echo 可能的原因：
    echo 1. 环境变量配置错误
    echo 2. 依赖安装不完整
    echo 3. 端口8501被占用
    echo 4. Python环境有问题
    echo.
    echo 请查看错误信息，或检查 logs/app.log 日志文件
    pause
    exit /b 1
)

pause