/**
 * ConnectionStatus Component
 *
 * Displays WebSocket connection status with visual indicator.
 * Shows connected, disconnected, or connecting states.
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface ConnectionStatusProps {
  /**
   * Connection status
   */
  status: 'connected' | 'disconnected' | 'connecting';

  /**
   * Optional reconnect callback
   */
  onReconnect?: () => void;

  /**
   * Show status text
   */
  showText?: boolean;

  /**
   * Compact mode (smaller indicator)
   */
  compact?: boolean;

  /**
   * Custom className
   */
  className?: string;
}

/**
 * Connection status indicator component
 */
export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  status,
  onReconnect,
  showText = true,
  compact = false,
  className = '',
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'bg-green-500';
      case 'connecting':
        return 'bg-yellow-500';
      case 'disconnected':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'disconnected':
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'connected':
        return '⚓';
      case 'connecting':
        return '🌊';
      case 'disconnected':
        return '⚠';
      default:
        return '❓';
    }
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Status indicator */}
      <div className="relative">
        <motion.div
          className={`
            ${getStatusColor()}
            ${compact ? 'w-2 h-2' : 'w-3 h-3'}
            rounded-full
          `}
          animate={status === 'connecting' ? {
            scale: [1, 1.2, 1],
            opacity: [1, 0.7, 1],
          } : {}}
          transition={{
            duration: 1.5,
            repeat: status === 'connecting' ? Infinity : 0,
          }}
        />

        {/* Pulse effect for connected state */}
        {status === 'connected' && !compact && (
          <motion.div
            className="absolute inset-0 bg-green-500 rounded-full"
            initial={{ scale: 1, opacity: 0.6 }}
            animate={{
              scale: 2,
              opacity: 0,
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
            }}
          />
        )}
      </div>

      {/* Status text */}
      {showText && !compact && (
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {getStatusIcon()} {getStatusText()}
        </span>
      )}

      {/* Reconnect button for disconnected state */}
      <AnimatePresence>
        {status === 'disconnected' && onReconnect && !compact && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={onReconnect}
            className="
              text-xs px-2 py-1 rounded
              bg-blue-500 text-white
              hover:bg-blue-600
              active:scale-95
              transition-all
            "
          >
            Reconnect
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
};

/**
 * Compact connection status badge
 */
export const ConnectionBadge: React.FC<{
  status: 'connected' | 'disconnected' | 'connecting';
}> = ({ status }) => {
  return (
    <ConnectionStatus
      status={status}
      compact
      showText={false}
    />
  );
};

/**
 * Full connection status bar
 */
export const ConnectionStatusBar: React.FC<{
  status: 'connected' | 'disconnected' | 'connecting';
  onReconnect?: () => void;
  message?: string;
}> = ({ status, onReconnect, message }) => {
  if (status === 'connected' && !message) {
    return null; // Hide when connected and no message
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`
        w-full px-4 py-2 text-sm
        flex items-center justify-between
        ${status === 'connected' ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-200' : ''}
        ${status === 'connecting' ? 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200' : ''}
        ${status === 'disconnected' ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200' : ''}
      `}
    >
      <div className="flex items-center gap-2">
        <ConnectionStatus
          status={status}
          showText
          compact={false}
          onReconnect={onReconnect}
        />
        {message && <span>{message}</span>}
      </div>
    </motion.div>
  );
};
