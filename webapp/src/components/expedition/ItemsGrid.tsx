import React from 'react';
import styled, { css } from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { pirateColors, spacing, pirateTypography, mixins, getQualityColor, getQualityEmoji } from '@/utils/pirateTheme';
import { QualityGrade } from '@/types/expedition';

interface Item {
  id: number;
  name: string;
  emoji?: string;
  quantity: number;
  price?: number;
  quality?: QualityGrade;
  consumed?: number;
  available?: number;
}

interface ItemsGridProps {
  items: Item[];
  compact?: boolean;
  maxItems?: number;
  showQuality?: boolean;
  showProgress?: boolean;
  editable?: boolean;
  onItemClick?: (item: Item) => void;
  onItemEdit?: (item: Item) => void;
  onConsumeClick?: (item: Item) => void;
  className?: string;
}

const GridContainer = styled.div<{ $compact: boolean; $columns: number }>`
  display: grid;
  grid-template-columns: ${props => `repeat(${Math.min(props.$columns, 2)}, 1fr)`};
  gap: ${props => props.$compact ? spacing.sm : spacing.md};
  width: 100%;

  @media (min-width: 640px) {
    grid-template-columns: ${props => `repeat(${props.$columns}, 1fr)`};
    gap: ${props => props.$compact ? spacing.md : spacing.lg};
  }

  @media (min-width: 768px) {
    grid-template-columns: ${props => `repeat(${Math.min(props.$columns, 4)}, 1fr)`};
  }
`;

const ItemCard = styled(motion.div)<{ $compact: boolean; $clickable: boolean }>`
  ${mixins.pirateCard}
  padding: ${props => props.$compact ? spacing.sm : spacing.md};
  text-align: center;
  position: relative;
  overflow: hidden;
  cursor: ${props => props.$clickable ? 'pointer' : 'default'};
  transition: all 0.3s ease;

  ${props => props.$clickable && css`
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(139, 69, 19, 0.2);
    }

    &:active {
      transform: translateY(0);
    }
  `}
`;

const QualityBadge = styled.div<{ $quality: QualityGrade }>`
  position: absolute;
  top: ${spacing.xs};
  right: ${spacing.xs};
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: ${props => getQualityColor(props.$quality)};
  color: ${pirateColors.white};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: ${pirateTypography.weights.bold};
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
`;

const ItemIcon = styled.div<{ $compact: boolean }>`
  font-size: ${props => props.$compact ? '1.5rem' : '2rem'};
  margin-bottom: ${props => props.$compact ? spacing.xs : spacing.sm};
  filter: drop-shadow(0 2px 4px rgba(139, 69, 19, 0.1));

  &:hover {
    animation: bounce 0.6s ease;
  }

  @keyframes bounce {
    0%, 20%, 53%, 80%, 100% { transform: translate3d(0,0,0); }
    40%, 43% { transform: translate3d(0, -6px, 0); }
    70% { transform: translate3d(0, -3px, 0); }
    90% { transform: translate3d(0, -1px, 0); }
  }
`;

const ItemName = styled.h4<{ $compact: boolean }>`
  font-family: ${pirateTypography.headings};
  font-size: ${props => props.$compact ? pirateTypography.sizes.sm : pirateTypography.sizes.base};
  color: ${pirateColors.primary};
  margin: 0 0 ${spacing.xs} 0;
  line-height: 1.2;
`;

const ItemQuantity = styled.div<{ $compact: boolean }>`
  font-weight: ${pirateTypography.weights.bold};
  font-size: ${props => props.$compact ? pirateTypography.sizes.sm : pirateTypography.sizes.base};
  color: ${pirateColors.secondary};
  margin-bottom: ${spacing.xs};
`;

const ItemPrice = styled.div`
  font-size: ${pirateTypography.sizes.xs};
  color: ${pirateColors.muted};
  font-weight: ${pirateTypography.weights.medium};
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 4px;
  background: ${pirateColors.lightGold};
  border-radius: 2px;
  overflow: hidden;
  margin-top: ${spacing.xs};
`;

const ProgressFill = styled(motion.div)<{ $percentage: number }>`
  height: 100%;
  background: ${props =>
    props.$percentage >= 80 ? pirateColors.danger :
    props.$percentage >= 50 ? pirateColors.warning :
    pirateColors.success
  };
  border-radius: 2px;
`;

const ItemStats = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: ${spacing.xs};
  font-size: ${pirateTypography.sizes.xs};
  color: ${pirateColors.muted};
`;

const StatItem = styled.span`
  display: flex;
  align-items: center;
  gap: 2px;
`;

const EmptyState = styled.div`
  grid-column: 1 / -1;
  text-align: center;
  padding: ${spacing['2xl']};
  color: ${pirateColors.muted};
`;

const EmptyIcon = styled.div`
  font-size: 3rem;
  margin-bottom: ${spacing.md};
  opacity: 0.5;
`;

const EmptyTitle = styled.h3`
  font-family: ${pirateTypography.headings};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.sm};
