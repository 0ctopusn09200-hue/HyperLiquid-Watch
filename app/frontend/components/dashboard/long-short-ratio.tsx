"use client"

import { useEffect, useState } from "react"
import { wsClient } from "@/lib/websocket"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown } from "lucide-react"

export function LongShortRatio() {
  const [longPercent, setLongPercent] = useState<number>(50)
  const [shortPercent, setShortPercent] = useState<number>(50)
  const [longVolume, setLongVolume] = useState<number>(0)
  const [shortVolume, setShortVolume] = useState<number>(0)
  const [longChange, setLongChange] = useState<number>(0)
  const [shortChange, setShortChange] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        setError(null)

        // 使用真实后端接口：/api/v1/long-short-ratios/current
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"
        const res = await fetch(`${baseUrl}/api/v1/long-short-ratios/current`, {
          cache: "no-store",
        })
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`)
        }
        const json = (await res.json()) as {
          data?: { ratios?: Array<{ long_ratio: number; short_ratio: number }> }
        }

        const ratios = json.data?.ratios ?? []
        if (!ratios.length) {
          if (!cancelled) {
            setLongPercent(50)
            setShortPercent(50)
            setLongVolume(0)
            setShortVolume(0)
          }
          setLoading(false)
          return
        }

        // 简单做一个平均值聚合（没有绝对 volume，只能用比例）
        const avgLong = ratios.reduce((sum, r) => sum + (r.long_ratio ?? 0), 0) / ratios.length
        const avgShort = ratios.reduce((sum, r) => sum + (r.short_ratio ?? 0), 0) / ratios.length

        if (cancelled) return

        setLongPercent(avgLong * 100)
        setShortPercent(avgShort * 100)
        // 当前方案下拿不到真实 USD 体量，这里先置 0，仅显示比例
        setLongVolume(0)
        setShortVolume(0)
        setLongChange(0)
        setShortChange(0)
        setLoading(false)
      } catch (e: any) {
        if (cancelled) return
        setError(e?.message || e?.detail || "Failed to load")
        setLoading(false)
      }
    }

    load()
    const t = setInterval(load, 5000)
    
    // WebSocket subscription to receive realtime long/short ratio updates
    let unsubRatio: (() => void) | undefined
    let unsubConnected: (() => void) | undefined
    let unsubSubscribed: (() => void) | undefined

    const connectAndSubscribe = async () => {
      try {
        await wsClient.connect()
        if (wsClient.isConnected()) {
          wsClient.subscribe(["long_short_ratio"])
        }
      } catch (err) {
        console.error("LongShortRatio: WebSocket connect failed", err)
      }
    }

    connectAndSubscribe()

    unsubRatio = wsClient.onMessage("long_short_ratio", (msg) => {
      const payload: any = msg.payload
      if (!payload) return
      try {
        if (typeof payload.longPercent === "number") setLongPercent(payload.longPercent)
        if (typeof payload.shortPercent === "number") setShortPercent(payload.shortPercent)
        if (typeof payload.longVolume === "number") setLongVolume(payload.longVolume)
        if (typeof payload.shortVolume === "number") setShortVolume(payload.shortVolume)
        // Note: longChange/shortChange not provided by realtime broadcast currently
        setLoading(false)
      } catch (e) {
        // ignore malformed payload
      }
    })

    unsubConnected = wsClient.onMessage("connected", () => {
      if (wsClient.isConnected()) wsClient.subscribe(["long_short_ratio"])
    })
    unsubSubscribed = wsClient.onMessage("subscribed", () => {})
    return () => {
      cancelled = true
      clearInterval(t)
      unsubRatio?.()
      unsubConnected?.()
      unsubSubscribed?.()
    }
  }, [])

  const formatUsd = (v: number) =>
    v >= 1e9
      ? `$${(v / 1e9).toFixed(2)}B`
      : v >= 1e6
        ? `$${(v / 1e6).toFixed(2)}M`
        : `$${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}`

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-zinc-100 text-lg font-medium">Global Long/Short Ratio</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Large progress bar */}
        <div className="relative h-8 rounded-lg overflow-hidden bg-zinc-800">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-emerald-600 to-emerald-500 transition-all duration-500"
            style={{ width: `${longPercent}%` }}
          />
          <div
            className="absolute inset-y-0 right-0 bg-gradient-to-l from-rose-600 to-rose-500 transition-all duration-500"
            style={{ width: `${shortPercent}%` }}
          />
          {/* Labels on bar */}
          <div className="absolute inset-0 flex items-center justify-between px-3">
            <span className="text-sm font-semibold text-white">
              {longPercent.toFixed(2)}% Long
            </span>
            <span className="text-sm font-semibold text-white">
              {shortPercent.toFixed(2)}% Short
            </span>
          </div>
        </div>

        {error && (
          <div className="text-xs text-rose-400">
            Failed to load long/short ratio: {String(error)}
          </div>
        )}

        {/* Statistics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-zinc-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="h-4 w-4 text-emerald-500" />
              <span className="text-xs text-zinc-400">Long Volume</span>
            </div>
            <p className="text-xl font-bold text-emerald-400">
              {loading ? "--" : formatUsd(longVolume)}
            </p>
            <p className="text-xs text-emerald-500/80">
              {loading ? "" : `${longChange >= 0 ? "+" : ""}${longChange.toFixed(2)}% (24h)`}
            </p>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <TrendingDown className="h-4 w-4 text-rose-500" />
              <span className="text-xs text-zinc-400">Short Volume</span>
            </div>
            <p className="text-xl font-bold text-rose-400">
              {loading ? "--" : formatUsd(shortVolume)}
            </p>
            <p className="text-xs text-rose-500/80">
              {loading ? "" : `${shortChange >= 0 ? "+" : ""}${shortChange.toFixed(2)}% (24h)`}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
