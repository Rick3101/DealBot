import React from 'react';
import styled, { css } from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { PirateButton } from '@/components/ui/PirateButton';
import { PirateCard } from '@/components/ui/PirateCard';
import { WarningBanner } from '@/components/ui/WarningBanner';
import { LoadingOverlay } from '@/components/ui/LoadingOverlay';
import { Input } from '@/components/ui/FormElements';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { Eye, EyeOff, Key, Users, Shuffle, Download, Upload, Plus, Edit2, Trash2, Save, Trash } from 'lucide-react';
import { TabNavigation } from '@/components/brambler/TabNavigation';
import { AddItemModal } from '@/components/brambler/AddItemModal';
import { AddPirateModal } from '@/components/brambler/AddPirateModal';
import { EditPirateModal } from '@/components/brambler/EditPirateModal';
import { ItemsTable } from '@/components/brambler/ItemsTable';
import { DeleteConfirmModal } from '@/components/brambler/DeleteConfirmModal';
import type { BramblerManagerContainerProps } from '@/containers/BramblerManagerContainer';

// ========================================
// STYLED COMPONENTS
// ========================================

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

const KeyInputStyled = styled(Input)`
  min-width: 200px;

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

// ========================================
// HELPER FUNCTIONS
// ========================================

const getAvatarInitials = (name: string): string => {
  return name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2);
};

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('pt-BR');
};

// ========================================
// PRESENTER COMPONENT
// ========================================

export const BramblerManagerPresenter: React.FC<BramblerManagerContainerProps> = ({
  // Data
  pirateNames,
  decryptedMappings,
  individualToggles,
  encryptedItems,
  decryptedItemMappings,

  // UI State
  activeTab,
  showRealNames,
  decryptionKey,
  isOwner,
  loading,
  error,

  // Modals
  showAddItemModal,
  showAddPirateModal,
  showEditPirateModal,
  editingPirate,
  showDeleteModal,
  deleteTarget,
  expeditions,

  // Event Handlers
  onToggleView,
  onKeyChange,
  onGetMasterKey,
  onSaveMasterKey,
  onClearSavedKey,
  onGenerateNewNames,
  onExportNames,
  onImportNames,
  onTabChange,
  onOpenAddPirateModal,
  onAddPirateSuccess,
  onOpenEditPirateModal,
  onEditPirateSuccess,
  onOpenAddItemModal,
  onAddItemSuccess,
  onOpenDeleteItemModal,
  onOpenDeletePirateModal,
  onToggleIndividualName,
  onConfirmDelete,
  onCloseAddPirateModal,
  onCloseEditPirateModal,
  onCloseAddItemModal,
  onCloseDeleteModal
}) => {
  return (
    <>
      {/* Loading Overlay - Shows on top without unmounting component */}
      <LoadingOverlay show={loading} message="Loading Brambler data..." />

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

        {showRealNames && (
          <WarningBanner
            type="warning"
            title="Security Warning"
            message="Real names are currently visible. Only the expedition owner should be able to see this information. Make sure you're in a secure environment and switch back to pirate names when finished."
          />
        )}

        <ControlsSection>
          <ViewToggle>
            <span style={{ color: pirateColors.muted, fontSize: pirateTypography.sizes.sm }}>
              Display Mode:
            </span>
            <PirateButton
              variant={showRealNames ? "danger" : "primary"}
              onClick={onToggleView}
              disabled={!isOwner}
            >
              {showRealNames ? <><EyeOff size={16} /> Hide Real Names</> : <><Eye size={16} /> Show Real Names</>}
            </PirateButton>
          </ViewToggle>

          {isOwner && (
            <KeySection>
              <Key size={20} color={pirateColors.muted} />
              <KeyInputStyled
                type="password"
                placeholder="Enter your master key..."
                value={decryptionKey}
                onChange={(e) => onKeyChange(e.target.value)}
                title="Click 'Load My Key' to fetch your master key. This key works for ALL your expeditions!"
              />
              <PirateButton
                variant="outline"
                size="sm"
                onClick={onGetMasterKey}
                disabled={loading}
                title="Fetch your master key from the server"
              >
                Load My Key
              </PirateButton>
              <PirateButton
                variant="secondary"
                size="sm"
                onClick={onSaveMasterKey}
                disabled={loading || !decryptionKey.trim()}
                title="Save your master key to Telegram Cloud Storage (or localStorage as fallback). It will auto-load next time!"
              >
                <Save size={14} /> Save Key
              </PirateButton>
              <PirateButton
                variant="outline"
                size="sm"
                onClick={onClearSavedKey}
                disabled={loading}
                title="Clear your saved master key from storage"
              >
                <Trash size={14} /> Clear Saved
              </PirateButton>
            </KeySection>
          )}
        </ControlsSection>

        {error && (
          <WarningBanner
            type="error"
            title="Error"
            message={error}
          />
        )}

        {/* Tab Navigation */}
        <TabNavigation
          activeTab={activeTab}
          onTabChange={onTabChange}
          piratesCount={pirateNames.length}
          itemsCount={encryptedItems.length}
        />

        {/* Add Button */}
        {isOwner && (
          <div style={{ marginBottom: spacing.xl }}>
            <PirateButton
              variant="primary"
              onClick={activeTab === 'pirates' ? onOpenAddPirateModal : onOpenAddItemModal}
            >
              <Plus size={16} />
              {activeTab === 'pirates' ? 'Add Pirate' : 'Add Item'}
            </PirateButton>
          </div>
        )}

        {/* Conditional rendering based on active tab */}
        {activeTab === 'pirates' ? (
          // Pirates View
          pirateNames.length === 0 ? (
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
                {pirateNames.map((pirate) => (
                  <motion.div
                    key={pirate.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.3 }}
                  >
                    <NameCard $showingReal={showRealNames || individualToggles[pirate.id]}>
                      <NameCardHeader>
                        <PirateAvatar>
                          {getAvatarInitials(
                            (showRealNames || individualToggles[pirate.id]) && decryptedMappings[pirate.pirate_name]
                              ? decryptedMappings[pirate.pirate_name]
                              : pirate.pirate_name
                          )}
                        </PirateAvatar>
                        {isOwner && (
                          <NameToggleButton
                            onClick={(e) => onToggleIndividualName(pirate.id, e)}
                            title={
                              individualToggles[pirate.id] || showRealNames
                                ? "Hide real name"
                                : Object.keys(decryptedMappings).length > 0
                                ? "Show real name"
                                : "Show real name (will decrypt all)"
                            }
                          >
                            {individualToggles[pirate.id] || showRealNames ? <EyeOff size={14} /> : <Eye size={14} />}
                          </NameToggleButton>
                        )}
                      </NameCardHeader>

                      <NameDisplay>
                        <PirateName $isReal={showRealNames || individualToggles[pirate.id]}>
                          {(showRealNames || individualToggles[pirate.id]) && decryptedMappings[pirate.pirate_name]
                            ? `👤 ${decryptedMappings[pirate.pirate_name]}`
                            : `🏴‍☠️ ${pirate.pirate_name}`
                          }
                        </PirateName>

                        <NameType $isReal={showRealNames || individualToggles[pirate.id]}>
                          {(showRealNames || individualToggles[pirate.id]) ? 'Real Identity' : 'Pirate Alias'}
                        </NameType>

                        {!(showRealNames || individualToggles[pirate.id]) && (
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

                      {isOwner && (
                        <CardActions>
                          <ActionButton
                            onClick={() => onOpenEditPirateModal(pirate)}
                            title="Edit pirate name"
                          >
                            <Edit2 size={14} />
                            Edit
                          </ActionButton>
                          <ActionButton
                            className="delete"
                            onClick={() => onOpenDeletePirateModal(pirate.id, pirate.pirate_name)}
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

            {isOwner && (
              <ActionSection>
                <ActionGroup>
                  <PirateButton
                    variant="secondary"
                    onClick={onGenerateNewNames}
                    disabled={loading}
                  >
                    <Shuffle size={16} /> Regenerate Names
                  </PirateButton>
                  <PirateButton
                    variant="outline"
                    onClick={onExportNames}
                  >
                    <Download size={16} /> Export Names
                  </PirateButton>
                  <PirateButton
                    variant="outline"
                    onClick={onImportNames}
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
                  {pirateNames.length} pirates managed
                </div>
              </ActionSection>
            )}
          </>
        )
        ) : (
          // Items View
          encryptedItems.length === 0 ? (
            <EmptyState>
              <EmptyIcon>📦</EmptyIcon>
              <EmptyTitle>No encrypted items yet</EmptyTitle>
              <EmptyDescription>
                Create encrypted items for your expedition to get started with secure item tracking.
              </EmptyDescription>
            </EmptyState>
          ) : (
            <ItemsTable
              items={encryptedItems}
              showRealNames={showRealNames}
              decryptedMappings={decryptedItemMappings}
              onDelete={onOpenDeleteItemModal}
              loading={loading}
            />
          )
        )}
    </BramblerContainer>

    {/* Modals */}
    <AddPirateModal
        isOpen={showAddPirateModal}
        onClose={onCloseAddPirateModal}
        onSuccess={onAddPirateSuccess}
        expeditions={expeditions}
      />

      <EditPirateModal
        isOpen={showEditPirateModal}
        onClose={onCloseEditPirateModal}
        onSuccess={onEditPirateSuccess}
        pirate={editingPirate}
      />

      <AddItemModal
        isOpen={showAddItemModal}
        onClose={onCloseAddItemModal}
        onSuccess={onAddItemSuccess}
        expeditions={expeditions}
        masterKey={decryptionKey}
      />

      <DeleteConfirmModal
        isOpen={showDeleteModal}
        onClose={onCloseDeleteModal}
        onConfirm={onConfirmDelete}
        title={deleteTarget?.type === 'pirate' ? 'Delete Pirate' : 'Delete Encrypted Item'}
        message={`Are you sure you want to delete this ${deleteTarget?.type}? This action cannot be undone.`}
        itemName={deleteTarget?.name || ''}
        loading={loading}
      />
    </>
  );
};
