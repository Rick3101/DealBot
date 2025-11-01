// CRITICAL: Import polyfills FIRST before any other imports
import './polyfills/fetch-polyfill';

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Error boundary component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('React Error Boundary caught an error:', error, errorInfo);

    // Log to external service in production
    if (import.meta.env.PROD) {
      // You could send this to a logging service
      console.error('Production error:', { error, errorInfo });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '2rem',
          textAlign: 'center',
          backgroundColor: '#F5DEB3',
          color: '#8B4513',
          fontFamily: 'Roboto, sans-serif'
        }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>💀</div>
          <h1 style={{
            fontFamily: '"Pirata One", cursive',
            fontSize: '1.5rem',
            marginBottom: '1rem'
          }}>
            Arrr! The ship has run aground
          </h1>
          <p style={{ marginBottom: '2rem', maxWidth: '400px' }}>
            Something went wrong with the Pirates Expedition app.
            The crew is working to fix it!
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              background: '#DAA520',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              fontFamily: '"Pirata One", cursive',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = '#8B4513';
              e.currentTarget.style.transform = 'translateY(-1px)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = '#DAA520';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            ⚓ Reload Ship
          </button>
          {import.meta.env.DEV && (
            <details style={{ marginTop: '2rem', textAlign: 'left' }}>
              <summary style={{ cursor: 'pointer', marginBottom: '1rem' }}>
                Error Details (Development)
              </summary>
              <pre style={{
                background: '#fff',
                padding: '1rem',
                borderRadius: '4px',
                fontSize: '0.8rem',
                overflow: 'auto',
                maxWidth: '100%'
              }}>
                {this.state.error?.stack}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

// Wait for Telegram WebApp to be ready
const waitForTelegram = (): Promise<void> => {
  return new Promise((resolve) => {
    // Check if Telegram is already available
    if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
      console.log('Telegram WebApp is ready');
      resolve();
      return;
    }

    // In development, proceed without Telegram after a short delay
    if (import.meta.env.DEV) {
      console.log('Development mode: proceeding without Telegram WebApp');
      setTimeout(resolve, 100);
      return;
    }

    // Wait for Telegram to load (max 3 seconds)
    const maxWaitTime = 3000;
    const checkInterval = 100;
    let elapsedTime = 0;

    const checkTelegram = setInterval(() => {
      elapsedTime += checkInterval;

      if (window.Telegram?.WebApp) {
        clearInterval(checkTelegram);
        console.log('Telegram WebApp loaded');
        resolve();
      } else if (elapsedTime >= maxWaitTime) {
        clearInterval(checkTelegram);
        console.warn('Telegram WebApp not available after timeout');
        resolve();
      }
    }, checkInterval);
  });
};

// Initialize the app
const initApp = async () => {
  // Wait for Telegram to be ready
  await waitForTelegram();

  const rootElement = document.getElementById('root');
  if (!rootElement) {
    throw new Error('Root element not found');
  }

  const root = ReactDOM.createRoot(rootElement);

  root.render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>
  );

  // Hide loading screen after React has mounted
  setTimeout(() => {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      loadingScreen.style.display = 'none';
    }
  }, 100);

  console.log('Pirates Expedition Mini App initialized');
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}

// Service Worker registration DISABLED for Telegram Mini Apps
// Telegram iframe environment doesn't support service workers properly
// if ('serviceWorker' in navigator && import.meta.env.PROD) {
//   window.addEventListener('load', () => {
//     navigator.serviceWorker
//       .register('/sw.js')
//       .then((registration) => {
//         console.log('SW registered: ', registration);
//       })
//       .catch((registrationError) => {
//         console.log('SW registration failed: ', registrationError);
//       });
//   });
// }

// Performance monitoring DISABLED for Telegram Mini Apps
// web-vitals library tries to access Request API which may not be available
// if (import.meta.env.PROD) {
//   // Monitor web vitals - using dynamic access for compatibility
//   import('web-vitals').then((webVitals: any) => {
//     ['onCLS', 'onFID', 'onFCP', 'onLCP', 'onTTFB'].forEach(metric => {
//       if (webVitals[metric]) {
//         webVitals[metric](console.log);
//       }
//     });
//   }).catch(() => {
//     // web-vitals not available
//   });
// }

// Handle unhandled errors
window.addEventListener('error', (event) => {
  console.error('Unhandled error:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  event.preventDefault(); // Prevent the default browser behavior
});