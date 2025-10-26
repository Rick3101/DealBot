import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { PirateCard } from '@/components/ui/PirateCard';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { formatCurrency } from '@/utils/formatters';
import { ExpeditionProgress } from '@/types/expedition';

interface AnalyticsTabProps {
  progress: ExpeditionProgress;
  totalPirates: number;
  totalConsumptions: number;
}

const TabContent = styled(motion.div)`
  min-height: 400px;
`;

const SectionTitle = styled.h3`
  font-family: ${pirateTypography.headings};
  font-size: 1.25rem;
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.lg};
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
`;

export const AnalyticsTab: React.FC<AnalyticsTabProps> = ({
  progress,
  totalPirates,
  totalConsumptions,
}) => {
  const revenueRate = progress.total_value > 0
    ? (progress.consumed_value / progress.total_value * 100).toFixed(1)
    : '0.0';

  const avgConsumptionsPerPirate = totalPirates > 0
    ? (totalConsumptions / totalPirates).toFixed(1)
    : '0';

  return (
    <TabContent
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <SectionTitle>📈 Expedition Analytics</SectionTitle>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: spacing.lg
      }}>
        <PirateCard>
          <h4 style={{
            fontFamily: pirateTypography.headings,
            color: pirateColors.primary,
            marginBottom: spacing.md
          }}>
            💰 Financial Summary
          </h4>
          <div style={{ marginBottom: spacing.sm }}>
            <strong>Total Value:</strong> {formatCurrency(progress.total_value)}
          </div>
          <div style={{ marginBottom: spacing.sm }}>
            <strong>Consumed:</strong> {formatCurrency(progress.consumed_value)}
          </div>
          <div style={{ marginBottom: spacing.sm }}>
            <strong>Remaining:</strong> {formatCurrency(progress.remaining_value)}
          </div>
          <div>
            <strong>Revenue Rate:</strong> {revenueRate}%
          </div>
        </PirateCard>

        <PirateCard>
          <h4 style={{
            fontFamily: pirateTypography.headings,
            color: pirateColors.primary,
            marginBottom: spacing.md
          }}>
            👥 Pirate Activity
          </h4>
          <div style={{ marginBottom: spacing.sm }}>
            <strong>Active Pirates:</strong> {totalPirates}
          </div>
          <div style={{ marginBottom: spacing.sm }}>
            <strong>Total Consumptions:</strong> {totalConsumptions}
          </div>
          <div style={{ marginBottom: spacing.sm }}>
            <strong>Avg per Pirate:</strong> {avgConsumptionsPerPirate}
          </div>
          <div>
            <strong>Completion:</strong> {progress.completion_percentage.toFixed(1)}%
          </div>
        </PirateCard>
      </div>
    </TabContent>
  );
};
