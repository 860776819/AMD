#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行为模拟模块
负责生成PCIe设备的行为模拟代码
"""

import os
import re

class BehaviorGenerator:
    """设备行为模拟代码生成类"""
    
    def __init__(self):
        """初始化行为模拟模块"""
        self.template = self._load_behavior_template()
        self.state_machine_template = self._load_state_machine_template()
        
    def _load_behavior_template(self):
        """加载行为模拟模板"""
        return """
// 设备行为模拟模块
// 自动生成的设备行为模拟代码: {device_name}
// 生成时间: {timestamp}

module {module_name} (
    input               clk,
    input               rst,
    
    // 控制接口
    input      [31:0]   control_reg,
    output reg [31:0]   status_reg,
    
    // 中断接口
    output reg [31:0]   int_status,
    input      [31:0]   int_enable,
    
    // 设备特定接口
    {device_interfaces}
);

    // ==========================================================================
    // 状态定义
    // ==========================================================================
    
    {state_definitions}
    
    // 当前设备状态
    reg [{state_bits}-1:0] device_state;
    
    // 计数器和定时器
    reg [31:0] operation_counter;
    reg [31:0] timeout_counter;
    
    // 设备特定变量
    {device_variables}
    
    // ==========================================================================
    // 状态转换和控制逻辑
    // ==========================================================================
    
    {state_machine}
    
    // ==========================================================================
    // 中断生成逻辑
    // ==========================================================================
    
    always @(posedge clk) begin
        if (rst) begin
            int_status <= 32'h0;
        end else begin
            // 自动清除已处理的中断状态位
            int_status <= int_status & ~(int_status & ~int_enable);
            
            // 在特定状态或条件下生成中断
            {interrupt_logic}
        end
    end
    
    // ==========================================================================
    // 时序特性模拟
    // ==========================================================================
    
    {timing_simulation}

endmodule
"""
    
    def _load_state_machine_template(self):
        """加载状态机模板"""
        return """
    always @(posedge clk) begin
        if (rst) begin
            device_state <= STATE_RESET;
            status_reg <= 32'h00000001; // 设备复位状态
            operation_counter <= 32'h0;
            timeout_counter <= 32'h0;
            {reset_logic}
        end else begin
            // 更新计数器
            if (operation_counter > 0)
                operation_counter <= operation_counter - 1;
                
            if (timeout_counter > 0)
                timeout_counter <= timeout_counter - 1;
            
            // 设备状态机
            case (device_state)
                STATE_RESET: begin
                    // 初始化状态
                    if (control_reg[0]) begin  // 设备启用位
                        device_state <= STATE_INIT;
                        status_reg <= 32'h00000002; // 初始化中
                        operation_counter <= 32'd100; // 初始化延迟
                    end
                end
                
                STATE_INIT: begin
                    // 初始化完成后转入空闲状态
                    if (operation_counter == 0) begin
                        device_state <= STATE_IDLE;
                        status_reg <= 32'h00000100; // 设备就绪
                        
                        // 设置初始化完成中断
                        int_status <= int_status | 32'h00000001;
                    end
                end
                
                STATE_IDLE: begin
                    // 等待命令
                    if (control_reg[1]) begin // 开始操作位
                        device_state <= STATE_ACTIVE;
                        status_reg <= 32'h00000200; // 操作中
                        
                        // 设置操作时间基于命令类型
                        case (control_reg[7:4]) // 命令类型字段
                            4'h0: operation_counter <= 32'd10;  // 快速命令
                            4'h1: operation_counter <= 32'd50;  // 中等命令
                            4'h2: operation_counter <= 32'd100; // 长命令
                            default: operation_counter <= 32'd30; // 默认延迟
                        endcase
                    end
                end
                
                STATE_ACTIVE: begin
                    // 执行操作
                    if (operation_counter == 0) begin
                        // 操作完成
                        device_state <= STATE_IDLE;
                        status_reg <= 32'h00000100; // 设备就绪
                        
                        // 设置操作完成中断
                        int_status <= int_status | 32'h00000002;
                    end
                    
                    // 错误检测
                    if (control_reg[8]) begin // 错误注入位
                        device_state <= STATE_ERROR;
                        status_reg <= 32'h00008000; // 错误状态
                        
                        // 设置错误中断
                        int_status <= int_status | 32'h00008000;
                    end
                end
                
                STATE_ERROR: begin
                    // 错误恢复
                    if (control_reg[9]) begin // 错误复位位
                        device_state <= STATE_RESET;
                        status_reg <= 32'h00000001; // 设备复位状态
                    end
                end
                
                {custom_states}
                
                default: begin
                    // 未知状态，回到复位
                    device_state <= STATE_RESET;
                end
            endcase
            
            {custom_behavior}
        end
    end
