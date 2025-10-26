import React, { useEffect } from 'react';
import type { BramblerMaintenanceItem, EncryptedItem } from '@/services/api/bramblerService';
import { useBramblerData } from '@/hooks/useBramblerData';
import { useBramblerDecryption } from '@/hooks/useBramblerDecryption';
import { useBramblerModals } from '@/hooks/useBramblerModals';
import { useBramblerActions } from '@/hooks/useBramblerActions';

export interface BramblerManagerProps {
  children: (props: BramblerManagerContainerProps) => React.ReactNode;
}

export interface BramblerManagerContainerProps {
  // Data State
  pirateNames: BramblerMaintenanceItem[];
  encryptedItems: EncryptedItem[];
  expeditions: Array<{ id: number; name: string }>;
  loading: boolean;
  error: string | null;
  isOwner: boolean;

  // Decryption State
  decryptionKey: string;
  showRealNames: boolean;
  decryptedMappings: Record<string, string>;
  decryptedItemMappings: Record<string, string>;
  individualToggles: Record<number, boolean>;

  // Modal State
  activeTab: 'pirates' | 'items';
  showAddItemModal: boolean;
  showAddPirateModal: boolean;
  showEditPirateModal: boolean;
  editingPirate: BramblerMaintenanceItem | null;
  showDeleteModal: boolean;
  deleteTarget: { type: 'pirate' | 'item'; id: number; name: string } | null;

  // Data Actions
  refreshData: () => Promise<void>;
  onAddPirateSuccess: (pirate: BramblerMaintenanceItem) => void;
  onEditPirateSuccess: (updatedPirate: BramblerMaintenanceItem) => void;
  onAddItemSuccess: (item: EncryptedItem) => void;

  // Decryption Actions
  onKeyChange: (key: string) => void;
  onToggleView: () => Promise<void>;
  onGetMasterKey: () => Promise<void>;
  onSaveMasterKey: () => Promise<void>;
  onClearSavedKey: () => Promise<void>;
  onToggleIndividualName: (pirateId: number, e?: React.MouseEvent) => Promise<void>;

  // Modal Actions
  onTabChange: (tab: 'pirates' | 'items') => void;
  onOpenAddPirateModal: () => void;
  onCloseAddPirateModal: () => void;
  onOpenEditPirateModal: (pirate: BramblerMaintenanceItem) => void;
  onCloseEditPirateModal: () => void;
  onOpenAddItemModal: () => void;
  onCloseAddItemModal: () => void;
  onOpenDeletePirateModal: (pirateId: number, pirateName: string) => void;
  onOpenDeleteItemModal: (itemId: number, itemName: string) => void;
  onCloseDeleteModal: () => void;
  onConfirmDelete: () => Promise<void>;

  // Utility Actions
  onGenerateNewNames: () => Promise<void>;
  onExportNames: () => void;
  onImportNames: () => void;
}

/**
 * Container component for BramblerManager
 * Manages all state and business logic using custom hooks
 * Implements Container/Presenter pattern for clean separation of concerns
 */
