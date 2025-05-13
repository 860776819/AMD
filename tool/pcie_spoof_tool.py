#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCIe设备伪装自动化工具
基于PCILeech-FPGA项目的PCIe设备伪装工具
"""

import os
import sys
import argparse
import json
import re
from pathlib import Path

# 导入子模块
from config_spoofer import ConfigSpoofer
from bar_generator import BARGenerator
from behavior_generator import BehaviorGenerator
from register_mapper import RegisterMapper
from interrupt_generator import InterruptGenerator
from test_generator import TestGenerator

# 版本号
VERSION = "1.0.0"

# 设备类型映射
DEVICE_TYPES = {
    "nic": "网络接口卡",
    "wifi": "无线网卡",
    "storage": "存储控制器",
    "gpu": "图形处理器",
    "usb": "USB控制器",
    "audio": "音频设备",
    "custom": "自定义设备"
}

# 预设设备信息
PRESET_DEVICES = {
    "intel_wireless_ac7260": {
        "name": "Intel(R) 双频 Wireless-AC 7260",
        "vendor_id": "8086",
        "device_id": "08b1",
        "class_code": "028000",
        "revision_id": "cb",
        "subsystem_vendor_id": "8086",
        "subsystem_id": "5070",
        "type": "wifi",
        "key_registers": [
            {"addr": "0x4000", "name": "设备控制", "value": "32'h00000000", "access": "RW"},
            {"addr": "0x4004", "name": "设备状态", "value": "32'h00000001", "access": "RO"}
        ]
    },
    "ar9287": {
        "name": "Atheros AR9287无线网卡",
        "vendor_id": "168C",
        "device_id": "002E",
        "class_code": "028000",
        "type": "wifi",
        "key_registers": [
            {"addr": "0x4020", "name": "MAC版本", "value": "32'h001800FF", "access": "RO"},
            {"addr": "0x4028", "name": "中断挂起1", "value": "32'h00000060", "access": "RO"},
            {"addr": "0x4038", "name": "中断挂起2", "value": "32'h00000002", "access": "RO"}
        ]
    },
    "intel_i350": {
        "name": "Intel I350千兆网卡",
        "vendor_id": "8086",
        "device_id": "1521",
        "class_code": "020000",
        "type": "nic",
        "key_registers": [
            {"addr": "0x00000", "name": "设备控制", "value": "32'h00280000", "access": "RW"},
            {"addr": "0x00008", "name": "设备状态", "value": "32'h00100000", "access": "RO"}
        ]
    },
    "nvme_ssd": {
        "name": "NVMe SSD控制器",
        "vendor_id": "144D",
        "device_id": "A808",
        "class_code": "010802",
        "type": "storage",
        "key_registers": [
            {"addr": "0x00000", "name": "控制器能力", "value": "32'h00000001", "access": "RO"},
            {"addr": "0x00004", "name": "版本", "value": "32'h00010300", "access": "RO"},
            {"addr": "0x00014", "name": "控制器配置", "value": "32'h00460001", "access": "RW"}
        ]
    }
}

class PCIeSpoofTool:
    """PCIe设备伪装工具主类"""
    
    def __init__(self):
        """初始化工具"""
        self.config_path = None
        self.output_path = None
        self.device_config = {}
        self.modules = {}
        self.initialize_modules()
        
    def initialize_modules(self):
        """初始化各个功能模块"""
        self.modules['config'] = ConfigSpoofer()
        self.modules['bar'] = BARGenerator()
        self.modules['behavior'] = BehaviorGenerator()
        self.modules['registers'] = RegisterMapper()
        self.modules['interrupt'] = InterruptGenerator()
        self.modules['test'] = TestGenerator()
        
    def load_config(self, config_path):
        """加载配置文件"""
        self.config_path = config_path
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.device_config = json.load(f)
            print(f"✅ 成功加载配置文件: {config_path}")
            return True
        except Exception as e:
            print(f"❌ 加载配置文件失败: {str(e)}")
            return False
    
    def create_new_config(self, device_type, preset=None):
        """创建新的设备配置"""
        if preset and preset in PRESET_DEVICES:
            self.device_config = PRESET_DEVICES[preset].copy()
            print(f"✅ 已加载预设设备: {self.device_config['name']}")
        else:
            self.device_config = {
                "name": f"自定义{DEVICE_TYPES.get(device_type, '未知')}",
                "vendor_id": "FFFF",  # 默认值
                "device_id": "FFFF",  # 默认值
                "class_code": "000000",  # 默认值
                "type": device_type,
                "key_registers": []
            }
            print(f"✅ 已创建新的设备配置: {self.device_config['name']}")
        return True
    
    def save_config(self, output_path=None):
        """保存当前配置到文件"""
        if output_path:
            self.output_path = output_path
        
        if not self.output_path:
            # 使用设备名称作为配置文件名
            safe_name = re.sub(r'[^\w]', '_', self.device_config.get('name', 'device'))
            self.output_path = f"{safe_name}_config.json"
        
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(self.device_config, f, indent=2, ensure_ascii=False)
            print(f"✅ 配置已保存到: {self.output_path}")
            return True
        except Exception as e:
            print(f"❌ 保存配置失败: {str(e)}")
            return False
    
    def generate_all(self, output_dir):
        """生成所有伪装文件"""
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 1. 生成配置空间文件
            cfg_result = self.modules['config'].generate_config_space(
                self.device_config, 
                os.path.join(output_dir, "pcileech_cfgspace.coe")
            )
            
            # 2. 生成写入掩码文件
            mask_result = self.modules['config'].generate_writemask(
                self.device_config, 
                os.path.join(output_dir, "pcileech_cfgspace_writemask.coe")
            )
            
            # 3. 生成BAR控制器代码
            bar_result = self.modules['bar'].generate_bar_controller(
                self.device_config, 
                os.path.join(output_dir, "bar_controller.sv")
            )
            
            # 4. 生成行为模拟代码
            behavior_result = self.modules['behavior'].generate_behavior_code(
                self.device_config, 
                os.path.join(output_dir, "device_behavior.sv")
            )
            
            # 5. 生成寄存器映射代码
            reg_result = self.modules['registers'].generate_register_map(
                self.device_config, 
                os.path.join(output_dir, "register_map.sv")
            )
            
            # 6. 生成中断处理代码
            int_result = self.modules['interrupt'].generate_interrupt_handler(
                self.device_config, 
                os.path.join(output_dir, "interrupt_handler.sv")
            )
            
            # 7. 生成测试文件
            test_result = self.modules['test'].generate_test_script(
                self.device_config, 
                os.path.join(output_dir, "test_device.py")
            )
            
            # 生成简单的包含脚本
            self._generate_include_script(output_dir)
            
            # 创建README文件
            self._generate_readme(output_dir)
            
            # 生成完成总结
            print("\n========= 生成结果汇总 =========")
            print(f"配置空间文件: {'✅ 成功' if cfg_result else '❌ 失败'}")
            print(f"写入掩码文件: {'✅ 成功' if mask_result else '❌ 失败'}")
            print(f"BAR控制器代码: {'✅ 成功' if bar_result else '❌ 失败'}")
            print(f"行为模拟代码: {'✅ 成功' if behavior_result else '❌ 失败'}")
            print(f"寄存器映射代码: {'✅ 成功' if reg_result else '❌ 失败'}")
            print(f"中断处理代码: {'✅ 成功' if int_result else '❌ 失败'}")
            print(f"测试脚本: {'✅ 成功' if test_result else '❌ 失败'}")
            print(f"\n所有文件已生成到目录: {output_dir}")
            print("================================\n")
            
            return True
        except Exception as e:
            print(f"❌ 生成文件时发生错误: {str(e)}")
            return False
    
    def _generate_include_script(self, output_dir):
        """生成简单的包含脚本"""
        include_content = """
