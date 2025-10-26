import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { PirateButton } from '@/components/ui/PirateButton';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { hapticFeedback } from '@/utils/telegram';
import { PirateName } from '@/types/expedition';

interface ConsumeItemModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (pirateName: string, quantity: number, price: number) => Promise<void>;
  itemName: string;
  itemEmoji?: string;
  availableQuantity: number;
  suggestedPrice?: number;
  pirateNames: PirateName[];
}

const ModalOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: ${spacing.lg};
`;

const ModalContent = styled(motion.div)`
  background: ${pirateColors.white};
  border-radius: 16px;
  padding: ${spacing.xl};
  max-width: 500px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
`;

const ModalHeader = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.md};
  margin-bottom: ${spacing.lg};
`;

const ItemIcon = styled.div`
  font-size: 2.5rem;
  filter: drop-shadow(0 2px 4px rgba(139, 69, 19, 0.1));
`;

const ModalTitle = styled.h2`
  font-family: ${pirateTypography.headings};
  font-size: 1.5rem;
  color: ${pirateColors.primary};
  margin: 0;
  flex: 1;
`;

const ModalDescription = styled.p`
  color: ${pirateColors.muted};
  margin-bottom: ${spacing.lg};
  font-size: ${pirateTypography.sizes.sm};
`;

const FormGroup = styled.div`
  margin-bottom: ${spacing.lg};
`;

const Label = styled.label`
  display: block;
  font-weight: ${pirateTypography.weights.medium};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.sm};
  font-size: ${pirateTypography.sizes.sm};
`;

