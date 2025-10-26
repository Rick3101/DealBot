/**
 * useWebSocketStatus Hook
 *
 * Monitors WebSocket connection status and provides connection management.
 * Extracts connection monitoring logic from layout components.
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from '@/contexts/WebSocketContext';

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

export interface WebSocketStatusResult {
  /**
   * Current connection status
   */
  status: ConnectionStatus;

  /**
   * Whether WebSocket is connected
   */
  isConnected: boolean;

  /**
   * Whether WebSocket is connecting
   */
  isConnecting: boolean;

  /**
   * Whether WebSocket is disconnected
   */
  isDisconnected: boolean;

  /**
   * Manually reconnect
   */
  reconnect: () => void;

  /**
   * Connection latency in ms (if available)
   */
  latency?: number;

  /**
   * Last connection error
   */
  lastError?: string;
}

/**
 * Hook for monitoring WebSocket connection status
 *
 * @returns WebSocket status and controls
 */
export function useWebSocketStatus(): WebSocketStatusResult {
  const { socket, reconnect } = useWebSocket();

  const [status, setStatus] = useState<ConnectionStatus>(() => {
    if (!socket) return 'disconnected';
    return socket.connected ? 'connected' : 'disconnected';
  });

  const [latency, setLatency] = useState<number | undefined>();
  const [lastError, setLastError] = useState<string | undefined>();

  /**
   * Handles connection status changes
   */
  useEffect(() => {
    if (!socket) {
      setStatus('disconnected');
      return;
    }

    const handleConnect = () => {
      setStatus('connected');
      setLastError(undefined);
    };

    const handleDisconnect = (reason: string) => {
      setStatus('disconnected');
      setLastError(reason);
    };

    const handleConnecting = () => {
      setStatus('connecting');
    };

    const handleConnectError = (error: Error) => {
      setStatus('disconnected');
      setLastError(error.message);
    };

    const handleReconnect = () => {
      setStatus('connecting');
    };

    // Set initial status
    setStatus(socket.connected ? 'connected' : 'disconnected');

    // Register event listeners
    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);
    socket.on('connect_error', handleConnectError);
    socket.on('reconnect_attempt', handleReconnect);

    // Cleanup
    return () => {
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      socket.off('connect_error', handleConnectError);
      socket.off('reconnect_attempt', handleReconnect);
    };
  }, [socket]);

  /**
   * Ping mechanism to measure latency
   */
  useEffect(() => {
    if (!socket || !socket.connected) {
      setLatency(undefined);
      return;
    }

    const pingInterval = setInterval(() => {
      const start = Date.now();

      socket.emit('ping', () => {
        const duration = Date.now() - start;
        setLatency(duration);
      });
    }, 5000); // Ping every 5 seconds

    return () => {
      clearInterval(pingInterval);
    };
  }, [socket, status]);

  const handleReconnect = useCallback(() => {
    setStatus('connecting');
    reconnect();
  }, [reconnect]);

  return {
    status,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    isDisconnected: status === 'disconnected',
    reconnect: handleReconnect,
    latency,
    lastError,
  };
}

/**
 * Hook for connection quality monitoring
 *
 * Provides additional metrics beyond basic status
 */
export interface ConnectionQuality {
  /**
   * Connection quality rating (1-5, 5 being best)
   */
  rating: number;

  /**
   * Connection quality label
   */
  label: 'excellent' | 'good' | 'fair' | 'poor' | 'disconnected';

  /**
   * Average latency
   */
  averageLatency: number;

  /**
   * Reconnection attempts in current session
   */
  reconnectionAttempts: number;
}

export function useConnectionQuality(): ConnectionQuality {
  const { status, latency } = useWebSocketStatus();
  const [reconnectionAttempts, setReconnectionAttempts] = useState(0);
  const [latencyHistory, setLatencyHistory] = useState<number[]>([]);

  // Track reconnection attempts
  useEffect(() => {
    if (status === 'connecting') {
      setReconnectionAttempts(prev => prev + 1);
    } else if (status === 'connected') {
      setReconnectionAttempts(0);
    }
  }, [status]);

  // Track latency history
  useEffect(() => {
    if (latency !== undefined) {
      setLatencyHistory(prev => [...prev.slice(-9), latency]); // Keep last 10 values
    }
  }, [latency]);

  // Calculate average latency
  const averageLatency = latencyHistory.length > 0
    ? latencyHistory.reduce((a, b) => a + b, 0) / latencyHistory.length
    : 0;

  // Determine connection quality
  const getQuality = (): { rating: number; label: ConnectionQuality['label'] } => {
    if (status === 'disconnected') {
      return { rating: 0, label: 'disconnected' };
    }

    if (averageLatency === 0) {
      return { rating: 3, label: 'fair' }; // No data yet
    }

    if (averageLatency < 50) {
      return { rating: 5, label: 'excellent' };
    } else if (averageLatency < 100) {
      return { rating: 4, label: 'good' };
    } else if (averageLatency < 200) {
      return { rating: 3, label: 'fair' };
    } else {
      return { rating: 2, label: 'poor' };
    }
  };

  const quality = getQuality();

  return {
    rating: quality.rating,
    label: quality.label,
    averageLatency,
    reconnectionAttempts,
  };
}
