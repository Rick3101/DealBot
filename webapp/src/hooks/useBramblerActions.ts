import type { BramblerMaintenanceItem, EncryptedItem } from '@/services/api/bramblerService';
import { hapticFeedback, showAlert } from '@/utils/telegram';

export interface BramblerActionsHandlers {
  handleGenerateNewNames: (isOwner: boolean) => Promise<void>;
  handleExportNames: (
    isOwner: boolean,
    pirateNames: BramblerMaintenanceItem[],
    encryptedItems: EncryptedItem[],
    showRealNames: boolean,
    decryptedMappings: Record<string, string>,
    decryptedItemMappings: Record<string, string>
  ) => void;
  handleImportNames: () => void;
  handleConfirmDelete: (
    deleteTarget: { type: 'pirate' | 'item'; id: number; name: string } | null,
    setLoading: (loading: boolean) => void,
    setError: (error: string | null) => void,
    onDeleteSuccess: (type: 'pirate' | 'item', id: number) => void
  ) => Promise<void>;
}

/**
 * Custom hook for Brambler CRUD actions
 * Handles generate, export, import, and delete operations
 */
export const useBramblerActions = (): BramblerActionsHandlers => {
  const handlers: BramblerActionsHandlers = {
    handleGenerateNewNames: async (isOwner: boolean) => {
      if (!isOwner) return;

      hapticFeedback('medium');

      // Show alert that this functionality regenerates names across all expeditions
      showAlert('Regenerate functionality coming soon! This will regenerate names for all expeditions.');

      // TODO: Implement bulk regeneration for all expeditions
      // For now, this feature is disabled since we're managing ALL expeditions
    },

    handleExportNames: (
      isOwner: boolean,
      pirateNames: BramblerMaintenanceItem[],
      encryptedItems: EncryptedItem[],
      showRealNames: boolean,
      decryptedMappings: Record<string, string>,
      decryptedItemMappings: Record<string, string>
    ) => {
      if (!isOwner) return;

      hapticFeedback('light');

      const pirateExpIds = new Set(pirateNames.map(p => p.expedition_id));
      const itemExpIds = new Set(encryptedItems.map(i => i.expedition_id));
      const allExpeditionIds = [...new Set([...pirateExpIds, ...itemExpIds])];

      const exportData = {
        exported_at: new Date().toISOString(),
        total_pirates: pirateNames.length,
        total_items: encryptedItems.length,
        expeditions: allExpeditionIds,
        pirates: pirateNames.map(name => ({
          expedition_id: name.expedition_id,
          expedition_name: name.expedition_name,
          pirate_name: name.pirate_name,
          original_name: showRealNames && decryptedMappings[name.pirate_name]
            ? decryptedMappings[name.pirate_name]
            : '[ENCRYPTED]',
          created_at: name.created_at
        })),
        items: encryptedItems.map(item => ({
          expedition_id: item.expedition_id,
          expedition_name: item.expedition_name,
          encrypted_item_name: item.encrypted_item_name,
          original_item_name: showRealNames && decryptedItemMappings[item.encrypted_item_name]
            ? decryptedItemMappings[item.encrypted_item_name]
            : '[ENCRYPTED]',
          item_type: item.item_type,
          item_status: item.item_status,
          quantity_required: item.quantity_required,
          quantity_consumed: item.quantity_consumed,
          anonymized_code: item.anonymized_item_code,
          created_at: item.created_at
        }))
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `brambler-all-data-${Date.now()}.json`;
      link.click();
      URL.revokeObjectURL(url);
    },

    handleImportNames: () => {
      hapticFeedback('light');
      // In a real app, this would open a file picker
      console.log('Import names functionality');
    },

    handleConfirmDelete: async (
      deleteTarget: { type: 'pirate' | 'item'; id: number; name: string } | null,
      setLoading: (loading: boolean) => void,
      setError: (error: string | null) => void,
      onDeleteSuccess: (type: 'pirate' | 'item', id: number) => void
    ) => {
      if (!deleteTarget) return;

      setLoading(true);
      setError(null);

      try {
        const { bramblerService } = await import('@/services/api/bramblerService');

        if (deleteTarget.type === 'pirate') {
          const success = await bramblerService.deletePirate(deleteTarget.id);
          if (success) {
            onDeleteSuccess('pirate', deleteTarget.id);
            hapticFeedback('success');
            showAlert('Pirate deleted successfully!');
          } else {
            throw new Error('Failed to delete pirate');
          }
        } else {
          const success = await bramblerService.deleteEncryptedItem(deleteTarget.id);
          if (success) {
            onDeleteSuccess('item', deleteTarget.id);
            hapticFeedback('success');
            showAlert('Item deleted successfully!');
          } else {
            throw new Error('Failed to delete item');
          }
        }
      } catch (error: any) {
        console.error('[useBramblerActions] Delete failed:', error);
        setError(error?.message || 'Failed to delete. Please try again.');
        hapticFeedback('error');
      } finally {
        setLoading(false);
      }
    }
  };

  return handlers;
};
