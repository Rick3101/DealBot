import { useRef, useCallback, useEffect } from 'react';
import { websocketService } from '@/services/websocketService';

interface ExpeditionRoomOptions {
  expeditionId?: number;
  autoJoin?: boolean;
}

interface UseExpeditionRoomReturn {
  joinExpedition: (expeditionId: number) => void;
  leaveExpedition: (expeditionId: number) => void;
  rejoinAll: () => void;
}

/**
 * Hook for managing expedition room subscriptions
 * Single Responsibility: Expedition room join/leave logic
 */
export const useExpeditionRoom = (
  isConnected: boolean,
  options: ExpeditionRoomOptions = {}
): UseExpeditionRoomReturn => {
  const { expeditionId, autoJoin = true } = options;

  const joinedExpeditionsRef = useRef<Set<number>>(new Set());

  // Join expedition room
  const joinExpedition = useCallback((expId: number) => {
    if (websocketService.isConnected()) {
      websocketService.joinExpedition(expId);
      joinedExpeditionsRef.current.add(expId);
      console.log(`Joined expedition ${expId}`);
    } else {
      console.warn(`Cannot join expedition ${expId}: WebSocket not connected`);
    }
  }, []);

  // Leave expedition room
  const leaveExpedition = useCallback((expId: number) => {
    if (websocketService.isConnected()) {
      websocketService.leaveExpedition(expId);
      joinedExpeditionsRef.current.delete(expId);
      console.log(`Left expedition ${expId}`);
    }
  }, []);

  // Rejoin all previously joined expeditions (e.g., after reconnection)
  const rejoinAll = useCallback(() => {
    if (websocketService.isConnected()) {
      joinedExpeditionsRef.current.forEach((expId) => {
        websocketService.joinExpedition(expId);
      });
      console.log('Rejoined all expeditions after reconnection');
    }
  }, []);

  // Auto-join expedition on mount or when connection is established
  useEffect(() => {
    if (expeditionId && autoJoin && isConnected) {
      joinExpedition(expeditionId);
    }

    return () => {
      if (expeditionId) {
        leaveExpedition(expeditionId);
      }
    };
  }, [expeditionId, autoJoin, isConnected, joinExpedition, leaveExpedition]);

  // Clear all joined expeditions on disconnect
  useEffect(() => {
    if (!isConnected) {
      joinedExpeditionsRef.current.clear();
    }
  }, [isConnected]);

  return {
    joinExpedition,
    leaveExpedition,
    rejoinAll,
  };
};
