"use client"

import { useEffect, useState } from "react"
import { wsClient } from "@/lib/websocket"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/api"
import type { WalletPositionBucket, WalletPositionDistributionResponse } from "@/lib/types/api"

function SplitBar({
  leftValue,
  rightValue,
  leftPercent,
  variant = "value",
}: {
  leftValue: string | number
  rightValue: string | number
  leftPercent: number
  variant?: "value" | "users"
}) {
  const rightPercent = 100 - leftPercent

  return (
    <div className="flex h-6 w-full overflow-hidden rounded text-[10px] font-semibold">
      <div
        className="flex items-center justify-center bg-emerald-500 text-white transition-all"
        style={{ width: `${leftPercent}%`, minWidth: leftPercent > 0 ? "40px" : "0" }}
      >
        {variant === "value" ? leftValue : leftValue.toLocaleString()}
      </div>
      <div
        className="flex items-center justify-center bg-rose-500 text-white transition-all"
        style={{ width: `${rightPercent}%`, minWidth: rightPercent > 0 ? "40px" : "0" }}
      >
        {variant === "value" ? rightValue : rightValue.toLocaleString()}
      </div>
    </div>
  )
}

export function WalletPositionDistribution() {
  const [buckets, setBuckets] = useState<WalletPositionBucket[]>([])
  const [totalWallets, setTotalWallets] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        setError(null)
        const data: WalletPositionDistributionResponse = await apiClient.getWalletDistribution()
        if (cancelled) return
        setBuckets(data.buckets || [])
        setTotalWallets(data.totalWallets || 0)
        setLoading(false)
      } catch (e: any) {
        if (cancelled) return
        setError(e?.message || e?.detail || "Failed to load")
        setLoading(false)
      }
    }

    load()
    const t = setInterval(load, 10000)
    
    // WebSocket: trigger reload when relevant realtime updates arrive
    let unsubPrice: (() => void) | undefined
    let unsubRatio: (() => void) | undefined
    let unsubConnected: (() => void) | undefined

    const connectAndSubscribe = async () => {
      try {
        await wsClient.connect()
        if (wsClient.isConnected()) {
          // Subscribe to price/ratio updates which may affect distribution view
          wsClient.subscribe(["price_updates", "long_short_ratio"])
        }
      } catch (err) {
        console.error("WalletPositionDistribution: WebSocket connect failed", err)
      }
    }

    connectAndSubscribe()

    unsubPrice = wsClient.onMessage("price_update", () => {
      // refresh distribution on any price update
      void load()
    })

    unsubRatio = wsClient.onMessage("long_short_ratio", () => {
      // refresh distribution when ratio updates
      void load()
    })

    unsubConnected = wsClient.onMessage("connected", () => {
      if (wsClient.isConnected()) wsClient.subscribe(["price_updates", "long_short_ratio"])
    })
    return () => {
      cancelled = true
      clearInterval(t)
      unsubPrice?.()
      unsubRatio?.()
      unsubConnected?.()
    }
  }, [])

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-zinc-100 text-lg font-medium">Hyperliquid 钱包仓位实时分布</CardTitle>
          <span className="text-[11px] text-zinc-500">
            {loading ? "Loading..." : `Total wallets: ${totalWallets.toLocaleString()}`}
          </span>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {error && (
          <div className="px-3 py-2 text-xs text-rose-400">
            Failed to load wallet distribution: {String(error)}
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-900/50">
                <th className="px-3 py-2.5 text-left font-medium text-zinc-400">Position Size</th>
                <th className="px-3 py-2.5 text-left font-medium text-zinc-400">Category</th>
                <th className="px-3 py-2.5 text-right font-medium text-zinc-400">Wallets</th>
                <th className="px-3 py-2.5 text-left font-medium text-zinc-400">Open Interest</th>
                <th className="px-3 py-2.5 text-left font-medium text-zinc-400">Long Value</th>
                <th className="px-3 py-2.5 text-left font-medium text-zinc-400">Short Value</th>
                <th className="px-3 py-2.5 text-left font-medium text-zinc-400">L/S Ratio</th>
                <th className="px-3 py-2.5 text-right font-medium text-zinc-400">In Profit</th>
                <th className="px-3 py-2.5 text-right font-medium text-zinc-400">In Loss</th>
                <th className="px-3 py-2.5 text-center font-medium text-zinc-400">Sentiment</th>
              </tr>
            </thead>
            <tbody>
              {buckets.map((row, index) => {
                const totalUsers = row.profitUsers + row.lossUsers
                const profitPercent = totalUsers > 0 ? Math.round((row.profitUsers / totalUsers) * 100) : 0
                return (
                  <tr
                    key={row.positionSize}
                    className={`border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors ${
                      index % 2 === 0 ? "bg-zinc-900/30" : ""
                    }`}
                  >
                    {/* Position Size */}
                    <td className="px-3 py-2.5 text-zinc-300 font-medium whitespace-nowrap">{row.positionSize}</td>

                    {/* Category */}
                    <td className="px-3 py-2.5">
                      <span className="text-amber-400 font-medium">{row.category}</span>
                    </td>

                    {/* Wallet Count */}
                    <td className="px-3 py-2.5 text-right text-zinc-300 font-mono">
                      {row.walletCount.toLocaleString()}
                    </td>

                    {/* Open Interest % */}
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-2">
                        <span className="text-zinc-400 text-[10px] w-12">{row.openInterestPercent.toFixed(2)}%</span>
                        <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden min-w-[60px]">
                          <div
                            className="h-full bg-sky-500 rounded-full transition-all"
                            style={{ width: `${row.openInterestPercent}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    {/* Long Value */}
                    <td className="px-3 py-2.5">
                      <span className="text-emerald-400 font-mono font-medium">
                        {row.longValue}
                      </span>
                    </td>

                    {/* Short Value */}
                    <td className="px-3 py-2.5">
                      <span className="text-rose-400 font-mono font-medium">
                        {row.shortValue}
                      </span>
                    </td>

                    {/* Long vs Short Split Bar */}
                    <td className="px-3 py-2.5 min-w-[140px]">
                      <SplitBar
                        leftValue={row.longValue}
                        rightValue={row.shortValue}
                        leftPercent={row.longPercent}
                        variant="value"
                      />
                    </td>

                    {/* Profit Users */}
                    <td className="px-3 py-2.5 text-right">
                      <span className="text-emerald-400 font-mono">{row.profitUsers.toLocaleString()}</span>
                    </td>

                    {/* Loss Users */}
                    <td className="px-3 py-2.5 text-right">
                      <span className="text-rose-400 font-mono">{row.lossUsers.toLocaleString()}</span>
                    </td>

                    {/* Sentiment */}
                    <td className="px-3 py-2.5 text-center">
                      <Badge
                        variant="outline"
                        className={`text-[10px] px-2 py-0.5 font-medium border-0 ${
                          row.sentiment === "bullish"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : row.sentiment === "bearish"
                              ? "bg-rose-500/20 text-rose-400"
                              : "bg-zinc-500/20 text-zinc-400"
                        }`}
                      >
                        {row.sentiment === "bullish" ? "Bullish" : row.sentiment === "bearish" ? "Bearish" : "Neutral"}
                      </Badge>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
