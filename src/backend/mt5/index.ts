import WebSocket from 'ws';
import { EventEmitter } from 'events';
import { config } from '@/config';
import { logger } from '@/logging';
import { MT5Connection, MT5Trade, TradingSignal, User } from '@/types';
import { DatabaseService } from '@/database';

export interface MT5Message {
  type: 'ping' | 'pong' | 'account_info' | 'market_data' | 'trade_request' | 'trade_response' | 'error';
  data: any;
  timestamp: number;
  requestId?: string;
}

export interface MT5AccountInfo {
  login: string;
  server: string;
  balance: number;
  equity: number;
  margin: number;
  freeMargin: number;
  marginLevel: number;
  profit: number;
  credit: number;
}

export interface MT5MarketData {
  symbol: string;
  bid: number;
  ask: number;
  spread: number;
  time: number;
  volume: number;
  change: number;
  changePercent: number;
}

export interface MT5TradeRequest {
  action: 'buy' | 'sell' | 'close' | 'modify';
  symbol: string;
  volume: number;
  price?: number;
  stopLoss?: number;
  takeProfit?: number;
  comment?: string;
  magic?: number;
  ticket?: number;
}

export interface MT5TradeResponse {
  success: boolean;
  ticket?: number;
  error?: string;
  retcode?: number;
  deal?: number;
  orderId?: number;
  volume?: number;
  price?: number;
  bid?: number;
  ask?: number;
  comment?: string;
}

export class MT5Connection extends EventEmitter {
  private ws: WebSocket | null = null;
  private isConnected: boolean = false;
  private connectionId: string;
  private userId: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = config.mt5.retryAttempts;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageQueue: MT5Message[] = [];
  private latencyStats: number[] = [];
  private requestCallbacks: Map<string, { resolve: Function; reject: Function; timeout: NodeJS.Timeout }> = new Map();

  constructor(userId: string, connectionId: string) {
    super();
    this.userId = userId;
    this.connectionId = connectionId;
  }

