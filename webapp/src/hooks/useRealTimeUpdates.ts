import { useWebSocketUpdates } from './useWebSocketUpdates';
import { useUpdateNotifications } from './useUpdateNotifications';
import { useExpeditionRoom } from './useExpeditionRoom';
import { WebSocketUpdate } from '@/types/expedition';

interface NotificationOptions {
  enableHaptic?: boolean;
  enablePopups?: boolean;
  autoJoinExpeditions?: boolean;
}

interface UseRealTimeUpdatesReturn {
  isConnected: boolean;
  updates: WebSocketUpdate[];
  connectionStatus: 'connected' | 'disconnected' | 'connecting' | 'error';
  joinExpedition: (expeditionId: number) => void;
  leaveExpedition: (expeditionId: number) => void;
  clearUpdates: () => void;
  reconnect: () => void;
}

/**
 * Main hook for real-time updates
 * Composes focused hooks for WebSocket, notifications, and room management
 *
 * Responsibilities:
 * - Hook composition
 * - Maintains backward-compatible API
 */
export const useRealTimeUpdates = (
  expeditionId?: number,
  options: NotificationOptions = {}
): UseRealTimeUpdatesReturn => {
  const {
    enableHaptic = true,
    enablePopups = true,
    autoJoinExpeditions = true,
  } = options;

  // Hook 1: Notification handling
  const { notify } = useUpdateNotifications({
    enableHaptic,
    enablePopups,
  });

  // Hook 2: WebSocket connection and updates
  const { isConnected, updates, connectionStatus, clearUpdates, reconnect } =
    useWebSocketUpdates({
      maxUpdates: 20,
      onUpdate: notify, // Trigger notifications when update is received
    });

  // Hook 3: Expedition room management
  const { joinExpedition, leaveExpedition } = useExpeditionRoom(
    isConnected,
    {
      expeditionId,
      autoJoin: autoJoinExpeditions,
    }
  );

  return {
    isConnected,
    updates,
    connectionStatus,
    joinExpedition,
    leaveExpedition,
    clearUpdates,
    reconnect,
  };
};
