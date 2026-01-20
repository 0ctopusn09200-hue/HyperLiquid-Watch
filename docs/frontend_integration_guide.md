# Frontend集成指南

本文档说明如何将前端组件与后端API集成。

## 已完成的工作

### ✅ 1. API客户端 (`lib/api.ts`)
- 完整的REST API客户端
- 错误处理
- TypeScript类型支持

### ✅ 2. WebSocket客户端 (`lib/websocket.ts`)
- 自动重连机制
- 心跳保持
- 消息订阅管理

### ✅ 3. TypeScript类型定义 (`lib/types/api.ts`)
- 完全匹配后端响应格式
- 与前端规范对齐

### ✅ 4. 配置文件
- `next.config.mjs`: 支持standalone模式和环境变量
- `Dockerfile`: 多阶段构建优化
- `.env.example`: 环境变量模板
- `docker-compose.yml`: 已添加frontend服务

## 下一步：更新组件使用真实API

### 组件更新清单

- [ ] `components/dashboard/liquidation-heatmap.tsx`
- [ ] `components/dashboard/long-short-ratio.tsx`
- [ ] `components/dashboard/whale-activities.tsx`
- [ ] `components/dashboard/wallet-position-distribution.tsx`

### 更新示例

#### 1. Liquidation Heatmap组件

```typescript
"use client";

import { useEffect, useState } from "react";
import { apiClient, wsClient } from "@/lib/api";
import type { LiquidationHeatmapResponse } from "@/lib/types/api";

export function LiquidationHeatmap() {
  const [data, setData] = useState<LiquidationHeatmapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState("BTC");

  // 初始加载
  useEffect(() => {
    async function fetchData() {
      try {
        const result = await apiClient.getLiquidationHeatmap(token, 4.5);
        setData(result);
      } catch (error) {
        console.error("Failed to fetch liquidation heatmap:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [token]);

  // WebSocket实时更新
  useEffect(() => {
    wsClient.connect();
    
    wsClient.subscribe(["price_updates"], { token });
    
    const unsubscribe = wsClient.onMessage("price_update", (message) => {
      if (message.payload.token === token) {
        setData({
          token: message.payload.token,
          currentPrice: message.payload.currentPrice,
          points: message.payload.points,
          minPrice: Math.min(...message.payload.points.map(p => p.price)),
          maxPrice: Math.max(...message.payload.points.map(p => p.price)),
        });
      }
    });

    return () => {
      unsubscribe();
    };
  }, [token]);

  if (loading || !data) return <div>Loading...</div>;

  // 使用data渲染图表...
}
```

#### 2. Long/Short Ratio组件

```typescript
"use client";

import { useEffect, useState } from "react";
import { apiClient, wsClient } from "@/lib/api";
import type { LongShortRatioResponse } from "@/lib/types/api";

export function LongShortRatio() {
  const [data, setData] = useState<LongShortRatioResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const result = await apiClient.getLongShortRatio();
        setData(result);
      } catch (error) {
        console.error("Failed to fetch ratio:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // WebSocket实时更新
  useEffect(() => {
    wsClient.connect();
    
    wsClient.subscribe(["long_short_ratio"]);
    
    const unsubscribe = wsClient.onMessage("long_short_ratio", (message) => {
      setData({
        ...message.payload,
        updatedAt: message.timestamp,
      });
    });

    return () => {
      unsubscribe();
    };
  }, []);

  if (loading || !data) return <div>Loading...</div>;

  return (
    // 使用data.longPercent, data.shortPercent等渲染...
  );
}
```

#### 3. Whale Activities组件

```typescript
"use client";

import { useEffect, useState } from "react";
import { apiClient, wsClient } from "@/lib/api";
import type { WhaleTransaction } from "@/lib/types/api";

export function WhaleActivities() {
  const [transactions, setTransactions] = useState<WhaleTransaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const result = await apiClient.getWhaleActivities({ limit: 10 });
        setTransactions(result.transactions);
      } catch (error) {
        console.error("Failed to fetch activities:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // WebSocket实时更新
  useEffect(() => {
    wsClient.connect();
    
    wsClient.subscribe(["whale_activities"], { minValue: 1000000 });
    
    const unsubscribe = wsClient.onMessage("whale_activity", (message) => {
      setTransactions((prev) => [message.payload, ...prev].slice(0, 10));
    });

    return () => {
      unsubscribe();
    };
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    // 渲染transactions列表...
  );
}
```

## 测试步骤

1. **启动后端服务**
```bash
cd app
docker-compose up -d backend postgres kafka
```

2. **启动前端开发服务器**
```bash
cd app/frontend
npm run dev
```

3. **测试API连接**
- 打开浏览器开发者工具
- 检查Network标签页的API请求
- 确认WebSocket连接成功

4. **验证数据流**
- 确认组件正确显示数据
- 测试WebSocket实时更新
- 检查错误处理

## 注意事项

1. **错误处理**: 所有API调用都应该有try-catch错误处理
2. **加载状态**: 显示loading状态提升用户体验
3. **WebSocket清理**: 组件卸载时记得断开WebSocket连接
4. **环境变量**: 确保 `.env.local` 配置正确
5. **CORS**: 开发环境需要确保后端CORS配置允许前端域名

## 完成状态

- [x] API客户端实现
- [x] WebSocket客户端实现
- [x] TypeScript类型定义
- [x] Docker配置
- [x] 环境变量配置
- [ ] 组件集成真实API（待完成）

---

**下一步**: 按照上述示例更新各个组件，将mock数据替换为真实API调用。
