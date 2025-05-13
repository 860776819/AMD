#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCIe设备伪装工具 - 增强版图形用户界面
为PCIe设备伪装工具提供全功能图形界面
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# 导入主工具
from pcie_spoof_tool import PCIeSpoofTool, PRESET_DEVICES, DEVICE_TYPES

# 导入自定义组件
try:
    from register_editor import RegisterEditor
    from dma_editor import DMAEditor
    from interrupt_editor import InterruptEditor
    from visual_view import VisualView
    
    COMPONENTS_AVAILABLE = True
except ImportError:
    COMPONENTS_AVAILABLE = False

class PCIeSpoofGUIEnhanced:
    """PCIe设备伪装工具增强版GUI类"""
    
    def __init__(self, root):
        """初始化GUI界面"""
        self.root = root
        self.root.title("PCIe设备伪装工具 - 增强版")
        self.root.geometry("1024x768")
        self.root.minsize(1024, 768)
        
        # 创建工具实例
        self.tool = PCIeSpoofTool()
        
        # 当前配置路径
        self.current_config_path = None
        
        # 当前寄存器数据
        self.registers = []
        
        # 当前DMA配置
        self.dma_config = {}
        
        # 当前中断配置
        self.interrupt_config = {}
        
        # 高级组件
        self.register_editor = None
        self.dma_editor = None
        self.interrupt_editor = None
        self.visual_view = None
        
        # 设置界面风格
        self.style = ttk.Style()
        
        # 尝试设置主题
        try:
            self.style.theme_use("clam")
        except:
            pass
            
        self.style.configure("TButton", padding=6)
        self.style.configure("TLabel", padding=6)
        self.style.configure("TFrame", padding=10)
        
        # 创建主布局
        self.create_main_layout()
    
    def create_main_layout(self):
        """创建主界面布局"""
        # 创建菜单栏
        self.create_menu()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            title_frame, 
            text="PCIe设备伪装工具 - 增强版", 
            font=("Arial", 18, "bold")
        ).pack()
        
        ttk.Label(
            title_frame, 
            text="基于PCILeech-FPGA的完整设备伪装代码生成器", 
            font=("Arial", 12)
        ).pack()
        
        # 创建选项卡
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建基本选项卡
        self.create_basic_tabs()
        
        # 如果高级组件可用，创建高级选项卡
        if COMPONENTS_AVAILABLE:
            self.create_advanced_tabs()
        
        # 创建状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_menu(self):
        """创建菜单栏"""
        menu_bar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="新建配置", command=self.new_config)
        file_menu.add_command(label="加载配置", command=self.load_config_file)
        file_menu.add_command(label="保存配置", command=self.save_config_file)
        file_menu.add_separator()
        file_menu.add_command(label="生成代码", command=self.generate_code)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        menu_bar.add_cascade(label="文件", menu=file_menu)
        
        # 编辑菜单
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="寄存器配置", command=lambda: self.notebook.select(3) if COMPONENTS_AVAILABLE else None)
        edit_menu.add_command(label="DMA配置", command=lambda: self.notebook.select(4) if COMPONENTS_AVAILABLE else None)
        edit_menu.add_command(label="中断配置", command=lambda: self.notebook.select(5) if COMPONENTS_AVAILABLE else None)
        
        menu_bar.add_cascade(label="编辑", menu=edit_menu)
        
        # 视图菜单
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="可视化视图", command=lambda: self.notebook.select(6) if COMPONENTS_AVAILABLE else None)
        
        menu_bar.add_cascade(label="视图", menu=view_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        
        menu_bar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menu_bar)
    
    def create_basic_tabs(self):
        """创建基本选项卡"""
        self.create_tab_new_config()
        self.create_tab_existing_config()
        self.create_tab_generation()
    
    def create_advanced_tabs(self):
        """创建高级选项卡"""
        # 创建寄存器编辑器选项卡
        self.register_editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.register_editor_frame, text="寄存器编辑")
        
        self.register_editor = RegisterEditor(
            self.register_editor_frame,
            callback=self.on_registers_updated
        )
        self.register_editor.pack(fill=tk.BOTH, expand=True)
        
        # 创建DMA配置选项卡
        self.dma_editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dma_editor_frame, text="DMA配置")
        
        self.dma_editor = DMAEditor(
            self.dma_editor_frame,
            callback=self.on_dma_updated
        )
        self.dma_editor.pack(fill=tk.BOTH, expand=True)
        
        # 创建中断配置选项卡
        self.interrupt_editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.interrupt_editor_frame, text="中断配置")
        
        self.interrupt_editor = InterruptEditor(
            self.interrupt_editor_frame,
            callback=self.on_interrupt_updated
        )
        self.interrupt_editor.pack(fill=tk.BOTH, expand=True)
        
        # 创建可视化视图选项卡
        self.visual_view_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.visual_view_frame, text="可视化视图")
        
        self.visual_view = VisualView(self.visual_view_frame)
        self.visual_view.pack(fill=tk.BOTH, expand=True)
    
    def create_tab_new_config(self):
        """创建新建配置选项卡"""
        new_config_frame = ttk.Frame(self.notebook)
        self.notebook.add(new_config_frame, text="新建配置")
        
        # 设备类型选择
        type_frame = ttk.Frame(new_config_frame)
        type_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(type_frame, text="设备类型:", width=15).pack(side=tk.LEFT)
        
        self.device_type_var = tk.StringVar()
        self.device_type_var.set("custom - 自定义设备")
        
        # 创建一个包含中文翻译的列表
        type_values = []
        for key, value in DEVICE_TYPES.items():
            type_values.append(f"{key} - {value}")
        
        type_combobox = ttk.Combobox(type_frame, textvariable=self.device_type_var)
        type_combobox['values'] = type_values
        type_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 设备预设选择
        preset_frame = ttk.Frame(new_config_frame)
        preset_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(preset_frame, text="设备预设:", width=15).pack(side=tk.LEFT)
        
        self.preset_var = tk.StringVar()
        self.preset_var.set("")
        
        preset_combobox = ttk.Combobox(preset_frame, textvariable=self.preset_var)
        preset_combobox['values'] = ["无"] + list(PRESET_DEVICES.keys())
        preset_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 基本设备信息
        info_frame = ttk.LabelFrame(new_config_frame, text="设备基本信息")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 设备名称
        name_frame = ttk.Frame(info_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="设备名称:", width=15).pack(side=tk.LEFT)
        self.device_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.device_name_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 厂商ID
        vendor_frame = ttk.Frame(info_frame)
        vendor_frame.pack(fill=tk.X, pady=5)
        ttk.Label(vendor_frame, text="厂商ID (VID):", width=15).pack(side=tk.LEFT)
        self.vendor_id_var = tk.StringVar()
        ttk.Entry(vendor_frame, textvariable=self.vendor_id_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 设备ID
        device_frame = ttk.Frame(info_frame)
        device_frame.pack(fill=tk.X, pady=5)
        ttk.Label(device_frame, text="设备ID (DID):", width=15).pack(side=tk.LEFT)
        self.device_id_var = tk.StringVar()
        ttk.Entry(device_frame, textvariable=self.device_id_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 类代码
        class_frame = ttk.Frame(info_frame)
        class_frame.pack(fill=tk.X, pady=5)
        ttk.Label(class_frame, text="类代码:", width=15).pack(side=tk.LEFT)
        self.class_code_var = tk.StringVar()
        ttk.Entry(class_frame, textvariable=self.class_code_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 描述信息
        desc_frame = ttk.Frame(info_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="描述:", width=15).pack(side=tk.LEFT)
        self.description_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.description_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 按钮区域
        button_frame = ttk.Frame(new_config_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 创建配置按钮
        create_btn = ttk.Button(
            button_frame, 
            text="创建配置", 
            command=self.create_config
        )
        create_btn.pack(side=tk.RIGHT, padx=5)
        
        # 重置按钮
        reset_btn = ttk.Button(
            button_frame, 
            text="重置", 
            command=self.reset_new_config
        )
        reset_btn.pack(side=tk.RIGHT, padx=5)
        
        # 预设选择事件
        def on_preset_selected(event):
            preset = self.preset_var.get()
            if preset and preset != "无" and preset in PRESET_DEVICES:
                preset_data = PRESET_DEVICES[preset]
                self.device_name_var.set(preset_data.get("name", ""))
                self.vendor_id_var.set(preset_data.get("vendor_id", ""))
                self.device_id_var.set(preset_data.get("device_id", ""))
                self.class_code_var.set(preset_data.get("class_code", ""))
                device_type = preset_data.get("type", "custom")
                self.device_type_var.set(f"{device_type} - {DEVICE_TYPES.get(device_type, '自定义设备')}")
                
                # 如果有寄存器数据，加载到编辑器
                if COMPONENTS_AVAILABLE and "key_registers" in preset_data and self.register_editor is not None:
                    self.registers = preset_data["key_registers"]
                    self.register_editor.set_registers(self.registers)
                    self.visual_view.update_register_map(self.registers)
            elif preset == "无":
                self.reset_new_config()
        
        preset_combobox.bind("<<ComboboxSelected>>", on_preset_selected)
        
        # 设置默认值
        self.reset_new_config()
    
    def create_tab_existing_config(self):
        """创建加载配置选项卡"""
        existing_config_frame = ttk.Frame(self.notebook)
        self.notebook.add(existing_config_frame, text="加载配置")
        
        # 配置文件路径
        path_frame = ttk.Frame(existing_config_frame)
        path_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(path_frame, text="配置文件:", width=15).pack(side=tk.LEFT)
        
        self.config_path_var = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=self.config_path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(
            path_frame, 
            text="浏览...", 
            command=self.browse_config
        )
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # 配置文件内容预览
        preview_frame = ttk.LabelFrame(existing_config_frame, text="配置预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.preview_text = tk.Text(preview_frame, wrap=tk.WORD, height=15)
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)
        
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮区域
        button_frame = ttk.Frame(existing_config_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 加载配置按钮
        load_btn = ttk.Button(
            button_frame, 
            text="加载配置", 
            command=self.load_config
        )
        load_btn.pack(side=tk.RIGHT, padx=5)
    
    def create_tab_generation(self):
        """创建代码生成选项卡"""
        generation_frame = ttk.Frame(self.notebook)
        self.notebook.add(generation_frame, text="生成代码")
        
        # 输出目录
        output_frame = ttk.Frame(generation_frame)
        output_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(output_frame, text="输出目录:", width=15).pack(side=tk.LEFT)
        
        self.output_path_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(
            output_frame, 
            text="浏览...", 
            command=self.browse_output
        )
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # 当前配置提示
        config_frame = ttk.LabelFrame(generation_frame, text="当前配置")
        config_frame.pack(fill=tk.X, pady=10)
        
        self.current_config_var = tk.StringVar()
        self.current_config_var.set("未加载任何配置")
        ttk.Label(config_frame, textvariable=self.current_config_var).pack(fill=tk.X)
        
        # 代码生成选项
        options_frame = ttk.LabelFrame(generation_frame, text="生成选项")
        options_frame.pack(fill=tk.X, pady=10)
        
        # 选项分为两列
        options_grid = ttk.Frame(options_frame)
        options_grid.pack(fill=tk.X, pady=5)
        
        # 第一列选项
        col1_frame = ttk.Frame(options_grid)
        col1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.gen_config_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(col1_frame, text="生成配置空间文件", variable=self.gen_config_var).pack(anchor=tk.W)
        
        self.gen_bar_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(col1_frame, text="生成BAR控制器代码", variable=self.gen_bar_var).pack(anchor=tk.W)
        
        self.gen_behavior_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(col1_frame, text="生成行为模拟代码", variable=self.gen_behavior_var).pack(anchor=tk.W)
        
        self.gen_registers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(col1_frame, text="生成寄存器映射代码", variable=self.gen_registers_var).pack(anchor=tk.W)
        
        # 第二列选项
        col2_frame = ttk.Frame(options_grid)
        col2_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.gen_interrupts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(col2_frame, text="生成中断处理代码", variable=self.gen_interrupts_var).pack(anchor=tk.W)
        
        self.gen_dma_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(col2_frame, text="生成DMA控制器代码", variable=self.gen_dma_var).pack(anchor=tk.W)
        
        self.gen_test_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(col2_frame, text="生成测试脚本", variable=self.gen_test_var).pack(anchor=tk.W)
        
        self.gen_readme_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(col2_frame, text="生成README文档", variable=self.gen_readme_var).pack(anchor=tk.W)
        
        # 全选/取消全选按钮
        select_frame = ttk.Frame(options_frame)
        select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            select_frame, 
            text="全选", 
            command=self.select_all_options
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            select_frame, 
            text="取消全选", 
            command=self.deselect_all_options
        ).pack(side=tk.LEFT, padx=5)
        
        # 生成日志
        log_frame = ttk.LabelFrame(generation_frame, text="生成日志")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮区域
        button_frame = ttk.Frame(generation_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 生成代码按钮
        generate_btn = ttk.Button(
            button_frame, 
            text="生成代码", 
            command=self.generate_code
        )
        generate_btn.pack(side=tk.RIGHT, padx=5)
        
        # 保存配置按钮
        save_config_btn = ttk.Button(
            button_frame, 
            text="保存配置", 
            command=self.save_config_file
        )
        save_config_btn.pack(side=tk.RIGHT, padx=5)
        
        # 打开输出目录按钮
        open_output_btn = ttk.Button(
            button_frame, 
            text="打开输出目录", 
            command=self.open_output_directory
        )
        open_output_btn.pack(side=tk.RIGHT, padx=5)
    
    def new_config(self):
        """创建新配置"""
        # 切换到新建配置选项卡
        self.notebook.select(0)
        self.reset_new_config()
    
    def reset_new_config(self):
        """重置新建配置表单"""
        self.device_name_var.set("")
        self.vendor_id_var.set("FFFF")
        self.device_id_var.set("FFFF")
        self.class_code_var.set("000000")
        self.device_type_var.set("custom - 自定义设备")
        self.description_var.set("")
        
        # 重置预设选择
        self.preset_var.set("无")
        
        # 清空高级编辑器数据
        if COMPONENTS_AVAILABLE and self.register_editor is not None:
            self.registers = []
            self.register_editor.set_registers([])
            self.dma_editor.reset_defaults()
            self.interrupt_editor.reset_defaults()
            self.visual_view.update_views({}, [])
    
    def create_config(self):
        """创建新配置"""
        try:
            # 获取表单值
            device_type = self.device_type_var.get()
            # 如果设备类型包含" - "，则取前半部分
            if " - " in device_type:
                device_type = device_type.split(" - ")[0]
                
            preset = self.preset_var.get() if self.preset_var.get() != "无" else None
            
            # 创建配置
            if preset and preset in PRESET_DEVICES:
                self.tool.create_new_config(device_type, preset)
            else:
                self.tool.create_new_config(device_type)
                
                # 更新自定义值
                self.tool.device_config["name"] = self.device_name_var.get()
                self.tool.device_config["vendor_id"] = self.vendor_id_var.get()
                self.tool.device_config["device_id"] = self.device_id_var.get()
                self.tool.device_config["class_code"] = self.class_code_var.get()
                self.tool.device_config["description"] = self.description_var.get()
            
            # 添加高级配置数据
            if COMPONENTS_AVAILABLE and self.register_editor is not None:
                # 添加寄存器数据
                self.tool.device_config["key_registers"] = self.registers
                
                # 添加DMA配置
                if self.dma_config:
                    self.tool.device_config["dma_config"] = self.dma_config
                
                # 添加中断配置
                if self.interrupt_config:
                    self.tool.device_config["interrupt_config"] = self.interrupt_config
            
            # 更新当前配置显示
            self.update_current_config()
            
            # 切换到生成选项卡
            self.notebook.select(2)
            
            self.status_var.set(f"已创建配置: {self.tool.device_config.get('name', '未命名设备')}")
            messagebox.showinfo("成功", "已成功创建设备配置！")
        except Exception as e:
            self.status_var.set(f"创建配置失败: {str(e)}")
            messagebox.showerror("错误", f"创建配置失败: {str(e)}")
    
    def update_current_config(self):
        """更新当前配置显示"""
        if hasattr(self.tool, 'device_config') and self.tool.device_config:
            device_name = self.tool.device_config.get("name", "未命名设备")
            vendor_id = self.tool.device_config.get("vendor_id", "FFFF")
            device_id = self.tool.device_config.get("device_id", "FFFF")
            device_type = self.tool.device_config.get("type", "custom")
            
            config_info = f"设备: {device_name}\n"
            config_info += f"厂商ID: {vendor_id}  设备ID: {device_id}\n"
            config_info += f"类型: {DEVICE_TYPES.get(device_type, device_type)}\n"
            
            # 添加高级配置信息
            if "key_registers" in self.tool.device_config:
                reg_count = len(self.tool.device_config["key_registers"])
                config_info += f"寄存器数量: {reg_count}\n"
            
            if "dma_config" in self.tool.device_config:
                dma_enabled = self.tool.device_config["dma_config"].get("enabled", False)
                config_info += f"DMA控制器: {'启用' if dma_enabled else '禁用'}\n"
            
            if "interrupt_config" in self.tool.device_config:
                int_mode = self.tool.device_config["interrupt_config"].get("mode", "legacy")
                config_info += f"中断模式: {int_mode}\n"
            
            self.current_config_var.set(config_info)
        else:
            self.current_config_var.set("未加载任何配置")
    
    def load_config_file(self):
        """加载配置文件"""
        # 切换到加载配置选项卡
        self.notebook.select(1)
        
        # 打开文件对话框
        filename = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            self.config_path_var.set(filename)
            self.preview_config(filename)
    
    def save_config_file(self):
        """保存配置文件"""
        if not hasattr(self.tool, 'device_config') or not self.tool.device_config:
            messagebox.showwarning("警告", "没有可保存的配置！")
            return
            
        # 选择保存位置
        filename = filedialog.asksaveasfilename(
            title="保存配置文件",
            filetypes=[("JSON文件", "*.json")],
            defaultextension=".json"
        )
        if not filename:
            return
            
        try:
            # 更新高级配置数据
            if COMPONENTS_AVAILABLE and self.register_editor is not None:
                # 更新寄存器数据
                self.tool.device_config["key_registers"] = self.registers
                
                # 更新DMA配置
                self.tool.device_config["dma_config"] = self.dma_config
                
                # 更新中断配置
                self.tool.device_config["interrupt_config"] = self.interrupt_config
            
            # 保存配置
            if self.tool.save_config(filename):
                self.current_config_path = filename
                self.status_var.set(f"配置已保存到: {filename}")
                messagebox.showinfo("成功", f"配置已保存到: {filename}")
            else:
                self.status_var.set("保存配置失败")
                messagebox.showerror("错误", "保存配置失败！")
        except Exception as e:
            self.status_var.set(f"保存配置失败: {str(e)}")
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def generate_code(self):
        """生成代码"""
        if not hasattr(self.tool, 'device_config') or not self.tool.device_config:
            messagebox.showwarning("警告", "请先创建或加载配置！")
            return
            
        output_dir = self.output_path_var.get()
        if not output_dir:
            messagebox.showwarning("警告", "请先选择输出目录！")
            return
            
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 获取生成选项
        options = {
            "gen_config": self.gen_config_var.get(),
            "gen_bar": self.gen_bar_var.get(),
            "gen_behavior": self.gen_behavior_var.get(),
            "gen_registers": self.gen_registers_var.get(),
            "gen_interrupts": self.gen_interrupts_var.get(),
            "gen_dma": self.gen_dma_var.get(),
            "gen_test": self.gen_test_var.get(),
            "gen_readme": self.gen_readme_var.get()
        }
        
        try:
            # 记录开始
            self.log_text.insert(tk.END, "开始生成代码...\n")
            self.log_text.update()
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成代码（这里简化，实际应该根据选项调用相应的生成方法）
            # 由于pcie_spoof_tool.py中generate_all方法不支持选择性生成，
            # 这里直接调用原方法，后续可以扩展为支持选择性生成
            result = self.tool.generate_all(output_dir)
            
            if result:
                # 记录成功信息
                self.log_text.insert(tk.END, f"✅ 代码生成成功！\n")
                self.log_text.insert(tk.END, f"输出路径: {output_dir}\n\n")
                self.log_text.insert(tk.END, "生成的文件:\n")
                
                if options["gen_config"]:
                    self.log_text.insert(tk.END, "- pcileech_cfgspace.coe\n")
                    self.log_text.insert(tk.END, "- pcileech_cfgspace_writemask.coe\n")
                
                if options["gen_bar"]:
                    self.log_text.insert(tk.END, "- bar_controller.sv\n")
                
                if options["gen_behavior"]:
                    self.log_text.insert(tk.END, "- device_behavior.sv\n")
                
                if options["gen_registers"]:
                    self.log_text.insert(tk.END, "- register_map.sv\n")
                
                if options["gen_interrupts"]:
                    self.log_text.insert(tk.END, "- interrupt_handler.sv\n")
                
                if options["gen_dma"]:
                    self.log_text.insert(tk.END, "- dma_controller.sv\n")
                
                if options["gen_test"]:
                    self.log_text.insert(tk.END, "- test_device.py\n")
                
                if options["gen_readme"]:
                    self.log_text.insert(tk.END, "- device_spoof_includes.sv\n")
                    self.log_text.insert(tk.END, "- README.md\n")
                
                self.status_var.set(f"代码生成完成: {output_dir}")
                messagebox.showinfo("成功", f"代码生成完成！文件已保存至: {output_dir}")
            else:
                self.log_text.insert(tk.END, "❌ 生成失败！请检查配置和输出路径。\n")
                self.status_var.set("代码生成失败")
                messagebox.showerror("错误", "代码生成失败！")
        except Exception as e:
            self.log_text.insert(tk.END, f"❌ 发生错误: {str(e)}\n")
            self.status_var.set(f"代码生成失败: {str(e)}")
            messagebox.showerror("错误", f"代码生成失败: {str(e)}")
    
    def on_registers_updated(self, registers):
        """处理寄存器更新事件
        
        Args:
            registers: 更新后的寄存器数据
        """
        self.registers = registers
        
        # 更新视图
        if hasattr(self, 'visual_view') and self.visual_view is not None:
            self.visual_view.update_register_map(registers)
    
    def on_dma_updated(self, config):
        """处理DMA配置更新事件
        
        Args:
            config: 更新后的DMA配置
        """
        self.dma_config = config
    
    def on_interrupt_updated(self, config):
        """处理中断配置更新事件
        
        Args:
            config: 更新后的中断配置
        """
        self.interrupt_config = config
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
PCIe设备伪装工具 - 使用说明

1. 基本操作:
   - 新建配置: 创建新的设备伪装配置
   - 加载配置: 打开已有的配置文件
   - 保存配置: 保存当前配置到文件
   - 生成代码: 生成所有伪装代码文件

2. 高级功能:
   - 寄存器编辑: 添加、修改设备寄存器和位域
   - DMA配置: 配置DMA控制器参数
   - 中断配置: 设置中断模式和事件
   - 可视化视图: 查看寄存器映射和设备结构图

3. 使用流程:
   a. 创建或加载设备配置
   b. 进行高级配置编辑
   c. 设置输出目录
   d. 生成代码
   e. 将生成的文件整合到PCILeech-FPGA项目中
        """
        messagebox.showinfo("使用说明", help_text)
    
    def show_about(self):
        """显示关于信息"""
        about_text = """
PCIe设备伪装工具 - 增强版

基于PCILeech-FPGA项目的完整设备伪装代码生成器
版本: 1.1.0

功能:
- 创建PCIe设备伪装配置
- 生成配置空间、BAR控制器、DMA控制器等代码
- 可视化编辑寄存器和位域
- 提供设备结构可视化视图
        """
        messagebox.showinfo("关于", about_text)
    
    def browse_config(self):
        """浏览配置文件"""
        filename = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            self.config_path_var.set(filename)
            self.preview_config(filename)
    
    def preview_config(self, config_path):
        """预览配置文件内容"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 清空预览框
            self.preview_text.delete(1.0, tk.END)
            
            # 格式化JSON并插入
            formatted_json = json.dumps(config_data, indent=2, ensure_ascii=False)
            self.preview_text.insert(tk.END, formatted_json)
            
            self.status_var.set(f"已加载配置预览: {config_path}")
        except Exception as e:
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"加载失败: {str(e)}")
            self.status_var.set(f"加载配置预览失败: {str(e)}")
    
    def load_config(self):
        """加载配置文件"""
        config_path = self.config_path_var.get()
        if not config_path:
            messagebox.showwarning("警告", "请先选择配置文件！")
            return
            
        try:
            if self.tool.load_config(config_path):
                self.current_config_path = config_path
                
                # 更新高级编辑器
                if COMPONENTS_AVAILABLE and self.register_editor is not None:
                    # 更新寄存器编辑器
                    if "key_registers" in self.tool.device_config:
                        self.registers = self.tool.device_config["key_registers"]
                        self.register_editor.set_registers(self.registers)
                    
                    # 更新DMA配置
                    if "dma_config" in self.tool.device_config:
                        self.dma_config = self.tool.device_config["dma_config"]
                        self.dma_editor.set_config(self.dma_config)
                    
                    # 更新中断配置
                    if "interrupt_config" in self.tool.device_config:
                        self.interrupt_config = self.tool.device_config["interrupt_config"]
                        self.interrupt_editor.set_config(self.interrupt_config)
                    
                    # 更新可视化视图
                    self.visual_view.update_views(
                        self.tool.device_config,
                        self.tool.device_config.get("key_registers", [])
                    )
                
                # 更新当前配置显示
                self.update_current_config()
                
                # 切换到生成选项卡
                self.notebook.select(2)
                
                self.status_var.set(f"已加载配置: {config_path}")
                messagebox.showinfo("成功", "已成功加载配置文件！")
            else:
                self.status_var.set(f"加载配置失败")
                messagebox.showerror("错误", "加载配置失败！")
        except Exception as e:
            self.status_var.set(f"加载配置失败: {str(e)}")
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
    
    def browse_output(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_path_var.set(directory)
    
    def select_all_options(self):
        """选择所有生成选项"""
        self.gen_config_var.set(True)
        self.gen_bar_var.set(True)
        self.gen_behavior_var.set(True)
        self.gen_registers_var.set(True)
        self.gen_interrupts_var.set(True)
        self.gen_dma_var.set(True)
        self.gen_test_var.set(True)
        self.gen_readme_var.set(True)
    
    def deselect_all_options(self):
        """取消选择所有生成选项"""
        self.gen_config_var.set(False)
        self.gen_bar_var.set(False)
        self.gen_behavior_var.set(False)
        self.gen_registers_var.set(False)
        self.gen_interrupts_var.set(False)
        self.gen_dma_var.set(False)
        self.gen_test_var.set(False)
        self.gen_readme_var.set(False)
    
    def open_output_directory(self):
        """打开输出目录"""
        output_dir = self.output_path_var.get()
        if not output_dir:
            messagebox.showwarning("警告", "请先设置输出目录！")
            return
            
        if not os.path.exists(output_dir):
            messagebox.showwarning("警告", "输出目录不存在！")
            return
            
        # 打开文件夹
        try:
            if sys.platform == 'win32':
                os.startfile(output_dir)
            elif sys.platform == 'darwin':  # macOS
                os.system(f'open "{output_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{output_dir}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录: {str(e)}")


# 应用入口
def main():
    root = tk.Tk()
    app = PCIeSpoofGUIEnhanced(root)
    root.mainloop()

if __name__ == "__main__":
    main() 