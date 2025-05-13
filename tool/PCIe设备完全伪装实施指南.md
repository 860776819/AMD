# PCIe设备完全伪装实施指南

## 文档说明

本文档提供了使用FPGA实现PCIe设备完全伪装的技术指南，适用于PCILeech FPGA项目或类似平台。完全伪装是指FPGA设备能够完美模拟目标PCIe设备的所有行为，使操作系统和驱动程序无法区分伪装设备与真实硬件。

## 目录

1. [基本原理与准备工作](#1-基本原理与准备工作)
2. [配置空间伪装](#2-配置空间伪装)
3. [BAR空间完整实现](#3-bar空间完整实现)
4. [行为模拟](#4-行为模拟)
5. [驱动交互](#5-驱动交互)
6. [高级功能模拟](#6-高级功能模拟)
7. [防检测措施](#7-防检测措施)
8. [测试与验证](#8-测试与验证)
9. [常见设备伪装案例](#9-常见设备伪装案例)

## 1. 基本原理与准备工作

### 1.1 完全伪装的基本原理

PCIe设备伪装的核心是让操作系统和驱动程序"相信"FPGA就是目标设备。这需要在以下层面进行模拟：

- **标识层**：设备ID、厂商ID等配置空间信息
- **功能层**：寄存器空间、命令响应、状态报告
- **行为层**：时序特性、中断处理、电源状态
- **协议层**：设备特有的通信协议和数据格式

### 1.2 前期分析与准备

1. **目标设备选择**：
   - 选择具有详细文档的设备
   - 考虑驱动开源性和复杂度
   - 评估伪装难度与可行性

2. **设备分析工具**：
   - PCIe协议分析仪
   - 操作系统驱动调试工具
   - 设备规格文档和数据手册

3. **资源准备**：
   - 目标设备样品（用于对比分析）
   - 足够资源的FPGA开发板
   - PCIe接口和分析工具

## 2. 配置空间伪装

配置空间是PCIe设备识别的基础，必须完美模拟。

### 2.1 设备标识修改

```
// 在pcileech_cfgspace.coe中修改
memory_initialization_radix=16;
memory_initialization_vector=
DDDDVVVV,fffff004,CCCCCC01,fffff00c,  // 设备ID/供应商ID + 类别代码
```

- `VVVV`：目标设备的Vendor ID
- `DDDD`：目标设备的Device ID
- `CCCCCC`：设备的Class Code

### 2.2 完整配置空间实现

1. **基本标识区域**：
   - Vendor ID 和 Device ID
   - Revision ID
   - Class Code
   - Header Type

2. **资源分配区域**：
   - 精确配置BAR大小与类型
   - 中断引脚和线路配置

3. **能力指针区域**：
   - PCIe能力结构
   - MSI/MSI-X能力
   - 电源管理能力
   - 设备特有能力

### 2.3 写入掩码配置

```
// 在pcileech_cfgspace_writemask.coe中设置
memory_initialization_radix=16;
memory_initialization_vector=
00000000,00000107,00000000,00000000,  // 关键区域写保护
```

- 设备ID/供应商ID区域设为只读（掩码为0）
- 命令寄存器允许必要位写入（如总线主控、内存空间使能）
- 配置设备特有的可写区域

## 3. BAR空间完整实现

BAR空间是驱动程序与设备交互的主要接口，需要全面实现。

### 3.1 寄存器映射分析

1. **寄存器分类**：
   - 控制寄存器
   - 状态寄存器
   - 配置寄存器
   - 数据缓冲区

2. **寄存器行为分析**：
   - 读写特性（只读、只写、读写）
   - 位掩码和清除方式（读清除、写清除、写置位）
   - 默认值和复位值

### 3.2 寄存器实现示例

```verilog
// 在BAR控制器中实现关键寄存器
case ({drd_addr[31:24], drd_addr[23:16], drd_addr[15:08], drd_addr[07:00]} - base_address_register)
    // 状态寄存器 - 只读
    16'h0000 : rd_rsp_data <= {status_bits, 24'h0};
    
    // 控制寄存器 - 读写
    16'h0004 : begin
        rd_rsp_data <= control_reg;
        if (dwr_valid) control_reg <= dwr_data;
    end
    
    // 中断状态 - 读清除
    16'h0008 : begin
        rd_rsp_data <= int_status;
        if (drd_valid) int_status <= 32'h0;
    end
    
    // 版本信息 - 只读
    16'h000C : rd_rsp_data <= 32'h00010023; // v1.0.35
endcase
```

### 3.3 内存区域实现

对于包含大量内存的设备（如网卡的发送/接收缓冲区）：

```verilog
// 实现内存区域
if (drd_addr >= MEM_BASE && drd_addr < MEM_BASE + MEM_SIZE) begin
    // 内存区域读取
    mem_addr = drd_addr - MEM_BASE;
    rd_rsp_data <= memory[mem_addr];
end else if (dwr_valid && dwr_addr >= MEM_BASE && dwr_addr < MEM_BASE + MEM_SIZE) begin
    // 内存区域写入
    mem_addr = dwr_addr - MEM_BASE;
    memory[mem_addr] <= dwr_data;
end
```

## 4. 行为模拟

### 4.1 设备初始化序列

模拟设备的上电和初始化行为：

```verilog
// 初始化状态机
reg [3:0] init_state;
always @(posedge clk) begin
    if (rst) begin
        init_state <= INIT_RESET;
        status_reg <= 32'h0;
    end else begin
        case (init_state)
            INIT_RESET: begin
                // 设备复位后的初始状态
                status_reg <= 32'h00000001; // 设备处于复位状态
                init_state <= INIT_SELFTEST;
            end
            INIT_SELFTEST: begin
                // 自检流程
                status_reg <= 32'h00000002; // 设备处于自检状态
                if (selftest_done)
                    init_state <= INIT_READY;
            end
            INIT_READY: begin
                // 准备就绪
                status_reg <= 32'h00000100; // 设备就绪标志
            end
        endcase
    end
end
```

### 4.2 完整中断处理

实现精确的中断生成机制：

```verilog
// 中断控制
reg [31:0] int_status;      // 中断状态寄存器
reg [31:0] int_enable;      // 中断使能寄存器

// 中断生成逻辑
always @(posedge clk) begin
    if (event_detected && (int_enable & EVENT_MASK)) begin
        int_status <= int_status | EVENT_MASK;
        generate_interrupt <= 1'b1;
    end else begin
        generate_interrupt <= 1'b0;
    end
end

// 连接到PCIe中断接口
assign cfg_interrupt_assert = generate_interrupt && !int_asserted;
always @(posedge clk) begin
    if (rst)
        int_asserted <= 1'b0;
    else if (generate_interrupt)
        int_asserted <= 1'b1;
    else if (int_acknowledge)
        int_asserted <= 1'b0;
end
```

### 4.3 内部状态机

创建复杂的内部状态机以模拟设备行为：

```verilog
// 设备状态机
localparam STATE_IDLE = 3'b000;
localparam STATE_INIT = 3'b001;
localparam STATE_ACTIVE = 3'b010;
localparam STATE_ERROR = 3'b011;
localparam STATE_RECOVERY = 3'b100;

reg [2:0] device_state;

always @(posedge clk) begin
    if (rst) begin
        device_state <= STATE_IDLE;
    end else begin
        case (device_state)
            STATE_IDLE: begin
                if (cmd_start) device_state <= STATE_INIT;
            end
            STATE_INIT: begin
                if (init_complete) device_state <= STATE_ACTIVE;
                if (error_detected) device_state <= STATE_ERROR;
            end
            // ...其他状态转换逻辑
        endcase
    end
end
```

## 5. 驱动交互

### 5.1 命令响应机制

实现设备的命令处理流程：

```verilog
// 命令解析与执行
reg [31:0] cmd_reg;         // 命令寄存器
reg [31:0] cmd_param[4];    // 命令参数寄存器

always @(posedge clk) begin
    if (dwr_valid && dwr_addr == CMD_REG_ADDR) begin
        cmd_reg <= dwr_data;
        start_cmd_execution <= 1'b1;
    end
end

// 命令执行状态机
always @(posedge clk) begin
    if (start_cmd_execution) begin
        case (cmd_reg[7:0])  // 命令码
            CMD_READ_CONFIG: begin
                // 读取配置命令实现
                result_data <= device_config[cmd_param[0]];
            end
            CMD_WRITE_CONFIG: begin
                // 写入配置命令实现
                device_config[cmd_param[0]] <= cmd_param[1];
            end
            CMD_START_OPERATION: begin
                // 启动特定操作
                operation_active <= 1'b1;
            end
            // 其他命令实现...
        endcase
    end
end
```

### 5.2 数据传输队列

实现数据传输队列，特别是对于网卡等设备：

```verilog
// 接收数据队列实现
module rx_queue #(
    parameter DEPTH = 256,
    parameter WIDTH = 32
)(
    input clk,
    input rst,
    input [WIDTH-1:0] data_in,
    input write_en,
    output [WIDTH-1:0] data_out,
    input read_en,
    output full,
    output empty,
    output [7:0] count
);
    // 队列实现代码...
endmodule

// 发送队列类似实现
```

### 5.3 DMA传输模拟

对于支持DMA的设备，实现DMA传输引擎：

```verilog
// DMA控制器
reg [63:0] dma_base_addr;    // DMA基址
reg [31:0] dma_length;       // 传输长度
reg        dma_start;        // 开始传输
reg        dma_direction;    // 0=设备到内存，1=内存到设备

// DMA状态机
always @(posedge clk) begin
    if (rst) begin
        dma_state <= DMA_IDLE;
    end else begin
        case (dma_state)
            DMA_IDLE: begin
                if (dma_start) dma_state <= DMA_PREPARE;
            end
            DMA_PREPARE: begin
                // 准备DMA传输参数
                current_addr <= dma_base_addr;
                bytes_remaining <= dma_length;
                dma_state <= DMA_TRANSFER;
            end
            DMA_TRANSFER: begin
                // 执行传输
                if (bytes_remaining == 0) begin
                    dma_state <= DMA_COMPLETE;
                end else if (tlp_ready) begin
                    // 生成读写TLP
                    generate_memory_tlp(current_addr, transfer_size);
                    current_addr <= current_addr + transfer_size;
                    bytes_remaining <= bytes_remaining - transfer_size;
                end
            end
            DMA_COMPLETE: begin
                // 传输完成，生成中断
                int_status <= int_status | DMA_COMPLETE_INT;
                dma_state <= DMA_IDLE;
            end
        endcase
    end
end
```

## 6. 高级功能模拟

### 6.1 特定设备功能单元

针对不同类型设备的特有功能实现：

#### 6.1.1 网卡特有功能

```verilog
// MAC地址过滤器
reg [47:0] device_mac_addr;      // 设备MAC地址
reg [47:0] mac_filter[16];       // MAC过滤表
reg [15:0] mac_filter_valid;     // 有效标志

// 接收包过滤
function is_packet_for_us;
    input [47:0] dst_mac;
    begin
        // 检查是否是广播包
        if (dst_mac == 48'hFFFFFFFFFFFF) begin
            is_packet_for_us = 1'b1;
        end 
        // 检查是否匹配设备MAC
        else if (dst_mac == device_mac_addr) begin
            is_packet_for_us = 1'b1;
        end
        // 检查MAC过滤表
        else begin
            is_packet_for_us = 1'b0;
            for (int i = 0; i < 16; i = i + 1) begin
                if (mac_filter_valid[i] && (dst_mac == mac_filter[i])) begin
                    is_packet_for_us = 1'b1;
                end
            end
        end
    end
endfunction
```

#### 6.1.2 存储控制器特有功能

```verilog
// RAID配置寄存器
reg [31:0] raid_config;        // RAID配置
reg [31:0] disk_status[8];     // 磁盘状态

// LBA转换逻辑
function [63:0] translate_lba;
    input [63:0] logical_lba;
    input [7:0] raid_level;
    begin
        case (raid_level)
            RAID_0: begin
                // RAID 0条带计算
                stripe_size = raid_config[7:0];
                stripe_number = logical_lba / stripe_size;
                stripe_offset = logical_lba % stripe_size;
                disk_number = stripe_number % disk_count;
                translate_lba = (stripe_number / disk_count) * stripe_size + stripe_offset;
            end
            // 其他RAID级别转换...
        endcase
    end
endfunction
```

### 6.2 电源管理完整实现

实现PCIe电源管理功能：

```verilog
// 电源状态寄存器
reg [2:0] power_state;  // D0, D1, D2, D3hot, D3cold

// ASPM控制
reg aspm_l0s_enable;
reg aspm_l1_enable;

// 电源状态转换
always @(posedge clk) begin
    if (rst) begin
        power_state <= PWR_D0;  // 全功率状态
    end else if (cfg_pmcsr_powerstate_change) begin
        case (cfg_pmcsr_powerstate)
            3'b000: begin  // D0
                power_state <= PWR_D0;
                // 唤醒所有功能单元
                enable_all_units <= 1'b1;
            end
            3'b001: begin  // D1
                power_state <= PWR_D1;
                // 部分功能单元进入低功耗
                enable_all_units <= 1'b0;
            end
            3'b011: begin  // D3hot
                power_state <= PWR_D3HOT;
                // 保留最小功能
                save_device_state <= 1'b1;
            end
            // 其他电源状态...
        endcase
    end
end
```

### 6.3 高级中断功能

实现MSI/MSI-X中断：

```verilog
// MSI-X表实现
reg [63:0] msix_table[32];  // 消息地址
reg [31:0] msix_data[32];   // 消息数据
reg [31:0] msix_mask;       // 中断掩码

// MSI-X中断生成
task generate_msix_interrupt;
    input [4:0] vector;
    begin
        if (!msix_mask[vector]) begin
            // 生成内存写TLP到MSI-X地址
            msi_addr <= msix_table[vector];
            msi_data <= msix_data[vector];
            generate_msi_tlp <= 1'b1;
        end
    end
endtask
```

## 7. 防检测措施

### 7.1 时序特征模拟

模拟真实设备的响应延迟和处理时间：

```verilog
// 命令响应延迟模拟
reg [15:0] response_delay_counter;
reg response_pending;

always @(posedge clk) begin
    if (cmd_received) begin
        // 根据命令类型设置不同的延迟
        case (cmd_type)
            CMD_TYPE_SIMPLE: response_delay <= 16'd10;  // 简单命令快速响应
            CMD_TYPE_IO: response_delay <= 16'd50;      // I/O命令中等延迟
            CMD_TYPE_COMPLEX: begin
                // 复杂命令使用略微随机的延迟
                response_delay <= 16'd100 + pseudo_random[5:0];
            end
        endcase
        response_delay_counter <= response_delay;
        response_pending <= 1'b1;
    end else if (response_pending) begin
        if (response_delay_counter == 0) begin
            // 延迟结束，生成响应
            generate_response <= 1'b1;
            response_pending <= 1'b0;
        end else begin
            response_delay_counter <= response_delay_counter - 1'b1;
        end
    end
end
```

### 7.2 特征隐藏

移除可能暴露伪装的标识：

```verilog
// 移除PCILeech特征
// 1. 不使用特定保留字段
// 2. 确保所有寄存器都有合理的默认值
// 3. 不使用固定模式的值
```

### 7.3 资源占用优化

优化FPGA资源使用，避免引起怀疑：

```verilog
// 资源使用优化
// 实现轻量级版本的非关键功能
// 使用时分复用减少逻辑资源占用
// 使用更少的缓冲区，但保持功能正确性
```

## 8. 测试与验证

### 8.1 分层测试方法

采用分层测试方法验证伪装效果：

1. **配置空间测试**：
   - 使用PCIe工具验证配置空间正确性
   - 测试每个寄存器的读写行为

2. **寄存器操作测试**：
   - 验证每个BAR寄存器的功能
   - 测试状态变化和命令响应

3. **驱动加载测试**：
   - 使用目标设备的官方驱动
   - 验证驱动初始化和功能识别

4. **功能测试**：
   - 验证设备主要功能
   - 测试性能和稳定性

### 8.2 TLP分析与比对

使用PCIe分析工具比较伪装设备与真实设备：

```
# tlscan配置文件示例
[HEADER]
Name=设备行为比对
Description=捕获设备响应进行比对分析

[FILTER]
Type=MRd,MWr,CplD
Address=0xF0000000-0xF00FFFFF
RequesterID=*

[TRIGGER]
Condition=PATTERN
Pattern=0xF0000000
Mask=0xFFFFF000
Action=CAPTURE

[EXPORT]
Format=BINARY
Filename=device_compare_%Y%m%d.bin
```

### 8.3 压力测试

在极端条件下验证伪装的稳定性：

- 高频率命令发送
- 并发操作测试
- 长时间运行测试
- 异常操作恢复测试

## 9. 常见设备伪装案例

### 9.1 网卡伪装

#### 9.1.1 Atheros AR9287无线网卡

关键实现点：
- Vendor ID: 0x168C, Device ID: 0x002E
- Class Code: 0x028000 (网络控制器)
- EEPROM模拟（MAC地址、区域码等）
- 中断寄存器实现（0x4028、0x4038）
- MAC版本寄存器（0x4020）
- 发送/接收队列模拟

#### 9.1.2 Intel I350千兆网卡

关键实现点：
- Vendor ID: 0x8086, Device ID: 0x1521
- 高级过滤功能
- MSI-X中断表
- 统计计数器

### 9.2 存储控制器伪装

关键实现点：
- 命令队列实现
- DMA引擎完整模拟
- 中断聚合功能
- 设备特有协议支持

### 9.3 GPU简化伪装

关键实现点：
- 基本显存管理
- 简化的渲染引擎响应
- PCI桥接功能
- 电源管理模式

## 总结

PCIe设备完全伪装是一项复杂的工程，需要深入理解PCIe协议和目标设备的行为特性。通过本指南中的技术和方法，可以构建能够欺骗操作系统和驱动程序的高级伪装设备，用于安全研究、兼容性测试或特殊应用场景。

成功的伪装不仅需要正确的标识和基本功能实现，还需要关注细节，如时序特性、电源管理、中断行为和特有协议。通过全面的测试和迭代优化，可以达到近乎完美的伪装效果。 