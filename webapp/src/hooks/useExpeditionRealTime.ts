import { useEffect } from 'react';
import { websocketService } from '@/services/websocketService';

interface ExpeditionUpdateEvent {
  type: 'EXPEDITION_CREATED' | 'EXPEDITION_COMPLETED' | 'EXPEDITION_UPDATED';
  expeditionId?: number;
  [key: string]: any;
}

interface ItemConsumedEvent {
  expeditionId: number;
  itemId: number;
  [key: string]: any;
}

interface UseExpeditionRealTimeOptions {
  enabled?: boolean;
  onExpeditionUpdate?: (data: ExpeditionUpdateEvent) => void;
  onItemConsumed?: (data: ItemConsumedEvent) => void;
  onExpeditionCompleted?: (data: ExpeditionUpdateEvent) => void;
  onExpeditionCreated?: (data: ExpeditionUpdateEvent) => void;
}

/**
 * Hook for managing real-time WebSocket updates for expeditions
 * Single Responsibility: WebSocket event subscription and handling
 * Reusable for any component that needs expedition real-time updates
 */
export const useExpeditionRealTime = (
  options: UseExpeditionRealTimeOptions = {}
): void => {
  const {
    enabled = true,
    onExpeditionUpdate,
    onItemConsumed,
    onExpeditionCompleted,
    onExpeditionCreated,
  } = options;

  useEffect(() => {
    if (!enabled) return;

    // Expedition update handler
    const handleExpeditionUpdate = (data: any) => {
      console.log('Real-time expedition update:', data);
      if (onExpeditionUpdate) {
        onExpeditionUpdate(data);
      }
    };

    // Item consumed handler
    const handleItemConsumed = (data: any) => {
      console.log('Real-time item consumed:', data);
      if (onItemConsumed) {
        onItemConsumed(data);
      }
    };

    // Expedition completed handler
    const handleExpeditionCompleted = (data: any) => {
      console.log('Real-time expedition completed:', data);
      if (onExpeditionCompleted) {
        onExpeditionCompleted(data);
      }
    };

    // Expedition created handler
    const handleExpeditionCreated = (data: any) => {
      console.log('Real-time expedition created:', data);
      if (onExpeditionCreated) {
        onExpeditionCreated(data);
      }
    };

    // Subscribe to WebSocket events
    websocketService.on('expeditionUpdate', handleExpeditionUpdate);
    websocketService.on('itemConsumed', handleItemConsumed);
    websocketService.on('expeditionCompleted', handleExpeditionCompleted);
    websocketService.on('expeditionCreated', handleExpeditionCreated);

    return () => {
      // Cleanup subscriptions
      websocketService.off('expeditionUpdate', handleExpeditionUpdate);
      websocketService.off('itemConsumed', handleItemConsumed);
      websocketService.off('expeditionCompleted', handleExpeditionCompleted);
      websocketService.off('expeditionCreated', handleExpeditionCreated);
    };
  }, [
    enabled,
    onExpeditionUpdate,
    onItemConsumed,
    onExpeditionCompleted,
    onExpeditionCreated,
  ]);
};
