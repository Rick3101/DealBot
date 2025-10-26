import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { PirateButton } from '@/components/ui/PirateButton';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { hapticFeedback } from '@/utils/telegram';
import type { BramblerMaintenanceItem } from '@/services/api/bramblerService';

interface EditPirateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (pirate: BramblerMaintenanceItem) => void;
  pirate: BramblerMaintenanceItem | null;
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
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
`;

const ModalHeader = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.md};
  margin-bottom: ${spacing.lg};
`;

const PirateIcon = styled.div`
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
  line-height: 1.5;
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
    background: ${pirateColors.lightGold}20;
  }
`;

const HelpText = styled.div`
  font-size: ${pirateTypography.sizes.xs};
  color: ${pirateColors.muted};
  margin-top: ${spacing.xs};
  font-style: italic;
`;

const InfoBox = styled.div`
  background: ${pirateColors.lightGold}40;
  padding: ${spacing.md};
  border-radius: 8px;
  border-left: 4px solid ${pirateColors.secondary};
  margin-bottom: ${spacing.lg};
  display: flex;
  align-items: start;
  gap: ${spacing.sm};
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.primary};
  line-height: 1.5;
`;

const InfoIcon = styled.span`
  font-size: 1.2rem;
  flex-shrink: 0;
`;

const ErrorMessage = styled.div`
  color: ${pirateColors.danger};
  font-size: ${pirateTypography.sizes.sm};
  margin-top: ${spacing.xs};
  padding: ${spacing.sm};
  background: ${pirateColors.danger}10;
  border-radius: 8px;
`;

const ModalActions = styled.div`
  display: flex;
  gap: ${spacing.md};
  justify-content: flex-end;
  margin-top: ${spacing.xl};
  padding-top: ${spacing.lg};
  border-top: 1px solid ${pirateColors.lightGold};
`;

const DetailRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: ${spacing.sm} 0;
  color: ${pirateColors.muted};
  font-size: ${pirateTypography.sizes.sm};

  strong {
    color: ${pirateColors.primary};
    font-weight: ${pirateTypography.weights.medium};
  }
`;

export const EditPirateModal: React.FC<EditPirateModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  pirate
}) => {
  const [newPirateName, setNewPirateName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && pirate) {
      setNewPirateName(pirate.pirate_name);
      setError(null);
      setLoading(false);
    }
  }, [isOpen, pirate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!pirate) return;

    setLoading(true);
    setError(null);

    // Validation
    if (!newPirateName.trim()) {
      setError('Please enter a pirate name');
      setLoading(false);
      hapticFeedback('error');
      return;
    }

    if (newPirateName.trim().length < 3) {
      setError('Pirate name must be at least 3 characters');
      setLoading(false);
      hapticFeedback('error');
      return;
    }

    if (newPirateName.trim() === pirate.pirate_name) {
      setError('New pirate name must be different from the current name');
      setLoading(false);
      hapticFeedback('error');
      return;
    }

    try {
      const { bramblerService } = await import('@/services/api/bramblerService');

      hapticFeedback('medium');

      const success = await bramblerService.updatePirateName(
        pirate.id,
        newPirateName.trim()
      );

      if (success) {
        hapticFeedback('success');

        // Create updated pirate object
        const updatedPirate: BramblerMaintenanceItem = {
          ...pirate,
          pirate_name: newPirateName.trim()
        };

        onSuccess(updatedPirate);
        onClose();

        // Show success message
        await import('@/utils/telegram').then(({ showAlert }) => {
          showAlert(`Pirate renamed to "${newPirateName.trim()}" successfully!`);
        });
      } else {
        setError('Failed to update pirate name');
        hapticFeedback('error');
      }
    } catch (err) {
      console.error('Failed to update pirate:', err);
      setError(err instanceof Error ? err.message : 'Failed to update pirate');
      hapticFeedback('error');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      hapticFeedback('light');
      onClose();
    }
  };

  if (!isOpen || !pirate) return null;

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
            <PirateIcon>✏️</PirateIcon>
            <ModalTitle>Edit Pirate</ModalTitle>
          </ModalHeader>

          <ModalDescription>
            Update the pirate's display name. The original encrypted identity remains unchanged.
          </ModalDescription>

          <InfoBox>
            <InfoIcon>ℹ️</InfoIcon>
            <div>
              <DetailRow>
                <span>Expedition:</span>
                <strong>{pirate.expedition_name}</strong>
              </DetailRow>
              <DetailRow>
                <span>Current Name:</span>
                <strong>{pirate.pirate_name}</strong>
              </DetailRow>
              {pirate.created_at && (
                <DetailRow>
                  <span>Created:</span>
                  <strong>{new Date(pirate.created_at).toLocaleDateString()}</strong>
                </DetailRow>
              )}
            </div>
          </InfoBox>

          <form onSubmit={handleSubmit}>
            <FormGroup>
              <Label>New Pirate Name</Label>
              <Input
                type="text"
                value={newPirateName}
                onChange={(e) => setNewPirateName(e.target.value)}
                placeholder="Enter new pirate name..."
                minLength={3}
                maxLength={100}
                required
                disabled={loading}
                autoFocus
              />
              <HelpText>This is the public name that will be displayed</HelpText>
            </FormGroup>

            {error && (
              <ErrorMessage>{error}</ErrorMessage>
            )}

            <ModalActions>
              <PirateButton
                variant="outline"
                onClick={handleClose}
                disabled={loading}
              >
                Cancel
              </PirateButton>
              <PirateButton
                variant="primary"
                onClick={(e) => {
                  e?.preventDefault();
                  handleSubmit(e as any);
                }}
                disabled={loading || !newPirateName.trim() || newPirateName.trim() === pirate.pirate_name}
              >
                {loading ? 'Updating...' : 'Update Pirate'}
              </PirateButton>
            </ModalActions>
          </form>
        </ModalContent>
      </ModalOverlay>
    </AnimatePresence>
  );
};
