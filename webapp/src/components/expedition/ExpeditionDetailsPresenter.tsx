import React from 'react';
import styled, { css } from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Edit3, Users, Package, RefreshCw, Activity, DollarSign } from 'lucide-react';
import { CaptainLayout } from '@/layouts/CaptainLayout';
import { PirateButton } from '@/components/ui/PirateButton';
import { ConsumeItemModal } from '@/components/expedition/ConsumeItemModal';
import { OverviewTab } from './tabs/OverviewTab';
import { ItemsTab } from './tabs/ItemsTab';
import { PiratesTab } from './tabs/PiratesTab';
import { ConsumptionsTab } from './tabs/ConsumptionsTab';
import { AnalyticsTab } from './tabs/AnalyticsTab';
import { pirateColors, spacing, pirateTypography, getStatusColor, getStatusEmoji } from '@/utils/pirateTheme';
import { formatDate } from '@/utils/formatters';
import { ExpeditionDetails, Product, QualityGrade } from '@/types/expedition';

interface ExpeditionDetailsPresenterProps {
  // Data
  expedition: ExpeditionDetails | null;
  pirateNames: any[];
  availableBuyers: { name: string }[];
  totalPirates: number;
  availableProducts: Product[];
  isOwner: boolean;
  currentUserId: number;

  // State
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  activeTab: string;
  showAddPirateModal: boolean;
  selectedPirateName: string;
  showConsumeModal: boolean;
  selectedItemForConsume: any | null;
  addingPirate: boolean;
  showAddItemModal: boolean;
  selectedProductId: number | null;
  itemQuantity: number;
  itemQuality: QualityGrade | '';
  addingItem: boolean;

  // Handlers
  onBack?: () => void;
  onEdit: () => void;
  onRefresh: () => void;
  onTabChange: (tabId: string) => void;
  onOpenAddPirateModal: () => void;
  onCloseAddPirateModal: () => void;
  onAddPirate: () => void;
  onSelectedPirateNameChange: (name: string) => void;
  onConsumeClick: (item: any) => void;
  onCloseConsumeModal: () => void;
  onConsumeConfirm: (pirateName: string, quantity: number, price: number) => Promise<void>;
  onPaymentSuccess?: () => void;
  onOpenAddItemModal: () => void;
  onCloseAddItemModal: () => void;
  onAddItem: () => void;
  onSelectedProductIdChange: (id: number | null) => void;
  onItemQuantityChange: (quantity: number) => void;
  onItemQualityChange: (quality: QualityGrade | '') => void;
}

const DetailsContainer = styled.div`
  max-width: 1000px;
  margin: 0 auto;
`;

const HeaderSection = styled.div`
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: ${spacing.xl};
  gap: ${spacing.lg};

  @media (min-width: 640px) {
    flex-direction: column;
    align-items: stretch;
  }
`;

const HeaderInfo = styled.div`
  flex: 1;
`;

const ExpeditionTitle = styled.h1`
  font-family: ${pirateTypography.headings};
  font-size: 2rem;
  color: ${pirateColors.primary};
  margin: 0 0 ${spacing.sm} 0;
  display: flex;
  align-items: center;
  gap: ${spacing.sm};

  @media (min-width: 640px) {
    font-size: 1.5rem;
  }
`;

const StatusBadge = styled.span<{ $status: string }>`
  background: ${props => getStatusColor(props.$status)};
  color: ${pirateColors.white};
  padding: ${spacing.sm} ${spacing.md};
  border-radius: 20px;
  font-size: ${pirateTypography.sizes.sm};
  font-weight: ${pirateTypography.weights.bold};
  text-transform: uppercase;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
`;

const ExpeditionDescription = styled.p`
  color: ${pirateColors.muted};
  font-size: ${pirateTypography.sizes.base};
  line-height: 1.6;
  margin: ${spacing.md} 0;
`;

const ActionsSection = styled.div`
  display: flex;
  gap: ${spacing.sm};
  align-items: center;
  flex-wrap: wrap;

  @media (min-width: 640px) {
    justify-content: flex-start;
  }
`;

const RefreshIcon = styled(motion.div)<{ $spinning: boolean }>`
  display: inline-flex;
  animation: ${props => props.$spinning ? 'spin 1s linear infinite' : 'none'};

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

const TabsContainer = styled.div`
  margin-bottom: ${spacing.xl};
