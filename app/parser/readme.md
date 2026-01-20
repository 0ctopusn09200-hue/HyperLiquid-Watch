# Parser Service - Hyperliquid WebSocket to Kafka

Parser 服务从 Hyperliquid WebSocket 订阅交易事件流，解析成标准格式并发送到 Kafka。

## 快速开始

### 1. 安装依赖

```bash
cd app/parser
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `env.example` 为 `.env`：

```bash
cp env.example .env
```

编辑 `.env` 文件根据需要修改配置。

### 3. 运行服务

**DRY_RUN 模式（仅打印，不写 Kafka）：**

```bash
DRY_RUN=1 python main.py
```

**正常模式（写入 Kafka）：**

```bash
python main.py
```

### 4. 验证消息

使用测试消费者验证 Kafka 中的消息：

```bash
python consumer_test.py
```

或使用 kafka-console-consumer：

```bash
# Docker Compose 环境
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic hyperliquid-raw-trades \
  --from-beginning

# 本地 Kafka
kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic hyperliquid-raw-trades \
  --from-beginning
```

## 详细文档

完整的使用说明、配置选项、消息格式等请查看 [README.md](./README.md)。

## 文件说明

- `main.py` - 主程序入口
- `hl_ws_client.py` - Hyperliquid WebSocket 客户端
- `producer.py` - Kafka Producer 封装
- `consumer_test.py` - Kafka 消费者测试工具
- `requirements.txt` - Python 依赖
- `env.example` - 环境变量示例
- `README.md` - 完整文档

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HL_COIN` | 交易对符号 | `BTC` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka 地址 | `localhost:9092` |
| `KAFKA_TOPIC` | Kafka Topic | `hyperliquid-raw-trades` |
| `DRY_RUN` | 仅打印模式 | `0` |

## 消息格式

符合 `docs/data_schemas.md` 定义的 "Parser → Computer: 交易记录消息" 格式：

```json
{
  "tx_hash": "0x...",
  "block_number": 0,
  "block_timestamp": "2026-01-20T10:30:00Z",
  "user_address": "UNKNOWN",
  "coin": "BTC",
  "side": "LONG",
  "size": "1.5",
  "price": "45000.0",
  "fee": "5.625",
  "tx_type": "ORDER",
  "raw_data": {...}
}
```
