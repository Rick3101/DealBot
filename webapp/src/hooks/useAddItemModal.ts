import { useState, useCallback } from 'react';
import { useModalState } from './useModalState';
import { Product, QualityGrade } from '@/types/expedition';
import { productService } from '@/services/api/productService';

export interface AddItemModalReturn {
  isOpen: boolean;
  availableProducts: Product[];
  selectedProductId: number | null;
  itemQuantity: number;
  itemQuality: QualityGrade | '';
  addingItem: boolean;
  open: () => Promise<void>;
  close: () => void;
  handleAdd: (
    expeditionId: number,
    addFn: (expeditionId: number, items: any) => Promise<void>,
    onSuccess: () => Promise<void>
  ) => Promise<void>;
  setSelectedProductId: (id: number | null) => void;
  setItemQuantity: (quantity: number) => void;
  setItemQuality: (quality: QualityGrade | '') => void;
}

/**
 * Specialized hook for managing the "Add Item" modal state and logic
 * Encapsulates product selection, quantity/quality configuration, and item addition flow
 */
export const useAddItemModal = (): AddItemModalReturn => {
  const modal = useModalState<Product[]>();
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [itemQuantity, setItemQuantity] = useState<number>(1);
  const [itemQuality, setItemQuality] = useState<QualityGrade | ''>('');
  const [addingItem, setAddingItem] = useState(false);

  const open = useCallback(async () => {
    try {
      const products = await productService.getAll();
      modal.openModal(products);
      setSelectedProductId(null);
      setItemQuantity(1);
      setItemQuality('');
    } catch (error) {
      console.error('Error loading products:', error);
      throw error;
    }
  }, [modal]);

  const close = useCallback(() => {
    modal.closeModal();
    setSelectedProductId(null);
    setItemQuantity(1);
    setItemQuality('');
  }, [modal]);

  const handleAdd = useCallback(async (
    expeditionId: number,
    addFn: (expeditionId: number, items: any) => Promise<void>,
    onSuccess: () => Promise<void>
  ) => {
    if (!selectedProductId || itemQuantity <= 0) {
      return;
    }

    setAddingItem(true);
    try {
      // Execute the add operation
      await addFn(expeditionId, {
        items: [{
          product_id: selectedProductId,
          quantity: itemQuantity,
          unit_cost: itemQuality ? parseFloat(itemQuality) : undefined,
        }],
      });

      // Wait for the refresh to complete before closing
      await onSuccess();

      // Now close the modal with fresh data loaded
      close();
    } catch (error) {
      console.error('Error adding item:', error);
      throw error;
    } finally {
      setAddingItem(false);
    }
  }, [selectedProductId, itemQuantity, itemQuality, close]);

  return {
    isOpen: modal.isOpen,
    availableProducts: modal.data || [],
    selectedProductId,
    itemQuantity,
    itemQuality,
    addingItem,
    open,
    close,
    handleAdd,
    setSelectedProductId,
    setItemQuantity,
    setItemQuality,
  };
};
