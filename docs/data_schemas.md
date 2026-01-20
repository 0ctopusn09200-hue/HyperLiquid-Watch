# Data Schemas Specification

本文档定义了系统中使用的数据格式规范，包括Kafka消息格式和数据传输格式。

## 目录
- [Kafka消息格式](#kafka消息格式)
  - [Parser → Computer: 交易记录消息](#parser--computer-交易记录消息)
  - [Computer → Backend: 计算结果消息（可选）](#computer--backend-计算结果消息可选)
- [数据字段说明](#数据字段说明)

---

## Kafka消息格式

### Parser → Computer: 交易记录消息

**Topic名称**: `hyperliquid.transactions`

**消息格式**: JSON

```json
{
  "tx_hash": "0x1234567890abcdef...",
  "block_number": 12345678,
  "block_timestamp": "2026-01-10T10:30:00Z",
  "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "coin": "BTC",
  "side": "LONG",
  "size": "1.50000000",
  "price": "45000.50000000",
  "leverage": "10.00",
  "margin": "6750.07500000",
  "fee": "6.75000000",
  "tx_type": "ORDER",
  "raw_data": {
    "additional_field": "value"
  }
}
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tx_hash | string | 是 | 交易哈希，唯一标识符 |
| block_number | integer | 是 | 区块号 |
| block_timestamp | string (ISO 8601) | 是 | 区块时间戳 |
| user_address | string | 是 | 用户钱包地址 |
| coin | string | 是 | 交易对符号（BTC, ETH等） |
| side | string | 是 | 方向：LONG, SHORT, OPEN, CLOSE |
| size | string (decimal) | 是 | 持仓大小 |
| price | string (decimal) | 是 | 成交价格 |
| leverage | string (decimal) | 否 | 杠杆倍数 |
| margin | string (decimal) | 否 | 保证金 |
| fee | string (decimal) | 否 | 手续费 |
| tx_type | string | 是 | 交易类型：ORDER, LIQUIDATION, TRANSFER等 |
| raw_data | object | 否 | 原始数据，包含其他扩展字段 |

#### 清算事件消息格式

当 `tx_type` 为 `LIQUIDATION` 时，消息格式如下：

```json
{
  "tx_hash": "0xabcdef1234567890...",
  "block_number": 12345679,
  "block_timestamp": "2026-01-10T10:31:00Z",
  "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "coin": "ETH",
  "side": "LONG",
  "size": "10.00000000",
  "price": "2800.00000000",
  "leverage": "20.00",
  "margin": "1400.00000000",
  "fee": "0.00000000",
  "tx_type": "LIQUIDATION",
  "liquidator_address": "0x1111111111111111111111111111111111111111",
  "liquidation_value_usd": "28000.00000000",
  "raw_data": {}
}
```

**额外字段**（仅在清算事件中）:
- `liquidator_address`: 清算人地址
- `liquidation_value_usd`: 清算价值（USD）

---

### Computer → Backend: 计算结果消息（可选）

如果Computer需要实时推送计算结果，可以使用以下格式：

**Topic名称**: `hyperliquid.computed_data`

**消息格式**: JSON

```json
{
  "data_type": "LONG_SHORT_RATIO",
  "coin": "BTC",
  "timestamp": "2026-01-10T10:35:00Z",
  "data": {
    "long_ratio": 0.6543,
    "short_ratio": 0.3457,
    "long_position_value": "123456789.12345678",
    "short_position_value": "65432100.98765432",
    "total_position_value": "188888890.11111110",
    "long_accounts": 1250,
    "short_accounts": 890
  }
}
```

或者清算地图数据：

```json
{
  "data_type": "LIQUIDATION_MAP",
  "coin": "ETH",
  "timestamp": "2026-01-10T10:35:00Z",
  "data": {
    "price_levels": [
      {
        "price": "2750.00000000",
        "long_liquidation_value": "1500000.00000000",
        "short_liquidation_value": "800000.00000000",
        "long_liquidation_count": 50,
        "short_liquidation_count": 30
      },
      {
        "price": "2800.00000000",
        "long_liquidation_value": "2000000.00000000",
        "short_liquidation_value": "1200000.00000000",
        "long_liquidation_count": 70,
        "short_liquidation_count": 45
      }
    ]
  }
}
```

---

## 数据字段说明

### 通用字段类型

- **timestamp**: ISO 8601格式的UTC时间戳，例如 `2026-01-10T10:30:00Z`
- **decimal**: 大数使用字符串格式表示，避免精度丢失，例如 `"123456789.12345678"`
- **address**: Ethereum格式地址，42个字符，以0x开头
- **hash**: 交易哈希，66个字符，以0x开头

### 枚举值

#### side (方向)
- `LONG`: 做多
- `SHORT`: 做空
- `OPEN`: 开仓
- `CLOSE`: 平仓

#### tx_type (交易类型)
- `ORDER`: 普通订单
- `LIQUIDATION`: 清算事件
- `TRANSFER`: 转账
- `DEPOSIT`: 充值
- `WITHDRAW`: 提取

#### data_type (计算结果类型)
- `LONG_SHORT_RATIO`: 多空比例
- `LIQUIDATION_MAP`: 清算地图
- `POSITION_SUMMARY`: 持仓汇总

---

## Kafka Topic配置建议

### hyperliquid.transactions
- **Partitions**: 10 (根据数据量调整)
- **Replication Factor**: 1 (开发环境) / 3 (生产环境)
- **Retention**: 7天
- **Compression**: gzip

### hyperliquid.computed_data
- **Partitions**: 5
- **Replication Factor**: 1 (开发环境) / 3 (生产环境)
- **Retention**: 1天（计算结果已持久化到数据库）
- **Compression**: gzip

---

## 版本控制

- **Version**: 1.0
- **Last Updated**: 2026-01-10
- **Author**: @zhang_yunan
