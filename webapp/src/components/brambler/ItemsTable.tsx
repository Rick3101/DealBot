import React from 'react';
import styled, { css } from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { PirateCard } from '@/components/ui/PirateCard';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { hapticFeedback } from '@/utils/telegram';
import type { EncryptedItem } from '@/services/api/bramblerService';
import { Trash2 } from 'lucide-react';

interface ItemsTableProps {
  items: EncryptedItem[];
  showRealNames: boolean;
  decryptedMappings: Record<string, string>;
  onDelete: (itemId: number, itemName: string) => void;
  loading?: boolean;
}

const ItemsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: ${spacing.lg};
  margin-bottom: ${spacing['2xl']};

  @media (min-width: 640px) {
    grid-template-columns: 1fr;
    gap: ${spacing.md};
  }

  @media (min-width: 768px) {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  }
`;

const ItemCard = styled(PirateCard)<{ $showingReal: boolean }>`
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;

  ${props => props.$showingReal && css`
    border-color: ${pirateColors.warning};
    box-shadow: 0 0 20px rgba(255, 140, 0, 0.2);
  `}

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(139, 69, 19, 0.15);
  }
`;

const ItemCardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing.md};
`;

const ItemIcon = styled.div`
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(145deg, ${pirateColors.secondary}, ${pirateColors.primary});
  color: ${pirateColors.white};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.2);
`;

const ItemActions = styled.div`
  display: flex;
  gap: ${spacing.xs};
`;

const IconButton = styled.button.attrs({ type: 'button' })`
  background: ${pirateColors.lightGold};
  border: 2px solid ${pirateColors.primary};
  border-radius: 8px;
  color: ${pirateColors.primary};
  padding: ${spacing.xs} ${spacing.sm};
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: ${spacing.xs};

  &:hover:not(:disabled) {
    background: ${pirateColors.secondary};
    color: ${pirateColors.white};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const DeleteButton = styled(IconButton)`
  &:hover:not(:disabled) {
    background: ${pirateColors.danger};
    border-color: ${pirateColors.danger};
    color: ${pirateColors.white};
  }
`;

const ItemDisplay = styled.div`
  text-align: center;
  margin-bottom: ${spacing.md};
`;

const ItemName = styled.div<{ $isReal: boolean }>`
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.lg};
  font-weight: ${pirateTypography.weights.bold};
  color: ${props => props.$isReal ? pirateColors.warning : pirateColors.primary};
  margin-bottom: ${spacing.xs};
  display: flex;
  align-items: center;
  justify-content: center;
  gap: ${spacing.xs};
  word-break: break-word;
`;

const NameType = styled.div<{ $isReal: boolean }>`
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.muted};
  margin-bottom: ${spacing.sm};
`;

const ItemMetadata = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.xs};
  padding: ${spacing.md};
  background: ${pirateColors.lightGold}20;
  border-radius: 8px;
  margin-bottom: ${spacing.md};
`;

const MetaRow = styled.div`
  display: flex;
  justify-content: space-between;
  font-size: ${pirateTypography.sizes.xs};

  .label {
    color: ${pirateColors.muted};
  }

  .value {
    font-weight: ${pirateTypography.weights.bold};
    color: ${pirateColors.primary};
  }
`;

const ItemStats = styled.div`
  display: flex;
  justify-content: space-around;
  padding-top: ${spacing.md};
  border-top: 1px solid ${pirateColors.lightGold};
  font-size: ${pirateTypography.sizes.xs};
  color: ${pirateColors.muted};
`;

const StatItem = styled.div`
  text-align: center;

  .value {
    font-weight: ${pirateTypography.weights.bold};
    color: ${props => props.color || pirateColors.primary};
    display: block;
    margin-bottom: ${spacing.xs};
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
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.sm};
`;

const EmptyDescription = styled.p`
  font-size: ${pirateTypography.sizes.base};
`;

