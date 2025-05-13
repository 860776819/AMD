#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BAR空间生成模块
负责生成PCIe设备的BAR寄存器实现
"""

import os
import re

class BARGenerator:
    """BAR空间控制器生成类"""
    
    def __init__(self):
        """初始化BAR空间生成模块"""
        self.templates = {
            "bar_controller": self._load_bar_controller_template(),
            "read_handler": self._load_read_handler_template(),
            "write_handler": self._load_write_handler_template()
        }
    
    def _load_bar_controller_template(self):
        """加载BAR控制器模板"""
        return """
// BAR空间控制器模块
// 自动生成的设备BAR控制器: {device_name}
// 生成时间: {timestamp}

module {module_name} #(
    parameter [31:0] PARAM_BASE_ADDRESS = 32'h00000000,
    parameter        PARAM_ENABLE_MMIO = 1'b1
)(
    input               clk,
    input               rst,
    
    // 地址和数据接口
    input      [31:0]   drd_addr,
    input               drd_valid,
    output reg [31:0]   rd_rsp_data,
    output reg          rd_rsp_valid,
    
    input      [31:0]   dwr_addr,
    input      [3:0]    dwr_be,
    input      [31:0]   dwr_data,
    input               dwr_valid,
    
    // 其他控制信号
    input      [31:0]   base_address_register,
    
    // 中断控制接口
    output reg          interrupt_assert,
    input               interrupt_ack
);

    // ==========================================================================
    // 寄存器定义
    // ==========================================================================
    
    // 状态寄存器
    reg [31:0] status_reg;
    
    // 控制寄存器
    reg [31:0] control_reg;
    
    // 中断控制
    reg [31:0] int_status;
    reg [31:0] int_enable;
    
    // 版本信息
    localparam VERSION_INFO = 32'h{version_info};
    
    // 设备特有寄存器
    {device_registers}
    
    // ==========================================================================
    // 中断控制逻辑
    // ==========================================================================
    
    reg int_pending;
    
    always @(posedge clk) begin
        if (rst) begin
            int_pending <= 1'b0;
            interrupt_assert <= 1'b0;
        end else begin
            // 检查是否有中断条件
            if ((int_status & int_enable) != 0 && !int_pending) begin
                int_pending <= 1'b1;
                interrupt_assert <= 1'b1;
            end
            
            // 中断确认
            if (interrupt_ack) begin
                interrupt_assert <= 1'b0;
            end
            
            // 中断清除
            if (int_pending && (int_status & int_enable) == 0) begin
                int_pending <= 1'b0;
            end
        end
    end
    
    // ==========================================================================
    // 读操作处理
    // ==========================================================================
    
    always @(posedge clk) begin
        if (rst) begin
            rd_rsp_valid <= 1'b0;
            rd_rsp_data <= 32'h0;
        end else begin
            rd_rsp_valid <= drd_valid;
            
            if (drd_valid) begin
                // 计算寄存器地址偏移
                reg_offset = drd_addr - base_address_register;
                
                {read_handler}
                
                else begin
                    // 未知寄存器返回默认值
                    rd_rsp_data <= 32'hDEADBEEF;
                end
            end
        end
    end
    
    // ==========================================================================
    // 写操作处理
    // ==========================================================================
    
    always @(posedge clk) begin
        if (rst) begin
            // 寄存器复位值
            status_reg <= 32'h00000000;
            control_reg <= 32'h00000000;
            int_status <= 32'h00000000;
            int_enable <= 32'h00000000;
            {reset_values}
        end else if (dwr_valid) begin
            // 计算寄存器地址偏移
            reg_offset = dwr_addr - base_address_register;
            
            {write_handler}
        end
    end

