import { useState, useCallback } from 'react';
import { hapticFeedback } from '@/utils/telegram';

export interface ModalState<T> {
  isOpen: boolean;
  data: T | null;
}

export interface UseModalStateReturn<T> {
  isOpen: boolean;
  data: T | null;
  openModal: (data?: T) => void;
  closeModal: () => void;
  updateData: (data: T | null) => void;
}

/**
 * Generic modal state management hook with haptic feedback
 * Provides type-safe modal state management with consistent patterns
 *
 * @template T - The type of data associated with the modal
 * @param initialData - Optional initial data for the modal
 * @returns Modal state and control functions
 *
 * @example
 * const modal = useModalState<ProductData>();
 * modal.openModal({ id: 1, name: 'Rum' });
 * modal.closeModal();
 */
export const useModalState = <T = any>(initialData: T | null = null): UseModalStateReturn<T> => {
  const [state, setState] = useState<ModalState<T>>({
    isOpen: false,
    data: initialData,
  });

  const openModal = useCallback((data?: T) => {
    hapticFeedback('medium');
    setState({
      isOpen: true,
      data: data ?? null,
    });
  }, []);

  const closeModal = useCallback(() => {
    hapticFeedback('light');
    setState({
      isOpen: false,
      data: null,
    });
  }, []);

  const updateData = useCallback((data: T | null) => {
    setState(prev => ({
      ...prev,
      data,
    }));
  }, []);

  return {
    isOpen: state.isOpen,
    data: state.data,
    openModal,
    closeModal,
    updateData,
  };
};
