# 设计文档索引

本文档索引了Task 2: System Architecture Design阶段创建的所有设计文档。

## 文档列表

### 1. 数据库Schema设计
📄 **文件**: `database_schema.sql`

包含完整的PostgreSQL数据库表结构设计，包括：
- `transactions` - 交易记录表
- `liquidations` - 清算事件表
- `long_short_ratios` - 多空比例表
- `liquidation_map` - 清算地图表
- `positions` - 持仓快照表
- `whale_watches` - 巨鲸监控表
- `whale_activities` - 巨鲸活动表
- 索引、视图和触发器的定义

### 2. 数据格式规范
📄 **文件**: `data_schemas.md`

定义了系统中使用的数据格式规范：
- Kafka消息格式（Parser → Computer）
- 交易记录消息格式
- 清算事件消息格式
- 计算结果消息格式
- 字段类型和枚举值说明

### 3. REST API规范
📄 **文件**: `api_specification.md`

定义了Backend模块提供的所有REST API接口：
- 清算事件API
- 多空比例API
- 清算地图API
- 交易记录API
- 巨鲸监控API
- 统一的响应格式和错误码

### 4. WebSocket规范
📄 **文件**: `websocket_specification.md`

定义了实时数据推送的WebSocket消息格式：
- 连接协议
- 消息类型（清算事件、多空比例、清算地图、巨鲸活动）
- 客户端订阅操作
- 错误处理

## Task 2 完成清单

- [x] Define order schemas（订单schema定义）
  - ✅ Kafka消息格式定义（`data_schemas.md`）

- [x] Design database schema and structure（数据库schema设计）
  - ✅ PostgreSQL表结构设计（`database_schema.sql`）

- [x] Define API specifications（API规范定义）
  - ✅ REST API规范（`api_specification.md`）

- [x] Define WebSocket message formats（WebSocket消息格式定义）
  - ✅ WebSocket规范（`websocket_specification.md`）

- [x] Setup docker-compose env（环境设置）
  - ✅ docker-compose.yml已配置

## 下一步（Task 3）

根据设计文档开始模块开发：
- Parser模块：按照`data_schemas.md`中的Kafka消息格式发送数据
- Computer模块：处理Kafka消息，计算结果并写入数据库（`database_schema.sql`）
- Backend模块：实现`api_specification.md`中的API和`websocket_specification.md`中的WebSocket服务
- Frontend模块：调用API并订阅WebSocket接收实时数据

---

**创建日期**: 2026-01-10  
**负责人**: @zhang_yunan