// 设备伪装模块包含文件
// 由PCIe设备伪装工具自动生成

// 基本包含文件
`include "register_map.sv"
`include "interrupt_handler.sv"
`include "device_behavior.sv"
`include "bar_controller.sv"

// 注意: 将这些文件复制到您的PCILeech项目相应目录中
// 然后在主模块中包含此文件: `include "device_spoof_includes.sv"
"""
        try:
            with open(os.path.join(output_dir, "device_spoof_includes.sv"), 'w') as f:
                f.write(include_content)
            return True
        except Exception:
            return False
    
    def _generate_readme(self, output_dir):
        """生成README文件"""
        device_name = self.device_config.get("name", "自定义设备")
        vendor_id = self.device_config.get("vendor_id", "FFFF")
        device_id = self.device_config.get("device_id", "FFFF")
        
        readme_content = f"""# {device_name} 伪装实现

此目录包含由PCIe设备伪装工具自动生成的文件，用于实现{device_name}的完全伪装。

## 设备信息

- 设备名称: {device_name}
- 厂商ID (Vendor ID): 0x{vendor_id}
- 设备ID (Device ID): 0x{device_id}
- 设备类型: {DEVICE_TYPES.get(self.device_config.get("type", "custom"), "自定义设备")}

## 文件说明

