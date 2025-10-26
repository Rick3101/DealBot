import { useCallback } from 'react';
import { useModalState } from './useModalState';

export interface ConsumeItemData {
  product_id: number;
  product_name: string;
  available: number;
  unit_price: number;
  [key: string]: any;
}

export interface ConsumeItemModalReturn {
  isOpen: boolean;
  selectedItem: ConsumeItemData | null;
  open: (item: ConsumeItemData) => void;
  close: () => void;
  handleConsume: (
    consumeFn: (pirateName: string, quantity: number, price: number) => Promise<void>,
    pirateName: string,
    quantity: number,
    price: number
  ) => Promise<void>;
}

/**
 * Specialized hook for managing the "Consume Item" modal state and logic
 * Encapsulates item consumption flow with validation
 */
export const useConsumeItemModal = (): ConsumeItemModalReturn => {
  const modal = useModalState<ConsumeItemData>();

  const open = useCallback((item: ConsumeItemData) => {
    modal.openModal(item);
  }, [modal]);

  const close = useCallback(() => {
    modal.closeModal();
  }, [modal]);

  const handleConsume = useCallback(async (
    consumeFn: (pirateName: string, quantity: number, price: number) => Promise<void>,
    pirateName: string,
    quantity: number,
    price: number
  ) => {
    if (!modal.data) {
      throw new Error('No item selected for consumption');
    }

    try {
      await consumeFn(pirateName, quantity, price);
      close();
    } catch (error) {
      console.error('Error consuming item:', error);
      throw error;
    }
  }, [modal.data, close]);

  return {
    isOpen: modal.isOpen,
    selectedItem: modal.data,
    open,
    close,
    handleConsume,
  };
};
