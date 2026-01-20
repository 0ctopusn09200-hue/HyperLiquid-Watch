type MessageType =
  | "whale_activity"
  | "price_update"
  | "long_short_ratio"
  | "connected"
  | "subscribed"
  | "unsubscribed"
  | "error"
  | "pong";

interface WSMessage {
  type: MessageType;
  payload: any;
  timestamp: string;
}

type MessageHandler = (message: WSMessage) => void;
type ErrorHandler = (error: Event | CloseEvent) => void;

/**
 * WebSocket client for real-time data streaming
 */
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000; // Start with 1 second
  private messageHandlers: Map<MessageType, MessageHandler[]> = new Map();
  private errorHandlers: ErrorHandler[] = [];
  private isManualClose = false;
  private pingInterval: NodeJS.Timeout | null = null;

  constructor() {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8080/api/v1/ws";
    this.url = wsUrl;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log("WebSocket connected");
          this.reconnectAttempts = 0;
          this.reconnectDelay = 1000;

          // Start ping interval (every 30 seconds)
          this.startPingInterval();

          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        };

        this.ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          this.errorHandlers.forEach((handler) => handler(error));
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log("WebSocket closed", event.code, event.reason);
          this.stopPingInterval();

          if (!this.isManualClose) {
            this.handleReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isManualClose = true;
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Subscribe to channels
   */
  subscribe(channels: string[], filters?: Record<string, any>): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn("WebSocket is not connected");
      return;
    }

    this.send({
      type: "subscribe",
      channels,
      filters: filters || {},
    });
  }

  /**
   * Unsubscribe from channels
   */
  unsubscribe(channels: string[]): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    this.send({
      type: "unsubscribe",
      channels,
    });
  }

  /**
   * Register message handler
   */
  onMessage(type: MessageType, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(type);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }

  /**
   * Register error handler
   */
  onError(handler: ErrorHandler): () => void {
    this.errorHandlers.push(handler);
    return () => {
      const index = this.errorHandlers.indexOf(handler);
      if (index > -1) {
        this.errorHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private handleMessage(message: WSMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => handler(message));
    }
  }

  private startPingInterval(): void {
    this.stopPingInterval();
    this.pingInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: "ping" });
      }
    }, 30000); // 30 seconds
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      30000
    ); // Exponential backoff, max 30 seconds

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      if (!this.isManualClose) {
        this.connect().catch((error) => {
          console.error("Reconnection failed:", error);
        });
      }
    }, delay);
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient();
