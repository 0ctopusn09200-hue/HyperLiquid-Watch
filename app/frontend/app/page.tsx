import { TopBar } from "@/components/dashboard/top-bar"
import { LiquidationHeatmap } from "@/components/dashboard/liquidation-heatmap"
import { LongShortRatio } from "@/components/dashboard/long-short-ratio"
import { WhaleActivities } from "@/components/dashboard/whale-activities"
import { WalletPositionDistribution } from "@/components/dashboard/wallet-position-distribution"

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <TopBar />

      <main className="p-4 space-y-4">
        {/* Main Grid: 65% / 35% */}
        <div className="grid grid-cols-1 lg:grid-cols-[65%_35%] gap-4">
          {/* Left Column - Liquidation Heatmap */}
          <LiquidationHeatmap />

          {/* Right Column - Ratio & Distribution */}
          <div className="space-y-4">
            <LongShortRatio />
            
          </div>
        </div>

        <WalletPositionDistribution />

        {/* Bottom Section - Full Width */}
        <WhaleActivities />
      </main>
    </div>
  )
}
