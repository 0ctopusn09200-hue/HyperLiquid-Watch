# API Specification

本文档定义了Backend模块提供的REST API接口规范。

**Base URL**: `http://localhost:8080/api/v1`

**Content-Type**: `application/json`

---

## 目录

- [通用规范](#通用规范)
- [清算事件API](#清算事件api)
- [多空比例API](#多空比例api)
- [清算地图API](#清算地图api)
- [交易记录API](#交易记录api)
- [巨鲸监控API](#巨鲸监控api)
- [错误码](#错误码)

---

## 通用规范

### 响应格式

所有API响应遵循以下格式：

#### 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": { ... },
  "timestamp": "2026-01-10T10:30:00Z"
}
```

#### 错误响应

```json
{
  "code": 400,
  "message": "Invalid parameter",
  "error": "coin parameter is required",
  "timestamp": "2026-01-10T10:30:00Z"
}
```

### 分页参数

支持分页的接口使用以下参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码，从1开始 |
| page_size | integer | 20 | 每页数量，最大100 |

分页响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ... ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

### 时间范围参数

| 参数 | 类型 | 格式 | 说明 |
|------|------|------|------|
| start_time | string | ISO 8601 | 开始时间（可选） |
| end_time | string | ISO 8601 | 结束时间（可选） |

---

## 清算事件API

### 1. 获取最近清算事件

**GET** `/liquidations/recent`

获取最近的清算事件列表。

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| coin | string | 否 | 交易对过滤（BTC, ETH等） |
| side | string | 否 | 方向过滤（LONG, SHORT） |
| limit | integer | 否 | 返回数量限制，默认20，最大100 |

**Response**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "liquidations": [
      {
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
    ]
  }
}
```

**Example**:

```
GET /api/v1/liquidations/recent?coin=BTC&side=LONG&limit=50
```

---

### 2. 查询清算事件（分页）

**GET** `/liquidations`

查询清算事件，支持分页和时间范围过滤。

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| coin | string | 否 | 交易对过滤 |
| side | string | 否 | 方向过滤 |
| start_time | string | 否 | 开始时间（ISO 8601） |
| end_time | string | 否 | 结束时间（ISO 8601） |
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |

**Response**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ... ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 150,
      "total_pages": 8
    }
  }
}
```

---

### 3. 获取清算统计

**GET** `/liquidations/stats`

获取清算统计数据。

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| coin | string | 否 | 交易对过滤 |
| start_time | string | 否 | 开始时间 |
| end_time | string | 否 | 结束时间 |

**Response**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_liquidations": 1250,
    "total_liquidation_value_usd": "125000000.50000000",
    "long_liquidations": 750,
    "long_liquidation_value_usd": "75000000.30000000",
    "short_liquidations": 500,
    "short_liquidation_value_usd": "50000000.20000000",
    "by_coin": {
      "BTC": {
        "count": 600,
        "value_usd": "60000000.00000000"
      },
      "ETH": {
        "count": 650,
        "value_usd": "65000000.50000000"
      }
    }
  }
}
```

---

## 多空比例API

### 1. 获取当前多空比例

**GET** `/long-short-ratios/current`

获取所有交易对的当前多空比例。

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| coin | string | 否 | 指定交易对，不传则返回所有 |

**Response**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "ratios": [
      {
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
    ]
  }
}
```

---

### 2. 获取多空比例历史数据

**GET** `/long-short-ratios/history`

获取多空比例的历史数据。

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| coin | string | 是 | 交易对 |
| start_time | string | 否 | 开始时间 |
| end_time | string | 否 | 结束时间 |
| interval | string | 否 | 时间间隔：1m, 5m, 15m, 1h, 1d，默认1h |
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |

**Response**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ... ],
    "pagination": { ... }
  }
}
```

---

## 清算地图API

### 1. 获取清算地图

**GET** `/liquidation-map`

获取指定交易对的清算地图数据。

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| coin | string | 是 | 交易对 |
| timestamp | string | 否 | 指定时间点，不传则返回最新 |
| price_range | string | 否 | 价格范围，格式：min,max |

**Response**:

```json
{
  "code": 200,
  "message": "success",
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

---

## 交易记录API

### 1. 查询交易记录

**GET** `/transactions`

查询交易记录。

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_address | string | 否 | 用户地址过滤 |
| coin | string | 否 | 交易对过滤 |
| side | string | 否 | 方向过滤 |
| tx_type | string | 否 | 交易类型过滤 |
| start_time | string | 否 | 开始时间 |
| end_time | string | 否 | 结束时间 |
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |

**Response**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ... ],
    "pagination": { ... }
  }
}
```

---

### 2. 获取交易详情

**GET** `/transactions/{tx_hash}`

根据交易哈希获取交易详情。

**Response**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
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
    "raw_data": { ... }
  }
}
```

---

## 巨鲸监控API

### 1. 获取监控列表

**GET** `/whales`

获取所有被监控的巨鲸地址列表。

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_active | boolean | 否 | 是否仅返回活跃的 |

**Response**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "whales": [
      {
        "id": 1,
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "alias": "Whale #1",
        "description": "Large BTC holder",
        "is_active": true,
        "created_at": "2026-01-10T10:00:00Z"
      }
    ]
  }
}
```

---

### 2. 添加监控地址

**POST** `/whales`

添加新的巨鲸监控地址。

**Request Body**:

```json
{
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "alias": "Whale #1",
  "description": "Large BTC holder"
}
```

**Response**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "alias": "Whale #1",
    "is_active": true
  }
}
```

---

### 3. 获取巨鲸活动

**GET** `/whales/{whale_id}/activities`

获取指定巨鲸的活动记录。

**Query Parameters**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_time | string | 否 | 开始时间 |
| end_time | string | 否 | 结束时间 |
| activity_type | string | 否 | 活动类型过滤 |
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |

**Response**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ... ],
    "pagination": { ... }
  }
}
```

---

## 错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 200 | 200 | 成功 |
| 400 | 400 | 请求参数错误 |
| 404 | 404 | 资源不存在 |
| 500 | 500 | 服务器内部错误 |

---

## 版本信息

- **Version**: 1.0
- **Last Updated**: 2026-01-10
- **Author**: @zhang_yunan
