import React from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { PirateButton } from '@/components/ui/PirateButton';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { hapticFeedback } from '@/utils/telegram';
import { AlertTriangle } from 'lucide-react';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  itemName: string;
  loading?: boolean;
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
  max-width: 450px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
`;

const ModalHeader = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.md};
  margin-bottom: ${spacing.lg};
`;

const WarningIcon = styled.div`
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(145deg, ${pirateColors.danger}, ${pirateColors.warning});
  color: ${pirateColors.white};
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
`;

const ModalTitle = styled.h2`
  font-family: ${pirateTypography.headings};
  font-size: 1.5rem;
  color: ${pirateColors.danger};
  margin: 0;
  flex: 1;
`;

const ModalMessage = styled.p`
  color: ${pirateColors.muted};
  margin-bottom: ${spacing.lg};
  font-size: ${pirateTypography.sizes.base};
  line-height: 1.6;
`;

const ItemNameBox = styled.div`
  background: ${pirateColors.lightGold}40;
  padding: ${spacing.md};
  border-radius: 8px;
  border-left: 4px solid ${pirateColors.danger};
  margin-bottom: ${spacing.lg};
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.lg};
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.primary};
  text-align: center;
`;

const WarningBox = styled.div`
  background: ${pirateColors.danger}10;
  padding: ${spacing.md};
  border-radius: 8px;
  margin-bottom: ${spacing.lg};
  display: flex;
  align-items: start;
  gap: ${spacing.sm};
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.danger};
  line-height: 1.5;
`;

const WarningText = styled.div`
  flex: 1;
`;

const ModalActions = styled.div`
  display: flex;
  gap: ${spacing.md};
  justify-content: flex-end;
`;

export const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  itemName,
  loading = false
}) => {
  const handleConfirm = () => {
    hapticFeedback('heavy');
    onConfirm();
  };

  const handleClose = () => {
    if (!loading) {
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
            <WarningIcon>
              <AlertTriangle size={24} />
            </WarningIcon>
            <ModalTitle>{title}</ModalTitle>
          </ModalHeader>

          <ModalMessage>{message}</ModalMessage>

          <ItemNameBox>{itemName}</ItemNameBox>

          <WarningBox>
            <AlertTriangle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
            <WarningText>
              This action cannot be undone. The item will be permanently deleted from the database.
            </WarningText>
          </WarningBox>

          <ModalActions>
            <PirateButton
              variant="outline"
              onClick={handleClose}
              disabled={loading}
            >
              Cancel
            </PirateButton>
            <PirateButton
              variant="danger"
              onClick={handleConfirm}
              disabled={loading}
            >
              {loading ? 'Deleting...' : 'Delete'}
            </PirateButton>
          </ModalActions>
        </ModalContent>
      </ModalOverlay>
    </AnimatePresence>
  );
};
