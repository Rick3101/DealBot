import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { CaptainLayout } from '@/layouts/CaptainLayout';
import { PirateButton } from '@/components/ui/PirateButton';
import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { ExpeditionTimeline } from '@/components/dashboard/ExpeditionTimeline';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { Loader2 } from 'lucide-react';
import { ExpeditionTimelineEntry } from '@/types/expedition';
import { DashboardActions } from '@/hooks/useDashboardActions';
import { DashboardStats as DashboardStatsType } from '@/hooks/useDashboardStats';

export interface DashboardPresenterProps {
  loading: boolean;
  error: string | null;
  stats: DashboardStatsType;
  expeditions: ExpeditionTimelineEntry[];
  actions: DashboardActions;
  refreshing: boolean;
}

const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.xl};
`;

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  padding: ${spacing['3xl']};
  flex-direction: column;
  gap: ${spacing.lg};
`;

const LoadingText = styled.div`
  font-family: ${pirateTypography.headings};
  font-size: 1.25rem;
  color: ${pirateColors.primary};
`;

const EmptyState = styled.div`
  text-align: center;
  padding: ${spacing['3xl']};
  color: ${pirateColors.muted};
`;

const EmptyIcon = styled.div`
  font-size: 4rem;
  margin-bottom: ${spacing.lg};
  opacity: 0.5;
`;

const EmptyTitle = styled.h3`
  font-family: ${pirateTypography.headings};
  font-size: 1.5rem;
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.md};
`;

const EmptyDescription = styled.p`
  font-size: ${pirateTypography.sizes.base};
  margin-bottom: ${spacing.xl};
`;

/**
 * Pure presenter component for Dashboard
 *
 * Responsible for:
 * - Conditional rendering (loading, error, success states)
 * - Layout composition
 * - Delegating to DashboardStats and ExpeditionTimeline components
 *
 * This component has NO business logic - only UI rendering based on props
 */
export const DashboardPresenter: React.FC<DashboardPresenterProps> = ({
  loading,
  error,
  stats,
  expeditions,
  actions,
  refreshing,
}) => {
  // Loading state
  if (loading) {
    return (
      <CaptainLayout>
        <LoadingContainer>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <Loader2 size={48} color={pirateColors.secondary} />
          </motion.div>
          <LoadingText>Loading your expeditions...</LoadingText>
        </LoadingContainer>
      </CaptainLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <CaptainLayout>
        <EmptyState>
          <EmptyIcon>💀</EmptyIcon>
          <EmptyTitle>Arrr! Something went wrong</EmptyTitle>
          <EmptyDescription>{error}</EmptyDescription>
          <PirateButton onClick={actions.handleRefresh} variant="primary">
            ⚓ Try Again
          </PirateButton>
        </EmptyState>
      </CaptainLayout>
    );
  }

  // Success state
  return (
    <CaptainLayout>
      <DashboardContainer>
        <DashboardStats stats={stats} />
        <ExpeditionTimeline
          expeditions={expeditions}
          onViewExpedition={actions.handleViewExpedition}
          onManageExpedition={actions.handleManageExpedition}
          onRefresh={actions.handleRefresh}
          onCreate={actions.handleCreateExpedition}
          refreshing={actions.refreshing || refreshing}
        />
      </DashboardContainer>
    </CaptainLayout>
  );
};
