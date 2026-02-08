"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ZoomIn, ZoomOut } from "lucide-react"
import { useState, useEffect } from "react"
import { apiClient } from "@/lib/api"
import type { LiquidationHeatmapResponse } from "@/lib/types/api"
import { Skeleton } from "@/components/ui/skeleton"
import { wsClient } from "@/lib/websocket"

export function LiquidationHeatmap() {
  const [hoveredBar, setHoveredBar] = useState<number | null>(null)
  const [data, setData] = useState<LiquidationHeatmapResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string>("")

  // Fetch initial data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        // Use smaller range (0.5%) to get more price levels for denser heatmap
        const response = await apiClient.getLiquidationHeatmap("BTC", 0.5)
        setData(response as any)
        setLastUpdate(new Date().toLocaleTimeString())
      } catch (err: any) {
        console.error("Failed to fetch liquidation heatmap:", err)
        setError(err.message || "Failed to load data")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    // Poll every 10 seconds
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  // WebSocket subscription for real-time updates
  useEffect(() => {
    let unsubscribe: (() => void) | null = null

    const startWs = async () => {
      try {
        await wsClient.connect()
        wsClient.subscribe(["liquidation_map"], { token: "BTC", range: 0.5 })

        unsubscribe = wsClient.onMessage("liquidation_map", (msg) => {
          try {
            const payload: any = msg.payload || {}
            const priceLevels = payload.price_levels || []
            const points = priceLevels.map((lvl: any) => {
              const longVal = Number(lvl.long_liquidation_value) || 0
              const shortVal = Number(lvl.short_liquidation_value) || 0
              return {
                price: Number(lvl.price) || 0,
                longVol: longVal,
                shortVol: shortVal,
                current: false,
              }
            })

            const dataObj: any = {
              token: payload.coin || "BTC",
              currentPrice: payload.currentPrice || (data?.currentPrice ?? 0),
              points,
              minPrice: points.length ? Math.min(...points.map((p: any) => p.price)) : 0,
              maxPrice: points.length ? Math.max(...points.map((p: any) => p.price)) : 0,
            }

            if (points.length > 0) {
              setData(dataObj)
              setLastUpdate(new Date().toLocaleTimeString())
            }
          } catch (e) {
            console.error("Failed to apply websocket update:", e)
          }
        })
      } catch (e) {
        console.error("WebSocket failed:", e)
      }
    }

    startWs()

    return () => {
      if (unsubscribe) unsubscribe()
      try {
        wsClient.unsubscribe(["liquidation_map"])
      } catch (e) {
        // ignore
      }
    }
  }, [data?.currentPrice])

  const liquidationData = data?.points || []
  const maxVol = liquidationData.length > 0
    ? Math.max(...liquidationData.flatMap((d) => [d.longVol, d.shortVol]))
    : 0

  // Mark current price point and filter out zero-volume current price points
  const dataWithCurrent = liquidationData
    .map((d) => ({
      ...d,
      current: Math.abs(d.price - (data?.currentPrice ?? 0)) < 100,
    }))
    .filter((d) => {
      // Keep all points except the current price point if it has zero volume
      if (d.current && d.longVol === 0 && d.shortVol === 0) {
        return false
      }
      return true
    })

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-zinc-100 text-lg font-medium">Liquidation Map</CardTitle>
          <p className="text-xs text-zinc-500 mt-1">Updated: {lastUpdate} • Data from: {data?.token || "..."}</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-4 mr-4 text-xs">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm bg-emerald-500" />
              <span className="text-zinc-400">Long Liquidations</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm bg-rose-500" />
              <span className="text-zinc-400">Short Liquidations</span>
            </div>
          </div>
          <Button variant="outline" size="icon" className="h-8 w-8 border-zinc-700 bg-zinc-800 hover:bg-zinc-700">
            <ZoomIn className="h-4 w-4 text-zinc-400" />
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8 border-zinc-700 bg-zinc-800 hover:bg-zinc-700">
            <ZoomOut className="h-4 w-4 text-zinc-400" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-64 w-full bg-zinc-800" />
          </div>
        ) : error ? (
          <div className="text-center py-8 text-zinc-400">
            <p>Error: {error}</p>
          </div>
        ) : liquidationData.length === 0 ? (
          <div className="text-center py-8 text-zinc-400">
            <p>No liquidation data available</p>
          </div>
        ) : (
          <>
            {/* Current price display */}
            <div className="mb-4 flex justify-between items-center">
              <div className="text-sm text-zinc-400">
                Current: <span className="text-emerald-400 font-bold text-lg">${data?.currentPrice?.toLocaleString() || "0"}</span>
              </div>
              <div className="text-xs text-zinc-500">
                Price Range: ${data?.minPrice?.toLocaleString()} - ${data?.maxPrice?.toLocaleString()}
              </div>
            </div>

            {/* Heatmap visualization with Y-axis */}
            <div className="relative bg-zinc-950 rounded-lg border border-zinc-800 overflow-hidden">
              <div className="flex" style={{ height: "280px" }}>
                {/* Y-axis labels */}
                <div className="w-16 flex flex-col justify-between py-4 px-2 text-xs text-zinc-500 border-r border-zinc-800 flex-shrink-0">
                  {[1, 0.75, 0.5, 0.25, 0].map((ratio) => (
                    <span key={ratio} className="text-right">
                      ${(maxVol * ratio).toFixed(0)}M
                    </span>
                  ))}
                </div>

                {/* Chart area */}
                <div className="flex-1 relative p-4 overflow-x-auto">
                  {/* Grid lines */}
                  <div className="absolute inset-4 flex flex-col justify-between pointer-events-none">
                    {[0, 1, 2, 3, 4].map((i) => (
                      <div key={i} className="border-t border-zinc-800/30 w-full" />
                    ))}
                  </div>

                  {/* Bars */}
                  <div className="relative h-full flex items-end gap-0.5 px-2">
                    {dataWithCurrent.map((data, idx) => {
                      const longHeight = (data.longVol / maxVol) * 100
                      const shortHeight = (data.shortVol / maxVol) * 100
                      const totalHeight = Math.max(longHeight + shortHeight, 2) // Min 2% height

                      return (
                        <div
                          key={idx}
                          className="flex-1 flex flex-col items-center justify-end relative group cursor-pointer"
                          style={{ height: "100%" }}
                          onMouseEnter={() => setHoveredBar(idx)}
                          onMouseLeave={() => setHoveredBar(null)}
                        >
                          {/* Stacked bars */}
                          <div
                            className="w-full flex flex-col rounded overflow-hidden"
                            style={{ height: `${totalHeight}%`, minHeight: "4px" }}
                          >
                            {/* Long bar (bottom) */}
                            {longHeight > 0 ? (
                              <div
                                className={`w-full transition-all duration-150 ${
                                  data.current ? "bg-emerald-400" : "bg-emerald-500/80 group-hover:bg-emerald-400"
                                }`}
                                style={{ 
                                  height: `${(longHeight / Math.max(longHeight + shortHeight, 1)) * 100}%`,
                                  flex: 1
                                }}
                              />
                            ) : null}

                            {/* Short bar (top) */}
                            {shortHeight > 0 ? (
                              <div
                                className={`w-full transition-all duration-150 ${
                                  data.current ? "bg-rose-400" : "bg-rose-500/80 group-hover:bg-rose-400"
                                }`}
                                style={{ 
                                  height: `${(shortHeight / Math.max(longHeight + shortHeight, 1)) * 100}%`,
                                  flex: 1
                                }}
                              />
                            ) : null}
                          </div>

                          {/* Current price indicator */}
                          {data.current && (
                            <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-yellow-400 ring-2 ring-yellow-400/30 z-10" />
                          )}

                          {/* Tooltip on hover */}
                          {hoveredBar === idx && (
                            <div className="absolute -top-28 left-1/2 -translate-x-1/2 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 z-20 whitespace-nowrap shadow-lg">
                              <p className="text-xs font-bold text-zinc-100 mb-1">Price: ${data.price.toLocaleString()}</p>
                              <p className="text-xs text-emerald-400 font-medium">
                                Long: ${data.longVol.toFixed(2)}M
                              </p>
                              <p className="text-xs text-rose-400 font-medium">
                                Short: ${data.shortVol.toFixed(2)}M
                              </p>
                              <p className="text-xs text-zinc-400 mt-1">Total: ${(data.longVol + data.shortVol).toFixed(2)}M</p>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>

              {/* X-axis with detailed price labels */}
              <div className="border-t border-zinc-800 px-4 py-2 overflow-x-auto">
                <div className="flex gap-0 text-xs text-zinc-500 min-w-max">
                  {dataWithCurrent.map((data, idx) => {
                    // Show labels every N points to avoid crowding
                    const step = Math.max(5, Math.floor(dataWithCurrent.length / 20))
                    const shouldShow = idx % step === 0 || idx === dataWithCurrent.length - 1
                    return (
                      <div key={idx} className="text-center flex-1 px-0.5 min-w-0">
                        {shouldShow && (
                          <span className="font-medium text-xs">${(data.price / 1000).toFixed(1)}k</span>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Volume legend */}
            <div className="flex justify-between text-xs text-zinc-500 mt-3 px-1">
              <span>$0M</span>
              <span>${maxVol.toFixed(0)}M (max)</span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
