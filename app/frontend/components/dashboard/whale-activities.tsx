"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ExternalLink } from "lucide-react"
import { wsClient } from "@/lib/websocket"

/** whale_activity payload from backend WebSocket */
interface WhaleActivityPayload {
  token: string
  value: number
  side: string
  timestamp: string
  txHash?: string
}

/** 表格展示用的一行数据 */
interface WhaleRow {
  id: string
  time: string
  address: string
  token: string
  value: number
  side: string
  type: string
}

const MAX_ITEMS = 50

function formatTimeAgo(isoStr: string): string {
  try {
    const date = new Date(isoStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffSec = Math.floor(diffMs / 1000)
    const diffMin = Math.floor(diffSec / 60)
    const diffHr = Math.floor(diffMin / 60)

    if (diffSec < 60) return "just now"
    if (diffMin < 60) return `${diffMin} min ago`
    if (diffHr < 24) return `${diffHr} hr ago`
    return `${Math.floor(diffHr / 24)} day(s) ago`
  } catch {
    return isoStr
  }
}

function shortenHash(hash: string | undefined): string {
  if (!hash) return "—"
  if (hash.length <= 14) return hash
  return `${hash.slice(0, 6)}...${hash.slice(-4)}`
}

function payloadToRow(payload: WhaleActivityPayload): WhaleRow {
  const txHash = payload.txHash || ""
  return {
    id: txHash || `whale-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    time: formatTimeAgo(payload.timestamp),
    address: shortenHash(txHash),
    token: payload.token || "N/A",
    value: payload.value ?? 0,
    side: payload.side === "BUY" || payload.side?.toLowerCase() === "long" ? "Long" : payload.side === "SELL" || payload.side?.toLowerCase() === "short" ? "Short" : payload.side || "—",
    type: "Liquidation",
  }
}

export function WhaleActivities() {
  const [activities, setActivities] = useState<WhaleRow[]>([])
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    let unsubWhale: (() => void) | undefined
    let unsubConnected: (() => void) | undefined
    let unsubSubscribed: (() => void) | undefined

    const connectAndSubscribe = async () => {
      try {
        await wsClient.connect()
        setIsConnected(wsClient.isConnected())

        if (wsClient.isConnected()) {
          wsClient.subscribe(["whale_activities"])
        }
      } catch (err) {
        console.error("WhaleActivities: WebSocket connect failed", err)
      }
    }

    // 连接
    connectAndSubscribe()

    // 处理 whale_activity 消息
    unsubWhale = wsClient.onMessage("whale_activity", (msg) => {
      const payload = msg.payload as WhaleActivityPayload
      if (!payload) return
      const row = payloadToRow(payload)
      setActivities((prev) => [row, ...prev].slice(0, MAX_ITEMS))
    })

    // 连接状态（可选：connected 时自动订阅）
    unsubConnected = wsClient.onMessage("connected", () => {
      setIsConnected(true)
      wsClient.subscribe(["whale_activities"])
    })

    // 重连后可能需要重新订阅
    unsubSubscribed = wsClient.onMessage("subscribed", () => {
      setIsConnected(true)
    })

    return () => {
      unsubWhale?.()
      unsubConnected?.()
      unsubSubscribed?.()
      // 不在这里 disconnect，其他组件可能共用 wsClient
    }
  }, [])

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-3">
          <CardTitle className="text-zinc-100 text-lg font-medium">Real-time Whale Activities</CardTitle>
          <Badge
            variant="outline"
            className={
              isConnected
                ? "bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse"
                : "bg-zinc-500/10 text-zinc-400 border-zinc-500/30"
            }
          >
            <span className="relative flex h-2 w-2 mr-1.5">
              {isConnected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
              )}
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${isConnected ? "bg-rose-500" : "bg-zinc-500"}`}
              ></span>
            </span>
            {isConnected ? "Live" : "Connecting..."}
          </Badge>
        </div>
        <span className="text-xs text-zinc-500">
          {isConnected ? "WebSocket 实时推送" : "等待连接..."}
        </span>
      </CardHeader>
      <CardContent>
        <div className="rounded-lg border border-zinc-800 overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-400 font-medium">Timestamp</TableHead>
                <TableHead className="text-zinc-400 font-medium">Tx Hash</TableHead>
                <TableHead className="text-zinc-400 font-medium">Token</TableHead>
                <TableHead className="text-zinc-400 font-medium text-right">Value (USD)</TableHead>
                <TableHead className="text-zinc-400 font-medium">Side</TableHead>
                <TableHead className="text-zinc-400 font-medium">Type</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {activities.length === 0 ? (
                <TableRow className="border-zinc-800">
                  <TableCell colSpan={6} className="text-center text-zinc-500 py-8">
                    {isConnected
                      ? "暂无数据，等待 whale activity 推送..."
                      : "正在连接 WebSocket..."}
                  </TableCell>
                </TableRow>
              ) : (
                activities.map((tx) => (
                  <TableRow key={tx.id} className="border-zinc-800 hover:bg-zinc-800/50">
                    <TableCell className="text-zinc-400 text-sm">{tx.time}</TableCell>
                    <TableCell>
                      <button className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors text-sm font-mono">
                        {tx.address}
                        <ExternalLink className="h-3 w-3" />
                      </button>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                            tx.token === "BTC"
                              ? "bg-amber-500/20 text-amber-400"
                              : tx.token === "ETH"
                                ? "bg-blue-500/20 text-blue-400"
                                : "bg-purple-500/20 text-purple-400"
                          }`}
                        >
                          {tx.token.charAt(0)}
                        </div>
                        <span className="text-zinc-100 font-medium">{tx.token}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono text-zinc-100 font-medium">
                      $
                      {tx.value.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={
                          tx.side === "Long"
                            ? "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border-emerald-500/30"
                            : "bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border-rose-500/30"
                        }
                      >
                        {tx.side}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className="border-amber-500/30 text-amber-400"
                      >
                        {tx.type}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
