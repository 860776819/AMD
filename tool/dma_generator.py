#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMA控制器模块
负责生成PCIe设备的DMA控制器代码
"""

import os
import re

class DMAGenerator:
    """DMA控制器生成类"""
    
    def __init__(self):
        """初始化DMA控制器模块"""
        self.template = self._load_dma_template()
        
    def _load_dma_template(self):
        """加载DMA控制器模板"""
        return """
// DMA控制器模块
// 自动生成的设备DMA控制器代码: {device_name}
// 生成时间: {timestamp}

module {module_name} (
    input               clk,
    input               rst,
    
    // 控制接口
    input      [31:0]   dma_control_reg,      // DMA控制寄存器
    output reg [31:0]   dma_status_reg,       // DMA状态寄存器
    
    // 地址接口
    input      [63:0]   dma_src_addr,         // DMA源地址
    input      [63:0]   dma_dst_addr,         // DMA目标地址
    input      [31:0]   dma_length,           // DMA传输长度
    
    // 中断接口
    output reg          dma_interrupt,        // DMA中断信号
    
    // TLP接口
    output reg          tlp_req,              // TLP请求信号
    input               tlp_ack,              // TLP确认信号
    output reg [7:0]    tlp_fmt_type,         // TLP格式和类型
    output reg [63:0]   tlp_address,          // TLP地址
    output reg [9:0]    tlp_length,           // TLP长度 (DW)
    output reg          tlp_is_wr,            // TLP是否为写操作
    output reg [3:0]    tlp_first_be,         // TLP首DWORD字节使能
    output reg [3:0]    tlp_last_be,          // TLP尾DWORD字节使能
    
    // 数据接口
    input      [127:0]  read_data,            // 读取数据
    input               read_data_valid,      // 读取数据有效
    output reg [127:0]  write_data,           // 写入数据
    output reg          write_data_valid,     // 写入数据有效
    
    // 设备特定接口
    {device_specific_interface}
);

    // ==========================================================================
    // 状态定义
    // ==========================================================================
    
    localparam DMA_IDLE     = 4'h0;           // 空闲状态
    localparam DMA_READ_REQ = 4'h1;           // 发起读请求
    localparam DMA_READ     = 4'h2;           // 读取数据
    localparam DMA_WRITE_REQ = 4'h3;          // 发起写请求
    localparam DMA_WRITE    = 4'h4;           // 写入数据
    localparam DMA_WAIT     = 4'h5;           // 等待完成
    localparam DMA_COMPLETE = 4'h6;           // 传输完成
    localparam DMA_ERROR    = 4'h7;           // 错误状态
    
    reg [3:0] dma_state;                      // DMA当前状态
    reg [31:0] bytes_remaining;               // 剩余字节数
    reg [63:0] current_src_addr;              // 当前源地址
    reg [63:0] current_dst_addr;              // 当前目标地址
    
    // TLP设置
    localparam TLP_MEM_READ32  = 8'h00;       // 内存读 - 32位地址
    localparam TLP_MEM_READ64  = 8'h20;       // 内存读 - 64位地址
    localparam TLP_MEM_WRITE32 = 8'h40;       // 内存写 - 32位地址
    localparam TLP_MEM_WRITE64 = 8'h60;       // 内存写 - 64位地址
    
    reg [9:0] current_tlp_length;             // 当前TLP长度(DW)
    reg [31:0] tlp_count;                     // TLP计数器
    
    // 数据缓冲区
    reg [127:0] data_buffer [0:{buffer_depth}-1];
    reg [9:0] buf_wr_ptr;                     // 缓冲区写指针
    reg [9:0] buf_rd_ptr;                     // 缓冲区读指针
    
    // ==========================================================================
    // DMA控制器状态机
    // ==========================================================================
    
    always @(posedge clk) begin
        if (rst) begin
            dma_state <= DMA_IDLE;
            dma_status_reg <= 32'h00000000;   // 清除状态
            dma_interrupt <= 1'b0;
            bytes_remaining <= 32'h0;
            tlp_req <= 1'b0;
            tlp_count <= 32'h0;
            buf_wr_ptr <= 10'h0;
            buf_rd_ptr <= 10'h0;
            write_data_valid <= 1'b0;
        end
        else begin
            // 默认值
            tlp_req <= 1'b0;
            write_data_valid <= 1'b0;
            
            case (dma_state)
                DMA_IDLE: begin
                    if (dma_control_reg[0]) begin  // 启动位
                        // 初始化DMA传输
                        current_src_addr <= dma_src_addr;
                        current_dst_addr <= dma_dst_addr;
                        bytes_remaining <= dma_length;
                        
                        // 更新状态
                        dma_state <= DMA_READ_REQ;
                        dma_status_reg <= 32'h00000001; // 传输中
                        tlp_count <= 32'h0;
                        buf_wr_ptr <= 10'h0;
                        buf_rd_ptr <= 10'h0;
                    end
                end
                
                DMA_READ_REQ: begin
                    // 计算本次传输长度
                    if (bytes_remaining >= {max_payload}) begin
                        current_tlp_length <= {max_payload_dw}; // 最大负载(DW)
                    end
                    else begin
                        // 计算剩余字节数的DW数，向上取整
                        current_tlp_length <= (bytes_remaining + 3) >> 2;
                    end
                    
                    // 发起内存读请求
                    tlp_req <= 1'b1;
                    tlp_is_wr <= 1'b0;  // 读操作
                    
                    // 设置TLP格式和类型
                    if (current_src_addr[63:32] == 32'h0) begin
                        tlp_fmt_type <= TLP_MEM_READ32;
                        tlp_address <= {{32{1'b0}}, current_src_addr[31:0]};
                    end
                    else begin
                        tlp_fmt_type <= TLP_MEM_READ64;
                        tlp_address <= current_src_addr;
                    end
                    
                    // 设置TLP长度和字节使能
                    tlp_length <= current_tlp_length;
                    tlp_first_be <= 4'hF; // 通常是所有字节都使能
                    tlp_last_be <= 4'hF;  // 可能需要根据长度调整
                    
                    // 移动到下一个状态
                    dma_state <= DMA_READ;
                end
                
                DMA_READ: begin
                    // 等待TLP确认
                    if (tlp_ack) begin
                        tlp_req <= 1'b0;
                    end
                    
                    // 接收数据
                    if (read_data_valid) begin
                        // 存储到缓冲区
                        data_buffer[buf_wr_ptr] <= read_data;
                        buf_wr_ptr <= buf_wr_ptr + 1;
                        
                        // 检查是否收到足够的数据
                        if (buf_wr_ptr == (current_tlp_length + 1) / 2 - 1) begin
                            // 读取完成，开始写入
                            dma_state <= DMA_WRITE_REQ;
                            buf_rd_ptr <= 10'h0;
                        end
                    end
                end
                
                DMA_WRITE_REQ: begin
                    // 发起内存写请求
                    tlp_req <= 1'b1;
                    tlp_is_wr <= 1'b1;  // 写操作
                    
                    // 设置TLP格式和类型
                    if (current_dst_addr[63:32] == 32'h0) begin
                        tlp_fmt_type <= TLP_MEM_WRITE32;
                        tlp_address <= {{32{1'b0}}, current_dst_addr[31:0]};
                    end
                    else begin
                        tlp_fmt_type <= TLP_MEM_WRITE64;
                        tlp_address <= current_dst_addr;
                    end
                    
                    // 使用与读相同的长度和字节使能
                    tlp_length <= current_tlp_length;
                    tlp_first_be <= 4'hF;
                    tlp_last_be <= 4'hF;
                    
                    // 移动到下一个状态
                    dma_state <= DMA_WRITE;
                end
                
                DMA_WRITE: begin
                    // 等待TLP确认
                    if (tlp_ack) begin
                        tlp_req <= 1'b0;
                    end
                    
                    // 发送数据
                    if (!tlp_req || tlp_ack) begin
                        // 从缓冲区读取并发送数据
                        if (buf_rd_ptr < buf_wr_ptr) begin
                            write_data <= data_buffer[buf_rd_ptr];
                            write_data_valid <= 1'b1;
                            buf_rd_ptr <= buf_rd_ptr + 1;
                        end
                        else if (buf_rd_ptr == buf_wr_ptr) begin
                            // 所有数据已发送
                            tlp_count <= tlp_count + 1;
                            
                            // 更新地址和剩余字节数
                            if (current_tlp_length <= (bytes_remaining >> 2)) begin
                                current_src_addr <= current_src_addr + (current_tlp_length << 2);
                                current_dst_addr <= current_dst_addr + (current_tlp_length << 2);
                                bytes_remaining <= bytes_remaining - (current_tlp_length << 2);
                            end
                            else begin
                                // 最后一个TLP，可能不是完整的DWORD倍数
                                current_src_addr <= current_src_addr + bytes_remaining;
                                current_dst_addr <= current_dst_addr + bytes_remaining;
                                bytes_remaining <= 32'h0;
                            end
                            
                            // 检查是否传输完成
                            if (bytes_remaining == 0) begin
                                dma_state <= DMA_COMPLETE;
                            end
                            else begin
                                // 继续下一个传输
                                dma_state <= DMA_READ_REQ;
                                buf_wr_ptr <= 10'h0;
                                buf_rd_ptr <= 10'h0;
                            end
                        end
                    end
                end
                
                DMA_COMPLETE: begin
                    // 传输完成
                    dma_status_reg <= 32'h00000002; // 传输完成
                    dma_interrupt <= 1'b1;          // 触发中断
                    
                    // 等待DMA控制寄存器清除启动位
                    if (!dma_control_reg[0]) begin
                        dma_state <= DMA_IDLE;
                        dma_status_reg <= 32'h00000000; // 回到空闲状态
                        dma_interrupt <= 1'b0;          // 清除中断
                    end
                end
                
                DMA_ERROR: begin
                    // 错误处理
                    dma_status_reg <= 32'h80000000; // 错误状态
                    dma_interrupt <= 1'b1;          // 触发中断
                    
                    // 等待重置
                    if (!dma_control_reg[0]) begin
                        dma_state <= DMA_IDLE;
                        dma_status_reg <= 32'h00000000;
                        dma_interrupt <= 1'b0;
                    end
                end
                
                default: begin
                    // 未知状态，回到空闲状态
                    dma_state <= DMA_IDLE;
                end
            endcase
            
            // 错误条件检测
            if (dma_control_reg[31]) begin // 通常错误位在高位
                dma_state <= DMA_ERROR;
            end
        end
    end
    
    // ==========================================================================
    // DMA性能统计
    // ==========================================================================
    
    // TLP计数器可用于性能监控和调试
    
    // ==========================================================================
    // 设备特定功能
    // ==========================================================================
    
    {device_specific_logic}

endmodule
"""
    
    def generate_dma_controller(self, device_config, output_file):
        """生成DMA控制器代码"""
        try:
            device_name = device_config.get("name", "自定义设备")
            module_name = self._sanitize_module_name(device_name) + "_dma_controller"
            device_type = device_config.get("type", "custom")
            
            # 缓冲区深度和最大负载配置
            buffer_depth = device_config.get("dma_buffer_depth", 64)
            max_payload_size = device_config.get("dma_max_payload", 256)
            max_payload_dw = max_payload_size // 4
            
            # 根据设备类型生成特定接口和逻辑
            device_specific_interface, device_specific_logic = self._generate_device_specific_parts(device_type, device_config)
            
            # 生成最终代码
            code = self.template.format(
                device_name=device_name,
                module_name=module_name,
                timestamp=__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                buffer_depth=buffer_depth,
                max_payload=max_payload_size,
                max_payload_dw=max_payload_dw,
                device_specific_interface=device_specific_interface,
                device_specific_logic=device_specific_logic
            )
            
            # 写入输出文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            print(f"✅ DMA控制器代码已生成: {output_file}")
            return True
        except Exception as e:
            print(f"❌ 生成DMA控制器代码失败: {str(e)}")
            return False
    
    def _generate_device_specific_parts(self, device_type, device_config):
        """根据设备类型生成特定部分"""
        # 默认值
        device_specific_interface = "// 无设备特定接口"
        device_specific_logic = "// 无设备特定逻辑"
        
        if device_type == "nic" or device_type == "wifi":
            # 网络设备特定部分
            device_specific_interface = """
    // 网络设备特定接口
    input      [15:0]   packet_length,    // 数据包长度
    output reg          packet_ready,     // 数据包就绪
    output reg          packet_eop        // 数据包结束标志"""
            
            device_specific_logic = """
    // 网络设备特定逻辑
    reg packet_in_progress;
    
    always @(posedge clk) begin
        if (rst) begin
            packet_in_progress <= 1'b0;
            packet_ready <= 1'b0;
            packet_eop <= 1'b0;
        end
        else begin
            // 默认值
            packet_eop <= 1'b0;
            
            // 数据包处理
            if (dma_state == DMA_WRITE && write_data_valid) begin
                if (!packet_in_progress) begin
                    packet_in_progress <= 1'b1;
                    packet_ready <= 1'b1;
                end
                
                // 检测包结束
                if (buf_rd_ptr + 1 == buf_wr_ptr) begin
                    packet_eop <= 1'b1;
                    packet_in_progress <= 1'b0;
                end
            end
            else if (dma_state == DMA_IDLE || dma_state == DMA_COMPLETE) begin
                packet_ready <= 1'b0;
                packet_in_progress <= 1'b0;
            end
        end
    end"""
            
        elif device_type == "storage":
            # 存储设备特定部分
            device_specific_interface = """
    // 存储设备特定接口
    input      [63:0]   lba_address,      // 逻辑块地址
    input      [15:0]   sector_count,     // 扇区数
    output reg          io_complete       // IO完成标志"""
            
            device_specific_logic = """
    // 存储设备特定逻辑
    always @(posedge clk) begin
        if (rst) begin
            io_complete <= 1'b0;
        end
        else begin
            // 默认值
            io_complete <= 1'b0;
            
            // IO完成
            if (dma_state == DMA_COMPLETE) begin
                io_complete <= 1'b1;
            end
        end
    end"""
            
        return device_specific_interface, device_specific_logic
    
    def _sanitize_module_name(self, name):
        """将设备名称转换为有效的模块名"""
        # 移除非字母数字字符，转换为小写
        name = re.sub(r'[^\w]', '_', name).lower()
        # 确保开头是字母
        if name and not name[0].isalpha():
            name = "dev_" + name
        return name 