- `pcileech_cfgspace.coe`: PCIe配置空间初始化文件
- `pcileech_cfgspace_writemask.coe`: 配置空间写入掩码文件
- `bar_controller.sv`: BAR空间控制器实现
- `device_behavior.sv`: 设备行为模拟代码
- `register_map.sv`: 寄存器映射实现
- `interrupt_handler.sv`: 中断处理器实现
- `test_device.py`: 设备测试脚本
- `device_spoof_includes.sv`: 包含文件

## 使用说明

1. 将生成的文件复制到PCILeech-FPGA项目的相应目录中
2. 在项目中包含`device_spoof_includes.sv`文件
3. 修改主项目文件，使用新的伪装实现
4. 编译并生成比特流
5. 使用`test_device.py`脚本进行测试

## 自动生成说明

此实现由PCIe设备伪装工具自动生成。
生成时间: {__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        try:
            with open(os.path.join(output_dir, "README.md"), 'w', encoding='utf-8') as f:
                f.write(readme_content)
            return True
        except Exception:
            return False

def main():
    """主函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description=f"PCIe设备伪装工具 v{VERSION}")
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 创建新配置命令
    create_parser = subparsers.add_parser("create", help="创建新的设备配置")
    create_parser.add_argument("--type", "-t", choices=DEVICE_TYPES.keys(), default="custom",
                              help="设备类型")
    create_parser.add_argument("--preset", "-p", choices=PRESET_DEVICES.keys(),
                              help="使用预设设备")
    create_parser.add_argument("--output", "-o", help="输出配置文件路径")
    
    # 加载配置命令
    load_parser = subparsers.add_parser("load", help="加载现有配置文件")
    load_parser.add_argument("config_file", help="配置文件路径")
    
    # 生成文件命令
    gen_parser = subparsers.add_parser("generate", help="生成伪装文件")
    gen_parser.add_argument("--config", "-c", help="配置文件路径")
    gen_parser.add_argument("--output-dir", "-o", default="./spoof_output", 
                           help="输出目录路径")
    gen_parser.add_argument("--preset", "-p", choices=PRESET_DEVICES.keys(),
                          help="使用预设设备")
    
    # 列出预设设备命令
    list_parser = subparsers.add_parser("list", help="列出可用的预设设备")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 创建工具实例
    tool = PCIeSpoofTool()
    
    # 根据命令执行相应操作
    if args.command == "create":
        # 创建新配置
        tool.create_new_config(args.type, args.preset)
        tool.save_config(args.output)
        
    elif args.command == "load":
        # 加载配置
        if tool.load_config(args.config_file):
            print(f"已加载设备: {tool.device_config.get('name', '未命名设备')}")
            
    elif args.command == "generate":
        # 生成文件
        if args.config:
            # 从文件加载配置
            if not tool.load_config(args.config):
                return 1
        elif args.preset:
            # 使用预设配置
            if not tool.create_new_config("custom", args.preset):
                return 1
        else:
            print("错误: 需要提供配置文件(--config)或使用预设设备(--preset)")
            return 1
            
        # 生成所有文件
        tool.generate_all(args.output_dir)
        
    elif args.command == "list":
        # 列出预设设备
        print("\n可用的预设设备:")
        print("================")
        for key, device in PRESET_DEVICES.items():
            print(f"- {key}: {device['name']} (VID:0x{device['vendor_id']}, "
                  f"DID:0x{device['device_id']})")
        print("\n使用方法: pcie_spoof_tool.py create --preset <设备名> 或")
        print("         pcie_spoof_tool.py generate --preset <设备名>\n")
        
    else:
        # 显示帮助信息
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 