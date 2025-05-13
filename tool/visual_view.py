#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化视图组件
为PCIe设备伪装工具提供设备结构和寄存器映射的可视化功能
"""

import tkinter as tk
from tkinter import ttk
import random

class VisualView(ttk.Frame):
    """可视化视图组件"""
    
    def __init__(self, parent):
        """初始化可视化视图
        
        Args:
            parent: 父级窗口
        """
        super().__init__(parent)
        
        # 设备配置
        self.device_config = {}
        
        # 寄存器数据
        self.registers = []
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建标签页
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 寄存器映射视图
        self.reg_map_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reg_map_frame, text="寄存器映射")
        
        # 设备结构视图
        self.device_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.device_frame, text="设备结构")
        
        # 创建寄存器映射视图
        self.create_register_map_view()
        
        # 创建设备结构视图
        self.create_device_structure_view()
    
    def create_register_map_view(self):
        """创建寄存器映射视图"""
        # 寄存器映射标题
        title_frame = ttk.Frame(self.reg_map_frame)
        title_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            title_frame, 
            text="寄存器内存映射", 
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT, padx=20)
        
        ttk.Label(
            title_frame, 
            text="(可视化表示设备寄存器的内存映射布局)", 
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=10)
        
        # 寄存器映射画布容器
        canvas_frame = ttk.Frame(self.reg_map_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建画布和滚动条
        self.reg_canvas = tk.Canvas(canvas_frame, bg="white")
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.reg_canvas.yview)
        self.reg_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.reg_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建寄存器映射图例
        legend_frame = ttk.LabelFrame(self.reg_map_frame, text="图例")
        legend_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 读写类型图例
        access_frame = ttk.Frame(legend_frame)
        access_frame.pack(side=tk.LEFT, padx=20, pady=5)
        
        ttk.Label(access_frame, text="访问类型:").pack(anchor=tk.W)
        
        rw_frame = ttk.Frame(access_frame)
        rw_frame.pack(fill=tk.X, pady=2)
        tk.Canvas(rw_frame, width=15, height=15, bg="#AED6F1").pack(side=tk.LEFT)
        ttk.Label(rw_frame, text="读写 (RW)").pack(side=tk.LEFT, padx=5)
        
        ro_frame = ttk.Frame(access_frame)
        ro_frame.pack(fill=tk.X, pady=2)
        tk.Canvas(ro_frame, width=15, height=15, bg="#D5F5E3").pack(side=tk.LEFT)
        ttk.Label(ro_frame, text="只读 (RO)").pack(side=tk.LEFT, padx=5)
        
        wo_frame = ttk.Frame(access_frame)
        wo_frame.pack(fill=tk.X, pady=2)
        tk.Canvas(wo_frame, width=15, height=15, bg="#FADBD8").pack(side=tk.LEFT)
        ttk.Label(wo_frame, text="只写 (WO)").pack(side=tk.LEFT, padx=5)
        
        # 内存类型图例
        mem_frame = ttk.Frame(legend_frame)
        mem_frame.pack(side=tk.LEFT, padx=20, pady=5)
        
        ttk.Label(mem_frame, text="内存类型:").pack(anchor=tk.W)
        
        cfg_frame = ttk.Frame(mem_frame)
        cfg_frame.pack(fill=tk.X, pady=2)
        tk.Canvas(cfg_frame, width=15, height=15, bg="#F9E79F").pack(side=tk.LEFT)
        ttk.Label(cfg_frame, text="配置空间").pack(side=tk.LEFT, padx=5)
        
        bar_frame = ttk.Frame(mem_frame)
        bar_frame.pack(fill=tk.X, pady=2)
        tk.Canvas(bar_frame, width=15, height=15, bg="#D2B4DE").pack(side=tk.LEFT)
        ttk.Label(bar_frame, text="BAR空间").pack(side=tk.LEFT, padx=5)
    
    def create_device_structure_view(self):
        """创建设备结构视图"""
        # 设备结构标题
        title_frame = ttk.Frame(self.device_frame)
        title_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            title_frame, 
            text="设备结构图", 
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT, padx=20)
        
        ttk.Label(
            title_frame, 
            text="(可视化表示设备的内部组件结构)", 
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=10)
        
        # 设备结构画布容器
        canvas_frame = ttk.Frame(self.device_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建画布和滚动条
        self.device_canvas = tk.Canvas(canvas_frame, bg="white")
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.device_canvas.yview)
        self.device_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.device_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def update_register_map(self, registers):
        """更新寄存器映射视图
        
        Args:
            registers: 寄存器数据列表
        """
        self.registers = registers
        
        # 清空画布
        self.reg_canvas.delete("all")
        
        if not registers:
            self.reg_canvas.create_text(
                300, 200, 
                text="没有寄存器数据", 
                font=("Arial", 14),
                fill="gray"
            )
            return
        
        # 设置基本参数
        start_x = 50
        start_y = 50
        width = 500
        reg_height = 50
        spacing = 10
        
        # 绘制标题
        self.reg_canvas.create_text(
            start_x + width/2, start_y - 30,
            text="设备寄存器内存布局",
            font=("Arial", 12, "bold")
        )
        
        # 绘制地址轴
        self.reg_canvas.create_line(
            start_x - 20, start_y,
            start_x - 20, start_y + (reg_height + spacing) * len(registers),
            width=2
        )
        
        # 排序寄存器（按地址）
        sorted_regs = sorted(registers, key=lambda r: int(r.get('address', '0x0').replace('0x', ''), 16))
        
        # 绘制每个寄存器
        for i, reg in enumerate(sorted_regs):
            y = start_y + i * (reg_height + spacing)
            name = reg.get('name', '未命名')
            addr = reg.get('address', '0x0')
            width_bits = reg.get('width', 32)
            access = reg.get('access', 'RW')
            
            # 为不同访问类型选择不同颜色
            if access == 'RO':
                color = "#D5F5E3"  # 绿色
            elif access == 'WO':
                color = "#FADBD8"  # 红色
            else:
                color = "#AED6F1"  # 蓝色
                
            # 绘制寄存器块
            self.reg_canvas.create_rectangle(
                start_x, y,
                start_x + width, y + reg_height,
                fill=color, outline="black"
            )
            
            # 绘制寄存器名称
            self.reg_canvas.create_text(
                start_x + width/2, y + reg_height/2,
                text=f"{name} ({addr}) - {width_bits} bits",
                font=("Arial", 10, "bold")
            )
            
            # 绘制地址标记
            self.reg_canvas.create_text(
                start_x - 25, y,
                text=addr,
                font=("Arial", 8),
                anchor=tk.E
            )
            
            # 如果有位域数据，绘制位域
            bitfields = reg.get('bitfields', [])
            if bitfields:
                bit_width = width / width_bits
                for bf in bitfields:
                    name = bf.get('name', '')
                    bits_str = bf.get('bits', '0')
                    
                    # 解析位范围
                    if ':' in bits_str:
                        high, low = map(int, bits_str.split(':'))
                        start_bit = low
                        end_bit = high
                    else:
                        start_bit = end_bit = int(bits_str)
                    
                    # 计算位域在寄存器中的位置
                    bit_x1 = start_x + start_bit * bit_width
                    bit_x2 = start_x + (end_bit + 1) * bit_width
                    
                    # 绘制位域分隔线
                    self.reg_canvas.create_line(
                        bit_x1, y,
                        bit_x1, y + reg_height,
                        fill="gray", dash=(2, 2)
                    )
        
        # 设置画布滚动区域
        total_height = start_y + (reg_height + spacing) * len(registers) + 50
        self.reg_canvas.configure(scrollregion=(0, 0, width + 100, total_height))
    
    def update_device_structure(self, config):
        """更新设备结构视图
        
        Args:
            config: 设备配置
        """
        # 清空画布
        self.device_canvas.delete("all")
        
        if not config:
            self.device_canvas.create_text(
                300, 200, 
                text="没有设备配置数据", 
                font=("Arial", 14),
                fill="gray"
            )
            return
        
        # 设置基本参数
        width = 600
        height = 500
        
        # 绘制PCIe设备框架
        self.draw_device_frame(width, height)
        
        # 绘制主要组件
        components = [
            ("配置空间", "#F9E79F", 100, 60, 400, 60, True),
            ("BAR控制器", "#D2B4DE", 100, 150, 180, 80, True)
        ]
        
        # 检查是否有DMA控制器
        if config.get("dma_config", {}).get("enabled", False):
            components.append(("DMA控制器", "#ABEBC6", 320, 150, 180, 80, True))
        
        # 检查中断模式
        int_mode = config.get("interrupt_config", {}).get("mode", "legacy")
        if int_mode == "legacy":
            components.append(("传统中断控制器", "#F5CBA7", 100, 260, 180, 60, True))
        elif int_mode == "msi":
            components.append(("MSI中断控制器", "#F5CBA7", 100, 260, 180, 60, True))
        elif int_mode == "msix":
            components.append(("MSI-X中断控制器", "#F5CBA7", 100, 260, 180, 60, True))
        
        # 检查是否有寄存器
        if self.registers:
            components.append(("寄存器映射", "#AED6F1", 320, 260, 180, 60, True))
        
        # 绘制各个组件
        for name, color, x, y, w, h, filled in components:
            self.draw_component(name, color, x, y, w, h, filled)
        
        # 绘制组件间连接
        self.draw_connections()
        
        # 设置画布滚动区域
        self.device_canvas.configure(scrollregion=(0, 0, width, height))
    
    def draw_device_frame(self, width, height):
        """绘制设备框架
        
        Args:
            width: 画布宽度
            height: 画布高度
        """
        # 设备名称等信息
        device_name = self.device_config.get("name", "未命名设备")
        vendor_id = self.device_config.get("vendor_id", "FFFF")
        device_id = self.device_config.get("device_id", "FFFF")
        
        # 绘制设备外框
        self.device_canvas.create_rectangle(
            50, 20, width - 50, height - 20,
            outline="#3498DB", width=3, dash=(8, 4)
        )
        
        # 绘制设备标题
        self.device_canvas.create_text(
            width/2, 40,
            text=f"{device_name} (VID:{vendor_id} DID:{device_id})",
            font=("Arial", 14, "bold")
        )
        
        # 绘制PCIe接口
        self.device_canvas.create_rectangle(
            width/2 - 60, height - 40,
            width/2 + 60, height - 20,
            fill="#5D6D7E", outline="black"
        )
        
        self.device_canvas.create_text(
            width/2, height - 30,
            text="PCIe接口",
            fill="white", font=("Arial", 10, "bold")
        )
    
    def draw_component(self, name, color, x, y, w, h, filled=True):
        """绘制设备组件
        
        Args:
            name: 组件名称
            color: 组件颜色
            x, y: 左上角坐标
            w, h: 宽度和高度
            filled: 是否填充
        """
        if filled:
            self.device_canvas.create_rectangle(
                x, y, x + w, y + h,
                fill=color, outline="black", width=2
            )
        else:
            self.device_canvas.create_rectangle(
                x, y, x + w, y + h,
                outline="black", width=2, dash=(4, 2)
            )
        
        self.device_canvas.create_text(
            x + w/2, y + h/2,
            text=name,
            font=("Arial", 11, "bold")
        )
    
    def draw_connections(self):
        """绘制组件间的连接线"""
        # 简单绘制几条连接线
        # 配置空间到BAR控制器
        self.device_canvas.create_line(
            190, 120, 190, 150,
            fill="#5D6D7E", width=2, arrow=tk.LAST
        )
        
        # 配置空间到DMA控制器
        self.device_canvas.create_line(
            410, 120, 410, 150,
            fill="#5D6D7E", width=2, arrow=tk.LAST
        )
        
        # BAR控制器到寄存器
        self.device_canvas.create_line(
            190, 230, 190, 260,
            fill="#5D6D7E", width=2, arrow=tk.BOTH
        )
        
        # DMA控制器到寄存器
        self.device_canvas.create_line(
            410, 230, 410, 260,
            fill="#5D6D7E", width=2, arrow=tk.BOTH
        )
        
        # PCIe接口连接线
        self.device_canvas.create_line(
            300, 370, 300, 430,
            fill="#5D6D7E", width=3, arrow=tk.BOTH
        )
    
    def update_views(self, config, registers):
        """更新所有视图
        
        Args:
            config: 设备配置数据
            registers: 寄存器数据列表
        """
        self.device_config = config
        self.registers = registers
        
        # 更新寄存器映射视图
        self.update_register_map(registers)
        
        # 更新设备结构视图
        self.update_device_structure(config)


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.geometry("800x600")
    
    view = VisualView(root)
    view.pack(fill=tk.BOTH, expand=True)
    
    # 添加测试数据
    test_config = {
        "name": "测试设备",
        "vendor_id": "1234",
        "device_id": "ABCD",
        "type": "custom",
        "dma_config": {
            "enabled": True
        },
        "interrupt_config": {
            "mode": "msi"
        }
    }
    
    test_registers = [
        {
            "name": "STATUS",
            "address": "0x00",
            "width": 32,
            "access": "RW",
            "bitfields": [
                {"name": "READY", "bits": "0"},
                {"name": "ERROR", "bits": "1"},
                {"name": "BUSY", "bits": "2"},
                {"name": "RESERVED", "bits": "31:3"}
            ]
        },
        {
            "name": "CONTROL",
            "address": "0x04",
            "width": 32,
            "access": "RW",
            "bitfields": [
                {"name": "ENABLE", "bits": "0"},
                {"name": "RESET", "bits": "1"},
                {"name": "INT_EN", "bits": "2"},
                {"name": "RESERVED", "bits": "31:3"}
            ]
        },
        {
            "name": "DATA",
            "address": "0x08",
            "width": 32,
            "access": "RO"
        }
    ]
    
    view.update_views(test_config, test_registers)
    
    root.mainloop() 