  /**
   * Connect to MT5 WebSocket server
   */
  public async connect(): Promise<boolean> {
    try {
      const wsUrl = `ws://${config.mt5.websocketHost}:${config.mt5.websocketPort}`;

      this.ws = new WebSocket(wsUrl, {
        handshakeTimeout: config.mt5.connectionTimeout,
        perMessageDeflate: false // Disable compression for lower latency
      });

      // Set up event handlers
      this.setupEventHandlers();

      // Wait for connection to open
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, config.mt5.connectionTimeout);

        this.ws!.once('open', () => {
          clearTimeout(timeout);
          this.onConnected();
          resolve(true);
        });

        this.ws!.once('error', (error) => {
          clearTimeout(timeout);
          reject(error);
        });
      });

    } catch (error) {
      logger.error('MT5 connection failed', {
        user_id: this.userId,
        connection_id: this.connectionId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return false;
    }
  }

  /**
   * Set up WebSocket event handlers for optimal performance
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.on('open', () => {
      this.onConnected();
    });

    this.ws.on('message', (data: Buffer) => {
      this.onMessage(data);
    });

    this.ws.on('close', (code: number, reason: Buffer) => {
      this.onDisconnected(code, reason.toString());
    });

    this.ws.on('error', (error: Error) => {
      this.onError(error);
    });

    this.ws.on('pong', () => {
      this.onPong();
    });
  }

  /**
   * Handle connection established
   */
  private onConnected(): void {
    this.isConnected = true;
    this.reconnectAttempts = 0;

    // Start heartbeat for connection health monitoring
    this.startHeartbeat();

    // Process any queued messages
    this.processMessageQueue();

    logger.info('MT5 connection established', {
      user_id: this.userId,
      connection_id: this.connectionId
    });

    this.emit('connected');
  }

  /**
   * Handle incoming messages with latency optimization
   */
  private onMessage(data: Buffer): void {
    try {
      const startTime = process.hrtime.bigint();

      // Parse message (optimized for speed)
      const message: MT5Message = JSON.parse(data.toString());

      // Calculate processing latency
      const processingTime = Number(process.hrtime.bigint() - startTime) / 1000000; // Convert to ms
      this.updateLatencyStats(processingTime);

      // Handle different message types
      switch (message.type) {
        case 'pong':
          this.handlePong(message);
          break;
        case 'account_info':
          this.handleAccountInfo(message);
          break;
        case 'market_data':
          this.handleMarketData(message);
          break;
        case 'trade_response':
          this.handleTradeResponse(message);
          break;
        case 'error':
          this.handleError(message);
          break;
        default:
          logger.warn('Unknown MT5 message type', {
            type: message.type,
            user_id: this.userId
          });
      }

      this.emit('message', message);

    } catch (error) {
      logger.error('Failed to process MT5 message', {
        user_id: this.userId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  /**
   * Handle disconnection with auto-reconnect
   */
  private onDisconnected(code: number, reason: string): void {
    this.isConnected = false;
    this.stopHeartbeat();

    logger.warn('MT5 connection disconnected', {
      user_id: this.userId,
      connection_id: this.connectionId,
      code,
      reason
    });

    this.emit('disconnected', { code, reason });

    // Attempt reconnection if not intentional
    if (code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }

  /**
   * Handle connection errors
   */
  private onError(error: Error): void {
    logger.error('MT5 connection error', {
      user_id: this.userId,
      connection_id: this.connectionId,
      error: error.message
    });

    this.emit('error', error);
  }

  /**
   * Handle pong response for latency measurement
   */
  private onPong(): void {
    const now = Date.now();
    // Calculate round-trip time (implement based on ping timestamp)
    this.emit('pong', now);
  }

  /**
   * Send message with guaranteed delivery and timeout
   */
  public async sendMessage(message: Omit<MT5Message, 'timestamp'>): Promise<MT5Message | null> {
    return new Promise((resolve, reject) => {
      if (!this.isConnected || !this.ws) {
        // Queue message for later delivery
        this.messageQueue.push({ ...message, timestamp: Date.now() });
        reject(new Error('Not connected'));
        return;
      }

      const requestId = this.generateRequestId();
      const fullMessage: MT5Message = {
        ...message,
        timestamp: Date.now(),
        requestId
      };

      try {
        // Send message
        this.ws.send(JSON.stringify(fullMessage));

        // Set up response handler for request-response pattern
        if (message.type === 'trade_request') {
          const timeout = setTimeout(() => {
            this.requestCallbacks.delete(requestId);
            reject(new Error('Request timeout'));
          }, 5000); // 5 second timeout

          this.requestCallbacks.set(requestId, { resolve, reject, timeout });
        } else {
          resolve(fullMessage);
        }

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Send trading signal for execution
   */
  public async executeTradingSignal(signal: TradingSignal): Promise<MT5TradeResponse> {
    const tradeRequest: MT5TradeRequest = {
      action: signal.type,
      symbol: signal.symbol,
      volume: signal.volume,
      price: signal.entry_price,
      stopLoss: signal.stop_loss,
      takeProfit: signal.take_profit,
      comment: `Signal_${signal.id}`
    };

    const response = await this.sendMessage({
      type: 'trade_request',
      data: tradeRequest
    });

    if (!response) {
      throw new Error('Failed to send trade request');
    }

    // Wait for trade response (handled by message callback)
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Trade execution timeout'));
      }, 10000); // 10 second timeout for trade execution

      const handleResponse = (message: MT5Message) => {
        if (message.type === 'trade_response' && message.requestId === response.requestId) {
          clearTimeout(timeout);
          this.removeListener('message', handleResponse);
          resolve(message.data as MT5TradeResponse);
        }
      };

      this.on('message', handleResponse);
    });
  }

  /**
   * Get account information
   */
  public async getAccountInfo(): Promise<MT5AccountInfo> {
    const response = await this.sendMessage({
      type: 'account_info',
      data: {}
    });

    if (!response) {
      throw new Error('Failed to get account info');
    }

    return response.data as MT5AccountInfo;
  }

  /**
   * Subscribe to market data for symbol
   */
  public async subscribeMarketData(symbol: string): Promise<void> {
    await this.sendMessage({
      type: 'market_data',
      data: { action: 'subscribe', symbol }
    });
  }

  /**
   * Unsubscribe from market data
   */
  public async unsubscribeMarketData(symbol: string): Promise<void> {
    await this.sendMessage({
      type: 'market_data',
      data: { action: 'unsubscribe', symbol }
    });
  }

  /**
   * Get connection statistics for monitoring
   */
  public getConnectionStats(): {
    isConnected: boolean;
    averageLatency: number;
    messageQueueSize: number;
    reconnectAttempts: number;
  } {
    const averageLatency = this.latencyStats.length > 0 ?
      this.latencyStats.reduce((a, b) => a + b) / this.latencyStats.length : 0;

    return {
      isConnected: this.isConnected,
      averageLatency,
      messageQueueSize: this.messageQueue.length,
      reconnectAttempts: this.reconnectAttempts
    };
  }

  /**
   * Close connection
   */
  public async disconnect(): Promise<void> {
    this.stopHeartbeat();

    if (this.ws && this.isConnected) {
      this.ws.close(1000, 'Client disconnect');
    }

    this.isConnected = false;
    this.emit('disconnected', { code: 1000, reason: 'Client disconnect' });
  }

  // Private helper methods

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.isConnected) {
        this.ws.ping();
      }
    }, 30000); // 30 second heartbeat
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000); // Exponential backoff, max 30s

    logger.info('Scheduling MT5 reconnection', {
      user_id: this.userId,
      attempt: this.reconnectAttempts,
      delay
    });

    setTimeout(() => {
      this.connect().catch(error => {
        logger.error('MT5 reconnection failed', {
          user_id: this.userId,
          attempt: this.reconnectAttempts,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      });
    }, delay);
  }

  private processMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected) {
      const message = this.messageQueue.shift();
      if (message) {
        this.sendMessage(message).catch(error => {
          logger.error('Failed to send queued message', {
            user_id: this.userId,
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        });
      }
    }
  }

  private updateLatencyStats(latency: number): void {
    this.latencyStats.push(latency);

    // Keep only last 100 measurements for rolling average
    if (this.latencyStats.length > 100) {
      this.latencyStats.shift();
    }

    // Log if latency exceeds threshold
    if (latency > 50) { // 50ms threshold
      logger.warn('High MT5 processing latency detected', {
        user_id: this.userId,
        latency,
        average: this.latencyStats.reduce((a, b) => a + b) / this.latencyStats.length
      });
    }
  }

  private generateRequestId(): string {
    return `mt5_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private handlePong(message: MT5Message): void {
    // Handle pong for latency measurement
    this.emit('latency', message.data);
  }

  private handleAccountInfo(message: MT5Message): void {
    this.emit('account_info', message.data);
  }

  private handleMarketData(message: MT5Message): void {
    this.emit('market_data', message.data);
  }

  private handleTradeResponse(message: MT5Message): void {
    // Handle response for pending requests
    if (message.requestId && this.requestCallbacks.has(message.requestId)) {
      const callback = this.requestCallbacks.get(message.requestId)!;
      clearTimeout(callback.timeout);
      this.requestCallbacks.delete(message.requestId);
      callback.resolve(message.data);
    }

    this.emit('trade_response', message.data);
  }

  private handleError(message: MT5Message): void {
    logger.error('MT5 server error', {
      user_id: this.userId,
      error: message.data
    });
    this.emit('mt5_error', message.data);
  }
}

/**
 * MT5 Connection Pool Manager for handling multiple user connections
 */
export class MT5ConnectionManager {
  private connections: Map<string, MT5Connection> = new Map();
  private databaseService: DatabaseService;

  constructor(databaseService: DatabaseService) {
    this.databaseService = databaseService;
  }

  /**
   * Get or create MT5 connection for user
   */
  public async getConnection(userId: string): Promise<MT5Connection> {
    const existingConnection = this.connections.get(userId);

    if (existingConnection && existingConnection.getConnectionStats().isConnected) {
      return existingConnection;
    }

    // Create new connection
    const connectionId = `mt5_${userId}_${Date.now()}`;
    const connection = new MT5Connection(userId, connectionId);

    // Set up event handlers
    connection.on('connected', () => {
      logger.info('MT5 connection established for user', { user_id: userId });
    });

    connection.on('disconnected', () => {
      logger.info('MT5 connection lost for user', { user_id: userId });
    });

    connection.on('error', (error: Error) => {
      logger.error('MT5 connection error for user', {
        user_id: userId,
        error: error.message
      });
    });

    // Connect
    const connected = await connection.connect();
    if (!connected) {
      throw new Error('Failed to establish MT5 connection');
    }

    this.connections.set(userId, connection);
    return connection;
  }

  /**
   * Close connection for user
   */
  public async closeConnection(userId: string): Promise<void> {
    const connection = this.connections.get(userId);
    if (connection) {
      await connection.disconnect();
      this.connections.delete(userId);
    }
  }

  /**
   * Get connection statistics for monitoring
   */
  public getConnectionStats(): Array<{ userId: string; stats: any }> {
    const stats: Array<{ userId: string; stats: any }> = [];

    this.connections.forEach((connection, userId) => {
      stats.push({
        userId,
        stats: connection.getConnectionStats()
      });
    });

    return stats;
  }

  /**
   * Cleanup inactive connections
   */
  public async cleanupInactiveConnections(): Promise<void> {
    const toRemove: string[] = [];

    this.connections.forEach((connection, userId) => {
      const stats = connection.getConnectionStats();
      if (!stats.isConnected && stats.reconnectAttempts >= config.mt5.retryAttempts) {
        toRemove.push(userId);
      }
    });

    for (const userId of toRemove) {
      await this.closeConnection(userId);
      logger.info('Cleaned up inactive MT5 connection', { user_id: userId });
    }
  }

  /**
   * Health check for all connections
   */
  public async healthCheck(): Promise<{ total: number; connected: number; errors: number }> {
    let connected = 0;
    let errors = 0;
    const total = this.connections.size;

    this.connections.forEach((connection) => {
      const stats = connection.getConnectionStats();
      if (stats.isConnected) {
        connected++;
      } else {
        errors++;
      }
    });

    return { total, connected, errors };
  }
}