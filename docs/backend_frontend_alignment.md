# Backend-Frontend 对齐说明

## 更新日期
2026-01-10

## 概述

后端已完全对齐前端TypeScript接口规范，所有API端点和WebSocket协议都已按照前端规范实现。

---

## ✅ 已对齐的API端点

### 1. Liquidation Heatmap
- **路径**: `GET /api/v1/market/liquidation`
- **查询参数**:
  - `token` (可选, 默认: "BTC"): 代币符号
  - `range` (可选, 默认: 4.5): 价格范围百分比
- **响应格式**: 完全符合 `LiquidationHeatmapResponse` 接口
  ```json
  {
    "token": "BTC",
    "currentPrice": 98400,
    "points": [
      {
        "price": 94000,
        "longVol": 120,
        "shortVol": 80,
        "current": false
      }
    ],
    "minPrice": 94000,
    "maxPrice": 102000
  }
  ```

### 2. Long/Short Ratio
- **路径**: `GET /api/v1/market/long-short-ratio`
- **查询参数**:
  - `token` (可选): 按代币过滤，不传则聚合所有代币
- **响应格式**: 完全符合 `LongShortRatioResponse` 接口
  ```json
  {
    "longPercent": 52,
    "shortPercent": 48,
    "longVolume": 2840000000,
    "shortVolume": 2620000000,
    "longChange24h": 5.2,
    "shortChange24h": 3.8,
    "updatedAt": "2024-01-15T10:30:00Z"
  }
  ```

### 3. Whale Activities
- **路径**: `GET /api/v1/whale/activities`
- **查询参数**:
  - `limit` (可选, 默认: 10, 最大: 100): 返回数量
  - `token` (可选): 按代币过滤
  - `side` (可选, "Long" | "Short"): 按方向过滤
  - `type` (可选, "Open" | "Close"): 按类型过滤
  - `minValue` (可选, 默认: 1000000): 最小USD价值
- **响应格式**: 完全符合 `WhaleActivitiesResponse` 接口
  ```json
  {
    "transactions": [
      {
        "time": "2 min ago",
        "address": "0x49f3...8d2b",
        "token": "BTC",
        "value": 2567735.06,
        "side": "Long",
        "type": "Open",
        "amount": "28.40572 BTC",
        "timestamp": "2024-01-15T10:28:00Z",
        "txHash": "0xabc123..."
      }
    ],
    "totalCount": 156,
    "updatedAt": "2024-01-15T10:30:00Z"
  }
  ```

### 4. Wallet Distribution
- **路径**: `GET /api/v1/wallet/distribution`
- **查询参数**:
  - `token` (可选): 按代币过滤，不传则聚合所有代币
- **响应格式**: 完全符合 `WalletPositionDistributionResponse` 接口
  ```json
  {
    "buckets": [
      {
        "positionSize": "$0 - $250",
        "category": "shrimp",
        "categoryEn": "Shrimp",
        "walletCount": 245912,
        "openInterestPercent": 8.64,
        "longValue": "$717M",
        "shortValue": "$181M",
        "longPercent": 80,
        "profitUsers": 8107,
        "lossUsers": 13128,
        "sentiment": "bearish"
      }
    ],
    "totalWallets": 307456,
    "updatedAt": "2024-01-15T10:30:00Z"
  }
  ```

---

## ✅ WebSocket协议对齐

### 连接URL
- **URL**: `ws://localhost:8080/api/v1/ws` (完全符合前端规范)

### 消息格式
所有消息使用统一格式：
```json
{
  "type": "message_type",
  "payload": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 支持的频道
- `whale_activities`: 巨鲸活动更新
- `price_updates`: 价格更新（用于清算热力图）
- `long_short_ratio`: 多空比例更新

### 订阅消息 (Client → Server)
```json
{
  "type": "subscribe",
  "channels": ["whale_activities", "price_updates"],
  "filters": {
    "token": "BTC",
    "minValue": 1000000
  }
}
```

### 推送消息 (Server → Client)

#### 1. Whale Activity
```json
{
  "type": "whale_activity",
  "payload": {
    "time": "just now",
    "address": "0x49f3...8d2b",
    "token": "BTC",
    "value": 2567735.06,
    "side": "Long",
    "type": "Open",
    "amount": "28.40572 BTC",
    "timestamp": "2024-01-15T10:30:05Z",
    "txHash": "0xabc123..."
  },
  "timestamp": "2024-01-15T10:30:05Z"
}
```

#### 2. Price Update
```json
{
  "type": "price_update",
  "payload": {
    "token": "BTC",
    "currentPrice": 98450,
    "points": [
      {
        "price": 98450,
        "longVol": 860,
        "shortVol": 325,
        "current": true
      }
    ]
  },
  "timestamp": "2024-01-15T10:30:05Z"
}
```

#### 3. Long/Short Ratio Update
```json
{
  "type": "long_short_ratio",
  "payload": {
    "longPercent": 52.1,
    "shortPercent": 47.9,
    "longVolume": 2842000000,
    "shortVolume": 2618000000,
    "longChange24h": 5.3,
    "shortChange24h": 3.9
  },
  "timestamp": "2024-01-15T10:30:05Z"
}
```

### 心跳机制
- **Client → Server**: `{"type": "ping"}`
- **Server → Client**: `{"type": "pong", "payload": {}, "timestamp": "..."}`

---

## 🔄 向后兼容

保留了原有的API端点（前缀为 `/api/v1/liquidations`, `/api/v1/long-short-ratios` 等），以便逐步迁移。新的前端兼容端点优先级更高。

---

## 📝 注意事项

1. **数据格式化**:
   - 所有金额字段已格式化为前端期望的格式
   - 时间字段使用相对时间（如 "2 min ago"）和ISO时间戳
   - 地址已自动截断显示

2. **24小时变化**:
   - `longChange24h` 和 `shortChange24h` 当前从历史数据计算
   - 如果历史数据不足，返回0.0作为占位符

3. **Wallet Distribution**:
   - 如果数据库中没有持仓数据，会返回空的bucket数组
   - 用于开发和测试时可以提供mock数据

4. **WebSocket过滤**:
   - 支持按 `token`, `minValue`, `side`, `type` 过滤
   - 过滤逻辑在服务器端实现，确保只推送符合条件的数据

---

## 🚀 测试建议

1. **API测试**:
   ```bash
   # 测试清算热力图
   curl "http://localhost:8080/api/v1/market/liquidation?token=BTC&range=5"
   
   # 测试多空比例
   curl "http://localhost:8080/api/v1/market/long-short-ratio"
   
   # 测试巨鲸活动
   curl "http://localhost:8080/api/v1/whale/activities?limit=20"
   
   # 测试钱包分布
   curl "http://localhost:8080/api/v1/wallet/distribution"
   ```

2. **WebSocket测试**:
   - 使用浏览器开发者工具或WebSocket客户端工具
   - 连接到 `ws://localhost:8080/api/v1/ws`
   - 发送订阅消息测试推送功能

---

## ✅ 完成状态

- [x] 所有API端点路径对齐
- [x] 所有响应格式对齐TypeScript接口
- [x] WebSocket URL和协议对齐
- [x] 消息格式统一为 `{type, payload, timestamp}`
- [x] 频道名称对齐
- [x] 订阅和过滤逻辑实现
- [x] 数据格式化工具函数
- [x] 错误处理符合规范

---

**状态**: ✅ 完全对齐前端规范  
**可开始前端集成**: 是
