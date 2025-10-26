import React from 'react';
import styled, { keyframes } from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { Loader2 } from 'lucide-react';

export interface LoadingOverlayProps {
  /**
   * Whether to show the loading overlay
   */
  show: boolean;

  /**
   * Optional loading message
   */
  message?: string;

  /**
   * Whether to blur the background
   */
  blur?: boolean;

  /**
   * Z-index of the overlay
   */
  zIndex?: number;
}

const spin = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

const Overlay = styled(motion.div)<{ $blur?: boolean; $zIndex: number }>`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: ${props => props.$zIndex};
  backdrop-filter: ${props => props.$blur ? 'blur(4px)' : 'none'};
`;

const LoadingContainer = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: ${spacing.lg};
  background: ${pirateColors.white};
  padding: ${spacing['2xl']};
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(139, 69, 19, 0.3);
  min-width: 200px;
`;

const SpinnerIcon = styled(Loader2)`
  animation: ${spin} 1s linear infinite;
  color: ${pirateColors.secondary};
`;

const LoadingMessage = styled.p`
  color: ${pirateColors.primary};
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.lg};
  font-weight: ${pirateTypography.weights.bold};
  margin: 0;
  text-align: center;
`;

/**
 * LoadingOverlay Component
 *
 * Full-screen loading overlay with spinner and optional message.
 * Prevents user interaction while loading.
 *
 * @example
 * ```tsx
 * const [loading, setLoading] = useState(false);
 *
 * <LoadingOverlay
 *   show={loading}
 *   message="Loading pirates..."
 *   blur
 * />
 * ```
 */
export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  show,
  message = 'Loading...',
  blur = true,
  zIndex = 9999,
}) => {
  return (
    <AnimatePresence>
      {show && (
        <Overlay
          $blur={blur}
          $zIndex={zIndex}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <LoadingContainer
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ duration: 0.2, delay: 0.1 }}
          >
            <SpinnerIcon size={48} />
            {message && <LoadingMessage>{message}</LoadingMessage>}
          </LoadingContainer>
        </Overlay>
      )}
    </AnimatePresence>
  );
};
