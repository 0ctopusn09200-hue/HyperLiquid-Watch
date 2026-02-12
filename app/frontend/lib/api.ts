import type {
  LiquidationHeatmapResponse,
  LongShortRatioResponse,
  WhaleActivitiesResponse,
  WalletPositionDistributionResponse,
  ApiError,
} from "./types/api";

// frontend/lib/api.ts

const PUBLIC_API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

// 给“容器内部 / SSR”用：走 docker compose 的 service name
const INTERNAL_API_BASE =
  process.env.API_INTERNAL_URL || "http://backend:8080";

// 关键：服务器端(容器里)用 INTERNAL，浏览器端用 PUBLIC
const API_BASE_URL = typeof window === "undefined"
  ? INTERNAL_API_BASE
  : PUBLIC_API_BASE;

const API_PREFIX = "/api/v1";

export const BASE_URL = `${API_BASE_URL}${API_PREFIX}`;


/**
 * API client for Hyperliquid data analysis backend
 */
class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}${API_PREFIX}`;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const error: ApiError = await response.json().catch(() => ({
          error: "Unknown error",
          message: `HTTP ${response.status}: ${response.statusText}`,
          statusCode: response.status,
          timestamp: new Date().toISOString(),
        }));
        throw error;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof TypeError) {
        // Network error
        throw {
          error: "NetworkError",
          message: "Failed to connect to API server",
          statusCode: 0,
          timestamp: new Date().toISOString(),
        } as ApiError;
      }
      throw error;
    }
  }

  /**
   * Get liquidation heatmap data
   */
  async getLiquidationHeatmap(
    token: string = "BTC",
    range: number = 4.5
  ): Promise<LiquidationHeatmapResponse> {
    const params = new URLSearchParams({
      token,
      range: range.toString(),
    });
    return this.request<LiquidationHeatmapResponse>(
      `/market/liquidation?${params.toString()}`
    );
  }

  /**
   * Get global long/short ratio
   */
  async getLongShortRatio(
    token?: string
  ): Promise<LongShortRatioResponse> {
    const params = token ? new URLSearchParams({ token }) : "";
    return this.request<LongShortRatioResponse>(
      `/market/long-short-ratio${params ? `?${params.toString()}` : ""}`
    );
  }

  /**
   * Get whale activities
   */
  async getWhaleActivities(params?: {
    limit?: number;
    token?: string;
    side?: "Long" | "Short";
    type?: "Open" | "Close";
    minValue?: number;
  }): Promise<WhaleActivitiesResponse> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.token) searchParams.set("token", params.token);
    if (params?.side) searchParams.set("side", params.side);
    if (params?.type) searchParams.set("type", params.type);
    if (params?.minValue) searchParams.set("minValue", params.minValue.toString());

    const query = searchParams.toString();
    return this.request<WhaleActivitiesResponse>(
      `/whale/activities${query ? `?${query}` : ""}`
    );
  }

  /**
   * Get wallet position distribution
   */
  async getWalletDistribution(
    token?: string
  ): Promise<WalletPositionDistributionResponse> {
    const params = token ? new URLSearchParams({ token }) : "";
    return this.request<WalletPositionDistributionResponse>(
      `/wallet/distribution${params ? `?${params.toString()}` : ""}`
    );
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
