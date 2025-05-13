#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置空间伪装模块
负责生成PCIe配置空间和写入掩码文件
"""

import os
import struct
import re

class ConfigSpoofer:
    """PCIe配置空间伪装类"""
    
    def __init__(self):
        """初始化配置空间伪装模块"""
        self.config_template = self._load_default_template()
        self.writemask_template = self._load_default_writemask()
        
    def _load_default_template(self):
        """加载默认的配置空间模板"""
        # 基本模板，包含256字节的配置空间（64个32位字）
        template = [
            "FFFFFFFF" for _ in range(64)  # 初始化为全F（无效值）
        ]
        
        # 设置一些默认值
        template[3] = "fffff00c"  # 头类型和BIST
        template[4] = "fffff010"  # BAR0
        template[5] = "fffff014"  # BAR1
        template[6] = "fffff018"  # BAR2
        template[7] = "fffff01c"  # BAR3
        template[8] = "fffff020"  # BAR4
        template[9] = "fffff024"  # BAR5
        template[10] = "00000000"  # Cardbus CIS Pointer
        template[11] = "00000000"  # Subsystem ID和Vendor ID
        template[12] = "00000000"  # 扩展ROM地址
        template[15] = "00010000"  # 中断引脚和线路
        
        return template
    
    def _load_default_writemask(self):
        """加载默认的写入掩码模板"""
        # 基本写入掩码，初始默认为不可写
        template = [
            "00000000" for _ in range(64)  # 初始化为全0（只读）
        ]
        
        # 设置一些默认的可写区域
        template[1] = "00000107"  # 命令和状态寄存器（部分位可写）
        
        # BAR通常是可写的
        for i in range(4, 10):
            template[i] = "FFFFFFFF"
        
        return template
    
    def generate_config_space(self, device_config, output_file):
        """根据设备配置生成配置空间文件"""
        try:
            # 复制模板
            config_data = self.config_template.copy()
            
            # 设置设备ID和供应商ID
            vendor_id = device_config.get("vendor_id", "8086")  # Intel
            device_id = device_config.get("device_id", "08b1")  # Wireless-AC 7260
            config_data[0] = f"{device_id}{vendor_id}"
            
            # 设置命令和状态寄存器
            config_data[1] = "fffff004"  # 默认状态和命令寄存器
            
            # 设置类别代码和修订版本
            class_code = device_config.get("class_code", "028000")  # Wireless-AC 7260
            revision_id = device_config.get("revision_id", "cb")  # Wireless-AC 7260
            config_data[2] = f"{class_code}{revision_id}"
            
            # 设置子系统ID和子系统供应商ID
            subsystem_vendor_id = device_config.get("subsystem_vendor_id", "8086")  # Intel
            subsystem_id = device_config.get("subsystem_id", "5070")  # Wireless-AC 7260
            config_data[11] = f"{subsystem_id}{subsystem_vendor_id}"
            
            # 设置PCIe能力指针
            config_data[13] = "000000c0"  # 指向偏移0xC0
            
            # 生成COE文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("memory_initialization_radix=16;\n")
                f.write("memory_initialization_vector=\n")
                
                # 写入数据，每行4个32位字
                for i in range(0, 64, 4):
                    if i + 3 < 64:
                        line = f"{config_data[i]},{config_data[i+1]},{config_data[i+2]},{config_data[i+3]}"
                        # 在第一行添加注释
                        if i == 0:
                            line += ",  // 设备ID/供应商ID + 命令/状态 + 类别代码 + 头类型"
                        f.write(line + ",\n")
                    else:
                        # 处理最后一行（可能不完整）
                        remaining = 64 - i
                        line = ",".join(config_data[i:i+remaining])
                        f.write(line + ";\n")
                        
            print(f"✅ 配置空间文件已生成: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 生成配置空间文件失败: {str(e)}")
            return False
    
    def generate_writemask(self, device_config, output_file):
        """根据设备配置生成写入掩码文件"""
        try:
            # 复制模板
            writemask_data = self.writemask_template.copy()
            
            # 特定设备类型的写入掩码设置
            device_type = device_config.get("type", "custom")
            if device_type == "nic" or device_type == "wifi":
                # 网络设备的特殊写入掩码
                writemask_data[1] = "00000107"  # 命令寄存器允许总线主控、内存空间使能和IO空间使能
            elif device_type == "storage":
                # 存储设备的特殊写入掩码
                writemask_data[1] = "00000107"  # 基本与网卡相同
                writemask_data[3] = "0000FF00"  # 允许修改Cache Line Size
            
            # 应用设备特定的写入掩码设置
            custom_writemask = device_config.get("writemask_overrides", {})
            for offset_str, mask in custom_writemask.items():
                try:
                    offset = int(offset_str, 0)  # 支持十六进制偏移
                    if 0 <= offset < 64:
                        writemask_data[offset] = mask
                except ValueError:
                    pass
            
            # 生成COE文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("memory_initialization_radix=16;\n")
                f.write("memory_initialization_vector=\n")
                
                # 写入数据，每行4个32位字
                for i in range(0, 64, 4):
                    if i + 3 < 64:
                        line = f"{writemask_data[i]},{writemask_data[i+1]},{writemask_data[i+2]},{writemask_data[i+3]}"
                        # 在第一行添加注释
                        if i == 0:
                            line += ",  // 设备ID/供应商ID(只读) + 命令/状态(部分可写) + 类别代码(只读)"
                        f.write(line + ",\n")
                    else:
                        # 处理最后一行（可能不完整）
                        remaining = 64 - i
                        line = ",".join(writemask_data[i:i+remaining])
                        f.write(line + ";\n")
                        
            print(f"✅ 写入掩码文件已生成: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 生成写入掩码文件失败: {str(e)}")
            return False
    
    def extract_fields_from_config_space(self, config_file):
        """从现有配置空间文件中提取字段信息"""
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 查找向量数据部分
            vector_match = re.search(r"memory_initialization_vector=\s*\n(.*?);", 
                                    content, re.DOTALL)
            if not vector_match:
                return None
                
            # 处理向量数据
            vector_data = vector_match.group(1)
            
            # 移除注释和空白
            vector_data = re.sub(r"//.*?$", "", vector_data, flags=re.MULTILINE)
            vector_data = re.sub(r"\s+", "", vector_data)
            
            # 分割为单独的值
            values = vector_data.strip(",").split(",")
            
            # 提取关键字段
            if len(values) < 3:
                return None
                
            # 第一个字段包含设备ID和供应商ID
            id_field = values[0]
            if len(id_field) == 8:
                device_id = id_field[0:4]
                vendor_id = id_field[4:8]
            else:
                return None
                
            # 第三个字段包含类别代码和修订版本
            class_field = values[2]
            if len(class_field) == 8:
                class_code = class_field[0:6]
                revision_id = class_field[6:8]
            else:
                return None
                
            return {
                "vendor_id": vendor_id,
                "device_id": device_id,
                "class_code": class_code,
                "revision_id": revision_id
            }
        except Exception:
            return None 