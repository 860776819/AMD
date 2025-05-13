#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中断处理器模块
负责生成PCIe设备的中断处理代码
"""

import os
import re

class InterruptGenerator:
    """中断处理器生成类"""
    
    def __init__(self):
        """初始化中断处理器模块"""
        self.template = self._load_interrupt_template()
        
    def _load_interrupt_template(self):
        """加载中断处理器模板"""
        return """
// 中断处理器模块
// 自动生成的设备中断处理代码: {device_name}
// 生成时间: {timestamp}

module {module_name} (
    input               clk,
    input               rst,
    
    // 中断控制接口
    input      [31:0]   int_status,      // 中断状态寄存器
    input      [31:0]   int_enable,      // 中断使能寄存器
    output reg          int_active,      // 中断活动标志
    
    // PCIe中断接口
    output reg          cfg_interrupt_assert,    // PCIe中断断言
    input               cfg_interrupt_rdy,       // PCIe中断就绪
    output     [7:0]    cfg_interrupt_di,        // PCIe中断数据
    
    // MSI中断接口
    {msi_signals}
    
    // 设备特定接口
    {device_signals}
);

    // ==========================================================================
    // 中断定义
    // ==========================================================================
    
    // 中断位定义
    {interrupt_definitions}
    
    // 中断状态
    reg [31:0] active_interrupts;   // 当前活动的中断
    reg [31:0] pending_interrupts;  // 等待处理的中断
    
    // 中断控制状态
    reg        int_in_progress;     // 中断处理进行中
    reg [7:0]  int_counter;         // 中断计数器
    
    // ==========================================================================
    // 中断状态检测和处理
    // ==========================================================================
    
    // 检测活动中断
    always @(posedge clk) begin
        if (rst) begin
            active_interrupts <= 32'h0;
            pending_interrupts <= 32'h0;
            int_active <= 1'b0;
        end else begin
            // 检测新的中断
            active_interrupts <= int_status & int_enable;
            
            // 保存未处理的中断
            if (active_interrupts != 0 && !int_in_progress) begin
                pending_interrupts <= active_interrupts;
                int_active <= 1'b1;
            end
            
            // 中断处理完成
            if (int_in_progress && cfg_interrupt_rdy) begin
                int_active <= 1'b0;
                pending_interrupts <= 32'h0;
            end
        end
    end
    
    // ==========================================================================
    // PCIe中断生成逻辑
    // ==========================================================================
    
    {interrupt_generation}
    
    // ==========================================================================
    // 中断类型处理
    // ==========================================================================
    
    // 中断向量路由
    {interrupt_routing}

