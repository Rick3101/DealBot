import React, { useState, useEffect } from 'react';
import styled, { css } from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { CaptainLayout } from '@/layouts/CaptainLayout';
import { PirateButton } from '@/components/ui/PirateButton';
import { PirateCard } from '@/components/ui/PirateCard';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { hapticFeedback } from '@/utils/telegram';
import type { BramblerMaintenanceItem, EncryptedItem } from '@/services/api/bramblerService';
import { Eye, EyeOff, Key, Users, Shuffle, Download, Upload, AlertTriangle, Plus, Edit2, Trash2, Save, Trash } from 'lucide-react';
import { TabNavigation } from '@/components/brambler/TabNavigation';
import { AddItemModal } from '@/components/brambler/AddItemModal';
import { AddPirateModal } from '@/components/brambler/AddPirateModal';
import { EditPirateModal } from '@/components/brambler/EditPirateModal';
import { ItemsTable } from '@/components/brambler/ItemsTable';
import { DeleteConfirmModal } from '@/components/brambler/DeleteConfirmModal';
import { masterKeyStorage } from '@/services/masterKeyStorage';

type TabKey = 'pirates' | 'items';

interface BramblerState {
  // Pirates
  pirateNames: BramblerMaintenanceItem[];
  decryptedMappings: Record<string, string>; // pirate_name -> original_name
  individualToggles: Record<number, boolean>; // pirate_id -> show_real_name

  // Items
  encryptedItems: EncryptedItem[];
  decryptedItemMappings: Record<string, string>; // encrypted_item_name -> original_item_name

  // UI State
  activeTab: TabKey;
  showRealNames: boolean;
  decryptionKey: string;
  isOwner: boolean;
  loading: boolean;
  error: string | null;

  // Modals
  showAddItemModal: boolean;
  showAddPirateModal: boolean;
  showEditPirateModal: boolean;
  editingPirate: BramblerMaintenanceItem | null;
  showDeleteModal: boolean;
  deleteTarget: { type: 'pirate' | 'item'; id: number; name: string } | null;
}

const BramblerContainer = styled.div`
  max-width: 900px;
  margin: 0 auto;
`;

const HeaderSection = styled.div`
  text-align: center;
  margin-bottom: ${spacing['2xl']};
`;

const BramblerTitle = styled.h1`
  font-family: ${pirateTypography.headings};
  font-size: 2.5rem;
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.md};
  display: flex;
  align-items: center;
  justify-content: center;
  gap: ${spacing.md};

  @media (min-width: 640px) {
    font-size: 2rem;
  }
`;

const BramblerDescription = styled.p`
  color: ${pirateColors.muted};
  font-size: ${pirateTypography.sizes.lg};
  line-height: 1.6;
  max-width: 600px;
  margin: 0 auto ${spacing.xl};
`;

const FeaturesList = styled.ul`
  text-align: left;
  color: ${pirateColors.muted};
  margin: 0 auto;
  max-width: 500px;
  list-style: none;
  padding: 0;

  li {
    margin-bottom: ${spacing.sm};
    display: flex;
    align-items: center;
    gap: ${spacing.sm};

    &::before {
      content: '⚔️';
      font-size: 1rem;
    }
  }
`;

const ControlsSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.lg};
  margin-bottom: ${spacing['2xl']};

  @media (min-width: 640px) {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
`;

const ViewToggle = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.md};
`;

const KeySection = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.md};
  flex-wrap: wrap;
`;

const KeyInput = styled.input`
  padding: ${spacing.sm} ${spacing.md};
  border: 2px solid ${pirateColors.lightGold};
  border-radius: 8px;
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.sm};
  background: ${pirateColors.white};
  color: ${pirateColors.primary};
  transition: all 0.3s ease;
  min-width: 200px;

  &:focus {
    outline: none;
    border-color: ${pirateColors.secondary};
    box-shadow: 0 0 0 3px rgba(218, 165, 32, 0.1);
  }

  &::placeholder {
    color: ${pirateColors.muted};
  }

  @media (min-width: 640px) {
    min-width: 250px;
  }
`;

const NamesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: ${spacing.lg};
  margin-bottom: ${spacing['2xl']};

  @media (min-width: 640px) {
    grid-template-columns: 1fr;
    gap: ${spacing.md};
  }

  @media (min-width: 768px) {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
`;

const NameCard = styled(PirateCard)<{ $showingReal: boolean }>`
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;

  ${props => props.$showingReal && css`
    border-color: ${pirateColors.warning};
    box-shadow: 0 0 20px rgba(255, 140, 0, 0.2);
  `}

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(139, 69, 19, 0.15);
  }
`;

const NameCardHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing.md};
`;

const PirateAvatar = styled.div`
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(145deg, ${pirateColors.secondary}, ${pirateColors.primary});
  color: ${pirateColors.white};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: ${pirateTypography.weights.bold};
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.2);
`;

const NameToggleButton = styled.button.attrs({ type: 'button' })`
  background: ${pirateColors.lightGold};
  border: 2px solid ${pirateColors.primary};
  border-radius: 8px;
  color: ${pirateColors.primary};
  padding: ${spacing.xs} ${spacing.sm};
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: ${spacing.xs};

  &:hover {
    background: ${pirateColors.secondary};
    color: ${pirateColors.white};
  }
`;

const NameDisplay = styled.div`
  text-align: center;
`;

const PirateName = styled.div<{ $isReal: boolean }>`
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.lg};
  font-weight: ${pirateTypography.weights.bold};
  color: ${props => props.$isReal ? pirateColors.warning : pirateColors.primary};
  margin-bottom: ${spacing.xs};
  display: flex;
  align-items: center;
  justify-content: center;
  gap: ${spacing.xs};
`;

const NameType = styled.div<{ $isReal: boolean }>`
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.muted};
  margin-bottom: ${spacing.sm};
`;

const NameStats = styled.div`
  display: flex;
  justify-content: space-around;
  padding-top: ${spacing.md};
  border-top: 1px solid ${pirateColors.lightGold};
  font-size: ${pirateTypography.sizes.xs};
  color: ${pirateColors.muted};
`;

const StatItem = styled.div`
  text-align: center;

  .value {
    font-weight: ${pirateTypography.weights.bold};
    color: ${pirateColors.primary};
    display: block;
    margin-bottom: ${spacing.xs};
  }
`;

const CardActions = styled.div`
  display: flex;
  gap: ${spacing.sm};
  margin-top: ${spacing.md};
  padding-top: ${spacing.md};
  border-top: 1px solid ${pirateColors.lightGold};
`;

const ActionButton = styled.button.attrs({ type: 'button' })`
  flex: 1;
  padding: ${spacing.sm} ${spacing.md};
  border: 2px solid ${pirateColors.lightGold};
  border-radius: 8px;
  background: ${pirateColors.white};
  color: ${pirateColors.primary};
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.sm};
  font-weight: ${pirateTypography.weights.medium};
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: ${spacing.xs};

  &:hover {
    background: ${pirateColors.lightGold};
    border-color: ${pirateColors.secondary};
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }

  &.delete {
    border-color: ${pirateColors.danger};
    color: ${pirateColors.danger};

    &:hover {
      background: ${pirateColors.danger};
      color: ${pirateColors.white};
    }
  }
`;

const ActionSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.lg};

  @media (min-width: 640px) {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
`;

const ActionGroup = styled.div`
  display: flex;
  gap: ${spacing.sm};
  flex-wrap: wrap;
`;

const WarningCard = styled(PirateCard)`
  background: linear-gradient(135deg, ${pirateColors.warning}20, ${pirateColors.danger}10);
  border-color: ${pirateColors.warning};
  margin-bottom: ${spacing.lg};
`;

const WarningHeader = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
  margin-bottom: ${spacing.md};
  color: ${pirateColors.warning};
  font-weight: ${pirateTypography.weights.bold};
`;

const WarningText = styled.p`
  color: ${pirateColors.muted};
  line-height: 1.5;
  margin: 0;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: ${spacing['3xl']};
  color: ${pirateColors.muted};
`;

const EmptyIcon = styled.div`
  font-size: 4rem;
  margin-bottom: ${spacing.lg};
  opacity: 0.5;
`;

const EmptyTitle = styled.h3`
  font-family: ${pirateTypography.headings};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.sm};
`;

const EmptyDescription = styled.p`
  font-size: ${pirateTypography.sizes.base};
`;

const LoadingOverlay = styled.div<{ $show: boolean }>`
  display: ${props => props.$show ? 'flex' : 'none'};
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(139, 69, 19, 0.8);
  z-index: 9999;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
`;

const LoadingSpinner = styled.div`
  width: 60px;
  height: 60px;
  border: 4px solid ${pirateColors.lightGold};
  border-top: 4px solid ${pirateColors.secondary};
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

