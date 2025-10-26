import { useCallback } from 'react';
import { WebSocketUpdate } from '@/types/expedition';
import { hapticFeedback, showAlert } from '@/utils/telegram';
import {
  getHapticTypeForUpdate,
  getNotificationMessage,
} from '@/utils/notifications/updateNotifications';

interface NotificationOptions {
  enableHaptic?: boolean;
  enablePopups?: boolean;
}

interface UseUpdateNotificationsReturn {
  notify: (update: WebSocketUpdate) => void;
}

/**
 * Hook for managing update notifications and haptic feedback
 * Single Responsibility: Handle notification display and haptic feedback
 */
export const useUpdateNotifications = (
  options: NotificationOptions = {}
): UseUpdateNotificationsReturn => {
  const { enableHaptic = true, enablePopups = true } = options;

  // Handle update notification with haptic feedback and popups
  const notify = useCallback(
    (update: WebSocketUpdate) => {
      // Haptic feedback
      if (enableHaptic) {
        const hapticType = getHapticTypeForUpdate(update.type);
        hapticFeedback(hapticType);
      }

      // Show popup notifications for important events
      if (enablePopups) {
        const notification = getNotificationMessage(update);
        if (notification && notification.shouldShow) {
          showAlert(notification.message);
        }
      }
    },
    [enableHaptic, enablePopups]
  );

  return {
    notify,
  };
};