`;

const TabsList = styled.div`
  display: flex;
  gap: ${spacing.sm};
  margin-bottom: ${spacing.lg};
  overflow-x: auto;
  padding-bottom: ${spacing.sm};
`;

const TabButton = styled.button<{ $active: boolean }>`
  padding: ${spacing.md} ${spacing.lg};
  border: none;
  border-radius: 8px;
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  font-size: ${pirateTypography.sizes.sm};
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: ${spacing.xs};

  ${props => props.$active ? css`
    background: ${pirateColors.secondary};
    color: ${pirateColors.white};
    box-shadow: 0 4px 12px rgba(218, 165, 32, 0.3);
  ` : css`
    background: ${pirateColors.lightGold};
    color: ${pirateColors.primary};

    &:hover {
      background: ${pirateColors.secondary};
      color: ${pirateColors.white};
    }
  `}
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

const ModalOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: ${spacing.lg};
`;

const ModalContent = styled(motion.div)`
  background: ${pirateColors.white};
  border-radius: 16px;
  padding: ${spacing.xl};
  max-width: 500px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
`;

const ModalTitle = styled.h2`
  font-family: ${pirateTypography.headings};
  font-size: 1.5rem;
  color: ${pirateColors.primary};
  margin: 0 0 ${spacing.md} 0;
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
`;

const ModalDescription = styled.p`
  color: ${pirateColors.muted};
  margin-bottom: ${spacing.lg};
  font-size: ${pirateTypography.sizes.sm};
`;

const Select = styled.select`
  width: 100%;
  padding: ${spacing.md};
  border: 2px solid ${pirateColors.lightGold};
  border-radius: 8px;
  font-size: ${pirateTypography.sizes.base};
  font-family: ${pirateTypography.headings};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.lg};
  transition: all 0.3s ease;
  background: ${pirateColors.white};
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: ${pirateColors.secondary};
    box-shadow: 0 0 0 3px rgba(218, 165, 32, 0.1);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const ModalActions = styled.div`
  display: flex;
  gap: ${spacing.md};
  justify-content: flex-end;
`;

const Input = styled.input`
  width: 100%;
  padding: ${spacing.md};
  border: 2px solid ${pirateColors.lightGold};
  border-radius: 8px;
  font-size: ${pirateTypography.sizes.base};
  font-family: ${pirateTypography.headings};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.lg};
  transition: all 0.3s ease;
  background: ${pirateColors.white};

  &:focus {
    outline: none;
    border-color: ${pirateColors.secondary};
    box-shadow: 0 0 0 3px rgba(218, 165, 32, 0.1);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const FormGroup = styled.div`
  margin-bottom: ${spacing.lg};
`;

const Label = styled.label`
  display: block;
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.sm};
  font-size: ${pirateTypography.sizes.sm};
