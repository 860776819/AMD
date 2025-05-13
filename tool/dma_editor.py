#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMA编辑器组件
为PCIe设备伪装工具提供DMA控制器配置功能
"""

import tkinter as tk
from tkinter import ttk, messagebox

class DMAEditor(ttk.Frame):
    """DMA编辑器组件"""
    
    def __init__(self, parent, callback=None):
        """初始化DMA编辑器
        
        Args:
            parent: 父级窗口
            callback: DMA配置更新回调函数
        """
        super().__init__(parent)
        
        # DMA配置
        self.config = self.get_default_config()
        
        # 更新回调
        self.update_callback = callback
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 顶部标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            title_frame, 
            text="DMA控制器配置", 
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT)
        
        # DMA使能开关
        self.enabled_var = tk.BooleanVar(value=False)
        self.enabled_checkbox = ttk.Checkbutton(
            title_frame, 
            text="启用DMA控制器", 
            variable=self.enabled_var,
            command=self.on_enabled_changed
        )
        self.enabled_checkbox.pack(side=tk.RIGHT)
        
        # 创建基本参数区域
        params_frame = ttk.LabelFrame(main_frame, text="基本参数")
        params_frame.pack(fill=tk.X, pady=10)
        
        # 创建两列布局
        left_frame = ttk.Frame(params_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        right_frame = ttk.Frame(params_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧参数
        # 最大负载大小
        max_payload_frame = ttk.Frame(left_frame)
        max_payload_frame.pack(fill=tk.X, pady=5)
        ttk.Label(max_payload_frame, text="最大负载大小:", width=20).pack(side=tk.LEFT)
        self.max_payload_var = tk.StringVar()
        max_payload_combobox = ttk.Combobox(max_payload_frame, textvariable=self.max_payload_var, width=15)
        max_payload_combobox['values'] = ["128", "256", "512", "1024", "2048", "4096"]
        max_payload_combobox.pack(side=tk.LEFT)
        ttk.Label(max_payload_frame, text="字节").pack(side=tk.LEFT, padx=5)
        
        # 最大读请求大小
        max_read_frame = ttk.Frame(left_frame)
        max_read_frame.pack(fill=tk.X, pady=5)
        ttk.Label(max_read_frame, text="最大读请求大小:", width=20).pack(side=tk.LEFT)
        self.max_read_var = tk.StringVar()
        max_read_combobox = ttk.Combobox(max_read_frame, textvariable=self.max_read_var, width=15)
        max_read_combobox['values'] = ["128", "256", "512", "1024", "2048", "4096"]
        max_read_combobox.pack(side=tk.LEFT)
        ttk.Label(max_read_frame, text="字节").pack(side=tk.LEFT, padx=5)
        
        # 传输队列深度
        queue_depth_frame = ttk.Frame(left_frame)
        queue_depth_frame.pack(fill=tk.X, pady=5)
        ttk.Label(queue_depth_frame, text="传输队列深度:", width=20).pack(side=tk.LEFT)
        self.queue_depth_var = tk.StringVar()
        queue_depth_entry = ttk.Entry(queue_depth_frame, textvariable=self.queue_depth_var, width=15)
        queue_depth_entry.pack(side=tk.LEFT)
        ttk.Label(queue_depth_frame, text="条目").pack(side=tk.LEFT, padx=5)
        
        # 右侧参数
        # 描述符大小
        desc_size_frame = ttk.Frame(right_frame)
        desc_size_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_size_frame, text="描述符大小:", width=20).pack(side=tk.LEFT)
        self.desc_size_var = tk.StringVar()
        desc_size_combobox = ttk.Combobox(desc_size_frame, textvariable=self.desc_size_var, width=15)
        desc_size_combobox['values'] = ["16", "32", "64", "128"]
        desc_size_combobox.pack(side=tk.LEFT)
        ttk.Label(desc_size_frame, text="字节").pack(side=tk.LEFT, padx=5)
        
        # 最大突发传输大小
        burst_size_frame = ttk.Frame(right_frame)
        burst_size_frame.pack(fill=tk.X, pady=5)
        ttk.Label(burst_size_frame, text="最大突发传输大小:", width=20).pack(side=tk.LEFT)
        self.burst_size_var = tk.StringVar()
        burst_size_combobox = ttk.Combobox(burst_size_frame, textvariable=self.burst_size_var, width=15)
        burst_size_combobox['values'] = ["1", "2", "4", "8", "16", "32", "64", "128", "256"]
        burst_size_combobox.pack(side=tk.LEFT)
        ttk.Label(burst_size_frame, text="次传输").pack(side=tk.LEFT, padx=5)
        
        # 地址宽度
        addr_width_frame = ttk.Frame(right_frame)
        addr_width_frame.pack(fill=tk.X, pady=5)
        ttk.Label(addr_width_frame, text="地址宽度:", width=20).pack(side=tk.LEFT)
        self.addr_width_var = tk.StringVar()
        addr_width_combobox = ttk.Combobox(addr_width_frame, textvariable=self.addr_width_var, width=15)
        addr_width_combobox['values'] = ["32", "64"]
        addr_width_combobox.pack(side=tk.LEFT)
        ttk.Label(addr_width_frame, text="位").pack(side=tk.LEFT, padx=5)
        
        # 创建高级参数区域
        adv_params_frame = ttk.LabelFrame(main_frame, text="高级参数")
        adv_params_frame.pack(fill=tk.X, pady=10)
        
        adv_left_frame = ttk.Frame(adv_params_frame)
        adv_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        adv_right_frame = ttk.Frame(adv_params_frame)
        adv_right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧高级参数
        # 支持写事务
        self.write_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            adv_left_frame, 
            text="支持写事务", 
            variable=self.write_enabled_var
        ).pack(anchor=tk.W, pady=5)
        
        # 支持读事务
        self.read_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            adv_left_frame, 
            text="支持读事务", 
            variable=self.read_enabled_var
        ).pack(anchor=tk.W, pady=5)
        
        # 支持IOMMU
        self.iommu_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            adv_left_frame, 
            text="支持IOMMU/VT-d", 
            variable=self.iommu_enabled_var
        ).pack(anchor=tk.W, pady=5)
        
        # 右侧高级参数
        # 支持64位寻址
        self.addr64_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            adv_right_frame, 
            text="支持64位寻址", 
            variable=self.addr64_enabled_var
        ).pack(anchor=tk.W, pady=5)
        
        # 支持中断
        self.int_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            adv_right_frame, 
            text="支持传输完成中断", 
            variable=self.int_enabled_var
        ).pack(anchor=tk.W, pady=5)
        
        # 支持传输进度报告
        self.progress_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            adv_right_frame, 
            text="支持传输进度报告", 
            variable=self.progress_enabled_var
        ).pack(anchor=tk.W, pady=5)
        
        # 创建DMA寄存器区域
        reg_frame = ttk.LabelFrame(main_frame, text="DMA寄存器配置")
        reg_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        reg_table_frame = ttk.Frame(reg_frame)
        reg_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建寄存器表格
        columns = ("寄存器名称", "偏移地址", "大小", "描述")
        self.reg_tree = ttk.Treeview(reg_table_frame, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            self.reg_tree.heading(col, text=col)
            self.reg_tree.column(col, width=100)
        
        # 添加滚动条
        reg_scroll = ttk.Scrollbar(reg_table_frame, orient=tk.VERTICAL, command=self.reg_tree.yview)
        self.reg_tree.configure(yscrollcommand=reg_scroll.set)
        
        self.reg_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        reg_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 填充默认寄存器
        self.refresh_registers()
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame, 
            text="应用配置", 
            command=self.apply_config
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="重置为默认", 
            command=self.reset_defaults
        ).pack(side=tk.RIGHT, padx=5)
    
    def get_default_config(self):
        """获取默认DMA配置"""
        return {
            "enabled": False,
            "max_payload_size": 256,
            "max_read_request_size": 512,
            "queue_depth": 32,
            "descriptor_size": 32,
            "max_burst_size": 16,
            "address_width": 64,
            "write_enabled": True,
            "read_enabled": True,
            "iommu_support": False,
            "addr64_support": True,
            "interrupt_support": True,
            "progress_report": False,
            "registers": [
                {
                    "name": "DMA_CTRL",
                    "offset": "0x00",
                    "size": 32,
                    "description": "DMA控制寄存器"
                },
                {
                    "name": "DMA_STATUS",
                    "offset": "0x04",
                    "size": 32,
                    "description": "DMA状态寄存器"
                },
                {
                    "name": "DMA_SRC_ADDR_L",
                    "offset": "0x08",
                    "size": 32,
                    "description": "DMA源地址低32位"
                },
                {
                    "name": "DMA_SRC_ADDR_H",
                    "offset": "0x0C",
                    "size": 32,
                    "description": "DMA源地址高32位"
                },
                {
                    "name": "DMA_DST_ADDR_L",
                    "offset": "0x10",
                    "size": 32,
                    "description": "DMA目标地址低32位"
                },
                {
                    "name": "DMA_DST_ADDR_H",
                    "offset": "0x14",
                    "size": 32,
                    "description": "DMA目标地址高32位"
                },
                {
                    "name": "DMA_LENGTH",
                    "offset": "0x18",
                    "size": 32,
                    "description": "DMA传输长度"
                },
                {
                    "name": "DMA_NEXT_DESC_L",
                    "offset": "0x1C",
                    "size": 32,
                    "description": "下一个描述符地址低32位"
                },
                {
                    "name": "DMA_NEXT_DESC_H",
                    "offset": "0x20",
                    "size": 32,
                    "description": "下一个描述符地址高32位"
                },
                {
                    "name": "DMA_INT_STATUS",
                    "offset": "0x24",
                    "size": 32,
                    "description": "DMA中断状态"
                },
                {
                    "name": "DMA_INT_MASK",
                    "offset": "0x28",
                    "size": 32,
                    "description": "DMA中断掩码"
                }
            ]
        }
    
    def load_config(self):
        """从配置加载到界面"""
        self.enabled_var.set(self.config.get("enabled", False))
        self.max_payload_var.set(str(self.config.get("max_payload_size", 256)))
        self.max_read_var.set(str(self.config.get("max_read_request_size", 512)))
        self.queue_depth_var.set(str(self.config.get("queue_depth", 32)))
        self.desc_size_var.set(str(self.config.get("descriptor_size", 32)))
        self.burst_size_var.set(str(self.config.get("max_burst_size", 16)))
        self.addr_width_var.set(str(self.config.get("address_width", 64)))
        
        self.write_enabled_var.set(self.config.get("write_enabled", True))
        self.read_enabled_var.set(self.config.get("read_enabled", True))
        self.iommu_enabled_var.set(self.config.get("iommu_support", False))
        self.addr64_enabled_var.set(self.config.get("addr64_support", True))
        self.int_enabled_var.set(self.config.get("interrupt_support", True))
        self.progress_enabled_var.set(self.config.get("progress_report", False))
        
        # 更新UI状态
        self.update_ui_state()
        
        # 刷新寄存器表格
        self.refresh_registers()
    
    def save_config(self):
        """从界面保存到配置"""
        try:
            self.config["enabled"] = self.enabled_var.get()
            self.config["max_payload_size"] = int(self.max_payload_var.get())
            self.config["max_read_request_size"] = int(self.max_read_var.get())
            self.config["queue_depth"] = int(self.queue_depth_var.get())
            self.config["descriptor_size"] = int(self.desc_size_var.get())
            self.config["max_burst_size"] = int(self.burst_size_var.get())
            self.config["address_width"] = int(self.addr_width_var.get())
            
            self.config["write_enabled"] = self.write_enabled_var.get()
            self.config["read_enabled"] = self.read_enabled_var.get()
            self.config["iommu_support"] = self.iommu_enabled_var.get()
            self.config["addr64_support"] = self.addr64_enabled_var.get()
            self.config["interrupt_support"] = self.int_enabled_var.get()
            self.config["progress_report"] = self.progress_enabled_var.get()
            
            return True
        except ValueError:
            messagebox.showerror("错误", "参数格式不正确，请检查输入")
            return False
    
    def refresh_registers(self):
        """刷新寄存器表格"""
        # 清空表格
        for item in self.reg_tree.get_children():
            self.reg_tree.delete(item)
        
        # 添加寄存器
        for reg in self.config.get("registers", []):
            name = reg.get("name", "")
            offset = reg.get("offset", "0x0")
            size = str(reg.get("size", 32))
            desc = reg.get("description", "")
            
            self.reg_tree.insert("", tk.END, values=(name, offset, size, desc))
    
    def on_enabled_changed(self):
        """DMA使能状态改变事件"""
        self.update_ui_state()
    
    def update_ui_state(self):
        """更新UI状态"""
        enabled = self.enabled_var.get()
        state = "normal" if enabled else "disabled"
        
        # 更新所有控件状态
        for frame in self.winfo_children():
            for child in frame.winfo_children():
                if isinstance(child, ttk.LabelFrame):
                    for subframe in child.winfo_children():
                        for widget in subframe.winfo_children():
                            if widget != self.enabled_checkbox:
                                if hasattr(widget, 'state'):
                                    widget.state([state] if state == "normal" else ["!focus", "disabled"])
    
    def apply_config(self):
        """应用DMA配置"""
        if self.save_config():
            # 调用回调函数
            if self.update_callback:
                self.update_callback(self.config)
            
            messagebox.showinfo("成功", "DMA配置已应用")
    
    def reset_defaults(self):
        """重置为默认配置"""
        if messagebox.askyesno("确认", "确定要重置为默认配置吗？"):
            self.config = self.get_default_config()
            self.load_config()
    
    def set_config(self, config):
        """设置DMA配置
        
        Args:
            config: DMA配置数据
        """
        if config:
            self.config = config
        else:
            self.config = self.get_default_config()
            
        self.load_config()


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.geometry("800x600")
    
    def on_dma_updated(config):
        print("DMA配置已更新")
        print(f"启用状态: {'是' if config.get('enabled') else '否'}")
    
    editor = DMAEditor(root, on_dma_updated)
    editor.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop() 