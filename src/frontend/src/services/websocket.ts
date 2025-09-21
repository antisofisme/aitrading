import { io, Socket } from 'socket.io-client';
import { WebSocketMessage, WebSocketConnection } from '../types';

// WebSocket connection manager
class WebSocketManager {
  private socket: Socket | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private subscriptions: Set<string> = new Set();
  private messageQueue: WebSocketMessage[] = [];
  private isConnecting = false;
  private maxReconnectAttempts = 5;
  private reconnectAttempts = 0;
  private reconnectDelay = 1000; // Start with 1 second

  // Event listeners
  private listeners: { [event: string]: ((data: any) => void)[] } = {};

  constructor() {
    this.connect();
  }

  // Connect to WebSocket server
  connect() {
    if (this.isConnecting || this.socket?.connected) {
      return;
    }

    this.isConnecting = true;
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

    // Get authentication token
    const token = this.getAuthToken();
    const tenantId = this.getTenantId();

    this.socket = io(wsUrl, {
      transports: ['websocket', 'polling'],
      auth: {
        token: token,
        tenantId: tenantId,
        clientId: this.generateClientId(),
      },
      reconnection: false, // Handle reconnection manually
      timeout: 10000, // 10 seconds connection timeout
    });

    this.setupEventHandlers();
  }

  // Setup socket event handlers
  private setupEventHandlers() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected:', this.socket?.id);
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;

      // Restore subscriptions
      this.restoreSubscriptions();

      // Send queued messages
      this.flushMessageQueue();

      // Start heartbeat
      this.startHeartbeat();

      // Emit connection event
      this.emit('connected', { socketId: this.socket?.id });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.isConnecting = false;
      this.stopHeartbeat();

      // Emit disconnection event
      this.emit('disconnected', { reason });

