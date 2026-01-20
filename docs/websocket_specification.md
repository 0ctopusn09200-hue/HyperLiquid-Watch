# WebSocket Specification

本文档定义了Backend模块通过WebSocket实时推送数据的消息格式规范。

**WebSocket URL**: `ws://localhost:8080/ws`

---

## 目录

- [连接协议](#连接协议)
- [消息格式](#消息格式)
- [消息类型](#消息类型)
- [客户端操作](#客户端操作)
- [错误处理](#错误处理)

---

## 连接协议

### 连接建立

客户端通过WebSocket连接到服务器后，需要发送订阅消息来指定需要接收的数据类型。

### 连接参数（可选）

可以通过URL参数传递配置：

```
ws://localhost:8080/ws?token=xxx&client_id=client_001
```

---

## 消息格式

所有WebSocket消息都采用JSON格式。

### 客户端 → 服务器（订阅消息）

```json
{
  "type": "subscribe",
  "channels": ["liquidations", "long_short_ratios"],
  "params": {
    "coins": ["BTC", "ETH"],
    "filters": {
      "side": "LONG"
    }
  }
}
```

### 服务器 → 客户端（数据推送）

```json
{
  "type": "liquidation",
  "channel": "liquidations",
  "timestamp": "2026-01-10T10:30:00Z",
  "data": {
    "tx_hash": "0x1234567890abcdef...",
    "block_number": 12345678,
    "block_timestamp": "2026-01-10T10:30:00Z",
    "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "coin": "BTC",
    "side": "LONG",
    "liquidated_size": "1.50000000",
    "liquidation_price": "45000.50000000",
    "liquidation_value_usd": "67500.75000000"
  }
}
```

---

## 消息类型

### 1. 清算事件推送

**Channel**: `liquidations`

**消息格式**:

```json
{
  "type": "liquidation",
  "channel": "liquidations",
  "timestamp": "2026-01-10T10:30:00Z",
  "data": {
    "tx_hash": "0x1234567890abcdef...",
    "block_number": 12345678,
    "block_timestamp": "2026-01-10T10:30:00Z",
    "user_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "coin": "BTC",
    "side": "LONG",
    "liquidated_size": "1.50000000",
    "liquidation_price": "45000.50000000",
    "liquidation_value_usd": "67500.75000000",
    "leverage": "10.00",
    "margin": "6750.07500000",
    "liquidator_address": "0x1111111111111111111111111111111111111111"
  }
}
```

**订阅参数**:

```json
{
  "type": "subscribe",
  "channels": ["liquidations"],
  "params": {
    "coins": ["BTC", "ETH"],  // 可选，不传则接收所有币种
    "filters": {
      "side": "LONG"  // 可选，LONG 或 SHORT
    }
  }
}
```

---

### 2. 多空比例更新推送

**Channel**: `long_short_ratios`

**消息格式**:

```json
{
  "type": "long_short_ratio",
  "channel": "long_short_ratios",
  "timestamp": "2026-01-10T10:35:00Z",
  "data": {
    "coin": "BTC",
    "timestamp": "2026-01-10T10:35:00Z",
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

**订阅参数**:

```json
{
  "type": "subscribe",
  "channels": ["long_short_ratios"],
  "params": {
    "coins": ["BTC", "ETH"]  // 可选，不传则接收所有币种
  }
}
```

---

### 3. 清算地图更新推送

**Channel**: `liquidation_map`

**消息格式**:

```json
{
  "type": "liquidation_map",
  "channel": "liquidation_map",
  "timestamp": "2026-01-10T10:35:00Z",
  "data": {
    "coin": "BTC",
    "timestamp": "2026-01-10T10:35:00Z",
    "price_levels": [
      {
        "price": "44000.00000000",
        "long_liquidation_value": "1500000.00000000",
        "short_liquidation_value": "800000.00000000",
        "long_liquidation_count": 50,
        "short_liquidation_count": 30
      },
      {
        "price": "45000.00000000",
        "long_liquidation_value": "2000000.00000000",
        "short_liquidation_value": "1200000.00000000",
        "long_liquidation_count": 70,
        "short_liquidation_count": 45
      }
    ]
  }
}
```

**订阅参数**:

```json
{
  "type": "subscribe",
  "channels": ["liquidation_map"],
  "params": {
    "coins": ["BTC"]  // 必填，指定交易对
  }
}
```

---

### 4. 巨鲸活动推送

**Channel**: `whale_activities`

**消息格式**:

```json
{
  "type": "whale_activity",
  "channel": "whale_activities",
  "timestamp": "2026-01-10T10:30:00Z",
  "data": {
    "whale_id": 1,
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "alias": "Whale #1",
    "activity_type": "LARGE_TRADE",
    "tx_hash": "0x1234567890abcdef...",
    "coin": "BTC",
    "size": "10.00000000",
    "value_usd": "450000.00000000",
    "timestamp": "2026-01-10T10:30:00Z",
    "details": {
      "side": "LONG",
      "price": "45000.00000000"
    }
  }
}
```

**订阅参数**:

```json
{
  "type": "subscribe",
  "channels": ["whale_activities"],
  "params": {
    "whale_ids": [1, 2, 3],  // 可选，不传则接收所有巨鲸
    "activity_types": ["LARGE_TRADE", "LIQUIDATION"]  // 可选
  }
}
```

---

## 客户端操作

### 1. 订阅频道

```json
{
  "type": "subscribe",
  "channels": ["liquidations", "long_short_ratios"],
  "params": {
    "coins": ["BTC", "ETH"]
  }
}
```

**响应**:

```json
{
  "type": "subscribed",
  "channels": ["liquidations", "long_short_ratios"],
  "message": "Successfully subscribed"
}
```

---

### 2. 取消订阅

```json
{
  "type": "unsubscribe",
  "channels": ["liquidations"]
}
```

**响应**:

```json
{
  "type": "unsubscribed",
  "channels": ["liquidations"],
  "message": "Successfully unsubscribed"
}
```

---

### 3. 心跳（Keep-alive）

客户端可以发送ping消息保持连接：

```json
{
  "type": "ping"
}
```

服务器响应：

```json
{
  "type": "pong",
  "timestamp": "2026-01-10T10:30:00Z"
}
```

---

### 4. 获取当前订阅状态

```json
{
  "type": "get_subscriptions"
}
```

**响应**:

```json
{
  "type": "subscriptions",
  "channels": ["liquidations", "long_short_ratios"],
  "params": {
    "coins": ["BTC", "ETH"]
  }
}
```

---

## 错误处理

### 错误消息格式

```json
{
  "type": "error",
  "code": "INVALID_CHANNEL",
  "message": "Channel 'invalid_channel' is not supported",
  "timestamp": "2026-01-10T10:30:00Z"
}
```

### 错误码

| 错误码 | 说明 |
|--------|------|
| INVALID_MESSAGE | 消息格式无效 |
| INVALID_CHANNEL | 不支持的频道 |
| INVALID_PARAMS | 参数无效 |
| UNAUTHORIZED | 未授权 |
| INTERNAL_ERROR | 服务器内部错误 |

---

## 连接生命周期

1. **建立连接**: 客户端连接到WebSocket服务器
2. **发送订阅**: 客户端发送订阅消息
3. **接收数据**: 服务器推送实时数据
4. **保持连接**: 使用ping/pong保持连接活跃
5. **关闭连接**: 客户端或服务器关闭连接

---

## 性能建议

- 服务器应该对每个客户端设置合理的订阅限制
- 客户端应该实现重连机制
- 建议使用心跳机制检测连接状态
- 大数据量时考虑使用消息压缩

---

## 版本信息

- **Version**: 1.0
- **Last Updated**: 2026-01-10
- **Author**: @zhang_yunan
