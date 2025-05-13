@echo off
chcp 936 > nul
color 0A

echo 正在启动PCIe设备伪装工具增强版...
echo.

REM 检查Python是否安装
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python未安装或未添加到环境变量中！
    echo 请安装Python并确保将其添加到PATH环境变量。
    echo.
    pause
    exit /b
)

REM 清除Python的缓存文件，确保使用最新代码
if exist __pycache__ (
    echo 清理缓存文件...
    rmdir /S /Q __pycache__
)

REM 直接启动程序
echo 正在启动程序，请稍候...
start "" python pcie_spoof_gui_enhanced.py

echo 启动完成！ 