"""
    
    def generate_behavior_code(self, device_config, output_file):
        """生成设备行为模拟代码"""
        try:
            device_name = device_config.get("name", "自定义设备")
            module_name = self._sanitize_module_name(device_name) + "_behavior"
            device_type = device_config.get("type", "custom")
            
            # 根据设备类型定制不同的行为
            device_interfaces, device_variables, state_definitions, custom_states, custom_behavior, interrupt_logic, timing_simulation, reset_logic = self._generate_type_specific_code(device_type, device_config)
            
            # 计算状态位宽
            num_states = state_definitions.count("localparam")
            state_bits = max(2, (num_states - 1).bit_length())
            
            # 生成状态机代码
            state_machine = self.state_machine_template.format(
                reset_logic=reset_logic,
                custom_states=custom_states,
                custom_behavior=custom_behavior
            )
            
            # 生成最终代码
            code = self.template.format(
                device_name=device_name,
                module_name=module_name,
                timestamp=__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                device_interfaces=device_interfaces,
                state_definitions=state_definitions,
                state_bits=state_bits,
                device_variables=device_variables,
                state_machine=state_machine,
                interrupt_logic=interrupt_logic,
                timing_simulation=timing_simulation
            )
            
            # 写入输出文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            print(f"✅ 设备行为模拟代码已生成: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 生成设备行为模拟代码失败: {str(e)}")
            return False
    
    def _generate_type_specific_code(self, device_type, device_config):
        """根据设备类型生成特定代码部分"""
        # 基本状态定义（所有设备都有）
        state_definitions = """
    // 基本状态
    localparam STATE_RESET  = 0;  // 复位状态
    localparam STATE_INIT   = 1;  // 初始化
    localparam STATE_IDLE   = 2;  // 空闲
    localparam STATE_ACTIVE = 3;  // 活动
    localparam STATE_ERROR  = 4;  // 错误"""
        
        # 默认值
        device_interfaces = "// 无设备特定接口"
        device_variables = "// 无设备特定变量"
        custom_states = "// 无自定义状态"
        custom_behavior = "// 无自定义行为"
        interrupt_logic = "// 无特定中断生成逻辑"
        timing_simulation = "// 无特定时序模拟"
        reset_logic = "// 无特定复位逻辑"
        
        # 根据设备类型生成特定代码
        if device_type == "nic" or device_type == "wifi":
            # 网络适配器特定代码
            device_interfaces = """
    // 网络接口
    input      [7:0]    rx_data,
    input               rx_valid,
    output reg          rx_ready,
    
    output reg [7:0]    tx_data,
    output reg          tx_valid,
    input               tx_ready"""
            
            device_variables = """
    // 网络设备变量
    reg [15:0] packet_length;
    reg [15:0] packet_counter;
    reg [7:0]  rx_buffer[1023:0];
    reg [9:0]  rx_wr_ptr;
    reg [9:0]  rx_rd_ptr;
    reg        rx_overflow;
    reg        packet_available;"""
            
            custom_states = """
                STATE_RX_PACKET: begin
                    // 接收数据包
                    if (packet_counter >= packet_length) begin
                        device_state <= STATE_IDLE;
                        packet_available <= 1'b1;
                        
                        // 设置包接收完成中断
                        int_status <= int_status | 32'h00000004;
                    end
                end
                
                STATE_TX_PACKET: begin
                    // 发送数据包
                    if (packet_counter >= packet_length) begin
                        device_state <= STATE_IDLE;
                        
                        // 设置包发送完成中断
                        int_status <= int_status | 32'h00000008;
                    end
                end"""
            
            custom_behavior = """
            // 网络数据接收逻辑
            if (rx_valid && rx_ready) begin
                if (rx_wr_ptr < 1023) begin
                    rx_buffer[rx_wr_ptr] <= rx_data;
                    rx_wr_ptr <= rx_wr_ptr + 1;
                end else begin
                    rx_overflow <= 1'b1;
                end
            end
            
            // 从STATE_IDLE状态接收数据包触发
            if (device_state == STATE_IDLE && rx_valid) begin
                device_state <= STATE_RX_PACKET;
                rx_ready <= 1'b1;
                packet_counter <= 16'h0001; // 已收到第一个字节
                packet_length <= {control_reg[31:16]}; // 从控制寄存器获取包长度
            end
            
            // 控制寄存器[2]位用于启动数据发送
            if (device_state == STATE_IDLE && control_reg[2]) begin
                device_state <= STATE_TX_PACKET;
                packet_counter <= 16'h0000;
                packet_length <= {control_reg[31:16]}; // 从控制寄存器获取包长度
            end"""
            
            interrupt_logic = """
            // 网络设备中断逻辑
            if (rx_overflow) begin
                // 接收缓冲区溢出中断
                int_status <= int_status | 32'h00010000;
            end
            
            // 链接状态变化中断
            if (control_reg[16] != status_reg[16]) begin
                int_status <= int_status | 32'h00000010;
            end"""
            
            reset_logic = """
            rx_wr_ptr <= 10'h000;
            rx_rd_ptr <= 10'h000;
            rx_overflow <= 1'b0;
            rx_ready <= 1'b0;
            tx_valid <= 1'b0;
            packet_available <= 1'b0;"""
            
        elif device_type == "storage":
            # 存储控制器特定代码
            device_interfaces = """
    // 存储接口
    input      [63:0]   lba_address,
    input      [31:0]   sector_count,
    input               command_start,
    output reg          command_done,
    
    input      [31:0]   write_data,
    input               write_valid,
    output reg          write_ready,
    
    output reg [31:0]   read_data,
    output reg          read_valid,
    input               read_ready"""
            
            device_variables = """
    // 存储设备变量
    reg [31:0] current_sector;
    reg [31:0] remaining_sectors;
    reg [7:0]  storage_command;
    reg        is_read_op;
    reg        is_write_op;
    reg        command_error;"""
            
            # 添加存储特定状态
            state_definitions += """
    
    // 存储特定状态
    localparam STATE_DATA_TRANSFER = 5;  // 数据传输
    localparam STATE_COMMAND_COMPLETE = 6;  // 命令完成"""
            
            custom_states = """
                STATE_DATA_TRANSFER: begin
                    // 数据传输状态
                    if (remaining_sectors == 0 || command_error) begin
                        device_state <= STATE_COMMAND_COMPLETE;
                        command_done <= 1'b1;
                        
                        // 设置命令完成中断
                        int_status <= int_status | (command_error ? 32'h00008000 : 32'h00000002);
                    end
                end
                
                STATE_COMMAND_COMPLETE: begin
                    // 命令完成，回到空闲
                    device_state <= STATE_IDLE;
                    command_done <= 1'b0;
                end"""
            
            custom_behavior = """
            // 存储命令处理
            if (device_state == STATE_IDLE && command_start) begin
                storage_command <= control_reg[7:0];
                is_read_op <= (control_reg[7:0] == 8'h25); // READ_DMA
                is_write_op <= (control_reg[7:0] == 8'h35); // WRITE_DMA
                
                if (control_reg[7:0] == 8'h25 || control_reg[7:0] == 8'h35) begin
                    // 读/写DMA操作
                    device_state <= STATE_DATA_TRANSFER;
                    current_sector <= 32'h0;
                    remaining_sectors <= sector_count;
                    command_error <= 1'b0;
                    
                    if (control_reg[7:0] == 8'h25) begin
                        // 读操作
                        read_valid <= 1'b1;
                    end else begin
                        // 写操作
                        write_ready <= 1'b1;
                    end
                end else begin
                    // 其他命令
                    device_state <= STATE_COMMAND_COMPLETE;
                    command_done <= 1'b1;
                    
                    // 设置命令完成中断
                    int_status <= int_status | 32'h00000002;
                }
            end
            
            // 数据传输处理
            if (device_state == STATE_DATA_TRANSFER) begin
                if (is_read_op && read_ready && read_valid) begin
                    // 读数据传输
                    read_data <= (lba_address + current_sector); // 简化：数据就是地址
                    current_sector <= current_sector + 1;
                    remaining_sectors <= remaining_sectors - 1;
                    
                    if (remaining_sectors == 1) begin
                        read_valid <= 1'b0; // 最后一个扇区
                    end
                end
                
                if (is_write_op && write_valid && write_ready) begin
                    // 写数据传输
                    current_sector <= current_sector + 1;
                    remaining_sectors <= remaining_sectors - 1;
                    
                    if (remaining_sectors == 1) begin
                        write_ready <= 1'b0; // 最后一个扇区
                    end
                end
                
                // 模拟随机错误
                if (control_reg[8] && operation_counter == 10) begin
                    command_error <= 1'b1;
                end
            end"""
            
            interrupt_logic = """
            // 存储设备中断逻辑
            if (command_error) begin
                // 命令错误中断
                int_status <= int_status | 32'h00008000;
            end"""
            
            reset_logic = """
            command_done <= 1'b0;
            read_valid <= 1'b0;
            write_ready <= 1'b0;
            command_error <= 1'b0;
            current_sector <= 32'h0;
            remaining_sectors <= 32'h0;"""
        
        # 添加通用时序模拟
        timing_simulation = """
    // 通用时序模拟 - 使用计数器和随机延迟
    reg [15:0] random_delay;
    reg [31:0] last_command;
    
    always @(posedge clk) begin
        if (rst) begin
            random_delay <= 16'h1234; // 初始种子
            last_command <= 32'h0;
        end else begin
            // 简单的伪随机数生成
            random_delay <= {random_delay[14:0], random_delay[15] ^ random_delay[13] ^ random_delay[12] ^ random_delay[10]};
            
            // 检测命令变化
            if (control_reg != last_command) begin
                last_command <= control_reg;
                
                // 在命令类型基础上添加小的随机延迟
                case (control_reg[7:4]) // 命令类型字段
                    4'h0: operation_counter <= 32'd10 + {26'h0, random_delay[5:0]};  // 快速命令
                    4'h1: operation_counter <= 32'd50 + {26'h0, random_delay[5:0]};  // 中等命令
                    4'h2: operation_counter <= 32'd100 + {26'h0, random_delay[5:0]}; // 长命令
                    default: operation_counter <= 32'd30 + {26'h0, random_delay[5:0]}; // 默认延迟
                endcase
            end
        end
    end"""
        
        return device_interfaces, device_variables, state_definitions, custom_states, custom_behavior, interrupt_logic, timing_simulation, reset_logic
    
    def _sanitize_module_name(self, name):
        """将设备名称转换为有效的模块名"""
        # 移除非字母数字字符，转换为小写
        name = re.sub(r'[^\w]', '_', name).lower()
        # 确保开头是字母
        if name and not name[0].isalpha():
            name = "dev_" + name
        return name 