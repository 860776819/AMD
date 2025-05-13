#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寄存器映射模块
负责生成PCIe设备的寄存器映射代码
"""

import os
import re

class RegisterMapper:
    """寄存器映射生成类"""
    
    def __init__(self):
        """初始化寄存器映射模块"""
        self.template = self._load_register_map_template()
        
    def _load_register_map_template(self):
        """加载寄存器映射模板"""
        return """
// 寄存器映射定义头文件
// 自动生成的设备寄存器映射: {device_name}
// 生成时间: {timestamp}

// 请在您的设备实现中包含此文件
`ifndef {include_guard}
`define {include_guard}

// ==========================================================================
// 设备基本信息
// ==========================================================================

// 设备ID和供应商ID
`define DEV_VENDOR_ID 16'h{vendor_id}
`define DEV_DEVICE_ID 16'h{device_id}

// 寄存器基地址
`define REG_BASE 32'h{reg_base}

// ==========================================================================
// 寄存器地址定义
// ==========================================================================

{register_definitions}

// ==========================================================================
// 位字段定义
// ==========================================================================

{bit_field_definitions}

// ==========================================================================
// 常数定义
// ==========================================================================

{constant_definitions}

`endif // {include_guard}
"""
    
    def generate_register_map(self, device_config, output_file):
        """生成寄存器映射代码"""
        try:
            device_name = device_config.get("name", "自定义设备")
            include_guard = self._create_include_guard(device_name)
            vendor_id = device_config.get("vendor_id", "FFFF")
            device_id = device_config.get("device_id", "FFFF")
            reg_base = "0000"  # 默认寄存器基地址，通常是BAR0
            
            # 生成寄存器定义
            registers = device_config.get("key_registers", [])
            register_definitions = []
            bit_field_definitions = []
            constant_definitions = []
            
            # 添加基本寄存器
            base_registers = [
                {"addr": "0x0000", "name": "状态寄存器", "description": "设备状态"},
                {"addr": "0x0004", "name": "控制寄存器", "description": "设备控制"},
                {"addr": "0x0008", "name": "中断状态", "description": "设备中断状态"},
                {"addr": "0x000C", "name": "中断使能", "description": "设备中断使能"}
            ]
            
            # 合并寄存器列表
            all_registers = base_registers + registers
            
            # 对寄存器进行排序
            all_registers.sort(key=lambda r: int(r["addr"].replace("0x", ""), 16))
            
            # 处理每个寄存器
            for reg in all_registers:
                addr = reg["addr"].replace("0x", "")
                name = reg.get("name", f"寄存器_{addr}")
                # 创建宏定义友好的名称
                macro_name = self._create_macro_name(name)
                
                # 添加寄存器地址定义
                register_definitions.append(f"`define {macro_name}_REG 32'h{addr}")
                
                # 添加寄存器描述（注释）
                description = reg.get("description", "")
                if description:
                    register_definitions[-1] += f" // {description}"
                
                # 处理位字段（如果存在）
                bit_fields = reg.get("bit_fields", [])
                for field in bit_fields:
                    field_name = field.get("name", "FIELD")
                    field_macro = f"{macro_name}_{self._create_macro_name(field_name)}"
                    
                    # 位位置
                    if "bit" in field:
                        # 单个位
                        bit_field_definitions.append(f"`define {field_macro}_BIT {field['bit']}")
                    elif "msb" in field and "lsb" in field:
                        # 位域
                        bit_field_definitions.append(f"`define {field_macro}_MSB {field['msb']}")
                        bit_field_definitions.append(f"`define {field_macro}_LSB {field['lsb']}")
                        bit_field_definitions.append(f"`define {field_macro}_MASK ({(1 << (field['msb'] - field['lsb'] + 1)) - 1} << {field['lsb']})")
                    
                    # 添加描述
                    field_desc = field.get("description", "")
                    if field_desc and "BIT" in bit_field_definitions[-1]:
                        bit_field_definitions[-1] += f" // {field_desc}"
                    elif field_desc and "MASK" in bit_field_definitions[-1]:
                        bit_field_definitions[-1] += f" // {field_desc}"
            
            # 添加设备类型特定的常量定义
            device_type = device_config.get("type", "custom")
            if device_type == "nic" or device_type == "wifi":
                # 网络设备特定常量
                constant_definitions.extend([
                    "// 网络设备特定常量",
                    "`define MAX_PACKET_SIZE 1518",
                    "`define MIN_PACKET_SIZE 64",
                    "`define MAC_ADDR_SIZE 6",
                    "`define RX_BUFFER_SIZE 4096",
                    "`define TX_BUFFER_SIZE 4096",
                    "",
                    "// 网络设备命令代码",
                    "`define CMD_NIC_RESET 8'h00",
                    "`define CMD_NIC_INIT 8'h01",
                    "`define CMD_NIC_TX 8'h02",
                    "`define CMD_NIC_RX 8'h03",
                    "`define CMD_NIC_GET_STATS 8'h04",
                    "`define CMD_NIC_SET_MAC 8'h05",
                    "`define CMD_NIC_GET_MAC 8'h06"
                ])
            elif device_type == "storage":
                # 存储设备特定常量
                constant_definitions.extend([
                    "// 存储设备特定常量",
                    "`define SECTOR_SIZE 512",
                    "`define MAX_TRANSFER_SIZE 128",
                    "`define MAX_LBA_ADDRESS 48'hFFFFFFFFFFFF",
                    "",
                    "// 存储设备命令代码",
                    "`define CMD_READ_SECTORS 8'h20",
                    "`define CMD_WRITE_SECTORS 8'h30",
                    "`define CMD_READ_DMA 8'h25",
                    "`define CMD_WRITE_DMA 8'h35",
                    "`define CMD_IDENTIFY 8'hEC",
                    "`define CMD_SET_FEATURES 8'hEF",
                    "`define CMD_FLUSH_CACHE 8'hE7"
                ])
            
            # 生成最终代码
            code = self.template.format(
                device_name=device_name,
                timestamp=__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                include_guard=include_guard,
                vendor_id=vendor_id,
                device_id=device_id,
                reg_base=reg_base,
                register_definitions="\n".join(register_definitions),
                bit_field_definitions="\n".join(bit_field_definitions),
                constant_definitions="\n".join(constant_definitions)
            )
            
            # 写入输出文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            print(f"✅ 寄存器映射代码已生成: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 生成寄存器映射代码失败: {str(e)}")
            return False
    
    def _create_include_guard(self, name):
        """创建包含保护宏"""
        # 创建全大写的宏名称
        guard = re.sub(r'[^\w]', '_', name).upper()
        return f"__{guard}_REGISTERS_H__"
    
    def _create_macro_name(self, name):
        """将寄存器名称转换为宏定义友好的名称"""
        # 移除非字母数字字符，转换为大写
        name = re.sub(r'[^\w]', '_', name).upper()
        # 替换多个连续下划线
        name = re.sub(r'_+', '_', name)
        # 移除开头和结尾的下划线
        name = name.strip('_')
        return name 