const Select = styled.select`
  width: 100%;
  padding: ${spacing.md};
  border: 2px solid ${pirateColors.lightGold};
  border-radius: 8px;
  font-size: ${pirateTypography.sizes.base};
  font-family: ${pirateTypography.headings};
  color: ${pirateColors.primary};
  transition: all 0.3s ease;
  background: ${pirateColors.white};
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: ${pirateColors.secondary};
    box-shadow: 0 0 0 3px rgba(218, 165, 32, 0.1);
  }

  option {
    padding: ${spacing.sm};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const Input = styled.input`
  width: 100%;
  padding: ${spacing.md};
  border: 2px solid ${pirateColors.lightGold};
  border-radius: 8px;
  font-size: ${pirateTypography.sizes.base};
  font-family: ${pirateTypography.body};
  color: ${pirateColors.primary};
  transition: all 0.3s ease;
  background: ${pirateColors.white};

  &:focus {
    outline: none;
    border-color: ${pirateColors.secondary};
    box-shadow: 0 0 0 3px rgba(218, 165, 32, 0.1);
  }

  &::placeholder {
    color: ${pirateColors.muted};
    opacity: 0.6;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const InputHint = styled.div`
  font-size: ${pirateTypography.sizes.xs};
  color: ${pirateColors.muted};
  margin-top: ${spacing.xs};
`;

const ErrorMessage = styled.div`
  color: ${pirateColors.danger};
  font-size: ${pirateTypography.sizes.sm};
  margin-top: ${spacing.xs};
`;

const ModalActions = styled.div`
  display: flex;
  gap: ${spacing.md};
  justify-content: flex-end;
  margin-top: ${spacing.xl};
`;

const TotalPreview = styled.div`
  background: ${pirateColors.lightGold};
  padding: ${spacing.md};
  border-radius: 8px;
  margin-bottom: ${spacing.lg};
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const TotalLabel = styled.span`
  font-weight: ${pirateTypography.weights.medium};
  color: ${pirateColors.primary};
`;

const TotalValue = styled.span`
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.lg};
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.secondary};
`;

export const ConsumeItemModal: React.FC<ConsumeItemModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  itemName,
  itemEmoji,
  availableQuantity,
  suggestedPrice,
  pirateNames,
}) => {
  const [selectedPirate, setSelectedPirate] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [price, setPrice] = useState(suggestedPrice || 0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setSelectedPirate('');
      setQuantity(1);
      setPrice(suggestedPrice || 0);
      setError('');
      setIsSubmitting(false);
    }
  }, [isOpen, suggestedPrice]);

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const totalPrice = quantity * price;

  const handleSubmit = async () => {
    setError('');

    // Validation
    if (!selectedPirate) {
      setError('Please select a pirate');
      hapticFeedback('error');
      return;
    }

    if (quantity <= 0) {
      setError('Quantity must be greater than 0');
      hapticFeedback('error');
      return;
    }

    if (quantity > availableQuantity) {
      setError(`Only ${availableQuantity} items available`);
      hapticFeedback('error');
      return;
    }

    if (price <= 0) {
      setError('Price must be greater than 0');
      hapticFeedback('error');
      return;
    }

    setIsSubmitting(true);
    hapticFeedback('medium');

    try {
      // Wait for the operation AND refresh to complete before closing
      await onConfirm(selectedPirate, quantity, price);
      hapticFeedback('success');

      // Close modal after operation completes
      // The onConfirm already triggers a refresh, so data will be fresh
      onClose();
    } catch (err) {
      console.error('Error consuming item:', err);
      setError(err instanceof Error ? err.message : 'Failed to consume item');
      hapticFeedback('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      hapticFeedback('light');
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <ModalOverlay
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={handleClose}
      >
        <ModalContent
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
        >
          <ModalHeader>
            <ItemIcon>{itemEmoji || '📦'}</ItemIcon>
            <ModalTitle>Consume {itemName}</ModalTitle>
          </ModalHeader>

          <ModalDescription>
            Select a pirate and specify the quantity and price for this consumption.
          </ModalDescription>

          <FormGroup>
            <Label>Pirate</Label>
            <Select
              value={selectedPirate}
              onChange={(e) => {
                setSelectedPirate(e.target.value);
                setError('');
              }}
              disabled={isSubmitting || pirateNames.length === 0}
              autoFocus
            >
              <option value="">
                {pirateNames.length === 0 ? 'No pirates available' : 'Select a pirate...'}
              </option>
              {pirateNames.map((pirate) => (
                <option key={pirate.id} value={pirate.pirate_name}>
                  {pirate.pirate_name}
                </option>
              ))}
            </Select>
            {pirateNames.length === 0 && (
              <InputHint>Add pirates to the expedition first</InputHint>
            )}
          </FormGroup>

          <FormGroup>
            <Label>Quantity</Label>
            <Input
              type="number"
              min="1"
              max={availableQuantity}
              value={quantity}
              onChange={(e) => {
                setQuantity(parseInt(e.target.value) || 1);
                setError('');
              }}
              disabled={isSubmitting}
              placeholder="Enter quantity"
            />
            <InputHint>Available: {availableQuantity} items</InputHint>
          </FormGroup>

          <FormGroup>
            <Label>Price per Unit (R$)</Label>
            <Input
              type="number"
              min="0"
              step="0.01"
              value={price}
              onChange={(e) => {
                setPrice(parseFloat(e.target.value) || 0);
                setError('');
              }}
              disabled={isSubmitting}
              placeholder="Enter price"
            />
            {suggestedPrice && (
              <InputHint>Suggested: {formatCurrency(suggestedPrice)}</InputHint>
            )}
          </FormGroup>

          {totalPrice > 0 && (
            <TotalPreview>
              <TotalLabel>Total Price:</TotalLabel>
              <TotalValue>{formatCurrency(totalPrice)}</TotalValue>
            </TotalPreview>
          )}

          {error && <ErrorMessage>{error}</ErrorMessage>}

          <ModalActions>
            <PirateButton
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
            >
              Cancel
            </PirateButton>
            <PirateButton
              variant="primary"
              onClick={handleSubmit}
              disabled={isSubmitting || !selectedPirate || quantity <= 0 || price <= 0}
            >
              {isSubmitting ? 'Consuming...' : 'Consume'}
            </PirateButton>
          </ModalActions>
        </ModalContent>
      </ModalOverlay>
    </AnimatePresence>
  );
};
