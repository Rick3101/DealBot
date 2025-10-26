import React from 'react';
import styled from 'styled-components';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';

export interface EmptyStateProps {
  /**
   * Emoji or icon to display (e.g., "🏴‍☠️", "📦", "🍽️")
   */
  icon: string;

  /**
   * Main title of the empty state
   */
  title: string;

  /**
   * Descriptive text explaining the empty state
   */
  description: string;

  /**
   * Optional action button or custom content
   */
  action?: React.ReactNode;

  /**
   * Optional custom styling
   */
  className?: string;
}

const Container = styled.div`
  text-align: center;
  padding: ${spacing['3xl']};
  color: ${pirateColors.muted};

  @media (max-width: 768px) {
    padding: ${spacing.xl} ${spacing.md};
  }
`;

const Icon = styled.div`
  font-size: 4rem;
  margin-bottom: ${spacing.lg};
  opacity: 0.5;
  line-height: 1;

  @media (max-width: 768px) {
    font-size: 3rem;
  }
`;

const Title = styled.h3`
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.xl};
  color: ${pirateColors.primary};
  margin: 0 0 ${spacing.sm} 0;
  font-weight: ${pirateTypography.weights.bold};

  @media (max-width: 768px) {
    font-size: ${pirateTypography.sizes.lg};
  }
`;

const Description = styled.p`
  font-size: ${pirateTypography.sizes.base};
  color: ${pirateColors.muted};
  margin: 0 0 ${spacing.lg} 0;
  line-height: 1.5;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;

  @media (max-width: 768px) {
    font-size: ${pirateTypography.sizes.sm};
  }
`;

const ActionContainer = styled.div`
  margin-top: ${spacing.lg};
`;

/**
 * EmptyState Component
 *
 * A reusable component for displaying empty states with consistent pirate-themed styling.
 * Perfect for showing when lists, tables, or data collections have no content.
 *
 * @example
 * <EmptyState
 *   icon="🏴‍☠️"
 *   title="No pirates yet"
 *   description="No pirates have joined this expedition yet."
 *   action={<Button onClick={handleAdd}>Add Pirate</Button>}
 * />
 */
export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <Container className={className}>
      <Icon role="img" aria-label={icon}>{icon}</Icon>
      <Title>{title}</Title>
      <Description>{description}</Description>
      {action && <ActionContainer>{action}</ActionContainer>}
    </Container>
  );
};
