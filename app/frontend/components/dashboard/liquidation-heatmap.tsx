"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ZoomIn, ZoomOut } from "lucide-react"
import { useState } from "react"

// Mock data for liquidation bars
const liquidationData = [
  { price: 94000, longVol: 120, shortVol: 80 },
  { price: 94500, longVol: 200, shortVol: 150 },
  { price: 95000, longVol: 350, shortVol: 280 },
  { price: 95500, longVol: 180, shortVol: 420 },
  { price: 96000, longVol: 280, shortVol: 320 },
  { price: 96500, longVol: 450, shortVol: 180 },
  { price: 97000, longVol: 380, shortVol: 250 },
  { price: 97500, longVol: 520, shortVol: 180 },
  { price: 98000, longVol: 680, shortVol: 420 },
  { price: 98400, longVol: 850, shortVol: 320, current: true },
  { price: 98800, longVol: 420, shortVol: 580 },
  { price: 99200, longVol: 280, shortVol: 750 },
  { price: 99600, longVol: 180, shortVol: 620 },
  { price: 100000, longVol: 350, shortVol: 480 },
  { price: 100500, longVol: 220, shortVol: 380 },
  { price: 101000, longVol: 150, shortVol: 520 },
  { price: 101500, longVol: 180, shortVol: 280 },
  { price: 102000, longVol: 120, shortVol: 450 },
]

export function LiquidationHeatmap() {
  const [hoveredBar, setHoveredBar] = useState<number | null>(null)
  const maxVol = Math.max(...liquidationData.flatMap((d) => [d.longVol, d.shortVol]))

  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-zinc-100 text-lg font-medium">Liquidation Map</CardTitle>
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
        {/* Price axis label */}
        <div className="flex justify-between text-xs text-zinc-500 mb-2 px-1">
          <span>$94,000</span>
          <span className="text-emerald-400 font-medium">Current: $98,400</span>
          <span>$102,000</span>
        </div>

        {/* Heatmap visualization */}
        <div className="relative h-64 bg-zinc-950 rounded-lg p-4 overflow-hidden">
          {/* Grid lines */}
          <div className="absolute inset-4 flex flex-col justify-between pointer-events-none">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className="border-t border-zinc-800/50 w-full" />
            ))}
          </div>

          {/* Liquidation bars */}
          <div className="relative h-full flex items-end justify-between gap-1">
            {liquidationData.map((data, idx) => {
              const longHeight = (data.longVol / maxVol) * 100
              const shortHeight = (data.shortVol / maxVol) * 100

              return (
                <div
                  key={idx}
                  className="flex-1 flex flex-col items-center gap-0.5 relative group cursor-pointer"
                  onMouseEnter={() => setHoveredBar(idx)}
                  onMouseLeave={() => setHoveredBar(null)}
                >
                  {/* Short bar (top) */}
                  <div
                    className={`w-full rounded-t transition-all duration-200 ${
                      data.current ? "bg-rose-400" : "bg-rose-500/70 group-hover:bg-rose-500"
                    }`}
                    style={{ height: `${shortHeight * 0.45}%` }}
                  />

                  {/* Current price indicator */}
                  {data.current && (
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 w-0.5 h-full bg-yellow-400/50 z-10" />
                  )}

                  {/* Long bar (bottom) */}
                  <div
                    className={`w-full rounded-b transition-all duration-200 ${
                      data.current ? "bg-emerald-400" : "bg-emerald-500/70 group-hover:bg-emerald-500"
                    }`}
                    style={{ height: `${longHeight * 0.45}%` }}
                  />

                  {/* Tooltip */}
                  {hoveredBar === idx && (
                    <div className="absolute -top-16 left-1/2 -translate-x-1/2 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 z-20 whitespace-nowrap shadow-xl">
                      <p className="text-xs font-medium text-zinc-100">Price: ${data.price.toLocaleString()}</p>
                      <p className="text-xs text-emerald-400">Long: ${(data.longVol * 10000).toLocaleString()}</p>
                      <p className="text-xs text-rose-400">Short: ${(data.shortVol * 10000).toLocaleString()}</p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Volume scale */}
        <div className="flex justify-between text-xs text-zinc-500 mt-2 px-1">
          <span>Vol: $0</span>
          <span>$5M</span>
          <span>$10M</span>
        </div>
      </CardContent>
    </Card>
  )
}
