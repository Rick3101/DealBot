import React from 'react';
import styled, { css } from 'styled-components';
import { motion } from 'framer-motion';
import { PirateButton } from '@/components/ui/PirateButton';
import { DeadlineTimer } from '@/components/ui/DeadlineTimer';
import { ExpeditionProgress } from './ExpeditionProgress';
import { ItemsGrid } from './ItemsGrid';
import { pirateColors, spacing, pirateTypography, getStatusColor, getStatusEmoji } from '@/utils/pirateTheme';
import { hapticFeedback } from '@/utils/telegram';
import { ExpeditionTimelineEntry } from '@/types/expedition';

interface ExpeditionCardProps {
  expedition: ExpeditionTimelineEntry;
  onViewDetails?: (expedition: ExpeditionTimelineEntry) => void;
  onManage?: (expedition: ExpeditionTimelineEntry) => void;
  compact?: boolean;
  className?: string;
}

const CardContainer = styled.div<{ $isOverdue: boolean }>`
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, ${pirateColors.parchment}, ${pirateColors.lightGold});
  border: 2px solid ${pirateColors.primary};
  border-radius: 12px;
  padding: ${spacing.lg};
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.15);

  ${props => props.$isOverdue && css`
    border-color: ${pirateColors.danger};
    box-shadow: 0 0 20px rgba(220, 20, 60, 0.2);
    animation: pulse 2s infinite;

    @keyframes pulse {
      0%, 100% { box-shadow: 0 0 20px rgba(220, 20, 60, 0.2); }
      50% { box-shadow: 0 0 30px rgba(220, 20, 60, 0.4); }
    }
  `}

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(139, 69, 19, 0.2);
  }
`;

const OverdueFlag = styled.div`
  position: absolute;
  top: ${spacing.md};
  right: ${spacing.md};
  background: ${pirateColors.danger};
  color: ${pirateColors.white};
  padding: ${spacing.xs} ${spacing.sm};
  border-radius: 12px;
  font-size: ${pirateTypography.sizes.xs};
  font-weight: ${pirateTypography.weights.bold};
  text-transform: uppercase;
  z-index: 2;
  animation: bounce 2s infinite;

  @keyframes bounce {
    0%, 20%, 53%, 80%, 100% { transform: translate3d(0,0,0); }
    40%, 43% { transform: translate3d(0, -4px, 0); }
    70% { transform: translate3d(0, -2px, 0); }
    90% { transform: translate3d(0, -1px, 0); }
  }
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: ${spacing.md};
  gap: ${spacing.md};
`;

const ExpeditionTitle = styled.h3`
  font-family: ${pirateTypography.headings};
  font-size: 1.25rem;
  color: ${pirateColors.primary};
  margin: 0;
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
  flex: 1;
  line-height: 1.3;
`;

const StatusBadge = styled.span<{ $status: string }>`
  background: ${props => getStatusColor(props.$status)};
  color: ${pirateColors.white};
  padding: ${spacing.xs} ${spacing.sm};
  border-radius: 16px;
  font-size: ${pirateTypography.sizes.xs};
  font-weight: ${pirateTypography.weights.bold};
  text-transform: uppercase;
  white-space: nowrap;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const ExpeditionMeta = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: ${spacing.md};
  margin-bottom: ${spacing.md};
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.muted};

  @media (max-width: 640px) {
    gap: ${spacing.sm};
    font-size: ${pirateTypography.sizes.xs};
  }
`;

const MetaItem = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.xs};
`;

const MetaIcon = styled.span`
  font-size: 1rem;
`;

const MetaValue = styled.span`
  font-weight: ${pirateTypography.weights.medium};
  color: ${pirateColors.primary};
`;

const ProgressSection = styled.div`
  margin: ${spacing.md} 0;
`;

const ItemsPreviewSection = styled.div`
  margin: ${spacing.md} 0;
`;

const ItemsPreviewTitle = styled.h4`
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.base};
  color: ${pirateColors.primary};
  margin: 0 0 ${spacing.sm} 0;
  display: flex;
  align-items: center;
  gap: ${spacing.xs};
`;

const MoreItemsIndicator = styled.div`
  text-align: center;
  padding: ${spacing.sm};
  color: ${pirateColors.muted};
  font-size: ${pirateTypography.sizes.sm};
  font-style: italic;
`;

const ExpeditionActions = styled.div`
  display: flex;
  gap: ${spacing.sm};
  margin-top: ${spacing.lg};
  justify-content: flex-end;

  @media (max-width: 640px) {
    flex-direction: column;
    gap: ${spacing.xs};
  }
