import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import styled, { createGlobalStyle, ThemeProvider } from 'styled-components';

// Components
import { AppRouter } from '@/components/app/AppRouter';
import { AppLoadingScreen } from '@/components/app/AppLoadingScreen';
import { AppErrorScreen } from '@/components/app/AppErrorScreen';

// Hooks
import { useAppInitialization } from '@/hooks/useAppInitialization';

// Utils and theme
import { pirateColors, pirateTypography, pirateAnimations } from '@/utils/pirateTheme';

// Global styles
const GlobalStyle = createGlobalStyle`
  ${pirateAnimations.sparkle}
  ${pirateAnimations.sway}
  ${pirateAnimations.wave}
  ${pirateAnimations.fadeIn}
  ${pirateAnimations.slideIn}
  ${pirateAnimations.bounce}
  ${pirateAnimations.pulse}
  ${pirateAnimations.float}

  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  html, body, #root {
    height: 100%;
    width: 100%;
    overflow-x: hidden;
  }

  body {
    font-family: ${pirateTypography.body};
    background: ${pirateColors.parchment};
    color: ${pirateColors.primary};
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    user-select: none;
    -webkit-user-select: none;
    -webkit-touch-callout: none;
    -webkit-tap-highlight-color: transparent;
  }

  #root {
    min-height: 100vh;
    min-height: 100dvh;
  }

  /* Scrollbar styling for webkit browsers */
  ::-webkit-scrollbar {
    width: 8px;
  }

  ::-webkit-scrollbar-track {
    background: ${pirateColors.lightGold};
  }

  ::-webkit-scrollbar-thumb {
    background: ${pirateColors.secondary};
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: ${pirateColors.primary};
  }

  /* Focus styles */
  *:focus {
    outline: 2px solid ${pirateColors.secondary};
    outline-offset: 2px;
  }

  /* Selection styles */
  ::selection {
    background: ${pirateColors.secondary};
    color: ${pirateColors.white};
  }

  /* Hide loading screen when app is ready */
  .app-ready #loading-screen {
    display: none;
  }
`;

const AppContainer = styled.div`
  min-height: 100vh;
  min-height: 100dvh;
  position: relative;
`;

// Theme object for styled-components
const theme = {
  colors: pirateColors,
  typography: pirateTypography,
};

/**
 * Main App Component
 *
 * Simplified using extracted hooks and components:
 * - useAppInitialization: Handles Telegram validation and app setup
 * - AppLoadingScreen: Loading UI
 * - AppErrorScreen: Error UI
 * - AppRouter: Routing configuration
 */
const App: React.FC = () => {
  // Initialize app using extracted hook
  const { isLoading, error, retry } = useAppInitialization({
    loadingDelay: 1500,
    strictValidation: false,
  });

  // Loading state
  if (isLoading) {
    return (
      <ThemeProvider theme={theme}>
        <GlobalStyle />
        <AppLoadingScreen />
      </ThemeProvider>
    );
  }

  // Error state
  if (error) {
    return (
      <ThemeProvider theme={theme}>
        <GlobalStyle />
        <AppErrorScreen
          error={error}
          onRetry={retry}
        />
      </ThemeProvider>
    );
  }

  // Main application
  return (
    <ThemeProvider theme={theme}>
      <GlobalStyle />
      <AppContainer>
        <Router>
          <AppRouter />
        </Router>
      </AppContainer>
    </ThemeProvider>
  );
};

export default App;
