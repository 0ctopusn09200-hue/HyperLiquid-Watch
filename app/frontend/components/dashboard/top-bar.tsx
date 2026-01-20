"use client"

import { Activity } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useState } from "react"

const timeframes = ["1H", "4H", "1D"]

export function TopBar() {
  const [activeTimeframe, setActiveTimeframe] = useState("4H")

  return (
    <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="flex items-center justify-between px-4 py-3">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <Activity className="h-6 w-6 text-emerald-500" />
          <span className="text-lg font-semibold tracking-tight">HyperLiquid Watch</span>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-6">
          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span className="text-sm text-zinc-400">Connected</span>
          </div>

          {/* Timeframe Selectors */}
          <div className="flex items-center gap-1 bg-zinc-900 rounded-lg p-1">
            {timeframes.map((tf) => (
              <Button
                key={tf}
                variant={activeTimeframe === tf ? "default" : "ghost"}
                size="sm"
                className={
                  activeTimeframe === tf
                    ? "bg-zinc-700 text-zinc-100 hover:bg-zinc-600"
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
                }
                onClick={() => setActiveTimeframe(tf)}
              >
                {tf}
              </Button>
            ))}
          </div>
        </div>
      </div>
    </header>
  )
}
