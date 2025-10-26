import React from 'react';
import styled, { css } from 'styled-components';
import { motion } from 'framer-motion';
import { pirateColors, spacing, mixins, shadows } from '@/utils/pirateTheme';

interface PirateCardProps {
  children: React.ReactNode;
  variant?: 'default' | 'bordered' | 'elevated' | 'flat';
  padding?: 'sm' | 'md' | 'lg';
  clickable?: boolean;
  onClick?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

const CardBase = styled(motion.div)<{
  $variant: string;
  $padding: string;
  $clickable: boolean;
}>`
  ${mixins.pirateCard}

  /* Padding variants */
  ${props => props.$padding === 'sm' && css`
    padding: ${spacing.md};
  `}

  ${props => props.$padding === 'md' && css`
    padding: ${spacing.lg};
  `}

  ${props => props.$padding === 'lg' && css`
    padding: ${spacing.xl};
  `}

  /* Visual variants */
  ${props => props.$variant === 'default' && css`
    background: linear-gradient(135deg, ${pirateColors.parchment}, ${pirateColors.lightGold});
    border: 2px solid ${pirateColors.primary};
    box-shadow: ${shadows.md};
  `}

  ${props => props.$variant === 'bordered' && css`
    background: ${pirateColors.white};
    border: 3px solid ${pirateColors.secondary};
    box-shadow: ${shadows.sm};
  `}

  ${props => props.$variant === 'elevated' && css`
    background: linear-gradient(135deg, ${pirateColors.parchment}, ${pirateColors.lightGold});
    border: 2px solid ${pirateColors.primary};
    box-shadow: ${shadows.lg};
    transform: translateY(-2px);
  `}

  ${props => props.$variant === 'flat' && css`
    background: ${pirateColors.parchment};
    border: 1px solid ${pirateColors.primary};
    box-shadow: none;
  `}

  /* Clickable styles */
  ${props => props.$clickable && css`
    cursor: pointer;
    user-select: none;
    -webkit-tap-highlight-color: transparent;

    &:hover {
      transform: translateY(-4px);
      box-shadow: ${shadows.xl};
    }

    &:active {
      transform: translateY(-1px);
      box-shadow: ${shadows.md};
    }
  `}

  /* Responsive design */
  @media (max-width: 768px) {
    border-radius: 8px;

    ${props => props.$padding === 'lg' && css`
      padding: ${spacing.lg};
    `}
  }
`;

const CardHeader = styled.div`
  margin-bottom: ${spacing.lg};
  padding-bottom: ${spacing.md};
  border-bottom: 2px solid ${pirateColors.secondary};

  &:last-child {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
  }
`;

const CardTitle = styled.h3`
  font-family: 'Pirata One', cursive;
  font-size: 1.5rem;
  color: ${pirateColors.primary};
  margin: 0;
  margin-bottom: ${spacing.sm};
`;

const CardSubtitle = styled.p`
  color: ${pirateColors.muted};
  margin: 0;
  font-size: 0.9rem;
`;

const CardBody = styled.div`
  flex: 1;
`;

const CardFooter = styled.div`
  margin-top: ${spacing.lg};
  padding-top: ${spacing.md};
  border-top: 1px solid ${pirateColors.lightGold};
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: ${spacing.md};

  &:first-child {
    margin-top: 0;
    padding-top: 0;
    border-top: none;
  }

  @media (max-width: 640px) {
    flex-direction: column;
    align-items: stretch;
  }
`;

const CardActions = styled.div`
  display: flex;
  gap: ${spacing.sm};
  align-items: center;

  @media (max-width: 640px) {
    justify-content: center;
  }
`;

export const PirateCard: React.FC<PirateCardProps> = ({
  children,
  variant = 'default',
  padding = 'md',
  clickable = false,
  onClick,
  className,
  style,
}) => {
  const handleClick = () => {
    if (clickable && onClick) {
      onClick();
    }
  };

  return (
    <CardBase
      className={className}
      style={style}
      $variant={variant}
      $padding={padding}
      $clickable={clickable}
      onClick={handleClick}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={clickable ? { y: -4 } : undefined}
      whileTap={clickable ? { y: -1 } : undefined}
    >
      {children}
    </CardBase>
  );
};

// Export sub-components for structured card content
export { CardHeader, CardTitle, CardSubtitle, CardBody, CardFooter, CardActions };