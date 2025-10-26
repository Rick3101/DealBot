import React from 'react';
import styled from 'styled-components';
import { PirateCard } from '@/components/ui/PirateCard';
import { PirateButton } from '@/components/ui/PirateButton';
import { ItemsGrid } from '@/components/expedition/ItemsGrid';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { formatCurrency } from '@/utils/formatters';
import { SelectedProductItem } from './ProductConfigurationStep';

const Header = styled.div`
  text-align: center;
  margin-bottom: ${spacing.xl};
`;

const Title = styled.h3`
  font-family: ${pirateTypography.headings};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.lg};
`;

const Subtitle = styled.p`
  color: ${pirateColors.muted};
  margin: 0;
`;

const SummaryCard = styled(PirateCard)`
  margin-bottom: ${spacing.lg};
`;

const SummaryTitle = styled.h4`
  font-family: ${pirateTypography.headings};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.md};
`;

const SummaryItem = styled.div`
  margin-bottom: ${spacing.md};

  strong {
    color: ${pirateColors.primary};
    font-weight: ${pirateTypography.weights.bold};
  }
`;

const LaunchContainer = styled.div`
  text-align: center;
  margin-top: ${spacing.xl};
  padding: ${spacing.lg};
  background: linear-gradient(135deg, ${pirateColors.lightGold}, ${pirateColors.parchment});
  border-radius: 12px;
  border: 2px solid ${pirateColors.secondary};
`;

export interface ReviewStepProps {
  name: string;
  selectedProducts: SelectedProductItem[];
  loading: boolean;
  onSubmit: () => void;
}

/**
 * Step 4: Review and Launch
 * Pure presentation component for reviewing expedition details before submission
 */
export const ReviewStep: React.FC<ReviewStepProps> = ({
  name,
  selectedProducts,
  loading,
  onSubmit,
}) => {
  const totalValue = selectedProducts.reduce(
    (sum, item) => sum + (item.quantity * item.unit_price),
    0
  );

  const itemsForGrid = selectedProducts.map(item => ({
    id: item.product_id,
    name: item.product.name,
    emoji: item.product.emoji,
    quantity: item.quantity,
    price: item.unit_price,
    quality: item.quality_grade,
  }));

  return (
    <>
      <Header>
        <Title>⛵ Launch Expedition</Title>
        <Subtitle>
          Review your expedition details before launching
        </Subtitle>
      </Header>

      <SummaryCard>
        <SummaryTitle>📋 Expedition Summary</SummaryTitle>

        <SummaryItem>
          <strong>Name:</strong> {name}
        </SummaryItem>

        <SummaryItem>
          <strong>Total Items:</strong> {selectedProducts.length}
        </SummaryItem>

        <SummaryItem>
          <strong>Total Value:</strong> {formatCurrency(totalValue)}
        </SummaryItem>
      </SummaryCard>

      <ItemsGrid
        items={itemsForGrid}
        showQuality
        compact={false}
      />

      <LaunchContainer>
        <PirateButton
          variant="primary"
          size="lg"
          onClick={onSubmit}
          loading={loading}
          disabled={loading}
          icon={loading ? undefined : "🚀"}
        >
          {loading ? 'Launching...' : 'Launch Expedition!'}
        </PirateButton>
      </LaunchContainer>
    </>
  );
};