export const BramblerManager: React.FC = () => {
  const [state, setState] = useState<BramblerState>({
    // Pirates
    pirateNames: [],
    decryptedMappings: {},
    individualToggles: {},

    // Items
    encryptedItems: [],
    decryptedItemMappings: {},

    // UI State
    activeTab: 'pirates',
    showRealNames: false,
    decryptionKey: '',
    isOwner: false,
    loading: true,
    error: null,

    // Modals
    showAddItemModal: false,
    showAddPirateModal: false,
    showEditPirateModal: false,
    editingPirate: null,
    showDeleteModal: false,
    deleteTarget: null,
  });

  // Store expeditions for the modals
  const [expeditions, setExpeditions] = useState<Array<{ id: number; name: string }>>([]);

  // Load ALL data (pirates, items, expeditions) AND auto-load saved master key on mount
  useEffect(() => {
    const loadAllData = async () => {
      setState(prev => ({ ...prev, loading: true, error: null }));

      try {
        const { bramblerService } = await import('@/services/api/bramblerService');
        const { expeditionService } = await import('@/services/api/expeditionService');

        // Load pirates, items, and expeditions in parallel
        const [allPirates, allItems, allExpeditions] = await Promise.all([
          bramblerService.getAllNames(),
          bramblerService.getAllEncryptedItems().catch(() => []), // Graceful fallback
          expeditionService.getAll().catch(() => []) // Graceful fallback
        ]);

        // User is owner if they have owner permission (checked by API)
        const isOwner = true; // API already validated permission

        console.log(`[BramblerManager] Loaded ${allPirates.length} pirates and ${allItems.length} items`);

        // Extract unique expeditions from items and pirates, merge with expedition list
        const expeditionMap = new Map<number, { id: number; name: string }>();

        // Add from pirates
        allPirates.forEach((pirate: BramblerMaintenanceItem) => {
          if (!expeditionMap.has(pirate.expedition_id)) {
            expeditionMap.set(pirate.expedition_id, {
              id: pirate.expedition_id,
              name: pirate.expedition_name
            });
          }
        });

        // Add from items
        allItems.forEach((item: EncryptedItem) => {
          if (!expeditionMap.has(item.expedition_id)) {
            expeditionMap.set(item.expedition_id, {
              id: item.expedition_id,
              name: item.expedition_name
            });
          }
        });

        // Add from full expedition list
        allExpeditions.forEach((exp: any) => {
          if (!expeditionMap.has(exp.id)) {
            expeditionMap.set(exp.id, {
              id: exp.id,
              name: exp.name
            });
          }
        });

        setExpeditions(Array.from(expeditionMap.values()));

        // AUTO-LOAD SAVED MASTER KEY
        let savedKey = '';
        let keySource = '';
        try {
          const keyMetadata = await masterKeyStorage.loadMasterKey();
          if (keyMetadata && keyMetadata.key) {
            savedKey = keyMetadata.key;
            keySource = keyMetadata.source === 'telegram_cloud' ? 'Telegram Cloud' : 'Local Storage';
            console.log(`[BramblerManager] Auto-loaded saved master key from ${keySource}`);
          }
        } catch (error) {
          console.warn('[BramblerManager] Failed to auto-load saved key:', error);
        }

        setState(prev => ({
          ...prev,
          pirateNames: allPirates,
          encryptedItems: allItems,
          isOwner,
          decryptionKey: savedKey, // Auto-populate if saved
          loading: false
        }));

        // Show notification if key was auto-loaded
        if (savedKey && keySource) {
          await import('@/utils/telegram').then(({ showAlert }) => {
            showAlert(`Master key auto-loaded from ${keySource}! Click "Show Real Names" to decrypt.`);
          });
        }
      } catch (error) {
        console.error('Failed to load data:', error);
        setState(prev => ({
          ...prev,
          loading: false,
          error: 'Failed to load data. Please try again.'
        }));
      }
    };

    loadAllData();
  }, []); // No dependencies - load once on mount

  const handleToggleView = async () => {
    console.log('[BramblerManager] handleToggleView START', {
      showRealNames: state.showRealNames,
      isOwner: state.isOwner,
      hasDecryptedData: Object.keys(state.decryptedMappings).length > 0
    });

    if (!state.showRealNames && state.isOwner) {
      // If trying to show real names, check if we already have decrypted data
      if (!state.decryptionKey.trim()) {
        console.log('[BramblerManager] No decryption key, showing error');
        setState(prev => ({ ...prev, error: 'Please enter your master key' }));
        return;
      }

      // Check if we already have decrypted mappings - if so, just toggle without API call
      if (Object.keys(state.decryptedMappings).length > 0) {
        console.log('[BramblerManager] Already have decrypted data, toggling instantly');
        hapticFeedback('light');
        setState(prev => ({
          ...prev,
          showRealNames: true,
          error: null
        }));
        return;
      }

      console.log('[BramblerManager] No cached data, calling API to decrypt...');
      // Call BULK decrypt API for ALL expeditions at once
      setState(prev => ({ ...prev, loading: true, error: null }));

      try {
        const { bramblerService } = await import('@/services/api/bramblerService');

        console.log('[BramblerManager] Decrypting ALL data using bulk decrypt API');

        // Decrypt ALL pirates and items across ALL expeditions in one API call
        const { pirate_mappings, item_mappings } = await bramblerService.decryptAll(state.decryptionKey);

        const totalDecryptedPirates = Object.keys(pirate_mappings).length;
        const totalDecryptedItems = Object.keys(item_mappings).length;

        console.log(`[BramblerManager] Total decrypted: ${totalDecryptedPirates} pirates, ${totalDecryptedItems} items`);

        setState(prev => ({
          ...prev,
          showRealNames: true,
          decryptedMappings: pirate_mappings,
          decryptedItemMappings: item_mappings,
          loading: false,
          error: null
        }));

        hapticFeedback('medium');
        console.log(`[BramblerManager] Successfully decrypted and cached ${totalDecryptedPirates} pirates and ${totalDecryptedItems} items`);
      } catch (error: any) {
        console.error('[BramblerManager] Decryption failed:', error);

        setState(prev => ({
          ...prev,
          loading: false,
          error: error?.message || 'Failed to decrypt names. Please check your master key and try again.'
        }));
      }
    } else {
      // Just toggle back to pirate names (no API call needed)
      console.log('[BramblerManager] Hiding real names (instant toggle)');
      hapticFeedback('light');
      setState(prev => ({
        ...prev,
        showRealNames: false,
        error: null
      }));
    }
  };

  const handleKeyChange = (key: string) => {
    setState(prev => ({ ...prev, decryptionKey: key, error: null }));
  };

  const handleGetMasterKey = async () => {
    if (!state.isOwner) return;

    hapticFeedback('light');
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const { bramblerService } = await import('@/services/api/bramblerService');

      console.log('[BramblerManager] Fetching user master key from API');

      // Get the user's master key (works for ALL expeditions)
      const masterKey = await bramblerService.getUserMasterKey();

      console.log('[BramblerManager] Master key retrieved, length:', masterKey.length);

      setState(prev => ({
        ...prev,
        decryptionKey: masterKey,
        loading: false,
        error: null
      }));

      // Show success message
      await import('@/utils/telegram').then(({ showAlert }) => {
        showAlert('Master key loaded! This key works for ALL your expeditions.');
      });
    } catch (error: any) {
      console.error('[BramblerManager] Failed to get master key:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to retrieve master key. Make sure you are an owner.'
      }));
    }
  };

  const handleSaveMasterKey = async () => {
    if (!state.isOwner || !state.decryptionKey.trim()) {
      setState(prev => ({ ...prev, error: 'Please enter a master key first' }));
      return;
    }

    hapticFeedback('medium');
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const result = await masterKeyStorage.saveMasterKey(state.decryptionKey);

      if (result.success) {
        setState(prev => ({ ...prev, loading: false, error: null }));

        const storageType = result.source === 'telegram_cloud' ? 'Telegram Cloud Storage' : 'Local Storage';
        hapticFeedback('success');

        await import('@/utils/telegram').then(({ showAlert }) => {
          showAlert(`Master key saved to ${storageType}! It will auto-load next time you visit.`);
        });
      } else {
        throw new Error(result.error || 'Failed to save key');
      }
    } catch (error: any) {
      console.error('[BramblerManager] Failed to save master key:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: error?.message || 'Failed to save master key. Please try again.'
      }));
      hapticFeedback('error');
    }
  };

  const handleClearSavedKey = async () => {
    if (!state.isOwner) return;

    // Confirm before clearing
    const confirmed = await import('@/utils/telegram').then(({ showConfirm }) =>
      showConfirm('Are you sure you want to remove your saved master key? You can always save it again later.')
    );

    if (!confirmed) return;

    hapticFeedback('medium');
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const result = await masterKeyStorage.clearMasterKey();

      if (result.success) {
        setState(prev => ({
          ...prev,
          decryptionKey: '', // Clear from UI too
          showRealNames: false, // Hide real names
          decryptedMappings: {},
          decryptedItemMappings: {},
          individualToggles: {},
          loading: false,
          error: null
        }));

        hapticFeedback('success');

        await import('@/utils/telegram').then(({ showAlert }) => {
          showAlert(`Master key cleared from ${result.clearedFrom.join(' and ')}!`);
        });
      } else {
        throw new Error('Failed to clear saved key');
      }
    } catch (error: any) {
      console.error('[BramblerManager] Failed to clear saved key:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: error?.message || 'Failed to clear saved key. Please try again.'
      }));
      hapticFeedback('error');
    }
  };

  const handleGenerateNewNames = async () => {
    if (!state.isOwner) return;

    hapticFeedback('medium');

    // Show alert that this functionality regenerates names across all expeditions
    await import('@/utils/telegram').then(({ showAlert }) => {
      showAlert('Regenerate functionality coming soon! This will regenerate names for all expeditions.');
    });

    // TODO: Implement bulk regeneration for all expeditions
    // For now, this feature is disabled since we're managing ALL expeditions
  };

  const handleExportNames = () => {
    if (!state.isOwner) return;

    hapticFeedback('light');

    const pirateExpIds = new Set(state.pirateNames.map(p => p.expedition_id));
    const itemExpIds = new Set(state.encryptedItems.map(i => i.expedition_id));
    const allExpeditionIds = [...new Set([...pirateExpIds, ...itemExpIds])];

    const exportData = {
      exported_at: new Date().toISOString(),
      total_pirates: state.pirateNames.length,
      total_items: state.encryptedItems.length,
      expeditions: allExpeditionIds,
      pirates: state.pirateNames.map(name => ({
        expedition_id: name.expedition_id,
        expedition_name: name.expedition_name,
        pirate_name: name.pirate_name,
        original_name: state.showRealNames && state.decryptedMappings[name.pirate_name]
          ? state.decryptedMappings[name.pirate_name]
          : '[ENCRYPTED]',
        created_at: name.created_at
      })),
      items: state.encryptedItems.map(item => ({
        expedition_id: item.expedition_id,
        expedition_name: item.expedition_name,
        encrypted_item_name: item.encrypted_item_name,
        original_item_name: state.showRealNames && state.decryptedItemMappings[item.encrypted_item_name]
          ? state.decryptedItemMappings[item.encrypted_item_name]
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
  };

  const handleImportNames = () => {
    hapticFeedback('light');
    // In a real app, this would open a file picker
    console.log('Import names functionality');
  };

  // NEW: Tab change handler
  const handleTabChange = (tab: TabKey) => {
    hapticFeedback('light');
    setState(prev => ({ ...prev, activeTab: tab }));
  };

  // NEW: Add pirate modal handlers
  const handleAddPirate = () => {
    if (!state.isOwner) return;
    hapticFeedback('medium');
    setState(prev => ({ ...prev, showAddPirateModal: true }));
  };

  const handleAddPirateSuccess = (pirate: BramblerMaintenanceItem) => {
    setState(prev => ({
      ...prev,
      pirateNames: [...prev.pirateNames, pirate]
    }));
  };

  // NEW: Edit pirate modal handlers
  const handleEditPirate = (pirate: BramblerMaintenanceItem) => {
    if (!state.isOwner) return;
    hapticFeedback('medium');
    setState(prev => ({
      ...prev,
      showEditPirateModal: true,
      editingPirate: pirate
    }));
  };

  const handleEditPirateSuccess = (updatedPirate: BramblerMaintenanceItem) => {
    setState(prev => ({
      ...prev,
      pirateNames: prev.pirateNames.map(p =>
        p.id === updatedPirate.id ? updatedPirate : p
      )
    }));
  };

  // NEW: Add item modal handlers
  const handleAddItem = () => {
    if (!state.isOwner) return;
    hapticFeedback('medium');
    setState(prev => ({ ...prev, showAddItemModal: true }));
  };

  const handleAddItemSuccess = (item: EncryptedItem) => {
    setState(prev => ({
      ...prev,
      encryptedItems: [...prev.encryptedItems, item]
    }));
  };

  // NEW: Delete handlers
  const handleDeleteItem = (itemId: number, itemName: string) => {
    if (!state.isOwner) return;
    hapticFeedback('medium');
    setState(prev => ({
      ...prev,
      showDeleteModal: true,
      deleteTarget: { type: 'item', id: itemId, name: itemName }
    }));
  };

  // NEW: Delete pirate handler
  const handleDeletePirate = (pirateId: number, pirateName: string) => {
    if (!state.isOwner) return;
    hapticFeedback('medium');
    setState(prev => ({
      ...prev,
      showDeleteModal: true,
      deleteTarget: { type: 'pirate', id: pirateId, name: pirateName }
    }));
  };

  const handleToggleIndividualName = async (pirateId: number, e?: React.MouseEvent) => {
    // Prevent event propagation
    e?.preventDefault();
    e?.stopPropagation();

    console.log('[BramblerManager] Toggle individual name for pirate ID:', pirateId);
    console.log('[BramblerManager] Current state:', {
      isOwner: state.isOwner,
      decryptedMappingsCount: Object.keys(state.decryptedMappings).length,
      individualToggles: state.individualToggles,
      hasDecryptionKey: !!state.decryptionKey
    });

    if (!state.isOwner) {
      console.warn('[BramblerManager] Cannot toggle - not owner');
      return;
    }

    // If no decrypted mappings yet, we need to decrypt first
    if (Object.keys(state.decryptedMappings).length === 0) {
      console.log('[BramblerManager] No decrypted mappings - need to decrypt first');

      if (!state.decryptionKey.trim()) {
        setState(prev => ({ ...prev, error: 'Please enter your master key first to view individual names' }));
        return;
      }

      // Decrypt all names first
      setState(prev => ({ ...prev, loading: true, error: null }));

      try {
        const { bramblerService } = await import('@/services/api/bramblerService');

        console.log('[BramblerManager] Decrypting ALL data for individual toggle');

        const { pirate_mappings, item_mappings } = await bramblerService.decryptAll(state.decryptionKey);

        console.log(`[BramblerManager] Decrypted ${Object.keys(pirate_mappings).length} pirates, ${Object.keys(item_mappings).length} items`);

        setState(prev => ({
          ...prev,
          decryptedMappings: pirate_mappings,
          decryptedItemMappings: item_mappings,
          individualToggles: {
            ...prev.individualToggles,
            [pirateId]: true // Show this specific pirate
          },
          loading: false,
          error: null
        }));

        hapticFeedback('medium');
      } catch (error: any) {
        console.error('[BramblerManager] Decryption failed:', error);
        setState(prev => ({
          ...prev,
          loading: false,
          error: error?.message || 'Failed to decrypt. Please check your master key.'
        }));
      }
    } else {
      // Already decrypted, just toggle the individual view
      hapticFeedback('light');
      setState(prev => ({
        ...prev,
        individualToggles: {
          ...prev.individualToggles,
          [pirateId]: !prev.individualToggles[pirateId]
        }
      }));

      console.log('[BramblerManager] Toggle completed for pirate ID:', pirateId);
    }
  };

  const handleConfirmDelete = async () => {
    if (!state.deleteTarget) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const { bramblerService } = await import('@/services/api/bramblerService');

      if (state.deleteTarget.type === 'pirate') {
        const success = await bramblerService.deletePirate(state.deleteTarget.id);
        if (success) {
          setState(prev => ({
            ...prev,
            pirateNames: prev.pirateNames.filter(p => p.id !== state.deleteTarget!.id),
            showDeleteModal: false,
            deleteTarget: null,
            loading: false
          }));

          hapticFeedback('success');
          await import('@/utils/telegram').then(({ showAlert }) => {
            showAlert('Pirate deleted successfully!');
          });
        } else {
          throw new Error('Failed to delete pirate');
        }
      } else {
        const success = await bramblerService.deleteEncryptedItem(state.deleteTarget.id);
        if (success) {
          setState(prev => ({
            ...prev,
            encryptedItems: prev.encryptedItems.filter(i => i.id !== state.deleteTarget!.id),
            showDeleteModal: false,
            deleteTarget: null,
            loading: false
          }));

          hapticFeedback('success');
          await import('@/utils/telegram').then(({ showAlert }) => {
            showAlert('Item deleted successfully!');
          });
        } else {
          throw new Error('Failed to delete item');
        }
      }
    } catch (error: any) {
      console.error('Delete failed:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: error?.message || 'Failed to delete. Please try again.'
      }));
      hapticFeedback('error');
    }
  };

  const getAvatarInitials = (name: string): string => {
    return name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  // Remove early return for loading state - handle it inline instead
  // This prevents React from unmounting/remounting the entire component tree

  return (
    <>
      {/* Loading Overlay - Shows on top without unmounting component */}
      <LoadingOverlay $show={state.loading}>
        <LoadingSpinner />
      </LoadingOverlay>

      <CaptainLayout
        title="Brambler - Name Manager"
        subtitle="Secure pirate name anonymization"
      >
        <BramblerContainer>
        <HeaderSection>
          <BramblerTitle>
            🎭 Brambler System
          </BramblerTitle>
          <BramblerDescription>
            Protect your pirates' identities with secure name anonymization.
            Transform real names into legendary pirate aliases while maintaining
            owner-only access to original identities.
          </BramblerDescription>
          <FeaturesList>
            <li>🔐 AES-256 encryption for real names</li>
            <li>🎲 Random pirate name generation</li>
            <li>🔑 Owner-only decryption access</li>
            <li>📊 Expedition-specific anonymization</li>
            <li>💾 Secure export/import functionality</li>
          </FeaturesList>
        </HeaderSection>

        {state.showRealNames && (
          <WarningCard>
            <WarningHeader>
              <AlertTriangle size={20} />
              Security Warning
            </WarningHeader>
            <WarningText>
              Real names are currently visible. Only the expedition owner should be able to see this information.
              Make sure you're in a secure environment and switch back to pirate names when finished.
            </WarningText>
          </WarningCard>
        )}

        <ControlsSection>
          <ViewToggle>
            <span style={{ color: pirateColors.muted, fontSize: pirateTypography.sizes.sm }}>
              Display Mode:
            </span>
            <PirateButton
              variant={state.showRealNames ? "danger" : "primary"}
              onClick={handleToggleView}
              disabled={!state.isOwner}
            >
              {state.showRealNames ? <><EyeOff size={16} /> Hide Real Names</> : <><Eye size={16} /> Show Real Names</>}
            </PirateButton>
          </ViewToggle>

          {state.isOwner && (
            <KeySection>
              <Key size={20} color={pirateColors.muted} />
              <KeyInput
                type="password"
                placeholder="Enter your master key..."
                value={state.decryptionKey}
                onChange={(e) => handleKeyChange(e.target.value)}
                title="Click 'Load My Key' to fetch your master key. This key works for ALL your expeditions!"
              />
              <PirateButton
                variant="outline"
                size="sm"
                onClick={handleGetMasterKey}
                disabled={state.loading}
                title="Fetch your master key from the server"
              >
                Load My Key
              </PirateButton>
              <PirateButton
                variant="secondary"
                size="sm"
                onClick={handleSaveMasterKey}
                disabled={state.loading || !state.decryptionKey.trim()}
                title="Save your master key to Telegram Cloud Storage (or localStorage as fallback). It will auto-load next time!"
              >
                <Save size={14} /> Save Key
              </PirateButton>
              <PirateButton
                variant="outline"
                size="sm"
                onClick={handleClearSavedKey}
                disabled={state.loading}
                title="Clear your saved master key from storage"
              >
                <Trash size={14} /> Clear Saved
              </PirateButton>
            </KeySection>
          )}
        </ControlsSection>

        {state.error && (
          <WarningCard>
            <WarningHeader>
              <AlertTriangle size={20} />
              Error
            </WarningHeader>
            <WarningText>{state.error}</WarningText>
          </WarningCard>
        )}

        {/* Tab Navigation */}
        <TabNavigation
          activeTab={state.activeTab}
          onTabChange={handleTabChange}
          piratesCount={state.pirateNames.length}
          itemsCount={state.encryptedItems.length}
        />

        {/* Add Button */}
        {state.isOwner && (
          <div style={{ marginBottom: spacing.xl }}>
            <PirateButton
              variant="primary"
              onClick={state.activeTab === 'pirates' ? handleAddPirate : handleAddItem}
            >
              <Plus size={16} />
              {state.activeTab === 'pirates' ? 'Add Pirate' : 'Add Item'}
            </PirateButton>
          </div>
        )}

        {/* Conditional rendering based on active tab */}
        {state.activeTab === 'pirates' ? (
          // Pirates View
          state.pirateNames.length === 0 ? (
          <EmptyState>
            <EmptyIcon>🏴‍☠️</EmptyIcon>
            <EmptyTitle>No pirate names yet</EmptyTitle>
            <EmptyDescription>
              Generate pirate names for your expedition to get started with the Brambler system.
            </EmptyDescription>
          </EmptyState>
        ) : (
          <>
            <NamesGrid>
              <AnimatePresence>
                {state.pirateNames.map((pirate) => (
                  <motion.div
                    key={pirate.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.3 }}
                  >
                    <NameCard $showingReal={state.showRealNames || state.individualToggles[pirate.id]}>
                      <NameCardHeader>
                        <PirateAvatar>
                          {getAvatarInitials(
                            (state.showRealNames || state.individualToggles[pirate.id]) && state.decryptedMappings[pirate.pirate_name]
                              ? state.decryptedMappings[pirate.pirate_name]
                              : pirate.pirate_name
                          )}
                        </PirateAvatar>
                        {state.isOwner && (
                          <NameToggleButton
                            onClick={(e) => handleToggleIndividualName(pirate.id, e)}
                            title={
                              state.individualToggles[pirate.id] || state.showRealNames
                                ? "Hide real name"
                                : Object.keys(state.decryptedMappings).length > 0
                                ? "Show real name"
                                : "Show real name (will decrypt all)"
                            }
                          >
                            {state.individualToggles[pirate.id] || state.showRealNames ? <EyeOff size={14} /> : <Eye size={14} />}
                          </NameToggleButton>
                        )}
                      </NameCardHeader>

                      <NameDisplay>
                        <PirateName $isReal={state.showRealNames || state.individualToggles[pirate.id]}>
                          {(state.showRealNames || state.individualToggles[pirate.id]) && state.decryptedMappings[pirate.pirate_name]
                            ? `👤 ${state.decryptedMappings[pirate.pirate_name]}`
                            : `🏴‍☠️ ${pirate.pirate_name}`
                          }
                        </PirateName>

                        <NameType $isReal={state.showRealNames || state.individualToggles[pirate.id]}>
                          {(state.showRealNames || state.individualToggles[pirate.id]) ? 'Real Identity' : 'Pirate Alias'}
                        </NameType>

                        {!(state.showRealNames || state.individualToggles[pirate.id]) && (
                          <div style={{
                            color: pirateColors.muted,
                            fontSize: pirateTypography.sizes.xs,
                            fontStyle: 'italic'
                          }}>
                            Original: [ENCRYPTED]
                          </div>
                        )}
                      </NameDisplay>

                      <NameStats>
                        <StatItem>
                          <span className="value">{pirate.expedition_name}</span>
                          <span>Expedition</span>
                        </StatItem>
                        <StatItem>
                          <span className="value">{formatDate(pirate.created_at || '')}</span>
                          <span>Joined</span>
                        </StatItem>
                      </NameStats>

                      {state.isOwner && (
                        <CardActions>
                          <ActionButton
                            onClick={() => handleEditPirate(pirate)}
                            title="Edit pirate name"
                          >
                            <Edit2 size={14} />
                            Edit
                          </ActionButton>
                          <ActionButton
                            className="delete"
                            onClick={() => handleDeletePirate(pirate.id, pirate.pirate_name)}
                            title="Delete pirate"
                          >
                            <Trash2 size={14} />
                            Delete
                          </ActionButton>
                        </CardActions>
                      )}
                    </NameCard>
                  </motion.div>
                ))}
              </AnimatePresence>
            </NamesGrid>

            {state.isOwner && (
              <ActionSection>
                <ActionGroup>
                  <PirateButton
                    variant="secondary"
                    onClick={handleGenerateNewNames}
                    disabled={state.loading}
                  >
                    <Shuffle size={16} /> Regenerate Names
                  </PirateButton>
                  <PirateButton
                    variant="outline"
                    onClick={handleExportNames}
                  >
                    <Download size={16} /> Export Names
                  </PirateButton>
                  <PirateButton
                    variant="outline"
                    onClick={handleImportNames}
                  >
                    <Upload size={16} /> Import Names
                  </PirateButton>
                </ActionGroup>

                <div style={{
                  color: pirateColors.muted,
                  fontSize: pirateTypography.sizes.sm,
                  textAlign: 'center'
                }}>
                  <Users size={16} style={{ marginRight: spacing.xs }} />
                  {state.pirateNames.length} pirates managed
                </div>
              </ActionSection>
            )}
          </>
        )
        ) : (
          // Items View
          state.encryptedItems.length === 0 ? (
            <EmptyState>
              <EmptyIcon>📦</EmptyIcon>
              <EmptyTitle>No encrypted items yet</EmptyTitle>
              <EmptyDescription>
                Create encrypted items for your expedition to get started with secure item tracking.
              </EmptyDescription>
            </EmptyState>
          ) : (
            <ItemsTable
              items={state.encryptedItems}
              showRealNames={state.showRealNames}
              decryptedMappings={state.decryptedItemMappings}
              onDelete={handleDeleteItem}
              loading={state.loading}
            />
          )
        )}
      </BramblerContainer>

      {/* Modals */}
      <AddPirateModal
        isOpen={state.showAddPirateModal}
        onClose={() => setState(prev => ({ ...prev, showAddPirateModal: false }))}
        onSuccess={handleAddPirateSuccess}
        expeditions={expeditions}
      />

      <EditPirateModal
        isOpen={state.showEditPirateModal}
        onClose={() => setState(prev => ({ ...prev, showEditPirateModal: false, editingPirate: null }))}
        onSuccess={handleEditPirateSuccess}
        pirate={state.editingPirate}
      />

      <AddItemModal
        isOpen={state.showAddItemModal}
        onClose={() => setState(prev => ({ ...prev, showAddItemModal: false }))}
        onSuccess={handleAddItemSuccess}
        expeditions={expeditions}
        masterKey={state.decryptionKey}
      />

      <DeleteConfirmModal
        isOpen={state.showDeleteModal}
        onClose={() => setState(prev => ({ ...prev, showDeleteModal: false, deleteTarget: null }))}
        onConfirm={handleConfirmDelete}
        title={state.deleteTarget?.type === 'pirate' ? 'Delete Pirate' : 'Delete Encrypted Item'}
        message={`Are you sure you want to delete this ${state.deleteTarget?.type}? This action cannot be undone.`}
        itemName={state.deleteTarget?.name || ''}
        loading={state.loading}
      />
    </CaptainLayout>
    </>
  );
};