`;

const EmptyDescription = styled.p`
  font-size: ${pirateTypography.sizes.sm};
`;

const EditButton = styled.button`
  position: absolute;
  top: ${spacing.xs};
  left: ${spacing.xs};
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: ${pirateColors.secondary};
  color: ${pirateColors.white};
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 2;

  ${ItemCard}:hover & {
    opacity: 1;
  }

  &:hover {
    background: ${pirateColors.primary};
    transform: scale(1.1);
  }
`;

const ConsumeButton = styled.button`
  margin-top: ${spacing.sm};
  width: 100%;
  padding: ${spacing.sm} ${spacing.md};
  background: ${pirateColors.secondary};
  color: ${pirateColors.white};
  border: none;
  border-radius: 8px;
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  font-size: ${pirateTypography.sizes.sm};
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: ${spacing.xs};

  &:hover {
    background: ${pirateColors.primary};
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(139, 69, 19, 0.3);
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    background: ${pirateColors.lightGold};
    color: ${pirateColors.muted};
    cursor: not-allowed;
    opacity: 0.8;

    &:hover {
      transform: none;
      box-shadow: none;
    }
  }
`;

export const ItemsGrid: React.FC<ItemsGridProps> = ({
  items,
  compact = false,
  maxItems,
  showQuality = true,
  showProgress = true,
  editable = false,
  onItemClick,
  onItemEdit,
  onConsumeClick,
  className,
}) => {
  const displayItems = maxItems ? items.slice(0, maxItems) : items;
  const columns = compact ? Math.min(displayItems.length, 4) : Math.min(displayItems.length, 3);

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const calculateProgress = (item: Item): number => {
    if (!item.consumed || !item.quantity) return 0;
    return (item.consumed / item.quantity) * 100;
  };

  const handleItemClick = (item: Item) => {
    if (onItemClick) {
      onItemClick(item);
    }
  };

  const handleEditClick = (e: React.MouseEvent, item: Item) => {
    e.stopPropagation();
    if (onItemEdit) {
      onItemEdit(item);
    }
  };

  const handleConsumeClick = (e: React.MouseEvent, item: Item) => {
    e.stopPropagation();
    if (onConsumeClick) {
      onConsumeClick(item);
    }
  };

  if (displayItems.length === 0) {
    return (
      <GridContainer $compact={compact} $columns={1} className={className}>
        <EmptyState>
          <EmptyIcon>📦</EmptyIcon>
          <EmptyTitle>No items yet</EmptyTitle>
          <EmptyDescription>
            Add items to this expedition to get started
          </EmptyDescription>
        </EmptyState>
      </GridContainer>
    );
  }

  return (
    <GridContainer $compact={compact} $columns={columns} className={className}>
      <AnimatePresence>
        {displayItems.map((item) => {
          const progressPercentage = calculateProgress(item);

          return (
            <ItemCard
              key={item.id}
              $compact={compact}
              $clickable={!!onItemClick}
              onClick={() => handleItemClick(item)}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
              whileHover={onItemClick ? { scale: 1.02 } : {}}
              whileTap={onItemClick ? { scale: 0.98 } : {}}
            >
              {editable && onItemEdit && (
                <EditButton onClick={(e) => handleEditClick(e, item)}>
                  ✏️
                </EditButton>
              )}

              {item.quality && showQuality && (
                <QualityBadge $quality={item.quality}>
                  {getQualityEmoji(item.quality)}
                </QualityBadge>
              )}

              <ItemIcon $compact={compact}>
                {item.emoji || '📦'}
              </ItemIcon>

              <ItemName $compact={compact}>
                {item.name}
              </ItemName>

              <ItemQuantity $compact={compact}>
                {item.available !== undefined ? (
                  `${item.available}/${item.quantity}`
                ) : (
                  item.quantity
                )}
              </ItemQuantity>

              {item.price && (
                <ItemPrice>
                  {formatCurrency(item.price)}
                </ItemPrice>
              )}

              {showProgress && item.consumed !== undefined && (
                <>
                  <ProgressBar>
                    <ProgressFill
                      $percentage={progressPercentage}
                      initial={{ width: 0 }}
                      animate={{ width: `${progressPercentage}%` }}
                      transition={{ duration: 1, delay: 0.2 }}
                    />
                  </ProgressBar>

                  <ItemStats>
                    <StatItem>
                      ✅ {item.consumed}
                    </StatItem>
                    <StatItem>
                      ⏳ {item.quantity - (item.consumed || 0)}
                    </StatItem>
                  </ItemStats>
                </>
              )}

              {onConsumeClick && item.available !== undefined && (
                <>
                  {item.available > 0 ? (
                    <ConsumeButton onClick={(e) => handleConsumeClick(e, item)}>
                      🍽️ Consume
                    </ConsumeButton>
                  ) : (
                    <ConsumeButton disabled>
                      ✅ Fully Consumed
                    </ConsumeButton>
                  )}
                </>
              )}
            </ItemCard>
          );
        })}
      </AnimatePresence>
    </GridContainer>
  );
};