export const BramblerManagerContainer: React.FC<BramblerManagerProps> = ({ children }) => {
  // Data Management
  const [dataState, dataActions] = useBramblerData();

  // Decryption Management
  const [decryptionState, decryptionActions] = useBramblerDecryption();

  // Modal Management
  const [modalState, modalActions] = useBramblerModals();

  // Actions Management
  const actionsHandlers = useBramblerActions();

  // Auto-load decryption key from data state
  useEffect(() => {
    if (dataState.autoLoadedKey && !decryptionState.decryptionKey) {
      decryptionActions.setDecryptionKey(dataState.autoLoadedKey);
    }
  }, [dataState.autoLoadedKey, decryptionState.decryptionKey, decryptionActions]);

  // Delete success handler
  const handleDeleteSuccess = (type: 'pirate' | 'item', id: number) => {
    if (type === 'pirate') {
      dataActions.removePirate(id);
    } else {
      dataActions.removeItem(id);
    }
    modalActions.closeDeleteModal();
  };

  // Compose all props for the presenter
  const containerProps: BramblerManagerContainerProps = {
    // Data State
    pirateNames: dataState.pirateNames,
    encryptedItems: dataState.encryptedItems,
    expeditions: dataState.expeditions,
    loading: dataState.loading,
    error: dataState.error,
    isOwner: dataState.isOwner,

    // Decryption State
    decryptionKey: decryptionState.decryptionKey,
    showRealNames: decryptionState.showRealNames,
    decryptedMappings: decryptionState.decryptedMappings,
    decryptedItemMappings: decryptionState.decryptedItemMappings,
    individualToggles: decryptionState.individualToggles,

    // Modal State
    activeTab: modalState.activeTab,
    showAddItemModal: modalState.showAddItemModal,
    showAddPirateModal: modalState.showAddPirateModal,
    showEditPirateModal: modalState.showEditPirateModal,
    editingPirate: modalState.editingPirate,
    showDeleteModal: modalState.showDeleteModal,
    deleteTarget: modalState.deleteTarget,

    // Data Actions
    refreshData: dataActions.refreshData,
    onAddPirateSuccess: dataActions.addPirate,
    onEditPirateSuccess: dataActions.updatePirate,
    onAddItemSuccess: dataActions.addItem,

    // Decryption Actions
    onKeyChange: decryptionActions.setDecryptionKey,
    onToggleView: () => decryptionActions.toggleView(dataState.isOwner, dataActions.setLoading, dataActions.setError),
    onGetMasterKey: () => decryptionActions.getMasterKey(dataState.isOwner, dataActions.setLoading, dataActions.setError),
    onSaveMasterKey: () => decryptionActions.saveMasterKey(dataState.isOwner, dataActions.setLoading, dataActions.setError),
    onClearSavedKey: () => decryptionActions.clearSavedKey(dataState.isOwner, dataActions.setLoading, dataActions.setError),
    onToggleIndividualName: (pirateId: number, e?: React.MouseEvent) =>
      decryptionActions.toggleIndividualName(pirateId, dataState.isOwner, dataActions.setLoading, dataActions.setError, e),

    // Modal Actions
    onTabChange: modalActions.handleTabChange,
    onOpenAddPirateModal: () => modalActions.openAddPirateModal(dataState.isOwner),
    onCloseAddPirateModal: modalActions.closeAddPirateModal,
    onOpenEditPirateModal: (pirate: BramblerMaintenanceItem) => modalActions.openEditPirateModal(pirate, dataState.isOwner),
    onCloseEditPirateModal: modalActions.closeEditPirateModal,
    onOpenAddItemModal: () => modalActions.openAddItemModal(dataState.isOwner),
    onCloseAddItemModal: modalActions.closeAddItemModal,
    onOpenDeletePirateModal: (pirateId: number, pirateName: string) =>
      modalActions.openDeletePirateModal(pirateId, pirateName, dataState.isOwner),
    onOpenDeleteItemModal: (itemId: number, itemName: string) =>
      modalActions.openDeleteItemModal(itemId, itemName, dataState.isOwner),
    onCloseDeleteModal: modalActions.closeDeleteModal,
    onConfirmDelete: () => actionsHandlers.handleConfirmDelete(
      modalState.deleteTarget,
      dataActions.setLoading,
      dataActions.setError,
      handleDeleteSuccess
    ),

    // Utility Actions
    onGenerateNewNames: () => actionsHandlers.handleGenerateNewNames(dataState.isOwner),
    onExportNames: () => actionsHandlers.handleExportNames(
      dataState.isOwner,
      dataState.pirateNames,
      dataState.encryptedItems,
      decryptionState.showRealNames,
      decryptionState.decryptedMappings,
      decryptionState.decryptedItemMappings
    ),
    onImportNames: actionsHandlers.handleImportNames,
  };

  return <>{children(containerProps)}</>;
};
