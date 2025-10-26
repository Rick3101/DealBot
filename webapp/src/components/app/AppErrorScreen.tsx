import React from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

interface AppErrorScreenProps {
  error?: Error | null;
  onRetry?: () => void;
}

/**
 * Global error screen for app-level failures
 * Used for critical errors that prevent the entire app from loading
 */
export const AppErrorScreen: React.FC<AppErrorScreenProps> = ({
  error,
  onRetry,
}) => {
  const handleReload = () => {
    window.location.reload();
  };

  const isDevelopment = import.meta.env.DEV;

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
      <div className="max-w-lg w-full bg-white rounded-xl shadow-2xl p-8 space-y-6">
        {/* Error Icon */}
        <div className="flex justify-center">
          <div className="rounded-full bg-red-500 p-4">
            <AlertOctagon className="w-12 h-12 text-white" />
          </div>
        </div>

        {/* Error Message */}
        <div className="text-center space-y-3">
          <h1 className="text-3xl font-bold text-gray-900">
            Application Error
          </h1>
          <p className="text-lg text-gray-600">
            The application encountered a critical error and cannot continue.
          </p>
        </div>

        {/* Error Details (Development Only) */}
        {isDevelopment && error && (
          <div className="bg-red-100 border-2 border-red-300 rounded-lg p-4 space-y-2">
            <div className="font-bold text-red-900">
              Error Details (Development Mode):
            </div>
            <div className="text-sm font-mono text-red-800 space-y-1">
              <div className="font-semibold">{error.name}</div>
              <div className="break-words">{error.message}</div>
              {error.stack && (
                <details className="mt-2">
                  <summary className="cursor-pointer font-semibold">
                    Stack Trace
                  </summary>
                  <pre className="mt-2 overflow-auto max-h-48 text-xs p-2 bg-red-50 rounded">
                    {error.stack}
                  </pre>
                </details>
              )}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold text-lg"
            >
              <RefreshCw className="w-6 h-6" />
              Retry
            </button>
          )}

          <button
            onClick={handleReload}
            className="w-full px-6 py-4 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 transition-colors font-semibold text-lg"
          >
            Reload Application
          </button>
        </div>

        {/* Support Information */}
        <div className="border-t border-gray-200 pt-6 space-y-2">
          <div className="text-center text-sm text-gray-600">
            <p className="font-semibold">Need help?</p>
            <p>Please try reloading the page or contact support if the issue persists.</p>
          </div>

          {isDevelopment && (
            <div className="text-center text-xs text-gray-500 mt-4">
              <p>Development Mode: Check console for additional error details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
