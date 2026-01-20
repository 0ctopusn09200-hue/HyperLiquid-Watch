# Backend

Backend模块负责查询数据库、提供REST API接口，以及订阅Kafka并实时推送数据到前端客户端。

## 设计文档

详细的设计文档位于 `docs/` 目录：

- **数据库Schema**: `docs/database_schema.sql`
- **API规范**: `docs/api_specification.md`
- **WebSocket规范**: `docs/websocket_specification.md`
- **数据格式规范**: `docs/data_schemas.md`

## 核心功能

1. **REST API服务**
   - 查询清算事件
   - 查询多空比例数据
   - 查询清算地图
   - 查询交易记录
   - 巨鲸监控管理

2. **WebSocket服务**
   - 实时推送清算事件
   - 实时推送多空比例更新
   - 实时推送清算地图更新
   - 实时推送巨鲸活动

3. **Kafka订阅**
   - 订阅Computer模块的计算结果
   - 实时处理并推送到前端

## 开发说明

请参考 `docs/api_specification.md` 和 `docs/websocket_specification.md` 实现API和WebSocket服务。
