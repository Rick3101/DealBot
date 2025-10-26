import { WebSocketUpdate } from '@/types/expedition';

/**
 * Notification utility functions for WebSocket updates
 * Extracted from useRealTimeUpdates to improve testability and separation of concerns
 */

export type HapticType = 'light' | 'success' | 'warning' | 'error';

/**
 * Get the appropriate haptic feedback type for an update
 */
export const getHapticTypeForUpdate = (updateType: string): HapticType => {
  switch (updateType) {
    case 'ITEM_CONSUMED':
      return 'light';
    case 'EXPEDITION_COMPLETED':
      return 'success';
    case 'DEADLINE_WARNING':
      return 'warning';
    case 'EXPEDITION_CREATED':
      return 'light';
    default:
      return 'light';
  }
};

/**
 * Generate notification message for an update
 * Returns null if no notification should be shown
 */
export const getNotificationMessage = (update: WebSocketUpdate): { message: string; shouldShow: boolean } | null => {
  let message = '';
  let shouldShow = false;

  switch (update.type) {
    case 'ITEM_CONSUMED':
      message = `${update.pirate_name || 'A pirate'} consumed ${update.item_name}!`;
      shouldShow = true;
      break;
    case 'EXPEDITION_COMPLETED':
      message = `Expedition "${update.expedition_name}" has been completed!`;
      shouldShow = true;
      break;
    case 'DEADLINE_WARNING':
      message = `Expedition "${update.expedition_name}" deadline is approaching!`;
      shouldShow = true;
      break;
    case 'EXPEDITION_CREATED':
      message = `New expedition "${update.expedition_name}" has been created!`;
      shouldShow = false; // Less critical
      break;
    default:
      return null;
  }

  if (!message) return null;

  return { message, shouldShow };
};

/**
 * Check if an update should trigger a notification
 */
export const shouldNotifyUpdate = (update: WebSocketUpdate): boolean => {
  const notification = getNotificationMessage(update);
  return notification !== null && notification.shouldShow;
};

/**
 * Format update for display
 */
export const formatUpdateForDisplay = (update: WebSocketUpdate): string => {
  const notification = getNotificationMessage(update);
  return notification?.message || `Update: ${update.type}`;
};