const StatusBadge = styled.span<{ $status: string }>`
  display: inline-block;
  padding: ${spacing.xs} ${spacing.sm};
  border-radius: 12px;
  font-size: ${pirateTypography.sizes.xs};
  font-weight: ${pirateTypography.weights.bold};

  ${props => {
    switch (props.$status) {
      case 'active':
        return css`
          background: ${pirateColors.success}30;
          color: ${pirateColors.success};
        `;
      case 'completed':
        return css`
          background: ${pirateColors.secondary}30;
          color: ${pirateColors.secondary};
        `;
      case 'cancelled':
      case 'suspended':
        return css`
          background: ${pirateColors.muted}30;
          color: ${pirateColors.muted};
        `;
      default:
        return css`
          background: ${pirateColors.lightGold};
          color: ${pirateColors.primary};
        `;
    }
  }}
`;

export const ItemsTable: React.FC<ItemsTableProps> = ({
  items,
  showRealNames,
  decryptedMappings,
  onDelete,
  loading = false
}) => {
  const getItemInitials = (name: string): string => {
    return name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getProgressColor = (consumed: number, required: number): string => {
    const percentage = required > 0 ? (consumed / required) * 100 : 0;
    if (percentage >= 100) return pirateColors.success;
    if (percentage >= 50) return pirateColors.secondary;
    return pirateColors.primary;
  };

  if (items.length === 0) {
    return (
      <EmptyState>
        <EmptyIcon>📦</EmptyIcon>
        <EmptyTitle>No encrypted items yet</EmptyTitle>
        <EmptyDescription>
          Create encrypted items to protect item names with fantasy aliases.
        </EmptyDescription>
      </EmptyState>
    );
  }

  return (
    <ItemsGrid>
      <AnimatePresence>
        {items.map((item) => {
          const displayName = showRealNames && decryptedMappings[item.encrypted_item_name]
            ? decryptedMappings[item.encrypted_item_name]
            : item.encrypted_item_name;

          const isDecrypted = showRealNames && !!decryptedMappings[item.encrypted_item_name];

          return (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
            >
              <ItemCard $showingReal={isDecrypted}>
                <ItemCardHeader>
                  <ItemIcon>
                    {isDecrypted ? '📝' : getItemInitials(displayName)}
                  </ItemIcon>
                  <ItemActions>
                    <DeleteButton
                      onClick={() => {
                        hapticFeedback('medium');
                        onDelete(item.id, displayName);
                      }}
                      disabled={loading}
                      title="Delete item"
                    >
                      <Trash2 size={14} />
                    </DeleteButton>
                  </ItemActions>
                </ItemCardHeader>

                <ItemDisplay>
                  <ItemName $isReal={isDecrypted}>
                    {isDecrypted ? `📝 ${displayName}` : `📦 ${displayName}`}
                  </ItemName>

                  <NameType $isReal={isDecrypted}>
                    {isDecrypted ? 'Real Item Name' : 'Encrypted Item Name'}
                  </NameType>

                  {!isDecrypted && (
                    <div style={{
                      color: pirateColors.muted,
                      fontSize: pirateTypography.sizes.xs,
                      fontStyle: 'italic'
                    }}>
                      Original: [ENCRYPTED]
                    </div>
                  )}
                </ItemDisplay>

                <ItemMetadata>
                  <MetaRow>
                    <span className="label">Expedition:</span>
                    <span className="value">{item.expedition_name}</span>
                  </MetaRow>
                  <MetaRow>
                    <span className="label">Type:</span>
                    <span className="value">{item.item_type}</span>
                  </MetaRow>
                  <MetaRow>
                    <span className="label">Status:</span>
                    <StatusBadge $status={item.item_status}>
                      {item.item_status}
                    </StatusBadge>
                  </MetaRow>
                  <MetaRow>
                    <span className="label">Code:</span>
                    <span className="value">{item.anonymized_item_code}</span>
                  </MetaRow>
                </ItemMetadata>

                <ItemStats>
                  <StatItem color={getProgressColor(item.quantity_consumed, item.quantity_required)}>
                    <span className="value">
                      {item.quantity_consumed}/{item.quantity_required}
                    </span>
                    <span>Progress</span>
                  </StatItem>
                  <StatItem>
                    <span className="value">
                      {item.quantity_required > 0
                        ? Math.round((item.quantity_consumed / item.quantity_required) * 100)
                        : 0}%
                    </span>
                    <span>Complete</span>
                  </StatItem>
                  <StatItem>
                    <span className="value">{formatDate(item.created_at)}</span>
                    <span>Created</span>
                  </StatItem>
                </ItemStats>
              </ItemCard>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </ItemsGrid>
  );
};
