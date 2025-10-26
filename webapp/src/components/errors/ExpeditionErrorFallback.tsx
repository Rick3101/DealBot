import React, { ErrorInfo } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface ExpeditionErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  onReset?: () => void;
}

/**
 * Fallback UI displayed when an error is caught by ExpeditionErrorBoundary
 * Provides user-friendly error message and recovery options
 */
export const ExpeditionErrorFallback: React.FC<ExpeditionErrorFallbackProps> = ({
  error,
  errorInfo,
  onReset,
}) => {
  const isDevelopment = import.meta.env.DEV;

  const handleGoHome = () => {
    window.location.href = '/';
  };

  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 space-y-6">
        {/* Error Icon */}
        <div className="flex justify-center">
          <div className="rounded-full bg-red-100 p-3">
            <AlertTriangle className="w-8 h-8 text-red-600" />
          </div>
        </div>

        {/* Error Message */}
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold text-gray-900">
            Something went wrong
          </h1>
          <p className="text-gray-600">
            We encountered an unexpected error. Don't worry, your data is safe.
          </p>
        </div>

        {/* Error Details (Development Only) */}
        {isDevelopment && error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 space-y-2">
            <div className="font-semibold text-red-900 text-sm">
              Error Details (Development Mode):
            </div>
            <div className="text-xs font-mono text-red-800 overflow-auto max-h-32">
              <div className="font-bold">{error.name}:</div>
              <div>{error.message}</div>
            </div>
            {errorInfo && (
              <details className="text-xs text-red-800">
                <summary className="cursor-pointer font-semibold">
                  Component Stack
                </summary>
                <pre className="mt-2 overflow-auto max-h-40 text-xs">
                  {errorInfo.componentStack}
                </pre>
              </details>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-3">
          {onReset && (
            <button
              onClick={onReset}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              <RefreshCw className="w-5 h-5" />
              Try Again
            </button>
          )}

          <button
            onClick={handleGoHome}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 transition-colors font-medium"
          >
            <Home className="w-5 h-5" />
            Go to Dashboard
          </button>

          <button
            onClick={handleReload}
            className="w-full text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            Reload Page
          </button>
        </div>

        {/* Support Message */}
        <div className="text-center text-sm text-gray-500">
          If this problem persists, please contact support.
        </div>
      </div>
    </div>
  );
};
