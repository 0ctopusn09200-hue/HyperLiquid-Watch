// ============================================
// Liquidation Heatmap Types
// ============================================

export interface LiquidationPoint {
  /** Price level in USD */
  price: number;
  /** Long liquidation volume at this price (in units, will be multiplied by 10000 for USD display) */
  longVol: number;
  /** Short liquidation volume at this price (in units, will be multiplied by 10000 for USD display) */
  shortVol: number;
  /** Whether this is the current market price */
  current?: boolean;
}

export interface LiquidationHeatmapResponse {
  /** Token symbol (e.g., "BTC", "ETH") */
  token: string;
  /** Current market price */
  currentPrice: number;
  /** Array of liquidation points sorted by price (ascending) */
  points: LiquidationPoint[];
  /** Minimum price in the range */
  minPrice: number;
  /** Maximum price in the range */
  maxPrice: number;
}

// ============================================
// Long/Short Ratio Types
// ============================================

export interface LongShortRatioResponse {
  /** Global long percentage (0-100) */
  longPercent: number;
  /** Global short percentage (0-100) */
  shortPercent: number;
  /** Total long volume in USD */
  longVolume: number;
  /** Total short volume in USD */
  shortVolume: number;
  /** 24h change in long volume (percentage) */
  longChange24h: number;
  /** 24h change in short volume (percentage) */
  shortChange24h: number;
  /** Timestamp of last update (ISO 8601) */
  updatedAt: string;
}

// ============================================
// Whale Activities Types
// ============================================

export type PositionSide = "Long" | "Short";
export type PositionType = "Open" | "Close";

export interface WhaleTransaction {
  /** Relative time string (e.g., "2 min ago", "1 hr ago") or ISO timestamp */
  time: string;
  /** Wallet address (full or truncated format) */
  address: string;
  /** Token symbol (e.g., "BTC", "ETH", "HYPE") */
  token: string;
  /** Transaction value in USD */
  value: number;
  /** Position side */
  side: PositionSide;
  /** Transaction type */
  type: PositionType;
  /** Amount as formatted string (e.g., "28.40572 BTC" or "-403.1808 ETH") */
  amount: string;
  /** Optional: Full timestamp in ISO 8601 for accurate sorting */
  timestamp?: string;
  /** Optional: Transaction hash for blockchain explorers */
  txHash?: string;
}

export interface WhaleActivitiesResponse {
  /** Array of whale transactions, sorted by time (most recent first) */
  transactions: WhaleTransaction[];
  /** Total count available (for pagination) */
  totalCount: number;
  /** Last update timestamp */
  updatedAt: string;
}

// ============================================
// Wallet Position Distribution Types
// ============================================

export type Sentiment = "bullish" | "bearish" | "neutral";

export interface WalletPositionBucket {
  /** Position size range (e.g., "$0 - $250", "$10K - $50K") */
  positionSize: string;
  /** Category name (e.g., "Shrimp", "Whale") */
  category: string;
  /** English category name */
  categoryEn: string;
  /** Number of unique wallets in this bucket */
  walletCount: number;
  /** Open interest percentage of total */
  openInterestPercent: number;
  /** Formatted long value string (e.g., "$717M") */
  longValue: string;
  /** Formatted short value string (e.g., "$181M") */
  shortValue: string;
  /** Long percentage (0-100) */
  longPercent: number;
  /** Number of wallets in profit */
  profitUsers: number;
  /** Number of wallets in loss */
  lossUsers: number;
  /** Market sentiment for this bucket */
  sentiment: Sentiment;
}

export interface WalletPositionDistributionResponse {
  /** Array of position buckets, sorted by position size (ascending) */
  buckets: WalletPositionBucket[];
  /** Total wallets across all buckets */
  totalWallets: number;
  /** Timestamp of last update */
  updatedAt: string;
}

// ============================================
// Error Types
// ============================================

export interface ApiError {
  error: string;
  message: string;
  statusCode: number;
  timestamp: string;
}
