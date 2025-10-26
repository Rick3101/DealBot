import { io, Socket } from 'socket.io-client';
import { WebSocketUpdate } from '@/types/expedition';
import { getUserId } from '@/utils/telegram';

type EventCallback = (data: any) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private connected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private eventCallbacks: Map<string, Set<EventCallback>> = new Map();
  private initialized = false;

  constructor() {
    // Defer initialization until first use
    if (typeof window !== 'undefined') {
      // Auto-initialize after a short delay to allow Telegram to load
      setTimeout(() => this.ensureInitialized(), 500);
    }
  }

  private ensureInitialized(): void {
    if (!this.initialized) {
      this.initializeConnection();
    }
  }

  private initializeConnection(): void {
    if (this.initialized) return;

    // Use environment variable API URL, fallback to current origin for development (uses Vite proxy)
    const envApiUrl = import.meta.env.VITE_API_URL;
    let baseUrl: string;

    if (import.meta.env.DEV && !envApiUrl) {
      baseUrl = window.location.origin; // Use Vite dev server origin - proxy handles forwarding
      console.log('DEV mode: Using Vite proxy for WebSocket (origin-relative)');
    } else {
      baseUrl = envApiUrl || window.location.origin;
    }

    console.log('WebSocket Base URL:', baseUrl);

    try {
      this.socket = io(baseUrl, {
        transports: ['websocket', 'polling'],
        timeout: 20000,
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
        reconnectionDelayMax: 5000,
      });

      this.setupEventHandlers();
      this.initialized = true;
    } catch (error) {
      console.error('Failed to initialize WebSocket connection:', error);
    }
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.connected = true;
      this.reconnectAttempts = 0;

      // Join user's personal room for notifications
      try {
        const userId = getUserId();
        if (userId) {
          this.joinUserRoom(userId);
        } else {
          console.warn('No user ID available for joining user room');
        }
      } catch (error) {
        console.error('Error getting user ID:', error);
      }

      this.emit('connected');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.connected = false;
      this.emit('disconnected', { reason });
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.connected = false;
      this.reconnectAttempts++;

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
        this.emit('maxReconnectAttemptsReached');
      }
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`WebSocket reconnected after ${attemptNumber} attempts`);
      this.connected = true;
      this.reconnectAttempts = 0;
      this.emit('reconnected', { attemptNumber });
    });

    // Expedition-specific events
    this.socket.on('expedition_update', (data: WebSocketUpdate) => {
      console.log('Expedition update received:', data);
      this.emit('expeditionUpdate', data);
    });

    this.socket.on('item_consumed', (data: WebSocketUpdate) => {
      console.log('Item consumed:', data);
      this.emit('itemConsumed', data);
      this.emit('expeditionUpdate', data);
    });

    this.socket.on('expedition_completed', (data: WebSocketUpdate) => {
      console.log('Expedition completed:', data);
      this.emit('expeditionCompleted', data);
      this.emit('expeditionUpdate', data);
    });

    this.socket.on('deadline_warning', (data: WebSocketUpdate) => {
      console.log('Deadline warning:', data);
      this.emit('deadlineWarning', data);
      this.emit('expeditionUpdate', data);
    });

    this.socket.on('expedition_created', (data: WebSocketUpdate) => {
      console.log('Expedition created:', data);
      this.emit('expeditionCreated', data);
      this.emit('expeditionUpdate', data);
    });

    // Error handling
    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    });

    // Metrics and status updates
    this.socket.on('expedition_metrics', (data) => {
      this.emit('expeditionMetrics', data);
    });

    this.socket.on('joined', (data) => {
      console.log('Joined room:', data);
      this.emit('joinedRoom', data);
    });

    this.socket.on('left', (data) => {
      console.log('Left room:', data);
      this.emit('leftRoom', data);
    });

    this.socket.on('joined_user_room', (data) => {
      console.log('Joined user room:', data);
      this.emit('joinedUserRoom', data);
    });
  }

  // Public methods
  public isConnected(): boolean {
    this.ensureInitialized();
    return this.connected && this.socket?.connected === true;
  }

  public getSocket(): Socket | null {
    this.ensureInitialized();
    return this.socket;
  }

  // Event subscription methods
  public on(event: string, callback: EventCallback): void {
    this.ensureInitialized();
    if (!this.eventCallbacks.has(event)) {
      this.eventCallbacks.set(event, new Set());
    }
    this.eventCallbacks.get(event)!.add(callback);
  }

  public off(event: string, callback: EventCallback): void {
    const callbacks = this.eventCallbacks.get(event);
    if (callbacks) {
      callbacks.delete(callback);
      if (callbacks.size === 0) {
        this.eventCallbacks.delete(event);
      }
    }
  }

  private emit(event: string, data?: any): void {
    const callbacks = this.eventCallbacks.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event callback for ${event}:`, error);
        }
      });
    }
  }

  // Room management
  public joinExpedition(expeditionId: number, userId?: number): void {
    if (!this.socket) return;

    const actualUserId = userId || getUserId();
    if (!actualUserId) {
      console.warn('Cannot join expedition: no user ID available');
      return;
    }

    this.socket.emit('join_expedition', {
      expedition_id: expeditionId,
      user_id: actualUserId,
    });
  }

  public leaveExpedition(expeditionId: number, userId?: number): void {
    if (!this.socket) return;

    const actualUserId = userId || getUserId();
    if (!actualUserId) return;

    this.socket.emit('leave_expedition', {
      expedition_id: expeditionId,
      user_id: actualUserId,
    });
  }

  public joinUserRoom(userId: number): void {
    if (!this.socket) return;

    this.socket.emit('join_user_room', {
      user_id: userId,
    });
  }

  // Metrics requests
  public requestExpeditionMetrics(expeditionId: number): void {
    if (!this.socket) return;

    this.socket.emit('get_expedition_metrics', {
      expedition_id: expeditionId,
    });
  }

  // Connection management
  public connect(): void {
    if (this.socket && !this.connected) {
      this.socket.connect();
    }
  }

  public disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.connected = false;
    }
  }

  public reconnect(): void {
    if (this.socket) {
      this.disconnect();
      setTimeout(() => {
        this.connect();
      }, 1000);
    }
  }

  // Cleanup
  public destroy(): void {
    this.eventCallbacks.clear();
    if (this.socket) {
      this.socket.removeAllListeners();
      this.socket.disconnect();
      this.socket = null;
    }
    this.connected = false;
  }

  // Status methods
  public getStatus(): {
    connected: boolean;
    reconnectAttempts: number;
    socketId?: string;
  } {
    return {
      connected: this.connected,
      reconnectAttempts: this.reconnectAttempts,
      socketId: this.socket?.id,
    };
  }

  public getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }

  public isReconnecting(): boolean {
    return this.socket?.disconnected === true && this.reconnectAttempts > 0;
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    websocketService.destroy();
  });
}

export default websocketService;