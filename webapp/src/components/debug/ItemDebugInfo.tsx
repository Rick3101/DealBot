import React, { useState } from 'react';
import styled from 'styled-components';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';

interface ItemDebugInfoProps {
  items: any[];
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
}

const DebugContainer = styled.div<{ $position: string }>`
  position: fixed;
  ${props => {
    switch (props.$position) {
      case 'top-right':
        return 'top: 10px; right: 10px;';
      case 'bottom-left':
        return 'bottom: 10px; left: 10px;';
      case 'bottom-right':
        return 'bottom: 10px; right: 10px;';
      default:
        return 'top: 10px; left: 10px;';
    }
  }}
  z-index: 9999;
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid ${pirateColors.secondary};
  border-radius: 8px;
  padding: ${spacing.sm};
  max-width: 350px;
  max-height: 400px;
  overflow: auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.xs};
`;

const ToggleButton = styled.button<{ $position: string }>`
  position: fixed;
  ${props => {
    switch (props.$position) {
      case 'top-right':
        return 'top: 10px; right: 10px;';
      case 'bottom-left':
        return 'bottom: 10px; left: 10px;';
      case 'bottom-right':
        return 'bottom: 10px; right: 10px;';
      default:
        return 'top: 10px; left: 10px;';
    }
  }}
  z-index: 9999;
  background: ${pirateColors.secondary};
  color: ${pirateColors.white};
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: ${pirateTypography.weights.bold};
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;

  &:hover {
    background: ${pirateColors.primary};
    transform: scale(1.1);
  }
`;

const DebugTitle = styled.div`
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.xs};
  border-bottom: 2px solid ${pirateColors.lightGold};
  padding-bottom: ${spacing.xs};
`;

const ItemDebug = styled.div`
  margin-bottom: ${spacing.sm};
  padding: ${spacing.xs};
  background: ${pirateColors.lightGold}30;
  border-radius: 4px;
  border-left: 3px solid ${pirateColors.secondary};
`;

const ItemName = styled.div`
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.xs};
`;

const ItemField = styled.div<{ $alert?: boolean }>`
  color: ${props => props.$alert ? pirateColors.danger : pirateColors.muted};
  font-size: ${pirateTypography.sizes.xs};
  margin-left: ${spacing.sm};
`;

const Summary = styled.div`
  background: ${pirateColors.secondary}20;
  padding: ${spacing.sm};
  border-radius: 4px;
  margin-bottom: ${spacing.sm};
  font-weight: ${pirateTypography.weights.medium};
`;

export const ItemDebugInfo: React.FC<ItemDebugInfoProps> = ({
  items,
  position = 'bottom-right'
}) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!items || items.length === 0) {
    return null;
  }

  const availableCount = items.filter(item => item.available > 0).length;
  const fullyConsumedCount = items.filter(item => item.available === 0).length;

  return (
    <>
      {!isOpen && (
        <ToggleButton
          $position={position}
          onClick={() => setIsOpen(true)}
          title="Show Item Debug Info"
        >
          ?
        </ToggleButton>
      )}

      {isOpen && (
        <DebugContainer $position={position}>
          <ToggleButton
            $position={position}
            onClick={() => setIsOpen(false)}
            title="Hide Debug Info"
          >
            X
          </ToggleButton>

          <DebugTitle>Item Debug Info</DebugTitle>

          <Summary>
            Total Items: {items.length}<br />
            Available: {availableCount}<br />
            Fully Consumed: {fullyConsumedCount}
          </Summary>

          {items.map((item) => (
            <ItemDebug key={item.id}>
              <ItemName>
                {item.emoji || '📦'} {item.name}
              </ItemName>
              <ItemField>ID: {item.id}</ItemField>
              <ItemField>Product ID: {item.product_id}</ItemField>
              <ItemField>Quantity: {item.quantity}</ItemField>
              <ItemField>Consumed: {item.consumed}</ItemField>
              <ItemField $alert={item.available === 0}>
                Available: {item.available} {item.available === 0 ? '⚠️' : '✅'}
              </ItemField>
              <ItemField>Price: R$ {item.price?.toFixed(2)}</ItemField>
              {item.quality && (
                <ItemField>Quality: {item.quality}</ItemField>
              )}
            </ItemDebug>
          ))}
        </DebugContainer>
      )}
    </>
  );
};
