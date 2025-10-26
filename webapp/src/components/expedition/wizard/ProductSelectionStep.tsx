import React from 'react';
import styled, { css } from 'styled-components';
import { PirateCard } from '@/components/ui/PirateCard';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { Product } from '@/types/expedition';
import { formatCurrency } from '@/utils/formatters';

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

const ProductGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: ${spacing.md};
  margin-bottom: ${spacing.xl};

  @media (min-width: 640px) {
    grid-template-columns: repeat(2, 1fr);
    gap: ${spacing.sm};
  }

  @media (min-width: 768px) {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
`;

const ProductCard = styled(PirateCard)<{ $selected: boolean }>`
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  ${props => props.$selected && css`
    border-color: ${pirateColors.secondary};
    box-shadow: 0 0 20px rgba(218, 165, 32, 0.3);
    transform: translateY(-2px);
  `}

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(139, 69, 19, 0.2);
  }
`;

const SelectedBadge = styled.div`
  position: absolute;
  top: ${spacing.sm};
  right: ${spacing.sm};
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: ${pirateColors.success};
  color: ${pirateColors.white};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: ${pirateTypography.weights.bold};
`;

const ProductIcon = styled.div`
  font-size: 2rem;
  text-align: center;
  margin-bottom: ${spacing.sm};
`;

const ProductName = styled.h4`
  font-family: ${pirateTypography.headings};
  color: ${pirateColors.primary};
  margin: 0 0 ${spacing.sm} 0;
  text-align: center;
`;

const ProductPrice = styled.div`
  text-align: center;
  color: ${pirateColors.muted};
  font-size: ${pirateTypography.sizes.sm};
`;

const SelectionCount = styled.div`
  text-align: center;
  color: ${pirateColors.success};
  font-weight: ${pirateTypography.weights.medium};
`;

export interface ProductSelectionStepProps {
  availableProducts: Product[];
  selectedProductIds: number[];
  onProductToggle: (product: Product) => void;
}

/**
 * Step 2: Product Selection
 * Pure presentation component for selecting expedition items
 */
export const ProductSelectionStep: React.FC<ProductSelectionStepProps> = ({
  availableProducts,
  selectedProductIds,
  onProductToggle,
}) => {
  const selectedCount = selectedProductIds.length;

  return (
    <>
      <Header>
        <Title>📦 Select Expedition Items</Title>
        <Subtitle>
          Choose the items your pirates will need for this expedition
        </Subtitle>
      </Header>

      <ProductGrid>
        {availableProducts.map(product => {
          const isSelected = selectedProductIds.includes(product.id);

          return (
            <ProductCard
              key={product.id}
              $selected={isSelected}
              clickable
              onClick={() => onProductToggle(product)}
            >
              {isSelected && <SelectedBadge>✓</SelectedBadge>}

              <ProductIcon>{product.emoji}</ProductIcon>
              <ProductName>{product.name}</ProductName>
              <ProductPrice>{formatCurrency(product.price)}</ProductPrice>
            </ProductCard>
          );
        })}
      </ProductGrid>

      {selectedCount > 0 && (
        <SelectionCount>
          ✓ {selectedCount} {selectedCount === 1 ? 'item' : 'items'} selected
        </SelectionCount>
      )}
    </>
  );
};
