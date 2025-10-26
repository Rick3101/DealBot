/**
 * AppLoadingScreen Component
 *
 * Displays loading screen during app initialization.
 * Provides visual feedback with pirate-themed animations.
 */

import React from 'react';
import styled from 'styled-components';
import { pirateColors, pirateTypography } from '@/utils/pirateTheme';

const LoadingOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: ${pirateColors.parchment};
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
`;

const LoadingContent = styled.div`
  text-align: center;
  max-width: 300px;
  padding: 2rem;
`;

const LoadingLogo = styled.div`
  font-size: 4rem;
  margin-bottom: 1rem;
  animation: float 2s ease-in-out infinite;
`;

const LoadingTitle = styled.h1`
  font-family: ${pirateTypography.headings};
  font-size: 1.5rem;
  color: ${pirateColors.primary};
  margin-bottom: 0.5rem;
`;

const LoadingSubtitle = styled.p`
  color: ${pirateColors.muted};
  margin-bottom: 2rem;
  font-size: 0.9rem;
`;

const LoadingSpinner = styled.div`
  width: 40px;
  height: 40px;
  border: 3px solid ${pirateColors.lightGold};
  border-top: 3px solid ${pirateColors.secondary};
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const LoadingProgress = styled.div<{ progress?: number }>`
  width: 100%;
  height: 4px;
  background: ${pirateColors.lightGold};
  border-radius: 2px;
  margin-top: 1.5rem;
  overflow: hidden;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: ${props => props.progress || 0}%;
    background: ${pirateColors.secondary};
    transition: width 0.3s ease;
  }
`;

export interface AppLoadingScreenProps {
  /**
   * Loading title
   */
  title?: string;

  /**
   * Loading subtitle
   */
  subtitle?: string;

  /**
   * Loading logo emoji
   */
  logo?: string;

  /**
   * Show progress bar
   */
  showProgress?: boolean;

  /**
   * Progress percentage (0-100)
   */
  progress?: number;
}

/**
 * App loading screen component
 */
export const AppLoadingScreen: React.FC<AppLoadingScreenProps> = ({
  title = 'Setting Sail...',
  subtitle = 'Preparing your pirate expedition dashboard',
  logo = '⛵',
  showProgress = false,
  progress = 0,
}) => {
  return (
    <LoadingOverlay>
      <LoadingContent>
        <LoadingLogo>{logo}</LoadingLogo>
        <LoadingTitle>{title}</LoadingTitle>
        <LoadingSubtitle>{subtitle}</LoadingSubtitle>
        <LoadingSpinner />
        {showProgress && <LoadingProgress progress={progress} />}
      </LoadingContent>
    </LoadingOverlay>
  );
};

/**
 * Minimal loading spinner component
 */
export const LoadingSpinnerMinimal: React.FC<{
  size?: 'small' | 'medium' | 'large';
}> = ({ size = 'medium' }) => {
  const sizes = {
    small: 20,
    medium: 40,
    large: 60,
  };

  const spinnerSize = sizes[size];

  const Spinner = styled.div`
    width: ${spinnerSize}px;
    height: ${spinnerSize}px;
    border: 3px solid ${pirateColors.lightGold};
    border-top: 3px solid ${pirateColors.secondary};
    border-radius: 50%;
    animation: spin 1s linear infinite;

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;

  return <Spinner />;
};

/**
 * Loading skeleton component for content placeholders
 */
export const LoadingSkeleton: React.FC<{
  width?: string;
  height?: string;
  borderRadius?: string;
}> = ({
  width = '100%',
  height = '20px',
  borderRadius = '4px',
}) => {
  const Skeleton = styled.div`
    width: ${width};
    height: ${height};
    border-radius: ${borderRadius};
    background: linear-gradient(
      90deg,
      ${pirateColors.lightGold} 25%,
      ${pirateColors.parchment} 50%,
      ${pirateColors.lightGold} 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;

    @keyframes shimmer {
      0% {
        background-position: -200% 0;
      }
      100% {
        background-position: 200% 0;
      }
    }
  `;

  return <Skeleton />;
};
