import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface WalletData {
  positionSize: string
  category: string
  categoryEn: string
  walletCount: number
  openInterestPercent: number
  longValue: string
  shortValue: string
  longPercent: number
  profitUsers: number
  lossUsers: number
  sentiment: "bullish" | "bearish" | "neutral"
}

const walletData: WalletData[] = [
  {
    positionSize: "$0 - $250",
    category: "Shrimp",
    categoryEn: "Shrimp",
    walletCount: 245912,
    openInterestPercent: 8.64,
    longValue: "$717M",
    shortValue: "$181M",
    longPercent: 80,
    profitUsers: 8107,
    lossUsers: 13128,
    sentiment: "bearish",
  },
  {
    positionSize: "$250 - $1K",
    category: "Fish",
    categoryEn: "Fish",
    walletCount: 44488,
    openInterestPercent: 52.21,
    longValue: "$1.21B",
    shortValue: "$401M",
    longPercent: 75,
    profitUsers: 10644,
    lossUsers: 13625,
    sentiment: "bearish",
  },
  {
    positionSize: "$1K - $5K",
    category: "Dolphin",
    categoryEn: "Dolphin",
    walletCount: 7407,
    openInterestPercent: 62.42,
    longValue: "$2.09B",
    shortValue: "$801M",
    longPercent: 72,
    profitUsers: 2080,
    lossUsers: 2544,
    sentiment: "bearish",
  },
  {
    positionSize: "$5K - $10K",
    category: "Shark",
    categoryEn: "Shark",
    walletCount: 1755,
    openInterestPercent: 65.3,
    longValue: "$1.44B",
    shortValue: "$499M",
    longPercent: 74,
    profitUsers: 529,
    lossUsers: 619,
    sentiment: "bearish",
  },
  {
    positionSize: "$10K - $50K",
    category: "Small Whale",
    categoryEn: "Small Whale",
    walletCount: 2062,
    openInterestPercent: 72.9,
    longValue: "$4.77B",
    shortValue: "$4.04B",
    longPercent: 54,
    profitUsers: 802,
    lossUsers: 701,
    sentiment: "bullish",
  },
  {
    positionSize: "$50K - $100K",
    category: "Whale",
    categoryEn: "Whale",
    walletCount: 346,
    openInterestPercent: 78.33,
    longValue: "$2.21B",
    shortValue: "$2.56B",
    longPercent: 46,
    profitUsers: 150,
    lossUsers: 108,
    sentiment: "bullish",
  },
  {
    positionSize: "$100K - $1M",
    category: "Humpback",
    categoryEn: "Humpback",
    walletCount: 392,
    openInterestPercent: 82.15,
    longValue: "$7.19B",
    shortValue: "$9.10B",
    longPercent: 44,
    profitUsers: 186,
    lossUsers: 136,
    sentiment: "bullish",
  },
  {
    positionSize: "$1M - $50M",
    category: "Giant",
    categoryEn: "Giant",
    walletCount: 94,
    openInterestPercent: 87.24,
    longValue: "$17.31B",
    shortValue: "$19.01B",
    longPercent: 48,
    profitUsers: 55,
    lossUsers: 27,
    sentiment: "bullish",
  },
]

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
  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="pb-3">
        <CardTitle className="text-zinc-100 text-lg font-medium">Hyperliquid 钱包仓位实时分布</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
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
              {walletData.map((row, index) => {
                const profitPercent = Math.round((row.profitUsers / (row.profitUsers + row.lossUsers)) * 100)
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
                      <span className="text-emerald-400 font-mono font-medium">{row.longValue}</span>
                    </td>

                    {/* Short Value */}
                    <td className="px-3 py-2.5">
                      <span className="text-rose-400 font-mono font-medium">{row.shortValue}</span>
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