`;

export const ExpeditionDetailsPresenter: React.FC<ExpeditionDetailsPresenterProps> = ({
  expedition,
  pirateNames,
  availableBuyers,
  totalPirates,
  availableProducts,
  isOwner,
  currentUserId,
  loading,
  refreshing,
  error,
  activeTab,
  showAddPirateModal,
  selectedPirateName,
  showConsumeModal,
  selectedItemForConsume,
  addingPirate,
  showAddItemModal,
  selectedProductId,
  itemQuantity,
  itemQuality,
  addingItem,
  onBack,
  onEdit,
  onRefresh,
  onTabChange,
  onOpenAddPirateModal,
  onCloseAddPirateModal,
  onAddPirate,
  onSelectedPirateNameChange,
  onConsumeClick,
  onCloseConsumeModal,
  onConsumeConfirm,
  onPaymentSuccess,
  onOpenAddItemModal,
  onCloseAddItemModal,
  onAddItem,
  onSelectedProductIdChange,
  onItemQuantityChange,
  onItemQualityChange,
}) => {
  const tabs = [
    { id: 'overview', label: 'Overview', icon: <Activity size={16} /> },
    { id: 'items', label: 'Items', icon: <Package size={16} /> },
    { id: 'pirates', label: 'Pirates', icon: <Users size={16} /> },
    { id: 'consumptions', label: 'Consumptions', icon: <Users size={16} /> },
    { id: 'analytics', label: 'Analytics', icon: <DollarSign size={16} /> },
  ];

  // Loading state
  if (loading) {
    return (
      <CaptainLayout>
        <DetailsContainer>
          <EmptyState>
            <EmptyIcon>⛵</EmptyIcon>
            <EmptyTitle>Loading expedition...</EmptyTitle>
          </EmptyState>
        </DetailsContainer>
      </CaptainLayout>
    );
  }

  // Error state
  if (error || !expedition) {
    return (
      <CaptainLayout>
        <DetailsContainer>
          <EmptyState>
            <EmptyIcon>💀</EmptyIcon>
            <EmptyTitle>{error ? 'Error Loading Expedition' : 'Expedition not found'}</EmptyTitle>
            <EmptyDescription>
              {error || "The expedition you're looking for doesn't exist or has been removed."}
            </EmptyDescription>
            {onBack && (
              <div style={{ marginTop: spacing.lg }}>
                <PirateButton variant="primary" onClick={onBack}>
                  <ArrowLeft size={16} /> Back to Dashboard
                </PirateButton>
              </div>
            )}
          </EmptyState>
        </DetailsContainer>
      </CaptainLayout>
    );
  }

  // Render tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <OverviewTab
            totalItems={expedition.progress.total_items}
            totalPirates={totalPirates}
            totalValue={expedition.progress.total_value}
            deadline={expedition.deadline}
            progress={expedition.progress}
          />
        );

      case 'items':
        return (
          <ItemsTab
            items={expedition.items}
            onConsumeClick={onConsumeClick}
            onAddItem={onOpenAddItemModal}
          />
        );

      case 'pirates':
        return (
          <PiratesTab
            pirateNames={pirateNames}
            onAddPirate={onOpenAddPirateModal}
            expeditionId={expedition.id}
            isOwner={isOwner}
            ownerChatId={currentUserId}
          />
        );

      case 'consumptions':
        return (
          <ConsumptionsTab
            consumptions={expedition.consumptions}
            onPaymentSuccess={onPaymentSuccess}
            isOwner={isOwner}
          />
        );

      case 'analytics':
        return (
          <AnalyticsTab
            progress={expedition.progress}
            totalPirates={totalPirates}
            totalConsumptions={expedition.consumptions.length}
          />
        );

      default:
        return null;
    }
  };

  return (
    <CaptainLayout
      title={expedition.name}
      subtitle="Expedition Management"
    >
      <DetailsContainer>
        <HeaderSection>
          <HeaderInfo>
            <div style={{ marginBottom: spacing.md }}>
              <PirateButton variant="outline" size="sm" onClick={onBack}>
                <ArrowLeft size={16} /> Back to Dashboard
              </PirateButton>
            </div>

            <ExpeditionTitle>
              {getStatusEmoji(expedition.status)} {expedition.name}
            </ExpeditionTitle>

            {expedition.description && (
              <ExpeditionDescription>{expedition.description}</ExpeditionDescription>
            )}

            <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md, marginTop: spacing.md }}>
              <StatusBadge $status={expedition.status}>
                {expedition.status}
              </StatusBadge>
              {expedition.created_at && (
                <span style={{ color: pirateColors.muted, fontSize: pirateTypography.sizes.sm }}>
                  Created {formatDate(expedition.created_at).split(' ')[0]}
                </span>
              )}
            </div>
          </HeaderInfo>

          <ActionsSection>
            <PirateButton variant="outline" size="sm" onClick={onRefresh} disabled={refreshing}>
              <RefreshIcon $spinning={refreshing}>
                <RefreshCw size={16} />
              </RefreshIcon>
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </PirateButton>
            {expedition.status === 'active' && (
              <PirateButton variant="primary" onClick={onEdit}>
                <Edit3 size={16} /> Edit
              </PirateButton>
            )}
          </ActionsSection>
        </HeaderSection>

        <TabsContainer>
          <TabsList>
            {tabs.map(tab => (
              <TabButton
                key={tab.id}
                $active={activeTab === tab.id}
                onClick={() => onTabChange(tab.id)}
              >
                {tab.icon}
                {tab.label}
              </TabButton>
            ))}
          </TabsList>

          <AnimatePresence mode="wait">
            {renderTabContent()}
          </AnimatePresence>
        </TabsContainer>
      </DetailsContainer>

      {/* Add Pirate Modal */}
      <AnimatePresence>
        {showAddPirateModal && (
          <ModalOverlay
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onCloseAddPirateModal}
          >
            <ModalContent
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <ModalTitle>
                <Users size={24} /> Add Pirate to Crew
              </ModalTitle>
              <ModalDescription>
                Select a buyer to add to this expedition. A unique pirate alias will be generated for anonymity.
              </ModalDescription>
              <Select
                value={selectedPirateName}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => onSelectedPirateNameChange(e.target.value)}
                disabled={availableBuyers.length === 0}
                autoFocus
              >
                <option value="">
                  {availableBuyers.length === 0 ? 'No available buyers (all buyers are already pirates)' : 'Select a buyer...'}
                </option>
                {availableBuyers.map((buyer) => (
                  <option key={buyer.name} value={buyer.name}>
                    {buyer.name}
                  </option>
                ))}
              </Select>
              <ModalActions>
                <PirateButton variant="outline" onClick={onCloseAddPirateModal} disabled={addingPirate}>
                  Cancel
                </PirateButton>
                <PirateButton
                  variant="primary"
                  onClick={onAddPirate}
                  disabled={!selectedPirateName.trim() || addingPirate}
                >
                  {addingPirate ? 'Adding...' : 'Add Pirate'}
                </PirateButton>
              </ModalActions>
            </ModalContent>
          </ModalOverlay>
        )}
      </AnimatePresence>

      {/* Add Item Modal */}
      <AnimatePresence>
        {showAddItemModal && (
          <ModalOverlay
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onCloseAddItemModal}
          >
            <ModalContent
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <ModalTitle>
                <Package size={24} /> Add Item to Expedition
              </ModalTitle>
              <ModalDescription>
                Select a product, specify the quantity needed, and optionally set a quality grade for this expedition item.
              </ModalDescription>

              <FormGroup>
                <Label>Product</Label>
                <Select
                  value={selectedProductId || ''}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                    onSelectedProductIdChange(e.target.value ? Number(e.target.value) : null)
                  }
                  disabled={availableProducts.length === 0}
                  autoFocus
                >
                  <option value="">
                    {availableProducts.length === 0 ? 'No available products' : 'Select a product...'}
                  </option>
                  {availableProducts.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.emoji ? `${product.emoji} ` : ''}{product.name} - ${product.price.toFixed(2)}
                    </option>
                  ))}
                </Select>
              </FormGroup>

              <FormGroup>
                <Label>Quantity Needed</Label>
                <Input
                  type="number"
                  min="1"
                  value={itemQuantity}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    onItemQuantityChange(Number(e.target.value))
                  }
                  placeholder="Enter quantity..."
                />
              </FormGroup>

              <FormGroup>
                <Label>Unit Cost</Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={itemQuality}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    onItemQualityChange(e.target.value as QualityGrade | '')
                  }
                  placeholder="Enter unit cost..."
                />
              </FormGroup>

              <ModalActions>
                <PirateButton variant="outline" onClick={onCloseAddItemModal} disabled={addingItem}>
                  Cancel
                </PirateButton>
                <PirateButton
                  variant="primary"
                  onClick={onAddItem}
                  disabled={!selectedProductId || itemQuantity <= 0 || addingItem}
                >
                  {addingItem ? 'Adding...' : 'Add Item'}
                </PirateButton>
              </ModalActions>
            </ModalContent>
          </ModalOverlay>
        )}
      </AnimatePresence>

      {/* Consume Item Modal */}
      <ConsumeItemModal
        isOpen={showConsumeModal}
        onClose={onCloseConsumeModal}
        onConfirm={onConsumeConfirm}
        itemName={selectedItemForConsume?.name || ''}
        itemEmoji={selectedItemForConsume?.emoji}
        availableQuantity={selectedItemForConsume?.available || 0}
        suggestedPrice={selectedItemForConsume?.price}
        pirateNames={pirateNames}
      />
    </CaptainLayout>
  );
};
