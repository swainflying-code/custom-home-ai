@echo off
chcp 65001 >nul
echo ========================================
echo 初始化 Git 仓库并推送到 GitHub
echo ========================================

REM 进入项目目录
cd /d "%~dp0"

REM 1. 初始化 Git 仓库
echo 步骤 1/5: 初始化 Git 仓库...
git init
if errorlevel 1 goto error

REM 2. 添加所有文件
echo 步骤 2/5: 添加所有文件到 Git...
git add .
if errorlevel 1 goto error

REM 3. 创建初始提交
echo 步骤 3/5: 创建初始提交...
git commit -m "Initial commit: 全屋定制AI助手 V2.0 完整代码"
if errorlevel 1 goto error

REM 4. 设置远程仓库（提示用户输入）
:ask_repo
echo.
echo 请输入你的 GitHub 仓库地址（例如：https://github.com/yourname/custom-home-ai.git）
set /p REPO_URL="GitHub 仓库地址: "
if "%REPO_URL%"=="" goto ask_repo

echo 步骤 4/5: 连接到 GitHub 仓库...
git remote add origin %REPO_URL%
if errorlevel 1 (
    echo 警告：远程仓库已存在，将使用已存在的配置
)

REM 5. 推送到 GitHub
echo 步骤 5/5: 推送到 GitHub...
echo 这可能需要几秒钟...
git push -u origin main
if errorlevel 1 goto error

echo.
echo ========================================
echo ✅ 成功！代码已推送到 GitHub
echo ========================================
echo.
echo 下一步：
echo 1. 登录 https://streamlit.io/cloud
echo 2. 连接你的 GitHub 仓库
echo 3. 配置 Secrets（环境变量）
echo 4. 点击 Deploy
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo ❌ 发生错误
echo ========================================
echo 请检查错误信息并手动执行 Git 命令
echo.
pause
exit /b 1
