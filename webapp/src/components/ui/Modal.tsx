import React from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { X } from 'lucide-react';
import { PirateButton } from './PirateButton';

export interface ModalProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean;

  /**
   * Function called when modal should close
   */
  onClose: () => void;

  /**
   * Modal title
   */
  title: string;

  /**
   * Optional icon to display next to title
   */
  titleIcon?: React.ReactNode;

  /**
   * Modal content
   */
  children: React.ReactNode;

  /**
   * Optional footer content (typically action buttons)
   */
  footer?: React.ReactNode;

  /**
   * Modal size
   */
  size?: 'sm' | 'md' | 'lg';

  /**
   * Whether to show close button in header
   */
  showCloseButton?: boolean;

  /**
   * Whether clicking backdrop closes modal
   */
  closeOnBackdropClick?: boolean;
}

const sizeConfig = {
  sm: '400px',
  md: '500px',
  lg: '700px',
};

const Backdrop = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: ${spacing.lg};
  overflow-y: auto;
`;

const ModalContainer = styled(motion.div)<{ $size: keyof typeof sizeConfig }>`
  background: ${pirateColors.white};
  border-radius: 16px;
  padding: ${spacing['2xl']};
  max-width: ${props => sizeConfig[props.$size]};
  width: 100%;
  box-shadow: 0 20px 60px rgba(139, 69, 19, 0.3);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  margin: auto;

  @media (max-width: 640px) {
    padding: ${spacing.xl};
    max-width: 100%;
    border-radius: 12px;
  }
`;

const ModalHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing.xl};
  flex-shrink: 0;
`;

const ModalTitle = styled.h2`
  font-family: ${pirateTypography.headings};
  color: ${pirateColors.primary};
  font-size: ${pirateTypography.sizes['2xl']};
  margin: 0;
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
  font-weight: ${pirateTypography.weights.bold};

  @media (max-width: 640px) {
    font-size: ${pirateTypography.sizes.xl};
  }
`;

const ModalBody = styled.div`
  flex: 1;
  overflow-y: auto;
  margin-bottom: ${spacing.xl};

  /* Custom scrollbar for webkit browsers */
  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: ${pirateColors.lightGold};
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: ${pirateColors.secondary};
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: ${pirateColors.primary};
  }
`;

const ModalFooter = styled.div`
  display: flex;
  gap: ${spacing.md};
  justify-content: flex-end;
  flex-shrink: 0;

  @media (max-width: 640px) {
    flex-direction: column-reverse;

    button {
      width: 100%;
    }
  }
`;

/**
 * Modal Component
 *
 * A reusable modal dialog with backdrop, header, body, and footer sections.
 * Supports different sizes, custom icons, and configurable close behavior.
 *
 * @example
 * ```tsx
 * const [isOpen, setIsOpen] = useState(false);
 *
 * <Modal
 *   isOpen={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   title="Create New Pirate"
 *   titleIcon={<Users size={24} />}
 *   size="md"
 *   footer={
 *     <>
 *       <PirateButton variant="secondary" onClick={() => setIsOpen(false)}>
 *         Cancel
 *       </PirateButton>
 *       <PirateButton variant="primary" onClick={handleSubmit}>
 *         Create
 *       </PirateButton>
 *     </>
 *   }
 * >
 *   <FormGroup>
 *     <Label>Name</Label>
 *     <Input type="text" placeholder="Enter name..." />
 *   </FormGroup>
 * </Modal>
 * ```
 */
export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  titleIcon,
  children,
  footer,
  size = 'md',
  showCloseButton = true,
  closeOnBackdropClick = true,
}) => {
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (closeOnBackdropClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <Backdrop
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={handleBackdropClick}
        >
          <ModalContainer
            $size={size}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
          >
            <ModalHeader>
              <ModalTitle>
                {titleIcon}
                {title}
              </ModalTitle>
              {showCloseButton && (
                <PirateButton
                  size="sm"
                  variant="outline"
                  onClick={onClose}
                  aria-label="Close modal"
                >
                  <X size={16} />
                </PirateButton>
              )}
            </ModalHeader>

            <ModalBody>
              {children}
            </ModalBody>

            {footer && (
              <ModalFooter>
                {footer}
              </ModalFooter>
            )}
          </ModalContainer>
        </Backdrop>
      )}
    </AnimatePresence>
  );
};