      // Attempt reconnection for certain disconnect reasons
      if (reason === 'io server disconnect') {
        // Server initiated disconnect - don't reconnect immediately
        this.scheduleReconnect(5000);
      } else {
        // Client side disconnect - attempt reconnection
        this.scheduleReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;
      this.emit('error', { error: error.message });
      this.scheduleReconnect();
    });

    // Handle incoming messages
    this.socket.on('message', (data: WebSocketMessage) => {
      this.handleMessage(data);
    });

    // Handle different message types
    this.socket.on('price_update', (data) => {
      this.emit('price_update', data);
    });

    this.socket.on('position_update', (data) => {
      this.emit('position_update', data);
    });

    this.socket.on('ai_prediction', (data) => {
      this.emit('ai_prediction', data);
    });

    this.socket.on('system_alert', (data) => {
      this.emit('system_alert', data);
    });

    this.socket.on('portfolio_update', (data) => {
      this.emit('portfolio_update', data);
    });

    // Handle subscription confirmations
    this.socket.on('subscribed', (data) => {
      console.log('Subscribed to channel:', data.channel);
      this.emit('subscribed', data);
    });

    this.socket.on('unsubscribed', (data) => {
      console.log('Unsubscribed from channel:', data.channel);
      this.subscriptions.delete(data.channel);
      this.emit('unsubscribed', data);
    });

    // Handle heartbeat
    this.socket.on('pong', () => {
      // Server responded to ping
    });
  }

  // Schedule reconnection
  private scheduleReconnect(delay?: number) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.emit('max_reconnect_attempts', { attempts: this.reconnectAttempts });
      return;
    }

    const reconnectDelay = delay || Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts), 30000);

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      this.connect();
    }, reconnectDelay);
  }

  // Start heartbeat to keep connection alive
  private startHeartbeat() {
    this.stopHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.socket?.connected) {
        this.socket.emit('ping');
      }
    }, 30000); // 30 seconds
  }

  // Stop heartbeat
  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  // Handle incoming messages
  private handleMessage(message: WebSocketMessage) {
    // Validate message
    if (!this.validateMessage(message)) {
      console.warn('Invalid message received:', message);
      return;
    }

    // Rate limiting check
    if (!this.checkRateLimit()) {
      console.warn('Rate limit exceeded, dropping message');
      return;
    }

    // Emit message to listeners
    this.emit('message', message);
    this.emit(message.type, message.data);
  }

  // Validate incoming message
  private validateMessage(message: any): message is WebSocketMessage {
    return (
      typeof message === 'object' &&
      message !== null &&
      typeof message.type === 'string' &&
      message.data !== undefined &&
      typeof message.timestamp === 'string'
    );
  }

  // Rate limiting for incoming messages
  private messageCount = 0;
  private windowStart = Date.now();
  private maxMessagesPerMinute = 1000;

  private checkRateLimit(): boolean {
    const now = Date.now();
    const windowSize = 60000; // 1 minute

    // Reset window if needed
    if (now - this.windowStart > windowSize) {
      this.messageCount = 0;
      this.windowStart = now;
    }

    this.messageCount++;
    return this.messageCount <= this.maxMessagesPerMinute;
  }

  // Subscribe to a channel
  subscribe(channel: string, filters?: any) {
    if (!this.socket?.connected) {
      console.warn(`Cannot subscribe to ${channel}: not connected`);
      return;
    }

    this.subscriptions.add(channel);
    this.socket.emit('subscribe', { channel, filters });
  }

  // Unsubscribe from a channel
  unsubscribe(channel: string) {
    if (!this.socket?.connected) {
      console.warn(`Cannot unsubscribe from ${channel}: not connected`);
      return;
    }

    this.subscriptions.delete(channel);
    this.socket.emit('unsubscribe', { channel });
  }

  // Send a message
  send(type: string, data: any, channel?: string) {
    const message: WebSocketMessage = {
      type,
      data,
      timestamp: new Date().toISOString(),
      channel,
    };

    if (!this.socket?.connected) {
      // Queue message for later
      this.messageQueue.push(message);
      console.warn('WebSocket not connected, message queued');
      return;
    }

    this.socket.emit('message', message);
  }

  // Restore subscriptions after reconnection
  private restoreSubscriptions() {
    for (const channel of this.subscriptions) {
      this.socket?.emit('subscribe', { channel });
    }
  }

  // Flush queued messages
  private flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.socket?.emit('message', message);
      }
    }
  }

  // Event listener management
  on(event: string, callback: (data: any) => void) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  off(event: string, callback?: (data: any) => void) {
    if (!this.listeners[event]) return;

    if (callback) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    } else {
      delete this.listeners[event];
    }
  }

  private emit(event: string, data: any) {
    const callbacks = this.listeners[event] || [];
    callbacks.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error);
      }
    });
  }

  // Get connection status
  getStatus(): WebSocketConnection {
    return {
      url: this.socket?.io.uri || '',
      isConnected: this.socket?.connected || false,
      connectionId: this.socket?.id,
      subscriptions: Array.from(this.subscriptions),
    };
  }

  // Utility methods
  private getAuthToken(): string | null {
    return localStorage.getItem('accessToken') || null;
  }

  private getTenantId(): string | null {
    const hostname = window.location.hostname;
    const subdomain = hostname.split('.')[0];

    if (subdomain && !['www', 'app', 'localhost'].includes(subdomain)) {
      return subdomain;
    }

    return localStorage.getItem('tenantId') || null;
  }

  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Disconnect and cleanup
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.stopHeartbeat();

    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }

    this.subscriptions.clear();
    this.messageQueue = [];
    this.listeners = {};
    this.isConnecting = false;
    this.reconnectAttempts = 0;
  }

  // Force reconnection
  reconnect() {
    this.disconnect();
    this.reconnectAttempts = 0;
    this.connect();
  }
}

// Create singleton instance
export const wsManager = new WebSocketManager();

// React hook for using WebSocket
export const useWebSocket = () => {
  return {
    subscribe: (channel: string, filters?: any) => wsManager.subscribe(channel, filters),
    unsubscribe: (channel: string) => wsManager.unsubscribe(channel),
    send: (type: string, data: any, channel?: string) => wsManager.send(type, data, channel),
    on: (event: string, callback: (data: any) => void) => wsManager.on(event, callback),
    off: (event: string, callback?: (data: any) => void) => wsManager.off(event, callback),
    getStatus: () => wsManager.getStatus(),
    reconnect: () => wsManager.reconnect(),
  };
};

// Subscription helpers
export const subscribeToSymbol = (symbol: string) => {
  wsManager.subscribe('prices', { symbol });
};

export const subscribeToPortfolio = (userId: string) => {
  wsManager.subscribe('portfolio', { userId });
};

export const subscribeToAIPredictions = (symbols?: string[]) => {
  wsManager.subscribe('ai_predictions', { symbols });
};

export const subscribeToSystemAlerts = () => {
  wsManager.subscribe('system_alerts');
};

// Export everything
export default wsManager;