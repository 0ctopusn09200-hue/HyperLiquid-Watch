import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ExternalLink } from "lucide-react"

const whaleData = [
  {
    time: "2 min ago",
    address: "0x49f3...8d2b",
    token: "BTC",
    value: 2567735.06,
    side: "Long",
    type: "Open",
    amount: "28.40572 BTC",
  },
  {
    time: "5 min ago",
    address: "0x69c2...07a1",
    token: "ETH",
    value: 1378665.67,
    side: "Short",
    type: "Open",
    amount: "-403.1808 ETH",
  },
  {
    time: "12 min ago",
    address: "0x7e4a...fd92",
    token: "ETH",
    value: 1545200.0,
    side: "Long",
    type: "Open",
    amount: "500.0000 ETH",
  },
  {
    time: "18 min ago",
    address: "0xf4d8...5f1c",
    token: "HYPE",
    value: 1705680.0,
    side: "Long",
    type: "Close",
    amount: "-60,000.00 HYPE",
  },
  {
    time: "25 min ago",
    address: "0xec3b...5b4d",
    token: "BTC",
    value: 1019044.89,
    side: "Long",
    type: "Open",
    amount: "11.28273 BTC",
  },
  {
    time: "32 min ago",
    address: "0xec7f...5b91",
    token: "BTC",
    value: 1018875.65,
    side: "Long",
    type: "Open",
    amount: "11.28273 BTC",
  },
  {
    time: "45 min ago",
    address: "0x0a2c...4532",
    token: "BTC",
    value: 7947647.29,
    side: "Long",
    type: "Open",
    amount: "88.92961 BTC",
  },
  {
    time: "1 hr ago",
    address: "0x9c8e...94f2",
    token: "ETH",
    value: 4172923.45,
    side: "Short",
    type: "Open",
    amount: "-1,347.7129 ETH",
  },
  {
    time: "1.5 hr ago",
    address: "0x41b7...ee83",
    token: "ETH",
    value: 1060360.33,
    side: "Long",
    type: "Close",
    amount: "342.5711 ETH",
  },
  {
    time: "2 hr ago",
    address: "0xd2f1...3a8c",
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
                <TableHead className="text-zinc-400 font-medium">Address</TableHead>
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
                  <TableCell>
                    <button className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors text-sm font-mono">
                      {tx.address}
                      <ExternalLink className="h-3 w-3" />
                    </button>
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