endmodule
"""
    
    def generate_interrupt_handler(self, device_config, output_file):
        """生成中断处理器代码"""
        try:
            device_name = device_config.get("name", "自定义设备")
            module_name = self._sanitize_module_name(device_name) + "_interrupt_handler"
            device_type = device_config.get("type", "custom")
            
            # 根据设备类型准备不同的中断设置
            msi_signals, device_signals, interrupt_definitions, interrupt_generation, interrupt_routing = self._generate_type_specific_interrupts(device_type, device_config)
            
            # 生成最终代码
            code = self.template.format(
                device_name=device_name,
                module_name=module_name,
                timestamp=__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                msi_signals=msi_signals,
                device_signals=device_signals,
                interrupt_definitions=interrupt_definitions,
                interrupt_generation=interrupt_generation,
                interrupt_routing=interrupt_routing
            )
            
            # 写入输出文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            print(f"✅ 中断处理器代码已生成: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 生成中断处理器代码失败: {str(e)}")
            return False
    
    def _generate_type_specific_interrupts(self, device_type, device_config):
        """根据设备类型生成中断处理代码"""
        # 默认MSI信号
        msi_signals = """// MSI禁用
    output              msi_enable,       // MSI使能状态
    input               msi_vector_width  // MSI向量宽度"""
        
        # 默认设备信号
        device_signals = "// 无设备特定信号"
        
        # 基本中断定义
        interrupt_definitions = """// 基本中断位
    localparam INT_INITIALIZED = 32'h00000001;  // 设备初始化完成
    localparam INT_OPERATION_DONE = 32'h00000002;  // 操作完成
    localparam INT_ERROR = 32'h00008000;  // 错误中断"""
        
        # 基本中断生成逻辑
        interrupt_generation = """
    // 基本中断生成
    always @(posedge clk) begin
        if (rst) begin
            cfg_interrupt_assert <= 1'b0;
            int_in_progress <= 1'b0;
            int_counter <= 8'h0;
        end else begin
            // 检测是否有新的中断需要处理
            if (pending_interrupts != 0 && !int_in_progress && cfg_interrupt_rdy) begin
                cfg_interrupt_assert <= 1'b1;
                int_in_progress <= 1'b1;
                
                // 使用中断计数器来追踪中断
                int_counter <= int_counter + 1;
            end
            
            // 中断已被确认
            if (int_in_progress && cfg_interrupt_rdy) begin
                cfg_interrupt_assert <= 1'b0;
                int_in_progress <= 1'b0;
            end
        end
    end
    
    // 中断数据（用于识别中断源）
    assign cfg_interrupt_di = int_counter;"""
        
        # 基本中断路由
        interrupt_routing = """
    // 基本中断路由
    wire [4:0] interrupt_vector;
    
    // 优先级编码器 - 将最高优先级的中断编码为向量
    assign interrupt_vector = 
        (pending_interrupts & INT_ERROR) ? 5'd16 :
        (pending_interrupts & INT_OPERATION_DONE) ? 5'd1 :
        (pending_interrupts & INT_INITIALIZED) ? 5'd0 : 5'd31;"""
        
        # 根据设备类型修改中断信息
        if device_type == "nic" or device_type == "wifi":
            # 网络设备特定中断
            interrupt_definitions = """// 网络设备中断位
    localparam INT_INITIALIZED = 32'h00000001;      // 设备初始化完成
    localparam INT_OPERATION_DONE = 32'h00000002;   // 操作完成
    localparam INT_RX_PACKET = 32'h00000004;        // 收到数据包
    localparam INT_TX_DONE = 32'h00000008;          // 数据包发送完成
    localparam INT_LINK_CHANGE = 32'h00000010;      // 链接状态变化
    localparam INT_RX_OVERFLOW = 32'h00010000;      // 接收缓冲区溢出
    localparam INT_ERROR = 32'h00008000;            // 错误中断"""
            
            interrupt_routing = """
    // 网络设备中断路由
    wire [4:0] interrupt_vector;
    
    // 优先级编码器 - 将最高优先级的中断编码为向量
    assign interrupt_vector = 
        (pending_interrupts & INT_ERROR) ? 5'd16 :
        (pending_interrupts & INT_RX_OVERFLOW) ? 5'd15 :
        (pending_interrupts & INT_RX_PACKET) ? 5'd2 :
        (pending_interrupts & INT_TX_DONE) ? 5'd3 :
        (pending_interrupts & INT_LINK_CHANGE) ? 5'd4 :
        (pending_interrupts & INT_OPERATION_DONE) ? 5'd1 :
        (pending_interrupts & INT_INITIALIZED) ? 5'd0 : 5'd31;"""
            
            # 网络设备使用MSI中断
            msi_signals = """// MSI信号
    output reg          msi_enable,        // MSI使能状态
    input      [2:0]    msi_vector_width,  // MSI向量宽度
    output reg [63:0]   msi_address,       // MSI地址
    output reg [15:0]   msi_data,          // MSI数据
    output reg          msi_request,       // MSI请求
    input               msi_grant          // MSI授权"""
            
            # 修改中断生成逻辑以支持MSI
            interrupt_generation = """
    // 网络设备中断生成
    reg use_msi;  // 是否使用MSI中断
    
    initial begin
        use_msi = 1'b0;        // 默认不使用MSI
        msi_enable = 1'b0;
        msi_address = 64'h0;
        msi_data = 16'h0;
    end
    
    always @(posedge clk) begin
        if (rst) begin
            cfg_interrupt_assert <= 1'b0;
            msi_request <= 1'b0;
            int_in_progress <= 1'b0;
            int_counter <= 8'h0;
            use_msi <= 1'b0;
        end else begin
            // 检测MSI使能
            if (msi_vector_width > 0)
                use_msi <= 1'b1;
            else
                use_msi <= 1'b0;
                
            // 更新MSI使能状态
            msi_enable <= use_msi;
            
            // 处理中断
            if (pending_interrupts != 0 && !int_in_progress) begin
                if (use_msi) begin
                    // 使用MSI中断
                    if (!msi_request) begin
                        msi_request <= 1'b1;
                        int_in_progress <= 1'b1;
                        
                        // 设置MSI地址和数据
                        msi_address <= 64'hFEE00000; // 默认MSI地址
                        msi_data <= {11'b0, interrupt_vector}; // 使用中断向量作为MSI数据
                    end
                end else begin
                    // 使用传统中断
                    if (cfg_interrupt_rdy && !cfg_interrupt_assert) begin
                        cfg_interrupt_assert <= 1'b1;
                        int_in_progress <= 1'b1;
                        int_counter <= int_counter + 1;
                    end
                end
            end
            
            // 中断确认处理
            if (int_in_progress) begin
                if (use_msi && msi_grant) begin
                    // MSI确认
                    msi_request <= 1'b0;
                    int_in_progress <= 1'b0;
                end else if (!use_msi && cfg_interrupt_rdy && cfg_interrupt_assert) begin
                    // 传统中断确认
                    cfg_interrupt_assert <= 1'b0;
                    int_in_progress <= 1'b0;
                end
            end
        end
    end
    
    // 中断数据（用于传统中断）
    assign cfg_interrupt_di = int_counter;"""
            
        elif device_type == "storage":
            # 存储设备特定中断
            interrupt_definitions = """// 存储设备中断位
    localparam INT_INITIALIZED = 32'h00000001;      // 设备初始化完成
    localparam INT_COMMAND_COMPLETE = 32'h00000002; // 命令完成
    localparam INT_DATA_TRANSFER = 32'h00000004;    // 数据传输相关
    localparam INT_MEDIA_CHANGE = 32'h00000008;     // 介质变化
    localparam INT_BUFFER_READY = 32'h00000010;     // 缓冲区就绪
    localparam INT_BUFFER_FULL = 32'h00000020;      // 缓冲区满
    localparam INT_ERROR = 32'h00008000;            // 错误中断
    localparam INT_MEDIA_ERROR = 32'h00010000;      // 介质错误"""
            
            interrupt_routing = """
    // 存储设备中断路由
    wire [4:0] interrupt_vector;
    
    // 优先级编码器 - 将最高优先级的中断编码为向量
    assign interrupt_vector = 
        (pending_interrupts & INT_ERROR) ? 5'd16 :
        (pending_interrupts & INT_MEDIA_ERROR) ? 5'd15 :
        (pending_interrupts & INT_COMMAND_COMPLETE) ? 5'd1 :
        (pending_interrupts & INT_DATA_TRANSFER) ? 5'd2 :
        (pending_interrupts & INT_MEDIA_CHANGE) ? 5'd3 :
        (pending_interrupts & INT_BUFFER_READY) ? 5'd4 :
        (pending_interrupts & INT_BUFFER_FULL) ? 5'd5 :
        (pending_interrupts & INT_INITIALIZED) ? 5'd0 : 5'd31;"""
            
            # 存储设备也可以使用MSI或MSI-X
            msi_signals = """// MSI/MSI-X信号
    output reg          msi_enable,        // MSI使能状态
    output reg          msix_enable,       // MSI-X使能状态
    input      [2:0]    msi_vector_width,  // MSI向量宽度
    output reg [63:0]   msi_address,       // MSI地址
    output reg [31:0]   msi_data,          // MSI数据
    output reg          msi_request,       // MSI请求
    input               msi_grant          // MSI授权"""
            
            device_signals = """// 存储设备特定信号
    input      [3:0]    command_queue_count,  // 命令队列计数
    input               media_present         // 介质是否存在"""
            
            # 修改中断生成逻辑以支持MSI和MSI-X
            interrupt_generation = """
    // 存储设备中断生成
    reg [1:0] int_mode;  // 中断模式: 0=传统, 1=MSI, 2=MSI-X
    
    initial begin
        int_mode = 2'b00;     // 默认使用传统中断
        msi_enable = 1'b0;
        msix_enable = 1'b0;
        msi_address = 64'h0;
        msi_data = 32'h0;
    end
    
    always @(posedge clk) begin
        if (rst) begin
            cfg_interrupt_assert <= 1'b0;
            msi_request <= 1'b0;
            int_in_progress <= 1'b0;
            int_counter <= 8'h0;
            int_mode <= 2'b00;
        end else begin
            // 检测中断模式
            if (msix_enable)
                int_mode <= 2'b10;      // MSI-X
            else if (msi_vector_width > 0)
                int_mode <= 2'b01;      // MSI
            else
                int_mode <= 2'b00;      // 传统中断
                
            // 更新中断模式状态
            msi_enable <= (int_mode == 2'b01);
            msix_enable <= (int_mode == 2'b10);
            
            // 处理中断
            if (pending_interrupts != 0 && !int_in_progress) begin
                case (int_mode)
                    2'b01, 2'b10: begin
                        // MSI或MSI-X中断
                        if (!msi_request) begin
                            msi_request <= 1'b1;
                            int_in_progress <= 1'b1;
                            
                            // 设置MSI地址和数据 - 在实际系统中这些应该从配置空间获取
                            if (int_mode == 2'b01) begin
                                // MSI模式
                                msi_address <= 64'hFEE00000; // 默认MSI地址
                                msi_data <= {27'b0, interrupt_vector}; // 使用中断向量作为MSI数据
                            end else begin
                                // MSI-X模式 - 通常使用表格寻址
                                case (interrupt_vector)
                                    5'd0:  begin msi_address <= 64'hFEE00000; msi_data <= 32'h00000001; end
                                    5'd1:  begin msi_address <= 64'hFEE00000; msi_data <= 32'h00000002; end
                                    5'd2:  begin msi_address <= 64'hFEE00000; msi_data <= 32'h00000004; end
                                    5'd3:  begin msi_address <= 64'hFEE00000; msi_data <= 32'h00000008; end
                                    5'd15: begin msi_address <= 64'hFEE00000; msi_data <= 32'h00008000; end
                                    5'd16: begin msi_address <= 64'hFEE00000; msi_data <= 32'h00010000; end
                                    default: begin msi_address <= 64'hFEE00000; msi_data <= 32'h80000000; end
                                endcase
                            end
                        end
                    end
                    
                    default: begin
                        // 传统中断
                        if (cfg_interrupt_rdy && !cfg_interrupt_assert) begin
                            cfg_interrupt_assert <= 1'b1;
                            int_in_progress <= 1'b1;
                            int_counter <= int_counter + 1;
                        end
                    end
                endcase
            end
            
            // 中断确认处理
            if (int_in_progress) begin
                if ((int_mode == 2'b01 || int_mode == 2'b10) && msi_grant) begin
                    // MSI/MSI-X确认
                    msi_request <= 1'b0;
                    int_in_progress <= 1'b0;
                end else if (int_mode == 2'b00 && cfg_interrupt_rdy && cfg_interrupt_assert) begin
                    // 传统中断确认
                    cfg_interrupt_assert <= 1'b0;
                    int_in_progress <= 1'b0;
                end
            end
            
            // 介质变化检测
            if (media_present != status_reg[24]) begin
                // 介质状态变化中断
                int_status <= int_status | INT_MEDIA_CHANGE;
            end
            
            // 命令队列状态变化
            if (command_queue_count == 4'hF) begin
                // 命令队列满中断
                int_status <= int_status | INT_BUFFER_FULL;
            end
        end
    end
    
    // 中断数据（用于传统中断）
    assign cfg_interrupt_di = int_counter;"""
            
        # 对于简单的设备，使用默认中断实现
        
        return msi_signals, device_signals, interrupt_definitions, interrupt_generation, interrupt_routing
    
    def _sanitize_module_name(self, name):
        """将设备名称转换为有效的模块名"""
        # 移除非字母数字字符，转换为小写
        name = re.sub(r'[^\w]', '_', name).lower()
        # 确保开头是字母
        if name and not name[0].isalpha():
            name = "dev_" + name
        return name 