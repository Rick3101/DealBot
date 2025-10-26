import React from 'react';
import styled, { css } from 'styled-components';
import { motion } from 'framer-motion';
import { pirateColors, pirateTypography, spacing, mixins } from '@/utils/pirateTheme';
import { hapticFeedback } from '@/utils/telegram';

interface PirateButtonProps {
  children: React.ReactNode;
  onClick?: (e?: React.MouseEvent<HTMLButtonElement>) => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: string;
  fullWidth?: boolean;
  className?: string;
  title?: string;
}

const ButtonBase = styled(motion.button)<{
  $variant: string;
  $size: string;
  $fullWidth: boolean;
}>`
  ${mixins.pirateButton}

  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: ${spacing.sm};
  border: none;
  border-radius: 8px;
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  user-select: none;
  -webkit-tap-highlight-color: transparent;

  width: ${props => props.$fullWidth ? '100%' : 'auto'};

  /* Size variants */
  ${props => props.$size === 'sm' && css`
    padding: ${spacing.sm} ${spacing.md};
    font-size: ${pirateTypography.sizes.sm};
    min-height: 36px;
  `}

  ${props => props.$size === 'md' && css`
    padding: ${spacing.md} ${spacing.xl};
    font-size: ${pirateTypography.sizes.base};
    min-height: 44px;
  `}

  ${props => props.$size === 'lg' && css`
    padding: ${spacing.lg} ${spacing['2xl']};
    font-size: ${pirateTypography.sizes.lg};
    min-height: 52px;
  `}

  /* Variant styles */
  ${props => props.$variant === 'primary' && css`
    background: linear-gradient(145deg, ${pirateColors.secondary}, ${pirateColors.primary});
    color: ${pirateColors.white};
    box-shadow: 0 2px 8px rgba(139, 69, 19, 0.2);

    &:hover:not(:disabled) {
      background: linear-gradient(145deg, ${pirateColors.primary}, ${pirateColors.darkBrown});
      box-shadow: 0 4px 12px rgba(139, 69, 19, 0.3);
    }
  `}

  ${props => props.$variant === 'secondary' && css`
    background: linear-gradient(145deg, ${pirateColors.lightGold}, ${pirateColors.parchment});
    color: ${pirateColors.primary};
    border: 2px solid ${pirateColors.primary};
    box-shadow: 0 2px 8px rgba(139, 69, 19, 0.1);

    &:hover:not(:disabled) {
      background: linear-gradient(145deg, ${pirateColors.parchment}, ${pirateColors.lightGold});
      box-shadow: 0 4px 12px rgba(139, 69, 19, 0.2);
    }
  `}

  ${props => props.$variant === 'danger' && css`
    background: linear-gradient(145deg, ${pirateColors.danger}, #B91C1C);
    color: ${pirateColors.white};
    box-shadow: 0 2px 8px rgba(220, 20, 60, 0.2);

    &:hover:not(:disabled) {
      background: linear-gradient(145deg, #B91C1C, #991B1B);
      box-shadow: 0 4px 12px rgba(220, 20, 60, 0.3);
    }
  `}

  ${props => props.$variant === 'success' && css`
    background: linear-gradient(145deg, ${pirateColors.success}, #16A34A);
    color: ${pirateColors.white};
    box-shadow: 0 2px 8px rgba(34, 139, 34, 0.2);

    &:hover:not(:disabled) {
      background: linear-gradient(145deg, #16A34A, #15803D);
      box-shadow: 0 4px 12px rgba(34, 139, 34, 0.3);
    }
  `}

  ${props => props.$variant === 'outline' && css`
    background: transparent;
    color: ${pirateColors.primary};
    border: 2px solid ${pirateColors.primary};
    box-shadow: none;

    &:hover:not(:disabled) {
      background: ${pirateColors.primary};
      color: ${pirateColors.white};
      box-shadow: 0 4px 12px rgba(139, 69, 19, 0.2);
    }
  `}

  &:active {
    transform: translateY(1px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none !important;
  }

  /* Ripple effect */
  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.3);
    transform: translate(-50%, -50%);
    transition: width 0.3s ease, height 0.3s ease;
  }

  &:active::before {
    width: 100%;
    height: 100%;
  }
`;

const LoadingSpinner = styled.div`
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const IconWrapper = styled.span`
  font-size: 1.2em;
  line-height: 1;
`;

export const PirateButton: React.FC<PirateButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  fullWidth = false,
  className,
  title,
}) => {
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled || loading) {
      return;
    }

    // Trigger haptic feedback
    hapticFeedback('light');

    // Call the onClick handler (no preventDefault needed - button type="button" handles it)
    onClick?.(e);
  };

  return (
    <ButtonBase
      type="button"
      className={className}
      title={title}
      $variant={variant}
      $size={size}
      $fullWidth={fullWidth}
      disabled={disabled || loading}
      onClick={handleClick}
      whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {icon && <IconWrapper>{icon}</IconWrapper>}
          {children}
        </>
      )}
    </ButtonBase>
  );
};