endmodule
"""
    
    def _load_read_handler_template(self):
        """加载读处理程序模板"""
        return """
                // 读操作处理
                if (reg_offset == 32'h{offset}) begin
                    // {name}
                    rd_rsp_data <= {read_value};
                end"""
    
    def _load_write_handler_template(self):
        """加载写处理程序模板"""
        return """
            // 写操作处理 - {name}
            if (reg_offset == 32'h{offset}) begin
                {write_action}
            end"""
    
    def _get_access_type_handler(self, register, is_read=True):
        """根据寄存器访问类型生成处理代码"""
        access_type = register.get("access", "RW").upper()
        reg_name = register.get("var_name", "custom_reg")
        
        if is_read:
            # 读取处理
            if "RO" in access_type:
                # 只读寄存器
                if "reg" in register.get("value", "").lower():
                    # 使用现有变量
                    return register.get("value", reg_name)
                else:
                    # 使用常量值
                    return register.get("value", "32'h00000000")
            elif "RC" in access_type:
                # 读清除寄存器
                result = f"{reg_name}"
                if not register.get("no_auto_clear", False):
                    result += f";\n                    {reg_name} <= 32'h0"
                return result
            else:
                # 可读写寄存器
                return reg_name
        else:
            # 写入处理
            if "WO" in access_type or "RW" in access_type:
                # 只写或读写寄存器
                return f"{reg_name} <= dwr_data"
            elif "W1C" in access_type:
                # 写1清除寄存器
                return f"{reg_name} <= {reg_name} & ~dwr_data"
            elif "W1S" in access_type:
                # 写1置位寄存器
                return f"{reg_name} <= {reg_name} | dwr_data"
            else:
                # 写入无效（只读寄存器）
                return "// 只读寄存器，忽略写入操作"
    
    def generate_bar_controller(self, device_config, output_file):
        """生成BAR控制器代码"""
        try:
            # 准备设备特有寄存器定义
            registers = device_config.get("key_registers", [])
            
            device_name = device_config.get("name", "自定义设备")
            module_name = self._sanitize_module_name(device_name)
            
            # 处理设备寄存器
            device_registers = []
            read_handlers = []
            write_handlers = []
            reset_values = []
            
            for i, reg in enumerate(registers):
                # 如果没有指定变量名，创建一个
                if "var_name" not in reg:
                    reg["var_name"] = f"custom_reg_{i}"
                
                # 添加寄存器定义
                if "RO" not in reg.get("access", "RW").upper() or "value" not in reg or "reg" in reg["value"].lower():
                    device_registers.append(f"reg [31:0] {reg['var_name']};")
                
                # 读处理程序
                read_value = self._get_access_type_handler(reg, is_read=True)
                read_handler = self.templates["read_handler"].format(
                    offset=reg["addr"].replace("0x", ""),
                    name=reg.get("name", f"寄存器 {reg['addr']}"),
                    read_value=read_value
                )
                read_handlers.append(read_handler)
                
                # 写处理程序
                access_type = reg.get("access", "RW").upper()
                if "RO" not in access_type:
                    write_action = self._get_access_type_handler(reg, is_read=False)
                    write_handler = self.templates["write_handler"].format(
                        offset=reg["addr"].replace("0x", ""),
                        name=reg.get("name", f"寄存器 {reg['addr']}"),
                        write_action=write_action
                    )
                    write_handlers.append(write_handler)
                
                # 复位值
                if "var_name" in reg and "reset_value" in reg:
                    reset_values.append(f"{reg['var_name']} <= {reg['reset_value']};")
                elif "var_name" in reg:
                    reset_values.append(f"{reg['var_name']} <= 32'h00000000;")
            
            # 版本信息，使用设备ID+供应商ID
            version_info = f"{device_config.get('device_id', 'FFFF')}{device_config.get('vendor_id', 'FFFF')}"
            
            # 格式化最终模板
            code = self.templates["bar_controller"].format(
                device_name=device_name,
                module_name=module_name + "_bar_controller",
                timestamp=__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                version_info=version_info,
                device_registers="\n    ".join(device_registers),
                read_handler="else".join(read_handlers),
                write_handler="\n".join(write_handlers),
                reset_values="\n            ".join(reset_values)
            )
            
            # 写入输出文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            print(f"✅ BAR控制器代码已生成: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 生成BAR控制器代码失败: {str(e)}")
            return False
    
    def _sanitize_module_name(self, name):
        """将设备名称转换为有效的模块名"""
        # 移除非字母数字字符，转换为小写
        name = re.sub(r'[^\w]', '_', name).lower()
        # 确保开头是字母
        if name and not name[0].isalpha():
            name = "dev_" + name
        return name 