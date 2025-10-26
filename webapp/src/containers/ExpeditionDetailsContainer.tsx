import React, { useState, useMemo } from 'react';
import { ExpeditionDetailsPresenter } from '@/components/expedition/ExpeditionDetailsPresenter';
import { useExpeditionDetails } from '@/hooks/useExpeditionDetails';
import { useExpeditionPirates } from '@/hooks/useExpeditionPirates';
import { useItemConsumption } from '@/hooks/useItemConsumption';
import { useAddPirateModal } from '@/hooks/useAddPirateModal';
import { useConsumeItemModal } from '@/hooks/useConsumeItemModal';
import { useAddItemModal } from '@/hooks/useAddItemModal';
import { hapticFeedback, getUserId } from '@/utils/telegram';
import { expeditionItemsService } from '@/services/api/expeditionItemsService';

interface ExpeditionDetailsContainerProps {
  expeditionId: number;
  onBack?: () => void;
}

export const ExpeditionDetailsContainer: React.FC<ExpeditionDetailsContainerProps> = ({
  expeditionId,
  onBack,
}) => {
  // State
  const [activeTab, setActiveTab] = useState('overview');

  // Data hooks
  const { expedition, loading, refreshing, error, refresh } = useExpeditionDetails(expeditionId);
  const { pirateNames, availableBuyers, addPirate } = useExpeditionPirates(expeditionId);
  const { consuming, consumeItem } = useItemConsumption(expeditionId);

  // Modal hooks
  const addPirateModal = useAddPirateModal();
  const consumeItemModal = useConsumeItemModal();
  const addItemModal = useAddItemModal();

  // Calculated values
  const totalPirates = useMemo(() => {
    if (!expedition) return 0;
    return new Set(expedition.consumptions.map(c => c.consumer_name)).size;
  }, [expedition]);

  // Check if current user is the expedition owner
  const currentUserId = getUserId();
  const isOwner = useMemo(() => {
    if (!expedition || !currentUserId) return false;
    return expedition.owner_chat_id === currentUserId;
  }, [expedition, currentUserId]);

  // Basic handlers
  const handleBack = () => {
    hapticFeedback('light');
    onBack?.();
  };

  const handleEdit = () => {
    hapticFeedback('medium');
    console.log('Edit expedition');
  };

  const handleRefresh = () => {
    hapticFeedback('light');
    refresh();
  };

  const handleTabChange = (tabId: string) => {
    hapticFeedback('light');
    setActiveTab(tabId);
  };

  // Add Pirate Modal handlers
  const handleOpenAddPirateModal = () => {
    // availableBuyers is already computed via useMemo and auto-updates
    // No need to call loadAvailableBuyers - it's called on mount
    addPirateModal.open(availableBuyers);
  };

  const handleAddPirate = () => {
    addPirateModal.handleAdd(addPirate, async () => {
      refresh();
    });
  };

  // Consume Item Modal handlers
  const handleConsumeClick = (item: any) => {
    consumeItemModal.open(item);
  };

  const handleConsumeConfirm = async (pirateName: string, quantity: number, price: number) => {
    await consumeItemModal.handleConsume(
      async (pirateName, quantity, price) => {
        if (!consumeItemModal.selectedItem) {
          throw new Error('No item selected');
        }
        await consumeItem(
          {
            product_id: consumeItemModal.selectedItem.product_id,
            pirate_name: pirateName,
            quantity,
            price,
          },
          refresh
        );
      },
      pirateName,
      quantity,
      price
    );
  };

  // Add Item Modal handlers
  const handleAddItem = () => {
    addItemModal.handleAdd(
      expeditionId,
      async (expId, items) => {
        await expeditionItemsService.addItems(expId, items);
      },
      async () => {
        refresh();
      }
    );
  };

  const handlePaymentSuccess = async () => {
    console.log('[ExpeditionDetailsContainer] handlePaymentSuccess called');
    hapticFeedback('success');
    console.log('[ExpeditionDetailsContainer] Calling refresh()');
    await refresh();
    console.log('[ExpeditionDetailsContainer] Refresh completed');
  };

  return (
    <ExpeditionDetailsPresenter
      // Data
      expedition={expedition}
      pirateNames={pirateNames}
      availableBuyers={addPirateModal.availableBuyers}
      totalPirates={totalPirates}
      availableProducts={addItemModal.availableProducts}
      isOwner={isOwner}
      currentUserId={currentUserId || 0}

      // State
      loading={loading}
      refreshing={refreshing}
      error={error}
      activeTab={activeTab}

      // Add Pirate Modal
      showAddPirateModal={addPirateModal.isOpen}
      selectedPirateName={addPirateModal.selectedName}
      addingPirate={consuming}

      // Consume Item Modal
      showConsumeModal={consumeItemModal.isOpen}
      selectedItemForConsume={consumeItemModal.selectedItem}

      // Add Item Modal
      showAddItemModal={addItemModal.isOpen}
      selectedProductId={addItemModal.selectedProductId}
      itemQuantity={addItemModal.itemQuantity}
      itemQuality={addItemModal.itemQuality}
      addingItem={addItemModal.addingItem}

      // Basic handlers
      onBack={handleBack}
      onEdit={handleEdit}
      onRefresh={handleRefresh}
      onTabChange={handleTabChange}

      // Add Pirate handlers
      onOpenAddPirateModal={handleOpenAddPirateModal}
      onCloseAddPirateModal={addPirateModal.close}
      onAddPirate={handleAddPirate}
      onSelectedPirateNameChange={addPirateModal.setSelectedName}

      // Consume Item handlers
      onConsumeClick={handleConsumeClick}
      onCloseConsumeModal={consumeItemModal.close}
      onConsumeConfirm={handleConsumeConfirm}
      onPaymentSuccess={handlePaymentSuccess}

      // Add Item handlers
      onOpenAddItemModal={addItemModal.open}
      onCloseAddItemModal={addItemModal.close}
      onAddItem={handleAddItem}
      onSelectedProductIdChange={addItemModal.setSelectedProductId}
      onItemQuantityChange={addItemModal.setItemQuantity}
      onItemQualityChange={addItemModal.setItemQuality}
    />
  );
};
