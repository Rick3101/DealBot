import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { Package, Users, DollarSign, Calendar } from 'lucide-react';
import { PirateCard } from '@/components/ui/PirateCard';
import { DeadlineTimer } from '@/components/ui/DeadlineTimer';
import { ExpeditionProgress } from '@/components/expedition/ExpeditionProgress';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { ExpeditionProgress as ExpeditionProgressType } from '@/types/expedition';

interface OverviewTabProps {
  totalItems: number;
  totalPirates: number;
  totalValue: number;
  deadline?: string;
  progress: ExpeditionProgressType;
}

const TabContent = styled(motion.div)`
  min-height: 400px;
`;

const ExpeditionMeta = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: ${spacing.md};
  margin: ${spacing.lg} 0;
`;

const MetaCard = styled(PirateCard)`
  text-align: center;
  padding: ${spacing.lg};
`;

const MetaIcon = styled.div`
  font-size: 2rem;
  margin-bottom: ${spacing.sm};
  color: ${pirateColors.secondary};
`;

const MetaValue = styled.div`
  font-family: ${pirateTypography.headings};
  font-size: 1.5rem;
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.xs};
`;

const MetaLabel = styled.div`
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.muted};
  font-weight: ${pirateTypography.weights.medium};
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

export const OverviewTab: React.FC<OverviewTabProps> = ({
  totalItems,
  totalPirates,
  totalValue,
  deadline,
  progress,
}) => {
  return (
    <TabContent
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <ExpeditionMeta>
        <MetaCard>
          <MetaIcon><Package /></MetaIcon>
          <MetaValue>{totalItems}</MetaValue>
          <MetaLabel>Total Items</MetaLabel>
        </MetaCard>

        <MetaCard>
          <MetaIcon><Users /></MetaIcon>
          <MetaValue>{totalPirates}</MetaValue>
          <MetaLabel>Active Pirates</MetaLabel>
        </MetaCard>

        <MetaCard>
          <MetaIcon><DollarSign /></MetaIcon>
          <MetaValue>{formatCurrency(totalValue)}</MetaValue>
          <MetaLabel>Total Value</MetaLabel>
        </MetaCard>

        <MetaCard>
          <MetaIcon><Calendar /></MetaIcon>
          <MetaValue>
            {deadline ? formatDate(deadline).split(' ')[0] : 'No deadline'}
          </MetaValue>
          <MetaLabel>Deadline</MetaLabel>
        </MetaCard>
      </ExpeditionMeta>

      {deadline && (
        <PirateCard style={{ marginBottom: spacing.lg }}>
          <SectionTitle>⏰ Deadline Status</SectionTitle>
          <DeadlineTimer deadline={deadline} compact={false} />
        </PirateCard>
      )}

      <PirateCard>
        <SectionTitle>📊 Progress Overview</SectionTitle>
        <ExpeditionProgress
          progress={progress}
          compact={false}
          showDetails
          animated
        />
      </PirateCard>
    </TabContent>
  );
};
