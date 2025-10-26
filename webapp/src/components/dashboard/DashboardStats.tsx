import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { TrendingUp, Calendar, Users, Package } from 'lucide-react';
import { pirateColors, spacing, pirateTypography, mixins } from '@/utils/pirateTheme';

export interface DashboardStatsProps {
  stats: {
    total_expeditions: number;
    active_expeditions: number;
    completed_expeditions: number;
    overdue_expeditions: number;
  };
}

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: ${spacing.lg};
  margin-bottom: ${spacing.xl};

  @media (min-width: 640px) {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }
`;

const StatCard = styled(motion.div)<{ $color: string }>`
  ${mixins.pirateCard}
  padding: ${spacing.lg};
  text-align: center;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: ${props => props.$color};
  }
`;

const StatIcon = styled.div<{ $color: string }>`
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: ${props => props.$color}20;
  color: ${props => props.$color};
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto ${spacing.md};
  font-size: 1.5rem;

  svg {
    width: 24px;
    height: 24px;
  }
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.xs};
`;

const StatLabel = styled.div`
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.muted};
  font-weight: ${pirateTypography.weights.medium};
`;

/**
 * Pure presentation component for dashboard statistics cards
 *
 * Displays 4 stat cards: Total, Active, Completed, and Overdue expeditions
 */
export const DashboardStats: React.FC<DashboardStatsProps> = ({ stats }) => {
  return (
    <StatsGrid>
      <StatCard $color={pirateColors.secondary}>
        <StatIcon $color={pirateColors.secondary}>
          <Package />
        </StatIcon>
        <StatValue>{stats.total_expeditions}</StatValue>
        <StatLabel>Total Expeditions</StatLabel>
      </StatCard>

      <StatCard $color={pirateColors.success}>
        <StatIcon $color={pirateColors.success}>
          <TrendingUp />
        </StatIcon>
        <StatValue>{stats.active_expeditions}</StatValue>
        <StatLabel>Active Expeditions</StatLabel>
      </StatCard>

      <StatCard $color={pirateColors.info}>
        <StatIcon $color={pirateColors.info}>
          <Users />
        </StatIcon>
        <StatValue>{stats.completed_expeditions}</StatValue>
        <StatLabel>Completed</StatLabel>
      </StatCard>

      <StatCard $color={pirateColors.danger}>
        <StatIcon $color={pirateColors.danger}>
          <Calendar />
        </StatIcon>
        <StatValue>{stats.overdue_expeditions}</StatValue>
        <StatLabel>Overdue</StatLabel>
      </StatCard>
    </StatsGrid>
  );
};
