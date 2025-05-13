#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
寄存器编辑器组件
为PCIe设备伪装工具提供寄存器和位域编辑功能
"""

import tkinter as tk
from tkinter import ttk, messagebox

class RegisterEditor(ttk.Frame):
    """寄存器编辑器组件"""
    
    def __init__(self, parent, callback=None):
        """初始化寄存器编辑器
        
        Args:
            parent: 父级窗口
            callback: 寄存器更新回调函数
        """
        super().__init__(parent)
        
        # 寄存器列表
        self.registers = []
        
        # 当前选中的寄存器
        self.current_register = None
        
        # 更新回调
        self.update_callback = callback
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建分割窗口
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧寄存器列表
        self.left_frame = ttk.Frame(self.paned)
        self.paned.add(self.left_frame, weight=1)
        
        # 寄存器列表标题
        ttk.Label(self.left_frame, text="寄存器列表", font=("Arial", 12, "bold")).pack(fill=tk.X, pady=5)
        
        # 寄存器列表框架
        list_frame = ttk.Frame(self.left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 寄存器列表
        self.register_listbox = tk.Listbox(list_frame, activestyle='none')
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.register_listbox.yview)
        self.register_listbox.configure(yscrollcommand=list_scrollbar.set)
        
        self.register_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 寄存器列表按钮
        btn_frame = ttk.Frame(self.left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="添加", command=self.add_register).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除", command=self.delete_register).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="上移", command=lambda: self.move_register(-1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="下移", command=lambda: self.move_register(1)).pack(side=tk.LEFT, padx=5)
        
        # 右侧编辑区域
        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.right_frame, weight=2)
        
        # 右侧标题
        self.edit_title = ttk.Label(self.right_frame, text="寄存器详情", font=("Arial", 12, "bold"))
        self.edit_title.pack(fill=tk.X, pady=5)
        
        # 寄存器详情编辑区域
        self.edit_frame = ttk.LabelFrame(self.right_frame, text="寄存器属性")
        self.edit_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 寄存器属性表单
        form_frame = ttk.Frame(self.edit_frame)
        form_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        # 寄存器名称
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="寄存器名称:", width=15).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 寄存器地址
        addr_frame = ttk.Frame(form_frame)
        addr_frame.pack(fill=tk.X, pady=5)
        ttk.Label(addr_frame, text="地址(hex):", width=15).pack(side=tk.LEFT)
        self.addr_var = tk.StringVar()
        ttk.Entry(addr_frame, textvariable=self.addr_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 寄存器宽度
        width_frame = ttk.Frame(form_frame)
        width_frame.pack(fill=tk.X, pady=5)
        ttk.Label(width_frame, text="宽度(bits):", width=15).pack(side=tk.LEFT)
        self.width_var = tk.StringVar()
        width_combobox = ttk.Combobox(width_frame, textvariable=self.width_var)
        width_combobox['values'] = ["8", "16", "32", "64"]
        width_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 访问模式
        access_frame = ttk.Frame(form_frame)
        access_frame.pack(fill=tk.X, pady=5)
        ttk.Label(access_frame, text="访问模式:", width=15).pack(side=tk.LEFT)
        self.access_var = tk.StringVar()
        access_combobox = ttk.Combobox(access_frame, textvariable=self.access_var)
        access_combobox['values'] = ["RO", "RW", "WO", "RW1C", "RW1S", "RC", "RS"]
        access_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 默认值
        default_frame = ttk.Frame(form_frame)
        default_frame.pack(fill=tk.X, pady=5)
        ttk.Label(default_frame, text="默认值(hex):", width=15).pack(side=tk.LEFT)
        self.default_var = tk.StringVar()
        ttk.Entry(default_frame, textvariable=self.default_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 描述
        desc_frame = ttk.Frame(form_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="描述:", width=15).pack(side=tk.LEFT)
        self.desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.desc_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 保存按钮
        save_frame = ttk.Frame(form_frame)
        save_frame.pack(fill=tk.X, pady=10)
        ttk.Button(save_frame, text="保存寄存器", command=self.save_register).pack(side=tk.RIGHT)
        
        # 位域编辑区域
        bitfield_frame = ttk.LabelFrame(self.right_frame, text="位域定义")
        bitfield_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 位域表格
        table_frame = ttk.Frame(bitfield_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建表格
        columns = ("位名称", "位范围", "访问", "描述")
        self.bitfield_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # 设置列标题
        for col in columns:
            self.bitfield_tree.heading(col, text=col)
            self.bitfield_tree.column(col, width=100)
        
        # 添加滚动条
        tree_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.bitfield_tree.yview)
        self.bitfield_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.bitfield_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 位域操作按钮
        bit_btn_frame = ttk.Frame(bitfield_frame)
        bit_btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(bit_btn_frame, text="添加位域", command=self.add_bitfield).pack(side=tk.LEFT, padx=5)
        ttk.Button(bit_btn_frame, text="编辑位域", command=self.edit_bitfield).pack(side=tk.LEFT, padx=5)
        ttk.Button(bit_btn_frame, text="删除位域", command=self.delete_bitfield).pack(side=tk.LEFT, padx=5)
        
        # 绑定事件
        self.register_listbox.bind('<<ListboxSelect>>', self.on_register_select)
        self.bitfield_tree.bind('<Double-1>', lambda e: self.edit_bitfield())
        
        # 初始化界面状态
        self.update_ui()
    
    def update_ui(self):
        """更新界面状态"""
        # 禁用编辑区域
        if not self.current_register:
            for child in self.edit_frame.winfo_children():
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Button)):
                        widget.configure(state="disabled")
            
            for child in self.bitfield_tree.winfo_children():
                child.configure(state="disabled")
        else:
            for child in self.edit_frame.winfo_children():
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Button)):
                        widget.configure(state="normal")
            
            for child in self.bitfield_tree.winfo_children():
                child.configure(state="normal")
    
    def set_registers(self, registers):
        """设置寄存器列表
        
        Args:
            registers: 寄存器数据列表
        """
        self.registers = registers
        self.refresh_register_list()
        self.current_register = None
        self.clear_form()
        self.update_ui()
    
    def refresh_register_list(self):
        """刷新寄存器列表"""
        self.register_listbox.delete(0, tk.END)
        for reg in self.registers:
            name = reg.get('name', '未命名')
            addr = reg.get('address', '0x0')
            self.register_listbox.insert(tk.END, f"{name} ({addr})")
    
    def clear_form(self):
        """清空表单"""
        self.name_var.set("")
        self.addr_var.set("")
        self.width_var.set("32")
        self.access_var.set("RW")
        self.default_var.set("0x0")
        self.desc_var.set("")
        
        # 清空位域表格
        for item in self.bitfield_tree.get_children():
            self.bitfield_tree.delete(item)
    
    def load_register_data(self, register):
        """加载寄存器数据到表单
        
        Args:
            register: 寄存器数据字典
        """
        self.name_var.set(register.get('name', ''))
        self.addr_var.set(register.get('address', '0x0'))
        self.width_var.set(str(register.get('width', 32)))
        self.access_var.set(register.get('access', 'RW'))
        self.default_var.set(register.get('default', '0x0'))
        self.desc_var.set(register.get('description', ''))
        
        # 加载位域数据
        for item in self.bitfield_tree.get_children():
            self.bitfield_tree.delete(item)
        
        bitfields = register.get('bitfields', [])
        for bf in bitfields:
            name = bf.get('name', '')
            bits = bf.get('bits', '0')
            access = bf.get('access', 'RW')
            desc = bf.get('description', '')
            
            self.bitfield_tree.insert('', tk.END, values=(name, bits, access, desc))
    
    def on_register_select(self, event):
        """寄存器选择事件处理
        
        Args:
            event: 事件对象
        """
        selection = self.register_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.registers):
                self.current_register = self.registers[index]
                self.load_register_data(self.current_register)
                self.update_ui()
                
                # 更新标题
                name = self.current_register.get('name', '未命名')
                self.edit_title.configure(text=f"编辑寄存器: {name}")
    
    def add_register(self):
        """添加新寄存器"""
        self.current_register = {
            'name': '新寄存器',
            'address': '0x0',
            'width': 32,
            'access': 'RW',
            'default': '0x0',
            'description': '',
            'bitfields': []
        }
        
        self.registers.append(self.current_register)
        self.refresh_register_list()
        
        # 选中新添加的寄存器
        last_index = len(self.registers) - 1
        self.register_listbox.selection_clear(0, tk.END)
        self.register_listbox.selection_set(last_index)
        self.register_listbox.see(last_index)
        self.on_register_select(None)
        
        # 触发回调
        if self.update_callback:
            self.update_callback(self.registers)
    
    def delete_register(self):
        """删除选中的寄存器"""
        selection = self.register_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个寄存器")
            return
            
        index = selection[0]
        if messagebox.askyesno("确认", "确定要删除选中的寄存器吗？"):
            del self.registers[index]
            self.refresh_register_list()
            
            # 清空表单
            self.current_register = None
            self.clear_form()
            self.update_ui()
            
            # 触发回调
            if self.update_callback:
                self.update_callback(self.registers)
    
    def move_register(self, direction):
        """移动寄存器位置
        
        Args:
            direction: 移动方向，-1表示上移，1表示下移
        """
        selection = self.register_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个寄存器")
            return
            
        index = selection[0]
        new_index = index + direction
        
        # 检查边界
        if new_index < 0 or new_index >= len(self.registers):
            return
            
        # 交换位置
        self.registers[index], self.registers[new_index] = self.registers[new_index], self.registers[index]
        self.refresh_register_list()
        
        # 选中移动后的位置
        self.register_listbox.selection_clear(0, tk.END)
        self.register_listbox.selection_set(new_index)
        self.register_listbox.see(new_index)
        
        # 触发回调
        if self.update_callback:
            self.update_callback(self.registers)
    
    def save_register(self):
        """保存寄存器数据"""
        if not self.current_register:
            return
            
        # 获取表单数据
        name = self.name_var.get()
        if not name:
            messagebox.showwarning("警告", "寄存器名称不能为空")
            return
            
        addr = self.addr_var.get()
        if not addr:
            messagebox.showwarning("警告", "寄存器地址不能为空")
            return
        
        try:
            width = int(self.width_var.get())
        except ValueError:
            messagebox.showwarning("警告", "寄存器宽度必须是数字")
            return
            
        access = self.access_var.get()
        default = self.default_var.get()
        desc = self.desc_var.get()
        
        # 获取位域数据
        bitfields = []
        for item in self.bitfield_tree.get_children():
            values = self.bitfield_tree.item(item, 'values')
            bitfields.append({
                'name': values[0],
                'bits': values[1],
                'access': values[2],
                'description': values[3]
            })
        
        # 更新寄存器数据
        self.current_register.update({
            'name': name,
            'address': addr,
            'width': width,
            'access': access,
            'default': default,
            'description': desc,
            'bitfields': bitfields
        })
        
        # 刷新寄存器列表
        self.refresh_register_list()
        
        # 触发回调
        if self.update_callback:
            self.update_callback(self.registers)
        
        messagebox.showinfo("成功", "寄存器保存成功")
    
    def add_bitfield(self):
        """添加位域"""
        if not self.current_register:
            messagebox.showwarning("警告", "请先选择一个寄存器")
            return
            
        # 创建位域编辑对话框
        dialog = BitfieldDialog(self, "添加位域")
        if dialog.result:
            name, bits, access, desc = dialog.result
            self.bitfield_tree.insert('', tk.END, values=(name, bits, access, desc))
    
    def edit_bitfield(self):
        """编辑位域"""
        selection = self.bitfield_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个位域")
            return
            
        item = selection[0]
        values = self.bitfield_tree.item(item, 'values')
        
        # 创建位域编辑对话框
        dialog = BitfieldDialog(self, "编辑位域", values)
        if dialog.result:
            name, bits, access, desc = dialog.result
            self.bitfield_tree.item(item, values=(name, bits, access, desc))
    
    def delete_bitfield(self):
        """删除位域"""
        selection = self.bitfield_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个位域")
            return
            
        if messagebox.askyesno("确认", "确定要删除选中的位域吗？"):
            for item in selection:
                self.bitfield_tree.delete(item)


class BitfieldDialog:
    """位域编辑对话框"""
    
    def __init__(self, parent, title, values=None):
        """初始化对话框
        
        Args:
            parent: 父级窗口
            title: 对话框标题
            values: 位域初始值，用于编辑模式
        """
        self.result = None
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
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
            values: 位域初始值
        """
        form_frame = ttk.Frame(self.dialog, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 位名称
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="位名称:", width=10).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 位范围
        bits_frame = ttk.Frame(form_frame)
        bits_frame.pack(fill=tk.X, pady=5)
        ttk.Label(bits_frame, text="位范围:", width=10).pack(side=tk.LEFT)
        self.bits_var = tk.StringVar()
        ttk.Entry(bits_frame, textvariable=self.bits_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(bits_frame, text="例如: 7:0 或 15").pack(side=tk.LEFT, padx=5)
        
        # 访问模式
        access_frame = ttk.Frame(form_frame)
        access_frame.pack(fill=tk.X, pady=5)
        ttk.Label(access_frame, text="访问:", width=10).pack(side=tk.LEFT)
        self.access_var = tk.StringVar()
        access_combobox = ttk.Combobox(access_frame, textvariable=self.access_var)
        access_combobox['values'] = ["RO", "RW", "WO", "RW1C", "RW1S", "RC", "RS"]
        access_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 描述
        desc_frame = ttk.Frame(form_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="描述:", width=10).pack(side=tk.LEFT)
        self.desc_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.desc_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 设置初始值
        if values:
            self.name_var.set(values[0])
            self.bits_var.set(values[1])
            self.access_var.set(values[2])
            self.desc_var.set(values[3])
        else:
            self.access_var.set("RW")
        
        # 按钮
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="确定", command=self.on_ok).pack(side=tk.RIGHT, padx=5)
    
    def on_ok(self):
        """确定按钮事件处理"""
        name = self.name_var.get()
        bits = self.bits_var.get()
        access = self.access_var.get()
        desc = self.desc_var.get()
        
        if not name:
            messagebox.showwarning("警告", "位名称不能为空", parent=self.dialog)
            return
            
        if not bits:
            messagebox.showwarning("警告", "位范围不能为空", parent=self.dialog)
            return
        
        self.result = (name, bits, access, desc)
        self.dialog.destroy()


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.geometry("800x600")
    
    def on_registers_updated(regs):
        print(f"寄存器已更新: {len(regs)}个")
    
    editor = RegisterEditor(root, on_registers_updated)
    editor.pack(fill=tk.BOTH, expand=True)
    
    # 添加测试数据
    test_registers = [
        {
            'name': 'STATUS',
            'address': '0x00',
            'width': 32,
            'access': 'RW',
            'default': '0x0',
            'description': '状态寄存器',
            'bitfields': [
                {'name': 'READY', 'bits': '0', 'access': 'RO', 'description': '就绪状态位'},
                {'name': 'ERROR', 'bits': '1', 'access': 'RW1C', 'description': '错误状态位'},
                {'name': 'BUSY', 'bits': '2', 'access': 'RO', 'description': '忙状态位'},
                {'name': 'RESERVED', 'bits': '31:3', 'access': 'RO', 'description': '保留位'}
            ]
        },
        {
            'name': 'CONTROL',
            'address': '0x04',
            'width': 32,
            'access': 'RW',
            'default': '0x0',
            'description': '控制寄存器',
            'bitfields': [
                {'name': 'ENABLE', 'bits': '0', 'access': 'RW', 'description': '使能位'},
                {'name': 'RESET', 'bits': '1', 'access': 'RW', 'description': '复位位'},
                {'name': 'INT_EN', 'bits': '2', 'access': 'RW', 'description': '中断使能位'},
                {'name': 'RESERVED', 'bits': '31:3', 'access': 'RO', 'description': '保留位'}
            ]
        }
    ]
    
    editor.set_registers(test_registers)
    
    root.mainloop() 