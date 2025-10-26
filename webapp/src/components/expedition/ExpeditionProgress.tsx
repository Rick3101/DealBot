import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { pirateColors, spacing, pirateTypography, mixins } from '@/utils/pirateTheme';
import { ExpeditionProgress as ExpeditionProgressType } from '@/types/expedition';

interface ExpeditionProgressProps {
  progress: ExpeditionProgressType;
  compact?: boolean;
  showDetails?: boolean;
  animated?: boolean;
  className?: string;
}

const ProgressContainer = styled.div<{ $compact: boolean }>`
  display: flex;
  flex-direction: column;
  gap: ${props => props.$compact ? spacing.sm : spacing.md};
`;

const ProgressHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${spacing.sm};
`;

const ProgressTitle = styled.h4`
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.base};
  color: ${pirateColors.primary};
  margin: 0;
  display: flex;
  align-items: center;
  gap: ${spacing.xs};
`;

const ProgressPercentage = styled.span<{ $percentage: number }>`
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  font-size: ${pirateTypography.sizes.lg};
  color: ${props =>
    props.$percentage >= 100 ? pirateColors.success :
    props.$percentage >= 75 ? pirateColors.secondary :
    props.$percentage >= 50 ? pirateColors.warning :
    props.$percentage >= 25 ? pirateColors.info :
    pirateColors.danger
  };
`;

const ProgressBarContainer = styled.div`
  position: relative;
  width: 100%;
  height: 12px;
  background: ${pirateColors.lightGold};
  border-radius: 8px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(139, 69, 19, 0.1);
`;

const ProgressBarFill = styled(motion.div)<{ $percentage: number }>`
  height: 100%;
  border-radius: 8px;
  background: ${props =>
    props.$percentage >= 100 ? `linear-gradient(90deg, ${pirateColors.success}, #16A34A)` :
    props.$percentage >= 75 ? `linear-gradient(90deg, ${pirateColors.secondary}, ${pirateColors.primary})` :
    props.$percentage >= 50 ? `linear-gradient(90deg, ${pirateColors.warning}, ${pirateColors.secondary})` :
    props.$percentage >= 25 ? `linear-gradient(90deg, ${pirateColors.info}, ${pirateColors.warning})` :
    `linear-gradient(90deg, ${pirateColors.danger}, #DC143C)`
  };
  position: relative;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg,
      transparent 25%,
      rgba(255, 255, 255, 0.1) 25%,
      rgba(255, 255, 255, 0.1) 50%,
      transparent 50%,
      transparent 75%,
      rgba(255, 255, 255, 0.1) 75%
    );
    background-size: 16px 16px;
    animation: shimmer 2s linear infinite;
  }

  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
`;

const ProgressStats = styled.div<{ $compact: boolean }>`
  display: grid;
  grid-template-columns: ${props => props.$compact ? 'repeat(2, 1fr)' : 'repeat(auto-fit, minmax(120px, 1fr))'};
  gap: ${spacing.md};
  margin-top: ${spacing.md};
`;

const StatCard = styled.div`
  ${mixins.pirateCard}
  padding: ${spacing.md};
  text-align: center;
  background: linear-gradient(135deg, ${pirateColors.white}, ${pirateColors.lightGold});
  border-width: 1px;
  box-shadow: 0 2px 6px rgba(139, 69, 19, 0.1);
`;

const StatIcon = styled.div`
  font-size: 1.5rem;
  margin-bottom: ${spacing.xs};
`;

const StatValue = styled.div`
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.lg};
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.xs};
`;

const StatLabel = styled.div`
  font-size: ${pirateTypography.sizes.xs};
  color: ${pirateColors.muted};
  font-weight: ${pirateTypography.weights.medium};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const ValueComparison = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: ${spacing.sm} ${spacing.md};
  background: rgba(139, 69, 19, 0.05);
  border-radius: 8px;
  margin-top: ${spacing.sm};
`;

const ComparisonItem = styled.div`
  text-align: center;
  flex: 1;
`;

const ComparisonValue = styled.div`
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.primary};
  font-size: ${pirateTypography.sizes.base};
`;

const ComparisonLabel = styled.div`
  font-size: ${pirateTypography.sizes.xs};
  color: ${pirateColors.muted};
  margin-top: ${spacing.xs};
`;

const Separator = styled.div`
  width: 1px;
  height: 20px;
  background: ${pirateColors.lightGold};
  margin: 0 ${spacing.sm};
`;

export const ExpeditionProgress: React.FC<ExpeditionProgressProps> = ({
  progress,
  compact = false,
  showDetails = true,
  animated = true,
  className,
}) => {
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const percentage = Math.min(100, Math.max(0, progress.completion_percentage));
  const isCompleted = percentage >= 100;

  return (
    <ProgressContainer $compact={compact} className={className}>
      <ProgressHeader>
        <ProgressTitle>
          {isCompleted ? '✅' : '📊'} Progress
        </ProgressTitle>
        <ProgressPercentage $percentage={percentage}>
          {percentage.toFixed(1)}%
        </ProgressPercentage>
      </ProgressHeader>

      <ProgressBarContainer>
        <ProgressBarFill
          $percentage={percentage}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{
            duration: animated ? 1.5 : 0,
            ease: 'easeOut',
            delay: animated ? 0.3 : 0
          }}
        />
      </ProgressBarContainer>

      {!compact && showDetails && (
        <ProgressStats $compact={compact}>
          <StatCard>
            <StatIcon>📦</StatIcon>
            <StatValue>{progress.total_items}</StatValue>
            <StatLabel>Total Items</StatLabel>
          </StatCard>

          <StatCard>
            <StatIcon>✅</StatIcon>
            <StatValue>{progress.consumed_items}</StatValue>
            <StatLabel>Consumed</StatLabel>
          </StatCard>

          <StatCard>
            <StatIcon>⏳</StatIcon>
            <StatValue>{progress.remaining_items}</StatValue>
            <StatLabel>Remaining</StatLabel>
          </StatCard>

          <StatCard>
            <StatIcon>💰</StatIcon>
            <StatValue>{formatCurrency(progress.total_value)}</StatValue>
            <StatLabel>Total Value</StatLabel>
          </StatCard>
        </ProgressStats>
      )}

      {!compact && progress.consumed_value > 0 && (
        <ValueComparison>
          <ComparisonItem>
            <ComparisonValue>{formatCurrency(progress.consumed_value)}</ComparisonValue>
            <ComparisonLabel>Consumed Value</ComparisonLabel>
          </ComparisonItem>

          <Separator />

          <ComparisonItem>
            <ComparisonValue>{formatCurrency(progress.remaining_value)}</ComparisonValue>
            <ComparisonLabel>Remaining Value</ComparisonLabel>
          </ComparisonItem>
        </ValueComparison>
      )}

      {compact && (
        <ValueComparison>
          <ComparisonItem>
            <ComparisonValue>{progress.consumed_items}/{progress.total_items}</ComparisonValue>
            <ComparisonLabel>Items Progress</ComparisonLabel>
          </ComparisonItem>

          <Separator />

          <ComparisonItem>
            <ComparisonValue>{formatCurrency(progress.total_value)}</ComparisonValue>
            <ComparisonLabel>Total Value</ComparisonLabel>
          </ComparisonItem>
        </ValueComparison>
      )}
    </ProgressContainer>
  );
};