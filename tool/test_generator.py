#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试生成模块
负责生成PCIe设备的测试脚本
"""

import os
import re

class TestGenerator:
    """测试脚本生成类"""
    
    def __init__(self):
        """初始化测试生成模块"""
        self.template = self._load_test_template()
        
    def _load_test_template(self):
        """加载测试脚本模板"""
        return """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
PCIe设备自动测试脚本
自动生成的设备测试代码: {device_name}
生成时间: {timestamp}

此脚本用于测试伪装的PCIe设备是否正常工作,
1. 配置空间检测与验证
2. BAR空间访问测试
3. 中断功能验证
4. 设备特定功能测试
\"\"\"

import os
import sys
import time
import argparse
import subprocess
import struct
from datetime import datetime

# 设备信息
DEVICE_NAME = "{device_name}"
VENDOR_ID = "0x{vendor_id}"
DEVICE_ID = "0x{device_id}"
CLASS_CODE = "0x{class_code}"

class DeviceTester:
    \"\"\"PCIe设备测试类\"\"\"
    
    def __init__(self, args):
        \"\"\"初始化测试类\"\"\"
        self.args = args
        self.device_path = None
        self.mem_path = None
        self.bar0_size = 0
        self.device_found = False
        
    def find_device(self):
        \"\"\"查找目标设备\"\"\"
        print(f"正在查找设备: VID={{VENDOR_ID}}, DID={{DEVICE_ID}}")
        
        try:
            # 在Linux系统上使用lspci查找设备
            if os.name == "posix":
                cmd = f"lspci -d {{VENDOR_ID}}:{{DEVICE_ID}} -vnn"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if DEVICE_ID.replace("0x", "") in result.stdout:
                    # 设备找到，提取BDF号
                    lines = result.stdout.strip().split("\\n")
                    if lines:
                        bdf = lines[0].split()[0]  # 获取bus:device.function
                        self.device_path = f"/sys/bus/pci/devices/0000:{{bdf}}"
                        self.mem_path = f"/sys/bus/pci/devices/0000:{{bdf}}/resource0"
                        
                        # 获取BAR0大小
                        resource_path = f"/sys/bus/pci/devices/0000:{{bdf}}/resource"
                        with open(resource_path, "r") as f:
                            resource_info = f.readlines()
                            if resource_info:
                                # 解析资源信息
                                bar0_info = resource_info[0].strip().split()
                                if len(bar0_info) >= 2:
                                    start = int(bar0_info[0], 16)
                                    end = int(bar0_info[1], 16)
                                    self.bar0_size = end - start + 1
                        
                        self.device_found = True
                        print(f"✅ 设备已找到: {{bdf}}")
                        print(f"✅ BAR0大小: {{self.bar0_size}} 字节")
                        return True
            
            # 在Windows系统上使用PowerShell查找设备
            elif os.name == "nt":
                cmd = f"Get-PnpDevice | Where-Object {{ $_.HardwareID -like '*VEN_{{VENDOR_ID.replace('0x', '')}}*&DEV_{{DEVICE_ID.replace('0x', '')}}*' }}"
                result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
                
                if f"VEN_{{VENDOR_ID.replace('0x', '')}}" in result.stdout:
                    # 设备找到
                    self.device_found = True
                    print(f"✅ 设备已找到（Windows）")
                    
                    # Windows通常使用devcon或专用工具访问设备
                    print("ℹ️ 在Windows上进行详细测试需要专用驱动程序")
                    return True
            
            print("❌ 未找到目标设备")
            return False
            
        except Exception as e:
            print(f"❌ 查找设备时出错: {{str(e)}}")
            return False
    
    def test_config_space(self):
        \"\"\"测试设备配置空间\"\"\"
        if not self.device_found:
            print("❌ 未找到设备，无法测试配置空间")
            return False
            
        print("正在测试配置空间...")
        
        try:
            if os.name == "posix":
                # 在Linux上读取配置空间
                config_path = os.path.join(self.device_path, "config")
                if not os.path.exists(config_path):
                    print(f"❌ 配置空间文件不存在: {{config_path}}")
                    return False
                
                with open(config_path, "rb") as f:
                    config_data = f.read(256)  # 读取256字节配置空间
                
                # 验证关键字段
                vendor_id = struct.unpack("<H", config_data[0:2])[0]
                device_id = struct.unpack("<H", config_data[2:4])[0]
                command = struct.unpack("<H", config_data[4:6])[0]
                status = struct.unpack("<H", config_data[6:8])[0]
                revision = config_data[8]
                class_code = (config_data[11] << 16) | (config_data[10] << 8) | config_data[9]
                
                print(f"✅ Vendor ID: 0x{{vendor_id:04x}} (预期: {{VENDOR_ID}})")
                print(f"✅ Device ID: 0x{{device_id:04x}} (预期: {{DEVICE_ID}})")
                print(f"✅ 命令寄存器: 0x{{command:04x}}")
                print(f"✅ 状态寄存器: 0x{{status:04x}}")
                print(f"✅ 修订版本: 0x{{revision:02x}}")
                print(f"✅ 类别代码: 0x{{class_code:06x}} (预期: {{CLASS_CODE}})")
                
                # 验证ID匹配
                if vendor_id != int(VENDOR_ID, 16):
                    print(f"❌ Vendor ID不匹配: 0x{{vendor_id:04x}} ≠ {{VENDOR_ID}}")
                    return False
                    
                if device_id != int(DEVICE_ID, 16):
                    print(f"❌ Device ID不匹配: 0x{{device_id:04x}} ≠ {{DEVICE_ID}}")
                    return False
                
                return True
                
            elif os.name == "nt":
                # Windows需要专用工具
                print("ℹ️ 在Windows上测试配置空间需要专用工具")
                return True
                
        except Exception as e:
            print(f"❌ 测试配置空间时出错: {{str(e)}}")
            return False
    
    def test_bar_access(self):
        \"\"\"测试BAR空间访问\"\"\"
        if not self.device_found:
            print("❌ 未找到设备，无法测试BAR空间")
            return False
            
        print("正在测试BAR空间访问...")
        
        try:
            if os.name == "posix" and self.mem_path and os.path.exists(self.mem_path):
                # 在Linux上访问BAR空间
                with open(self.mem_path, "rb") as f:
                    # 读取状态寄存器 (通常在偏移0x00处)
                    f.seek(0)
                    status_data = f.read(4)
                    status_value = struct.unpack("<I", status_data)[0]
                    print(f"✅ 状态寄存器值: 0x{{status_value:08x}}")
                    
                    # 读取版本信息 (通常在偏移0x0C处)
                    f.seek(0x0C)
                    version_data = f.read(4)
                    version_value = struct.unpack("<I", version_data)[0]
                    print(f"✅ 版本信息值: 0x{{version_value:08x}}")
                    
                    {bar_access_tests}
                
                return True
                
            else:
                print("ℹ️ 无法在当前系统上直接访问BAR空间")
                return True
                
        except Exception as e:
            print(f"❌ 测试BAR空间访问时出错: {{str(e)}}")
            return False
    
    def test_interrupts(self):
        \"\"\"测试中断功能\"\"\"
        if not self.device_found:
            print("❌ 未找到设备，无法测试中断功能")
            return False
            
        print("正在测试中断功能...")
        print("ℹ️ 完整的中断测试需要加载驱动程序，这里只执行基本检查")
        
        try:
            if os.name == "posix" and self.device_path:
                # 检查中断分配
                msi_irqs_path = os.path.join(self.device_path, "msi_irqs")
                if os.path.exists(msi_irqs_path):
                    irqs = os.listdir(msi_irqs_path)
                    print(f"✅ 设备已分配MSI中断: {{', '.join(irqs)}}")
                else:
                    print("ℹ️ 设备未使用MSI中断")
                    
                # 检查传统中断
                irq_path = os.path.join(self.device_path, "irq")
                if os.path.exists(irq_path):
                    with open(irq_path, "r") as f:
                        irq = f.read().strip()
                        if irq and irq != "0":
                            print(f"✅ 设备已分配传统中断: {{irq}}")
                        else:
                            print("ℹ️ 设备未使用传统中断")
                
                return True
                
            else:
                print("ℹ️ 无法在当前系统上检查中断分配")
                return True
                
        except Exception as e:
            print(f"❌ 测试中断功能时出错: {{str(e)}}")
            return False
    
    def test_device_functionality(self):
        \"\"\"测试设备特定功能\"\"\"
        if not self.device_found:
            print("❌ 未找到设备，无法测试设备功能")
            return False
            
        print("正在测试设备特定功能...")
        
        {device_specific_tests}
        
        return True
    
    def run_all_tests(self):
        \"\"\"运行所有测试\"\"\"
        print(f"=== 开始测试设备: {{DEVICE_NAME}} ===")
        print(f"时间: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
        print("")
        
        # 查找设备
        if not self.find_device():
            print("❌ 设备未找到，测试中止")
            return False
            
        # 测试配置空间
        config_result = self.test_config_space()
        print("")
        
        # 测试BAR空间
        bar_result = self.test_bar_access()
        print("")
        
        # 测试中断
        interrupt_result = self.test_interrupts()
        print("")
        
        # 测试设备功能
        functionality_result = self.test_device_functionality()
        print("")
        
        # 汇总结果
        print("=== 测试结果汇总 ===")
        print(f"配置空间测试: {'✅ 通过' if config_result else '❌ 失败'}")
        print(f"BAR空间测试: {'✅ 通过' if bar_result else '❌ 失败'}")
        print(f"中断功能测试: {'✅ 通过' if interrupt_result else '❌ 失败'}")
        print(f"设备功能测试: {'✅ 通过' if functionality_result else '❌ 失败'}")
        print("")
        
        overall_result = config_result and bar_result and interrupt_result and functionality_result
        print(f"总体结果: {'✅ 通过' if overall_result else '❌ 失败'}")
        
        return overall_result


def main():
    \"\"\"主函数\"\"\"
    parser = argparse.ArgumentParser(description=f"{{DEVICE_NAME}} 自动测试工具")
    parser.add_argument("--skip-config", action="store_true", help="跳过配置空间测试")
    parser.add_argument("--skip-bar", action="store_true", help="跳过BAR空间测试")
    parser.add_argument("--skip-interrupt", action="store_true", help="跳过中断测试")
    parser.add_argument("--skip-functionality", action="store_true", help="跳过设备功能测试")
    
    args = parser.parse_args()
    
    tester = DeviceTester(args)
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    def generate_test_script(self, device_config, output_file):
        """生成测试脚本"""
        try:
            device_name = device_config.get("name", "自定义设备")
            vendor_id = device_config.get("vendor_id", "FFFF")
            device_id = device_config.get("device_id", "FFFF")
            class_code = device_config.get("class_code", "000000")
            device_type = device_config.get("type", "custom")
            
            # 生成BAR访问测试代码
            bar_access_tests = self._generate_bar_access_tests(device_config)
            
            # 生成设备特定测试代码
            device_specific_tests = self._generate_device_specific_tests(device_type, device_config)
            
            # 生成最终代码
            code = self.template.format(
                device_name=device_name,
                timestamp=__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                vendor_id=vendor_id,
                device_id=device_id,
                class_code=class_code,
                bar_access_tests=bar_access_tests,
                device_specific_tests=device_specific_tests
            )
            
            # 写入输出文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            # 设置执行权限（Linux）
            if os.name == "posix":
                os.chmod(output_file, 0o755)
            
            print(f"✅ 测试脚本已生成: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 生成测试脚本失败: {str(e)}")
            return False
    
    def _generate_bar_access_tests(self, device_config):
        """生成BAR访问测试代码"""
        registers = device_config.get("key_registers", [])
        
        # 生成每个关键寄存器的读取代码
        test_code = []
        
        # 如果没有特定寄存器，使用默认测试
        if not registers:
            return """# 默认BAR寄存器读取测试
                    # 尝试读取一些常见的寄存器偏移
                    for offset in [0x00, 0x04, 0x08, 0x0C, 0x10, 0x14]:
                        f.seek(offset)
                        reg_data = f.read(4)
                        reg_value = struct.unpack("<I", reg_data)[0]
                        print(f"✅ 偏移 0x{offset:04x} 的寄存器值: 0x{reg_value:08x}")"""
        
        # 为每个寄存器添加读取测试
        for reg in registers:
            addr = reg["addr"].replace("0x", "")
            name = reg.get("name", f"寄存器_{addr}")
            
            # 将16进制地址字符串转换为整数
            try:
                offset = int(addr, 16)
                test_code.append(f"""
                    # 读取{name}
                    f.seek(0x{addr})
                    reg_data = f.read(4)
                    reg_value = struct.unpack("<I", reg_data)[0]
                    print(f"✅ {name}值: 0x{{reg_value:08x}}")""")
            except ValueError:
                # 如果地址无法解析，跳过
                continue
                
        return "\n".join(test_code)
    
    def _generate_device_specific_tests(self, device_type, device_config):
        """生成设备特定的功能测试代码"""
        if device_type == "nic" or device_type == "wifi":
            # 网络设备特定测试
            return """print("正在执行网络设备特定测试...")
            
        try:
            if os.name == "posix" and self.mem_path and os.path.exists(self.mem_path):
                with open(self.mem_path, "rb+") as f:
                    # 1. 读取MAC地址
                    # MAC地址通常存储在特定寄存器中，这里假设在偏移0x40-0x48
                    f.seek(0x40)
                    mac_data = f.read(6)
                    mac_addr = ":".join([f"{b:02x}" for b in mac_data])
                    print(f"✅ MAC地址: {mac_addr}")
                    
                    # 2. 测试控制寄存器写入
                    # 写入设备控制寄存器 (通常在偏移0x04处)
                    f.seek(0x04)
                    control_value = 0x00000001  # 启用设备
                    f.write(struct.pack("<I", control_value))
                    
                    # 重新读取确认写入成功
                    f.seek(0x04)
                    control_read = struct.unpack("<I", f.read(4))[0]
                    if (control_read & 0x1) == 0x1:
                        print("✅ 控制寄存器写入测试通过")
                    else:
                        print(f"❌ 控制寄存器写入测试失败: 写入0x{control_value:08x}，读回0x{control_read:08x}")
                        
                    # 重置设备
                    f.seek(0x04)
                    f.write(struct.pack("<I", 0x00000000))
            else:
                print("ℹ️ 无法在当前系统上执行详细的网络设备测试")
                
            # 检查系统是否识别了网络接口
            if os.name == "posix":
                result = subprocess.run(["ip", "link", "show"], capture_output=True, text=True)
                if result.returncode == 0:
                    print("ℹ️ 系统网络接口列表:")
                    for line in result.stdout.strip().split("\\n"):
                        if "state" in line:
                            print(f"  {line.strip()}")
            
        except Exception as e:
            print(f"❌ 网络设备测试出错: {str(e)}")"""
            
        elif device_type == "storage":
            # 存储设备特定测试
            return """print("正在执行存储设备特定测试...")
            
        try:
            if os.name == "posix" and self.mem_path and os.path.exists(self.mem_path):
                with open(self.mem_path, "rb+") as f:
                    # 1. 读取设备标识
                    f.seek(0x40)  # 假设标识寄存器在偏移0x40
                    ident_data = f.read(4)
                    ident_value = struct.unpack("<I", ident_data)[0]
                    print(f"✅ 设备标识值: 0x{ident_value:08x}")
                    
                    # 2. 测试命令寄存器
                    f.seek(0x04)  # 控制/命令寄存器
                    cmd_value = 0x00000001  # 标识命令
                    f.write(struct.pack("<I", cmd_value))
                    
                    # 等待命令完成
                    time.sleep(0.5)
                    
                    # 读取状态
                    f.seek(0x00)
                    status = struct.unpack("<I", f.read(4))[0]
                    print(f"✅ 命令执行后状态: 0x{status:08x}")
            else:
                print("ℹ️ 无法在当前系统上执行详细的存储设备测试")
                
            # 检查系统是否识别了存储设备
            if os.name == "posix":
                result = subprocess.run(["lsblk"], capture_output=True, text=True)
                if result.returncode == 0:
                    print("ℹ️ 系统存储设备列表:")
                    for line in result.stdout.strip().split("\\n")[:5]:  # 只显示前5行
                        print(f"  {line.strip()}")
            
        except Exception as e:
            print(f"❌ 存储设备测试出错: {str(e)}")"""
            
        else:
            # 默认测试
            return """print("设备特定功能测试需要根据具体设备类型实现")
        print("ℹ️ 这是一个通用设备测试，没有实现特定功能测试")
            
        try:
            if os.name == "posix" and self.mem_path and os.path.exists(self.mem_path):
                with open(self.mem_path, "rb+") as f:
                    # 读取并修改控制寄存器
                    f.seek(0x04)  # 控制寄存器
                    control_orig = struct.unpack("<I", f.read(4))[0]
                    print(f"✅ 控制寄存器原值: 0x{control_orig:08x}")
                    
                    # 设置控制寄存器第0位
                    new_control = control_orig | 0x00000001
                    f.seek(0x04)
                    f.write(struct.pack("<I", new_control))
                    
                    # 读回验证
                    f.seek(0x04)
                    control_new = struct.unpack("<I", f.read(4))[0]
                    print(f"✅ 控制寄存器新值: 0x{control_new:08x}")
                    
                    # 恢复原值
                    f.seek(0x04)
                    f.write(struct.pack("<I", control_orig))
            else:
                print("ℹ️ 无法在当前系统上执行详细的设备功能测试")
                
        except Exception as e:
            print(f"❌ 设备功能测试出错: {str(e)}")""" 