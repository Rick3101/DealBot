import React from 'react';
import styled from 'styled-components';
import { PirateCard } from '@/components/ui/PirateCard';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { QualityGrade, Product } from '@/types/expedition';

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

const ItemsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.lg};
`;

const ItemHeader = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.md};
  margin-bottom: ${spacing.md};
`;

const ItemIcon = styled.span`
  font-size: 1.5rem;
`;

const ItemTitle = styled.h4`
  font-family: ${pirateTypography.headings};
  color: ${pirateColors.primary};
  margin: 0;
  flex: 1;
`;

const ConfigGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: ${spacing.md};
`;

const FormLabel = styled.label`
  display: block;
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.sm};
  font-size: ${pirateTypography.sizes.base};
`;

const FormInput = styled.input`
  width: 100%;
  padding: ${spacing.md};
  border: 2px solid ${pirateColors.lightGold};
  border-radius: 8px;
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.base};
  background: ${pirateColors.white};
  color: ${pirateColors.primary};
  transition: all 0.3s ease;

  &:focus {
    outline: none;
    border-color: ${pirateColors.secondary};
    box-shadow: 0 0 0 3px rgba(218, 165, 32, 0.1);
  }
`;

const FormSelect = styled.select`
  width: 100%;
  padding: ${spacing.md};
  border: 2px solid ${pirateColors.lightGold};
  border-radius: 8px;
  background: ${pirateColors.white};
  color: ${pirateColors.primary};
  font-size: ${pirateTypography.sizes.base};
  cursor: pointer;
  transition: all 0.3s ease;

  &:focus {
    outline: none;
    border-color: ${pirateColors.secondary};
    box-shadow: 0 0 0 3px rgba(218, 165, 32, 0.1);
  }
`;

export interface SelectedProductItem {
  product_id: number;
  product: Product;
  quantity: number;
  quality_grade: QualityGrade;
  unit_price: number;
}

export interface ProductConfigurationStepProps {
  selectedProducts: SelectedProductItem[];
  onQuantityChange: (productId: number, quantity: number) => void;
  onQualityChange: (productId: number, qualityGrade: QualityGrade) => void;
  onPriceChange: (productId: number, unitPrice: number) => void;
}

/**
 * Step 3: Product Configuration
 * Pure presentation component for configuring quantities, quality grades, and prices
 */
export const ProductConfigurationStep: React.FC<ProductConfigurationStepProps> = ({
  selectedProducts,
  onQuantityChange,
  onQualityChange,
  onPriceChange,
}) => {
  return (
    <>
      <Header>
        <Title>💰 Configure Items</Title>
        <Subtitle>
          Set quantities, quality grades, and prices for each item
        </Subtitle>
      </Header>

      <ItemsContainer>
        {selectedProducts.map(item => (
          <PirateCard key={item.product_id}>
            <ItemHeader>
              <ItemIcon>{item.product.emoji}</ItemIcon>
              <ItemTitle>{item.product.name}</ItemTitle>
            </ItemHeader>

            <ConfigGrid>
              <div>
                <FormLabel>Quantity</FormLabel>
                <FormInput
                  type="number"
                  min="1"
                  value={item.quantity}
                  onChange={(e) => onQuantityChange(
                    item.product_id,
                    parseInt(e.target.value) || 1
                  )}
                />
              </div>

              <div>
                <FormLabel>Quality Grade</FormLabel>
                <FormSelect
                  value={item.quality_grade}
                  onChange={(e) => onQualityChange(
                    item.product_id,
                    e.target.value as QualityGrade
                  )}
                >
                  <option value="A">A - Premium 🌟</option>
                  <option value="B">B - Standard ⭐</option>
                  <option value="C">C - Basic 🔸</option>
                </FormSelect>
              </div>

              <div>
                <FormLabel>Unit Price</FormLabel>
                <FormInput
                  type="number"
                  min="0"
                  step="0.01"
                  value={item.unit_price}
                  onChange={(e) => onPriceChange(
                    item.product_id,
                    parseFloat(e.target.value) || 0
                  )}
                />
              </div>
            </ConfigGrid>
          </PirateCard>
        ))}
      </ItemsContainer>
    </>
  );
};