`;

const DeadlineSection = styled.div`
  margin: ${spacing.md} 0;
`;

export const ExpeditionCard: React.FC<ExpeditionCardProps> = ({
  expedition,
  onViewDetails,
  onManage,
  compact = false,
  className,
}) => {
  const handleCardClick = (e: React.MouseEvent) => {
    // Don't trigger if clicking on buttons
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }

    hapticFeedback('light');
    onViewDetails?.(expedition);
  };

  const handleManageClick = (e?: React.MouseEvent<HTMLButtonElement>) => {
    e?.stopPropagation();
    hapticFeedback('medium');
    onManage?.(expedition);
  };

  const handleDetailsClick = (e?: React.MouseEvent<HTMLButtonElement>) => {
    e?.stopPropagation();
    hapticFeedback('light');
    onViewDetails?.(expedition);
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  // Items count from progress data
  const itemsCount = expedition.progress?.total_items || 0;

  // Show items preview only when we have detailed data
  // For now, hide preview items since we don't have item details in timeline
  const previewItems: any[] = [];

  // Get pirate count from consumptions (unique consumer names)
  // This would need to be added to the expedition data from backend
  // For now, hide pirates count as we don't have this data
  // const totalPirates = 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className={className}
    >
      <CardContainer
        $isOverdue={expedition.is_overdue}
        onClick={handleCardClick}
      >
        {expedition.is_overdue && (
          <OverdueFlag>
            ⚠️ Overdue
          </OverdueFlag>
        )}

        <CardHeader>
          <ExpeditionTitle>
            {getStatusEmoji(expedition.status)} {expedition.name}
          </ExpeditionTitle>
          <StatusBadge $status={expedition.status}>
            {expedition.status}
          </StatusBadge>
        </CardHeader>

        {!compact && expedition.description && (
          <div style={{
            marginBottom: spacing.md,
            color: pirateColors.muted,
            fontSize: pirateTypography.sizes.sm,
            lineHeight: 1.4
          }}>
            {expedition.description}
          </div>
        )}

        <ExpeditionMeta>
          {itemsCount > 0 && (
            <MetaItem>
              <MetaIcon>📦</MetaIcon>
              <MetaValue>{itemsCount}</MetaValue>
              <span>Items</span>
            </MetaItem>
          )}
          {expedition.progress && expedition.progress.total_value > 0 && (
            <MetaItem>
              <MetaIcon>💰</MetaIcon>
              <MetaValue>{formatCurrency(expedition.progress.total_value)}</MetaValue>
            </MetaItem>
          )}
          {expedition.progress && expedition.progress.consumed_items > 0 && (
            <MetaItem>
              <MetaIcon>✅</MetaIcon>
              <MetaValue>{expedition.progress.consumed_items}</MetaValue>
              <span>Consumed</span>
            </MetaItem>
          )}
          {expedition.created_at && (
            <MetaItem>
              <MetaIcon>📅</MetaIcon>
              <MetaValue>{formatDate(expedition.created_at)}</MetaValue>
            </MetaItem>
          )}
        </ExpeditionMeta>

        {expedition.deadline && (
          <DeadlineSection>
            <DeadlineTimer
              deadline={expedition.deadline}
              compact={compact}
            />
          </DeadlineSection>
        )}

        {expedition.progress && (
          <ProgressSection>
            <ExpeditionProgress
              progress={expedition.progress}
              compact={compact}
            />
          </ProgressSection>
        )}

        {!compact && previewItems.length > 0 && (
          <ItemsPreviewSection>
            <ItemsPreviewTitle>
              📦 Expedition Items
            </ItemsPreviewTitle>
            <ItemsGrid
              items={previewItems.slice(0, 4)}
              compact
              maxItems={4}
            />
            {previewItems.length > 4 && (
              <MoreItemsIndicator>
                +{previewItems.length - 4} more items
              </MoreItemsIndicator>
            )}
          </ItemsPreviewSection>
        )}

        <ExpeditionActions>
          <PirateButton
            variant="outline"
            size="sm"
            onClick={handleDetailsClick}
          >
            🗺️ Details
          </PirateButton>
          {expedition.status === 'active' && (
            <PirateButton
              variant="primary"
              size="sm"
              onClick={handleManageClick}
            >
              ⚔️ Manage
            </PirateButton>
          )}
        </ExpeditionActions>
      </CardContainer>
    </motion.div>
  );
};