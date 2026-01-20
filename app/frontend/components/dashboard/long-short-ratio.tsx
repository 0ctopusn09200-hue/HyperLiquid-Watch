import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown } from "lucide-react"

export function LongShortRatio() {
  const longPercent = 52
  const shortPercent = 48

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
            <span className="text-sm font-semibold text-white">{longPercent}% Long</span>
            <span className="text-sm font-semibold text-white">{shortPercent}% Short</span>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-zinc-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="h-4 w-4 text-emerald-500" />
              <span className="text-xs text-zinc-400">Long Volume</span>
            </div>
            <p className="text-xl font-bold text-emerald-400">$2.84B</p>
            <p className="text-xs text-emerald-500/80">+5.2% (24h)</p>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <TrendingDown className="h-4 w-4 text-rose-500" />
              <span className="text-xs text-zinc-400">Short Volume</span>
            </div>
            <p className="text-xl font-bold text-rose-400">$2.62B</p>
            <p className="text-xs text-rose-500/80">+3.8% (24h)</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
