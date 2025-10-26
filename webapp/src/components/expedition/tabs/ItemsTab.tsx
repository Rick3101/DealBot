import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { Plus } from 'lucide-react';
import { ItemsGrid } from '@/components/expedition/ItemsGrid';
import { PirateButton } from '@/components/ui/PirateButton';
import { ItemDebugInfo } from '@/components/debug/ItemDebugInfo';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { ExpeditionItem } from '@/types/expedition';
import { transformExpeditionItems } from '@/utils/transforms/itemTransforms';

interface ItemsTabProps {
  items: ExpeditionItem[];
  onConsumeClick: (item: any) => void;
  onAddItem: () => void;
}

const TabContent = styled(motion.div)`
  min-height: 400px;
`;

const SectionHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing.lg};
  gap: ${spacing.md};
`;

const SectionTitle = styled.h3`
  font-family: ${pirateTypography.headings};
  font-size: 1.25rem;
  color: ${pirateColors.primary};
  margin: 0;
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
`;

export const ItemsTab: React.FC<ItemsTabProps> = ({
  items,
  onConsumeClick,
  onAddItem,
}) => {
  const transformedItems = transformExpeditionItems(items);

  return (
    <TabContent
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <SectionHeader>
        <SectionTitle>📦 Expedition Items</SectionTitle>
        <PirateButton variant="primary" size="sm" onClick={onAddItem}>
          <Plus size={16} /> Add Item
        </PirateButton>
      </SectionHeader>
      <ItemsGrid
        items={transformedItems}
        showQuality
        showProgress
        compact={false}
        onConsumeClick={onConsumeClick}
      />
      {/* Debug info - shows item availability data */}
      <ItemDebugInfo items={transformedItems} position="bottom-right" />
    </TabContent>
  );
};
