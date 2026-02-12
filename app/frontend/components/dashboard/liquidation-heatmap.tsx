"use client"

import { useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ZoomIn, ZoomOut } from "lucide-react"
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as ReTooltip,
  CartesianGrid,
  Legend,
} from "recharts"

type BarData = {
  price: number
  longVol: number
  shortVol: number
  current?: boolean
  longCount: number
  shortCount: number
}

type ApiPriceLevel = {
  price: number
  long_liquidation_value?: number
  short_liquidation_value?: number
  long_liquidation_count?: number
  short_liquidation_count?: number
}

type ApiResponse = {
  code: number
  message: string
  data: {
    coin: string
    timestamp: string
    window_seconds: number
    step: number
    price_levels: ApiPriceLevel[]
  }
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"
const API_PREFIX = "/api/v1"

function formatMoneyCompact(v: number) {
  if (!Number.isFinite(v)) return "$0"
  const abs = Math.abs(v)
  if (abs >= 1e9) return `$${(v / 1e9).toFixed(2)}B`
  if (abs >= 1e6) return `$${(v / 1e6).toFixed(2)}M`
  if (abs >= 1e3) return `$${(v / 1e3).toFixed(2)}K`
  return `$${v.toFixed(0)}`
}

export function LiquidationHeatmap() {
  const [hoveredBar, setHoveredBar] = useState<number | null>(null)

  // 先固定 BTC + 4.5% 范围，后面再接前端选择器
  const [token] = useState("BTC")
  const [rangePercent] = useState(4.5)

  const [bars, setBars] = useState<BarData[]>([])
  const [currentPrice, setCurrentPrice] = useState<number | null>(null)
  const [minPrice, setMinPrice] = useState<number | null>(null)
  const [maxPrice, setMaxPrice] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        setError(null)

        const url =
          `${API_BASE_URL}${API_PREFIX}/liquidation-map` +
          `?coin=${encodeURIComponent(token)}` +
          `&window_seconds=${encodeURIComponent(4 * 3600)}` +
          `&step=${encodeURIComponent(50)}`

        const res = await fetch(url, { cache: "no-store" })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const json = (await res.json()) as ApiResponse
        const levels = json?.data?.price_levels || []

        // 先按后端返回的有数据的 price_bucket 生成映射
        const mapped: BarData[] = levels.map((lv) => {
          const longValue = Number(lv.long_liquidation_value ?? 0)
          const shortValue = Number(lv.short_liquidation_value ?? 0)
          const longCount = Number(lv.long_liquidation_count ?? 0)
          const shortCount = Number(lv.short_liquidation_count ?? 0)

          // 如果金额很小/为 0，则退化为按笔数画高度，避免“看起来完全没柱子”
          const longVol = longValue > 0 ? longValue : longCount
          const shortVol = shortValue > 0 ? shortValue : shortCount

          return {
            price: Number(lv.price),
            longVol,
            shortVol,
            longCount,
            shortCount,
          }
        })

        // 根据最小/最大价格 + 步长，对价格轴做连续填充，让图看起来是完整热力图
        let filled: BarData[] = mapped
        if (mapped.length > 0) {
          const ps = mapped.map((b) => b.price).filter((p) => Number.isFinite(p))
          const localMin = Math.min(...ps)
          const localMax = Math.max(...ps)

          // 尝试从返回的 step 推断价格步长，回退到 50
          const rawStep = Number(json.data?.step ?? 50)
          const step = !Number.isFinite(rawStep) || rawStep <= 0 ? 50 : rawStep

          const byPrice = new Map<number, BarData>()
          mapped.forEach((b) => byPrice.set(b.price, b))

          const tmp: BarData[] = []
          // 从高到低填充所有 price 桶
          for (let p = localMax; p >= localMin; p -= step) {
            const rounded = Number(p.toFixed(2))
            const existing = byPrice.get(rounded)
            if (existing) {
              tmp.push(existing)
            } else {
              tmp.push({
                price: rounded,
                longVol: 0,
                shortVol: 0,
                longCount: 0,
                shortCount: 0,
              })
            }
          }
          filled = tmp

          // 计算“当前价”指示：用中位价匹配最近的桶
          const prices = filled.map((x) => x.price).filter((p) => Number.isFinite(p))
          const midPrice = prices.length > 0 ? prices[Math.floor(prices.length / 2)] : null

          const cp = currentPrice ?? midPrice
          if (cp != null) {
            let bestIdx = -1
            let bestDist = Number.POSITIVE_INFINITY
            filled.forEach((b, i) => {
              const d = Math.abs(b.price - cp)
              if (d < bestDist) {
                bestDist = d
                bestIdx = i
              }
            })
            if (bestIdx >= 0) filled[bestIdx].current = true
            setCurrentPrice(cp)
          }

          if (!cancelled) {
            setBars(filled)
            setMinPrice(localMin)
            setMaxPrice(localMax)
          }
        } else if (!cancelled) {
          // 完全没数据
          setBars([])
          setCurrentPrice(null)
          setMinPrice(null)
          setMaxPrice(null)
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.message || e?.detail || "Failed to load")
          setBars([])
          setCurrentPrice(null)
          setMinPrice(null)
          setMaxPrice(null)
        }
      }
    }

    load()
    const t = setInterval(load, 3000) // 每 3 秒刷新一次
    return () => {
      cancelled = true
      clearInterval(t)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [API_BASE_URL, token])

  const maxVol = useMemo(() => {
    if (bars.length === 0) return 1
    return Math.max(...bars.flatMap((d) => [d.longVol, d.shortVol, 1]))
  }, [bars])

  // 全局累计指标：累计清算强度（USD）+ 累计笔数
  const totals = useMemo(() => {
    return bars.reduce(
      (acc, b) => {
        acc.longValue += b.longVol
        acc.shortValue += b.shortVol
        acc.longCount += b.longCount
        acc.shortCount += b.shortCount
        return acc
      },
      { longValue: 0, shortValue: 0, longCount: 0, shortCount: 0 },
    )
  }, [bars])

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex flex-col gap-1">
          <CardTitle className="text-zinc-100 text-lg font-medium">Liquidation Map</CardTitle>
          <div className="flex flex-wrap gap-3 text-[11px] text-zinc-400">
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-sm bg-emerald-500" />
              <span>累计多单清算强度: </span>
              <span className="text-emerald-400 font-medium">
                {formatMoneyCompact(totals.longValue)}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-sm bg-rose-500" />
              <span>累计空单清算强度: </span>
              <span className="text-rose-400 font-medium">
                {formatMoneyCompact(totals.shortValue)}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full border border-emerald-400" />
              <span>多单笔数: </span>
              <span className="text-emerald-300 font-mono">
                {totals.longCount.toLocaleString()}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full border border-rose-400" />
              <span>空单笔数: </span>
              <span className="text-rose-300 font-mono">
                {totals.shortCount.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" className="h-8 w-8 border-zinc-700 bg-zinc-800 hover:bg-zinc-700">
            <ZoomIn className="h-4 w-4 text-zinc-400" />
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8 border-zinc-700 bg-zinc-800 hover:bg-zinc-700">
            <ZoomOut className="h-4 w-4 text-zinc-400" />
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {/* 顶部 price axis */}
        <div className="flex justify-between text-xs text-zinc-500 mb-2 px-1">
          <span>{minPrice != null ? `$${minPrice.toLocaleString()}` : "--"}</span>
          <span className="text-emerald-400 font-medium">
            Current: {currentPrice != null ? `$${currentPrice.toLocaleString()}` : "--"}
          </span>
          <span>{maxPrice != null ? `$${maxPrice.toLocaleString()}` : "--"}</span>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-2 text-xs text-rose-400">
            Failed to load liquidation map: {String(error)}
          </div>
        )}

        {/* Heatmap */}
        <div className="relative h-64 bg-zinc-950 rounded-lg p-4 overflow-hidden">
          {/* Grid lines */}
          <div className="absolute inset-4 flex flex-col justify-between pointer-events-none">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className="border-t border-zinc-800/50 w-full" />
            ))}
          </div>

          {/* Chart: Grouped Bar Chart using Recharts */}
          <div className="relative h-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={(bars || [])
                  .slice()
                  .sort((a, b) => a.price - b.price)
                  .map((d) => ({
                    price: d.price,
                    long: Number(d.longVol || 0),
                    short: Number(d.shortVol || 0),
                    longCount: d.longCount,
                    shortCount: d.shortCount,
                    current: d.current,
                  }))}
                margin={{ top: 6, right: 12, left: 6, bottom: 36 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#0f1720" />
                <XAxis
                  dataKey="price"
                  tickFormatter={(p) => {
                    const v = Number(p)
                    if (!Number.isFinite(v)) return String(p)
                    // show only integer ticks in thousands, e.g., 66.0, 67.0 (representing 66k, 67k)
                    const vK = v / 1000
                    if (Math.abs(vK - Math.round(vK)) < 1e-9) {
                      // display with one decimal as requested (e.g., 66.0)
                      return `${vK.toFixed(1)}`
                    }
                    // hide other intermediate ticks
                    return ""
                  }}
                  interval={0}
                  angle={-30}
                  textAnchor="end"
                  height={48}
                />
                <YAxis
                  tickFormatter={(v) => {
                    if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`
                    if (v >= 1e6) return `$${(v / 1e6).toFixed(2)}M`
                    if (v >= 1e3) return `$${(v / 1e3).toFixed(2)}K`
                    return `$${v}`
                  }}
                />
                <ReTooltip
                  formatter={(value: any, name: any, props: any) => {
                    const n = Number(value) || 0
                    return [`$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, name === 'long' ? '多头清算' : '空头清算']
                  }}
                  labelFormatter={(label) => `BTC $${Number(label).toLocaleString()}`}
                />
                <Legend
                  payload={[
                    { value: '多头清算：价格下跌到该点位时触发的爆仓', type: 'square', id: 'long', color: '#ef4444' },
                    { value: '空头清算：价格上涨到该点位时触发的爆仓', type: 'square', id: 'short', color: '#10b981' },
                  ]}
                />
                <Bar dataKey="long" name="多头清算" fill="#ef4444" />
                <Bar dataKey="short" name="空头清算" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>

            {/* 没数据时提示 */}
            {bars.length === 0 && !error && (
              <div className="absolute inset-0 flex items-center justify-center text-zinc-500 text-sm">
                Loading liquidation map...
              </div>
            )}
          </div>
        </div>

        {/* 底部 volume scale（示意用） */}
        <div className="flex justify-between text-xs text-zinc-500 mt-2 px-1">
          <span>Vol: $0</span>
          <span>{formatMoneyCompact(maxVol / 2)}</span>
          <span>{formatMoneyCompact(maxVol)}</span>
        </div>
      </CardContent>
    </Card>
  )
}
