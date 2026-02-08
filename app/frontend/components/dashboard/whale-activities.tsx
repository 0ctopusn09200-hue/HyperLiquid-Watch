"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ExternalLink } from "lucide-react"

const whaleData = [
  {
    time: "2 min ago",
    address: "0x49f3a1a6b47ecb59d0da5b5b87b7e5e1d8d2b8d",
    token: "BTC",
    value: 2567735.06,
    side: "Long",
    type: "Open",
    amount: "28.40572 BTC",
  },
  {
    time: "5 min ago",
    address: "0x69c2b4d5f7e8a3c1b6d9e2f4a8c7d1e5f07a1bc",
    token: "ETH",
    value: 1378665.67,
    side: "Short",
    type: "Open",
    amount: "-403.1808 ETH",
  },
  {
    time: "12 min ago",
    address: "0x7e4a5b3c2d1e9f8a7b6c5d4e3f2a1b0c9d8e7fd92",
    token: "ETH",
    value: 1545200.0,
    side: "Long",
    type: "Open",
    amount: "500.0000 ETH",
  },
  {
    time: "18 min ago",
    address: "0xf4d8c7b6a5e9d2c1f3e8a7b6c5d4e3f2a1b0c9d5f1c",
    token: "HYPE",
    value: 1705680.0,
    side: "Long",
    type: "Close",
    amount: "-60,000.00 HYPE",
  },
  {
    time: "25 min ago",
    address: "0xec3b1a2d9c8e7f6a5b4c3d2e1f0a9b8c7d6e5f4b5d",
    token: "BTC",
    value: 1019044.89,
    side: "Long",
    type: "Open",
    amount: "11.28273 BTC",
  },
  {
    time: "32 min ago",
    address: "0xec7f5b9a1e8d3c7b2a9f4e6d5c1b8a3f7e2d9c5b91",
    token: "BTC",
    value: 1018875.65,
    side: "Long",
    type: "Open",
    amount: "11.28273 BTC",
  },
  {
    time: "45 min ago",
    address: "0x0a2c7b3e1f9d8a6c5b4e7d2a9f3c1b6e8d2f5a4532",
    token: "BTC",
    value: 7947647.29,
    side: "Long",
    type: "Open",
    amount: "88.92961 BTC",
  },
  {
    time: "1 hr ago",
    address: "0x9c8e1b7a3f6d2e5c9a8b7c6d5e4f3a2b1c0d9e8f94f2",
    token: "ETH",
    value: 4172923.45,
    side: "Short",
    type: "Open",
    amount: "-1,347.7129 ETH",
  },
  {
    time: "1.5 hr ago",
    address: "0x41b7e3d9c5f2a8e1b6d4c7a9f3e2c5b8a1d4e7f9ee83",
    token: "ETH",
    value: 1060360.33,
    side: "Long",
    type: "Close",
    amount: "342.5711 ETH",
  },
  {
    time: "2 hr ago",
    address: "0xd2f1c8e5a3b9d6f1c4e7a2b5d8c3f6a9e1b4d7f03a8c",
    token: "BTC",
    value: 890420.15,
    side: "Short",
    type: "Open",
    amount: "-9.8421 BTC",
  },
]

export function WhaleActivities() {
  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-3">
          <CardTitle className="text-zinc-100 text-lg font-medium">Real-time Whale Activities</CardTitle>
          <Badge variant="outline" className="bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse">
            <span className="relative flex h-2 w-2 mr-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
            </span>
            Live
          </Badge>
        </div>
        <span className="text-xs text-zinc-500">Updated every 30s</span>
      </CardHeader>
      <CardContent>
        <div className="rounded-lg border border-zinc-800 overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-400 font-medium">Timestamp</TableHead>
                <TableHead className="text-zinc-400 font-medium min-w-[240px]">Address</TableHead>
                <TableHead className="text-zinc-400 font-medium">Token</TableHead>
                <TableHead className="text-zinc-400 font-medium text-right">Value (USD)</TableHead>
                <TableHead className="text-zinc-400 font-medium">Amount</TableHead>
                <TableHead className="text-zinc-400 font-medium">Side</TableHead>
                <TableHead className="text-zinc-400 font-medium">Type</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {whaleData.map((tx, idx) => (
                <TableRow key={idx} className="border-zinc-800 hover:bg-zinc-800/50">
                  <TableCell className="text-zinc-400 text-sm">{tx.time}</TableCell>
                  <TableCell className="text-zinc-300 min-w-max">
                    <div className="group relative inline-block">
                      <button className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors text-sm font-mono whitespace-nowrap">
                        {tx.address.slice(0, 6)}...{tx.address.slice(-4)}
                      </button>
                      {/* Tooltip showing full address on hover */}
                      <div className="absolute left-0 top-full mt-2 hidden group-hover:block bg-zinc-800 border border-zinc-700 rounded px-3 py-2 z-10 shadow-lg whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <code className="font-mono text-xs text-zinc-200">{tx.address}</code>
                          <button 
                            onClick={() => navigator.clipboard.writeText(tx.address)}
                            className="text-zinc-400 hover:text-zinc-100 text-xs ml-1"
                            title="Copy full address"
                          >
                            📋
                          </button>
                        </div>
                      </div>
                    </div>
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
                    ${tx.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell className="font-mono text-sm text-zinc-400">{tx.amount}</TableCell>
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
                      className={
                        tx.type === "Open" ? "border-zinc-600 text-zinc-300" : "border-amber-500/30 text-amber-400"
                      }
                    >
                      {tx.type}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
