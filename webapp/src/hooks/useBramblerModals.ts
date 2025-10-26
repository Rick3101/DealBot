import { useState } from 'react';
import type { BramblerMaintenanceItem } from '@/services/api/bramblerService';
import { hapticFeedback } from '@/utils/telegram';

export type TabKey = 'pirates' | 'items';

export interface ModalsState {
  // Tab State
  activeTab: TabKey;

  // Modals
  showAddItemModal: boolean;
  showAddPirateModal: boolean;
  showEditPirateModal: boolean;
  editingPirate: BramblerMaintenanceItem | null;
  showDeleteModal: boolean;
  deleteTarget: { type: 'pirate' | 'item'; id: number; name: string } | null;
}

export interface ModalsActions {
  // Tab Actions
  handleTabChange: (tab: TabKey) => void;

  // Add Pirate Modal
  openAddPirateModal: (isOwner: boolean) => void;
  closeAddPirateModal: () => void;

  // Edit Pirate Modal
  openEditPirateModal: (pirate: BramblerMaintenanceItem, isOwner: boolean) => void;
  closeEditPirateModal: () => void;

  // Add Item Modal
  openAddItemModal: (isOwner: boolean) => void;
  closeAddItemModal: () => void;

  // Delete Modal
  openDeletePirateModal: (pirateId: number, pirateName: string, isOwner: boolean) => void;
  openDeleteItemModal: (itemId: number, itemName: string, isOwner: boolean) => void;
  closeDeleteModal: () => void;
}

/**
 * Custom hook for managing modal states in Brambler
 * Handles all modal open/close logic and tab navigation
 */
export const useBramblerModals = (): [ModalsState, ModalsActions] => {
  const [state, setState] = useState<ModalsState>({
    activeTab: 'pirates',
    showAddItemModal: false,
    showAddPirateModal: false,
    showEditPirateModal: false,
    editingPirate: null,
    showDeleteModal: false,
    deleteTarget: null,
  });

  const actions: ModalsActions = {
    handleTabChange: (tab: TabKey) => {
      hapticFeedback('light');
      setState(prev => ({ ...prev, activeTab: tab }));
    },

    openAddPirateModal: (isOwner: boolean) => {
      if (!isOwner) return;
      hapticFeedback('medium');
      setState(prev => ({ ...prev, showAddPirateModal: true }));
    },

    closeAddPirateModal: () => {
      setState(prev => ({ ...prev, showAddPirateModal: false }));
    },

    openEditPirateModal: (pirate: BramblerMaintenanceItem, isOwner: boolean) => {
      if (!isOwner) return;
      hapticFeedback('medium');
      setState(prev => ({
        ...prev,
        showEditPirateModal: true,
        editingPirate: pirate
      }));
    },

    closeEditPirateModal: () => {
      setState(prev => ({
        ...prev,
        showEditPirateModal: false,
        editingPirate: null
      }));
    },

    openAddItemModal: (isOwner: boolean) => {
      if (!isOwner) return;
      hapticFeedback('medium');
      setState(prev => ({ ...prev, showAddItemModal: true }));
    },

    closeAddItemModal: () => {
      setState(prev => ({ ...prev, showAddItemModal: false }));
    },

    openDeletePirateModal: (pirateId: number, pirateName: string, isOwner: boolean) => {
      if (!isOwner) return;
      hapticFeedback('medium');
      setState(prev => ({
        ...prev,
        showDeleteModal: true,
        deleteTarget: { type: 'pirate', id: pirateId, name: pirateName }
      }));
    },

    openDeleteItemModal: (itemId: number, itemName: string, isOwner: boolean) => {
      if (!isOwner) return;
      hapticFeedback('medium');
      setState(prev => ({
        ...prev,
        showDeleteModal: true,
        deleteTarget: { type: 'item', id: itemId, name: itemName }
      }));
    },

    closeDeleteModal: () => {
      setState(prev => ({
        ...prev,
        showDeleteModal: false,
        deleteTarget: null
      }));
    }
  };

  return [state, actions];
};
