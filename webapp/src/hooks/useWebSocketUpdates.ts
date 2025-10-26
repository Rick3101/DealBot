import { useState, useEffect, useRef, useCallback } from 'react';
import { WebSocketUpdate } from '@/types/expedition';
import { websocketService } from '@/services/websocketService';

interface WebSocketUpdateOptions {
  maxUpdates?: number;
  onUpdate?: (update: WebSocketUpdate) => void;
}

interface UseWebSocketUpdatesReturn {
  isConnected: boolean;
  updates: WebSocketUpdate[];
  connectionStatus: 'connected' | 'disconnected' | 'connecting' | 'error';
  clearUpdates: () => void;
  reconnect: () => void;
}

/**
 * Hook for managing WebSocket connection and update collection
 * Single Responsibility: WebSocket event handling and update state management
 */
export const useWebSocketUpdates = (
  options: WebSocketUpdateOptions = {}
): UseWebSocketUpdatesReturn => {
  const { maxUpdates = 20, onUpdate } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [updates, setUpdates] = useState<WebSocketUpdate[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<
    'connected' | 'disconnected' | 'connecting' | 'error'
  >('disconnected');

  const mountedRef = useRef(true);

  // Add update to the list
  const addUpdate = useCallback(
    (update: WebSocketUpdate) => {
      if (!mountedRef.current) return;

      setUpdates((prev) => {
        const newUpdates = [update, ...prev.slice(0, maxUpdates - 1)];
        return newUpdates;
      });

      // Trigger callback if provided
      if (onUpdate) {
        onUpdate(update);
      }
    },
    [maxUpdates, onUpdate]
  );

  // Connection event handlers
  const handleConnected = useCallback(() => {
    console.log('WebSocket connected');
    setIsConnected(true);
    setConnectionStatus('connected');
  }, []);

  const handleDisconnected = useCallback((data: any) => {
    console.log('WebSocket disconnected:', data);
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const handleConnectError = useCallback(() => {
    console.error('WebSocket connection error');
    setIsConnected(false);
    setConnectionStatus('error');
  }, []);

  const handleReconnected = useCallback((data: any) => {
    console.log('WebSocket reconnected:', data);
    setIsConnected(true);
    setConnectionStatus('connected');
  }, []);

  // Clear updates
  const clearUpdates = useCallback(() => {
    setUpdates([]);
  }, []);

  // Reconnect
  const reconnect = useCallback(() => {
    setConnectionStatus('connecting');
    websocketService.reconnect();
  }, []);

  // Set up WebSocket event listeners
  useEffect(() => {
    // Connection events
    websocketService.on('connected', handleConnected);
    websocketService.on('disconnected', handleDisconnected);
    websocketService.on('error', handleConnectError);
    websocketService.on('reconnected', handleReconnected);

    // Update events
    websocketService.on('expeditionUpdate', addUpdate);
    websocketService.on('itemConsumed', addUpdate);
    websocketService.on('expeditionCompleted', addUpdate);
    websocketService.on('expeditionCreated', addUpdate);
    websocketService.on('deadlineWarning', addUpdate);

    // Check initial connection status
    if (websocketService.isConnected()) {
      handleConnected();
    }

    return () => {
      websocketService.off('connected', handleConnected);
      websocketService.off('disconnected', handleDisconnected);
      websocketService.off('error', handleConnectError);
      websocketService.off('reconnected', handleReconnected);

      websocketService.off('expeditionUpdate', addUpdate);
      websocketService.off('itemConsumed', addUpdate);
      websocketService.off('expeditionCompleted', addUpdate);
      websocketService.off('expeditionCreated', addUpdate);
      websocketService.off('deadlineWarning', addUpdate);
    };
  }, [
    handleConnected,
    handleDisconnected,
    handleConnectError,
    handleReconnected,
    addUpdate,
  ]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return {
    isConnected,
    updates,
    connectionStatus,
    clearUpdates,
    reconnect,
  };
};
