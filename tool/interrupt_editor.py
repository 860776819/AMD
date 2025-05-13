#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中断编辑器组件
为PCIe设备伪装工具提供中断控制器配置功能
"""

import tkinter as tk
from tkinter import ttk, messagebox

class InterruptEditor(ttk.Frame):
    """中断编辑器组件"""
    
    def __init__(self, parent, callback=None):
        """初始化中断编辑器
        
        Args:
            parent: 父级窗口
            callback: 中断配置更新回调函数
        """
        super().__init__(parent)
        
        # 中断配置
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
            text="中断控制器配置", 
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT)
        
        # 创建中断模式区域
        mode_frame = ttk.LabelFrame(main_frame, text="中断模式")
        mode_frame.pack(fill=tk.X, pady=10)
        
        # 中断模式选择
        mode_inner_frame = ttk.Frame(mode_frame)
        mode_inner_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(mode_inner_frame, text="中断模式:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.mode_var = tk.StringVar(value="legacy")
        ttk.Radiobutton(mode_inner_frame, text="传统中断", variable=self.mode_var, value="legacy", command=self.on_mode_changed).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_inner_frame, text="MSI中断", variable=self.mode_var, value="msi", command=self.on_mode_changed).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_inner_frame, text="MSI-X中断", variable=self.mode_var, value="msix", command=self.on_mode_changed).pack(side=tk.LEFT, padx=10)
        
        # 创建基本参数区域
        params_frame = ttk.LabelFrame(main_frame, text="基本参数")
        params_frame.pack(fill=tk.X, pady=10)
        
        # 创建两列布局
        left_frame = ttk.Frame(params_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        right_frame = ttk.Frame(params_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧参数
        # PIN号码（传统中断）
        self.legacy_frame = ttk.Frame(left_frame)
        self.legacy_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.legacy_frame, text="中断PIN:", width=15).pack(side=tk.LEFT)
        self.pin_var = tk.StringVar()
        pin_combobox = ttk.Combobox(self.legacy_frame, textvariable=self.pin_var, width=10)
        pin_combobox['values'] = ["INTA#", "INTB#", "INTC#", "INTD#"]
        pin_combobox.pack(side=tk.LEFT)
        
        # MSI数量（MSI中断）
        self.msi_frame = ttk.Frame(left_frame)
        # 不要立即pack，根据模式显示
        ttk.Label(self.msi_frame, text="MSI向量数量:", width=15).pack(side=tk.LEFT)
        self.msi_count_var = tk.StringVar()
        msi_count_combobox = ttk.Combobox(self.msi_frame, textvariable=self.msi_count_var, width=10)
        msi_count_combobox['values'] = ["1", "2", "4", "8", "16", "32"]
        msi_count_combobox.pack(side=tk.LEFT)
        
        # MSI-X表大小（MSI-X中断）
        self.msix_frame = ttk.Frame(left_frame)
        # 不要立即pack，根据模式显示
        ttk.Label(self.msix_frame, text="MSI-X表大小:", width=15).pack(side=tk.LEFT)
        self.msix_count_var = tk.StringVar()
        msix_count_entry = ttk.Entry(self.msix_frame, textvariable=self.msix_count_var, width=10)
        msix_count_entry.pack(side=tk.LEFT)
        
        # 右侧参数
        # 中断线路状态（传统中断）
        self.legacy_status_frame = ttk.Frame(right_frame)
        self.legacy_status_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.legacy_status_frame, text="线路默认状态:", width=15).pack(side=tk.LEFT)
        self.pin_status_var = tk.StringVar()
        pin_status_combobox = ttk.Combobox(self.legacy_status_frame, textvariable=self.pin_status_var, width=15)
        pin_status_combobox['values'] = ["高电平有效", "低电平有效"]
        pin_status_combobox.pack(side=tk.LEFT)
        
        # 中断控制模式
        int_control_frame = ttk.Frame(right_frame)
        int_control_frame.pack(fill=tk.X, pady=5)
        ttk.Label(int_control_frame, text="控制模式:", width=15).pack(side=tk.LEFT)
        self.int_control_var = tk.StringVar()
        int_control_combobox = ttk.Combobox(int_control_frame, textvariable=self.int_control_var, width=15)
        int_control_combobox['values'] = ["寄存器控制", "自动触发"]
        int_control_combobox.pack(side=tk.LEFT)
        
        # 中断延迟
        int_delay_frame = ttk.Frame(right_frame)
        int_delay_frame.pack(fill=tk.X, pady=5)
        ttk.Label(int_delay_frame, text="中断延迟:", width=15).pack(side=tk.LEFT)
        self.int_delay_var = tk.StringVar()
        int_delay_entry = ttk.Entry(int_delay_frame, textvariable=self.int_delay_var, width=15)
        int_delay_entry.pack(side=tk.LEFT)
        ttk.Label(int_delay_frame, text="周期").pack(side=tk.LEFT, padx=5)
        
        # 创建中断事件区域
        events_frame = ttk.LabelFrame(main_frame, text="中断事件")
        events_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        events_inner_frame = ttk.Frame(events_frame)
        events_inner_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建中断事件表格
        columns = ("中断名称", "向量号", "条件", "描述")
        self.events_tree = ttk.Treeview(events_inner_frame, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            self.events_tree.heading(col, text=col)
            self.events_tree.column(col, width=100)
        
        # 添加滚动条
        events_scroll = ttk.Scrollbar(events_inner_frame, orient=tk.VERTICAL, command=self.events_tree.yview)
        self.events_tree.configure(yscrollcommand=events_scroll.set)
        
        self.events_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        events_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 事件操作按钮
        events_btn_frame = ttk.Frame(events_frame)
        events_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(events_btn_frame, text="添加事件", command=self.add_event).pack(side=tk.LEFT, padx=5)
        ttk.Button(events_btn_frame, text="编辑事件", command=self.edit_event).pack(side=tk.LEFT, padx=5)
        ttk.Button(events_btn_frame, text="删除事件", command=self.delete_event).pack(side=tk.LEFT, padx=5)
        
        # 创建中断寄存器区域
        reg_frame = ttk.LabelFrame(main_frame, text="中断寄存器")
        reg_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        reg_inner_frame = ttk.Frame(reg_frame)
        reg_inner_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建中断寄存器表格
        columns = ("寄存器名称", "偏移地址", "宽度", "描述")
        self.reg_tree = ttk.Treeview(reg_inner_frame, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            self.reg_tree.heading(col, text=col)
            self.reg_tree.column(col, width=100)
        
        # 添加滚动条
        reg_scroll = ttk.Scrollbar(reg_inner_frame, orient=tk.VERTICAL, command=self.reg_tree.yview)
        self.reg_tree.configure(yscrollcommand=reg_scroll.set)
        
        self.reg_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        reg_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
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
        
        # 初始化界面
        self.load_config()
    
    def get_default_config(self):
        """获取默认中断配置"""
        return {
            "mode": "legacy",
            "pin": "INTA#",
            "pin_status": "高电平有效",
            "msi_count": 1,
            "msix_count": 16,
            "control_mode": "寄存器控制",
            "delay": 10,
            "events": [
                {
                    "name": "DATA_READY",
                    "vector": 0,
                    "condition": "数据就绪",
                    "description": "数据准备就绪时触发"
                },
                {
                    "name": "ERROR",
                    "vector": 1,
                    "condition": "发生错误",
                    "description": "设备发生错误时触发"
                },
                {
                    "name": "DMA_COMPLETE",
                    "vector": 2,
                    "condition": "DMA传输完成",
                    "description": "DMA传输完成时触发"
                }
            ],
            "registers": [
                {
                    "name": "INT_STATUS",
                    "offset": "0x30",
                    "width": 32,
                    "description": "中断状态寄存器"
                },
                {
                    "name": "INT_MASK",
                    "offset": "0x34",
                    "width": 32,
                    "description": "中断掩码寄存器"
                },
                {
                    "name": "INT_CLEAR",
                    "offset": "0x38",
                    "width": 32,
                    "description": "中断清除寄存器"
                },
                {
                    "name": "INT_FORCE",
                    "offset": "0x3C",
                    "width": 32,
                    "description": "中断强制触发寄存器"
                }
            ]
        }
    
    def load_config(self):
        """从配置加载到界面"""
        mode = self.config.get("mode", "legacy")
        self.mode_var.set(mode)
        
        self.pin_var.set(self.config.get("pin", "INTA#"))
        self.pin_status_var.set(self.config.get("pin_status", "高电平有效"))
        self.msi_count_var.set(str(self.config.get("msi_count", 1)))
        self.msix_count_var.set(str(self.config.get("msix_count", 16)))
        self.int_control_var.set(self.config.get("control_mode", "寄存器控制"))
        self.int_delay_var.set(str(self.config.get("delay", 10)))
        
        # 根据模式显示相应的控件
        self.update_mode_ui()
        
        # 加载中断事件
        self.refresh_events()
        
        # 加载中断寄存器
        self.refresh_registers()
    
    def save_config(self):
        """从界面保存到配置"""
        try:
            self.config["mode"] = self.mode_var.get()
            self.config["pin"] = self.pin_var.get()
            self.config["pin_status"] = self.pin_status_var.get()
            self.config["msi_count"] = int(self.msi_count_var.get())
            self.config["msix_count"] = int(self.msix_count_var.get())
            self.config["control_mode"] = self.int_control_var.get()
            self.config["delay"] = int(self.int_delay_var.get())
            
            # 保存事件数据
            events = []
            for item in self.events_tree.get_children():
                values = self.events_tree.item(item, 'values')
                events.append({
                    "name": values[0],
                    "vector": int(values[1]),
                    "condition": values[2],
                    "description": values[3]
                })
            self.config["events"] = events
            
            return True
        except ValueError:
            messagebox.showerror("错误", "参数格式不正确，请检查输入")
            return False
    
    def refresh_events(self):
        """刷新中断事件表格"""
        # 清空表格
        for item in self.events_tree.get_children():
            self.events_tree.delete(item)
        
        # 添加事件
        for event in self.config.get("events", []):
            name = event.get("name", "")
            vector = str(event.get("vector", 0))
            condition = event.get("condition", "")
            desc = event.get("description", "")
            
            self.events_tree.insert("", tk.END, values=(name, vector, condition, desc))
    
    def refresh_registers(self):
        """刷新中断寄存器表格"""
        # 清空表格
        for item in self.reg_tree.get_children():
            self.reg_tree.delete(item)
        
        # 添加寄存器
        for reg in self.config.get("registers", []):
            name = reg.get("name", "")
            offset = reg.get("offset", "0x0")
            width = str(reg.get("width", 32))
            desc = reg.get("description", "")
            
            self.reg_tree.insert("", tk.END, values=(name, offset, width, desc))
    
    def on_mode_changed(self):
        """中断模式改变事件"""
        self.update_mode_ui()
    
    def update_mode_ui(self):
        """根据中断模式更新UI"""
        mode = self.mode_var.get()
        
        # 隐藏所有模式特定的控件
        self.legacy_frame.pack_forget()
        self.msi_frame.pack_forget()
        self.msix_frame.pack_forget()
        self.legacy_status_frame.pack_forget()
        
        # 根据模式显示对应控件
        if mode == "legacy":
            self.legacy_frame.pack(fill=tk.X, pady=5)
            self.legacy_status_frame.pack(fill=tk.X, pady=5)
        elif mode == "msi":
            self.msi_frame.pack(fill=tk.X, pady=5)
        elif mode == "msix":
            self.msix_frame.pack(fill=tk.X, pady=5)
    
    def add_event(self):
        """添加中断事件"""
        dialog = EventDialog(self, "添加中断事件")
        if dialog.result:
            name, vector, condition, desc = dialog.result
            self.events_tree.insert("", tk.END, values=(name, vector, condition, desc))
    
    def edit_event(self):
        """编辑中断事件"""
        selection = self.events_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个中断事件")
            return
            
        item = selection[0]
        values = self.events_tree.item(item, 'values')
        
        dialog = EventDialog(self, "编辑中断事件", values)
        if dialog.result:
            name, vector, condition, desc = dialog.result
            self.events_tree.item(item, values=(name, vector, condition, desc))
    
    def delete_event(self):
        """删除中断事件"""
        selection = self.events_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个中断事件")
            return
            
        if messagebox.askyesno("确认", "确定要删除选中的中断事件吗？"):
            for item in selection:
                self.events_tree.delete(item)
    
    def apply_config(self):
        """应用中断配置"""
        if self.save_config():
            # 调用回调函数
            if self.update_callback:
                self.update_callback(self.config)
            
            messagebox.showinfo("成功", "中断配置已应用")
    
    def reset_defaults(self):
        """重置为默认配置"""
        if messagebox.askyesno("确认", "确定要重置为默认配置吗？"):
            self.config = self.get_default_config()
            self.load_config()
    
    def set_config(self, config):
        """设置中断配置
        
        Args:
            config: 中断配置数据
        """
        if config:
            self.config = config
        else:
            self.config = self.get_default_config()
            
        self.load_config()


class EventDialog:
    """中断事件编辑对话框"""
    
    def __init__(self, parent, title, values=None):
        """初始化对话框
        
        Args:
            parent: 父级窗口
            title: 对话框标题
            values: 事件初始值，用于编辑模式
        """
        self.result = None
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 创建表单
        self.create_form(values)
        
        # 模态等待
        parent.wait_window(self.dialog)
    
    def create_form(self, values):
        """创建表单
        
        Args:
            values: 事件初始值
        """
        form_frame = ttk.Frame(self.dialog, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 事件名称
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="事件名称:", width=10).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 向量号
        vector_frame = ttk.Frame(form_frame)
        vector_frame.pack(fill=tk.X, pady=5)
        ttk.Label(vector_frame, text="向量号:", width=10).pack(side=tk.LEFT)
        self.vector_var = tk.StringVar()
        ttk.Entry(vector_frame, textvariable=self.vector_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 触发条件
        condition_frame = ttk.Frame(form_frame)
        condition_frame.pack(fill=tk.X, pady=5)
        ttk.Label(condition_frame, text="触发条件:", width=10).pack(side=tk.LEFT)
        self.condition_var = tk.StringVar()
        ttk.Entry(condition_frame, textvariable=self.condition_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 描述
        desc_frame = ttk.Frame(form_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="描述:", width=10).pack(side=tk.LEFT)
        self.desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.desc_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 设置初始值
        if values:
            self.name_var.set(values[0])
            self.vector_var.set(values[1])
            self.condition_var.set(values[2])
            self.desc_var.set(values[3])
        else:
            # 默认值
            self.vector_var.set("0")
        
        # 按钮
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="确定", command=self.on_ok).pack(side=tk.RIGHT, padx=5)
    
    def on_ok(self):
        """确定按钮事件处理"""
        name = self.name_var.get()
        vector = self.vector_var.get()
        condition = self.condition_var.get()
        desc = self.desc_var.get()
        
        if not name:
            messagebox.showwarning("警告", "事件名称不能为空", parent=self.dialog)
            return
            
        try:
            int(vector)
        except ValueError:
            messagebox.showwarning("警告", "向量号必须是数字", parent=self.dialog)
            return
        
        self.result = (name, vector, condition, desc)
        self.dialog.destroy()


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.geometry("800x600")
    
    def on_interrupt_updated(config):
        print("中断配置已更新")
        print(f"中断模式: {config.get('mode')}")
    
    editor = InterruptEditor(root, on_interrupt_updated)
    editor.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop() 