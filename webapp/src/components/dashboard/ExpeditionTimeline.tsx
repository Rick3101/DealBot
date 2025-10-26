import React from 'react';
import styled from 'styled-components';
import { AnimatePresence } from 'framer-motion';
import { PirateButton } from '@/components/ui/PirateButton';
import { ExpeditionCard } from '@/components/expedition/ExpeditionCard';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { ExpeditionTimelineEntry } from '@/types/expedition';

export interface ExpeditionTimelineProps {
  expeditions: ExpeditionTimelineEntry[];
  onViewExpedition: (expedition: ExpeditionTimelineEntry) => void;
  onManageExpedition: (expedition: ExpeditionTimelineEntry) => void;
  onRefresh: () => void;
  onCreate: () => void;
  refreshing: boolean;
}

const SectionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${spacing.lg};
  gap: ${spacing.md};
`;

const SectionTitle = styled.h2`
  font-family: ${pirateTypography.headings};
  font-size: 1.5rem;
  color: ${pirateColors.primary};
  margin: 0;
  display: flex;
  align-items: center;
  gap: ${spacing.sm};

  @media (min-width: 640px) {
    font-size: 1.75rem;
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: ${spacing.sm};
  align-items: center;

  @media (min-width: 640px) {
    gap: ${spacing.md};
  }
`;

const ExpeditionsGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  gap: ${spacing.lg};

  @media (min-width: 640px) {
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  }

  @media (min-width: 1024px) {
    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  }
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
 * Pure presentation component for expedition timeline section
 *
 * Displays expedition list or empty state with action buttons
 */
export const ExpeditionTimeline: React.FC<ExpeditionTimelineProps> = ({
  expeditions,
  onViewExpedition,
  onManageExpedition,
  onRefresh,
  onCreate,
  refreshing,
}) => {
  return (
    <div>
      <SectionHeader>
        <SectionTitle>
          ⛵ Expedition Timeline
        </SectionTitle>
        <ActionButtons>
          <PirateButton
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={refreshing}
            loading={refreshing}
          >
            🔄 Refresh
          </PirateButton>
          <PirateButton
            variant="primary"
            size="sm"
            onClick={onCreate}
            icon="+"
          >
            New Expedition
          </PirateButton>
        </ActionButtons>
      </SectionHeader>

      {expeditions.length === 0 ? (
        <EmptyState>
          <EmptyIcon>⛵</EmptyIcon>
          <EmptyTitle>No expeditions yet, Captain!</EmptyTitle>
          <EmptyDescription>
            Start your first pirate expedition to begin tracking your adventures.
          </EmptyDescription>
          <PirateButton onClick={onCreate} variant="primary" icon="+">
            Create First Expedition
          </PirateButton>
        </EmptyState>
      ) : (
        <ExpeditionsGrid>
          <AnimatePresence>
            {expeditions.map((expedition) => (
              <ExpeditionCard
                key={expedition.id}
                expedition={expedition}
                onViewDetails={onViewExpedition}
                onManage={onManageExpedition}
                compact={false}
              />
            ))}
          </AnimatePresence>
        </ExpeditionsGrid>
      )}
    </div>
  );
};
