import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { CaptainLayout } from '@/layouts/CaptainLayout';
import { PirateButton } from '@/components/ui/PirateButton';
import { WarningBanner } from '@/components/ui/WarningBanner';
import { Modal } from '@/components/ui/Modal';
import { FormGroup, Input, Select, EditInput } from '@/components/ui/FormElements';
import { LoadingOverlay } from '@/components/ui/LoadingOverlay';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { hapticFeedback } from '@/utils/telegram';
import { bramblerService, type BramblerMaintenanceItem } from '@/services/api/bramblerService';
import { expeditionService } from '@/services/api/expeditionService';
import { Eye, EyeOff, Key, Edit2, Save, X, Plus, Users } from 'lucide-react';
import type { Expedition } from '@/types/expedition';

interface MaintenanceState {
  pirates: BramblerMaintenanceItem[];
  showOriginalNames: boolean;
  decryptedMappings: Record<string, string>;
  loading: boolean;
  error: string | null;
  editingId: number | null;
  editValue: string;
  saving: boolean;
  showCreateModal: boolean;
  expeditions: Expedition[];
  createForm: {
    expedition_id: number | null;
    original_name: string;
    pirate_name: string;
  };
  creating: boolean;
}

const MaintenanceContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`;

const HeaderSection = styled.div`
  text-align: center;
  margin-bottom: ${spacing['2xl']};
`;

const MaintenanceTitle = styled.h1`
  font-family: ${pirateTypography.headings};
  font-size: 2.5rem;
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.md};

  @media (max-width: 640px) {
    font-size: 2rem;
  }
`;

const MaintenanceDescription = styled.p`
  color: ${pirateColors.muted};
  font-size: ${pirateTypography.sizes.lg};
  line-height: 1.6;
  max-width: 600px;
  margin: 0 auto;
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

const PiratesTable = styled.div`
  background: ${pirateColors.white};
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(139, 69, 19, 0.1);
`;

const TableRow = styled(motion.div)<{ $isHeader?: boolean }>`
  display: grid;
  grid-template-columns: 2fr 2fr 2fr 1fr;
  gap: ${spacing.md};
  padding: ${spacing.md} ${spacing.lg};
  border-bottom: 1px solid ${pirateColors.lightGold};
  align-items: center;

  ${props => props.$isHeader && `
    background: ${pirateColors.lightGold};
    font-weight: ${pirateTypography.weights.bold};
    color: ${pirateColors.primary};
    position: sticky;
    top: 0;
    z-index: 1;
  `}

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: ${spacing.sm};
    padding: ${spacing.md};
  }
`;

const TableCell = styled.div<{ $warning?: boolean }>`
  color: ${props => props.$warning ? pirateColors.warning : pirateColors.primary};
  font-size: ${pirateTypography.sizes.base};
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  @media (max-width: 768px) {
    white-space: normal;
  }
`;

const PirateNameDisplay = styled.div<{ $showingOriginal?: boolean }>`
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
  color: ${props => props.$showingOriginal ? pirateColors.warning : pirateColors.primary};
  font-weight: ${pirateTypography.weights.bold};
`;

const ActionButtons = styled.div`
  display: flex;
  gap: ${spacing.xs};
  justify-content: flex-end;

  @media (max-width: 768px) {
    justify-content: flex-start;
  }
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

export const BramblerMaintenance: React.FC = () => {
  const [state, setState] = useState<MaintenanceState>({
    pirates: [],
    showOriginalNames: false,
    decryptedMappings: {},
    loading: true,
    error: null,
    editingId: null,
    editValue: '',
    saving: false,
    showCreateModal: false,
    expeditions: [],
    createForm: {
      expedition_id: null,
      original_name: '',
      pirate_name: '',
    },
    creating: false,
  });

  useEffect(() => {
    loadAllPirates();
    loadExpeditions();
  }, []);

  const loadAllPirates = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const pirates = await bramblerService.getAllNames();
      setState(prev => ({
        ...prev,
        pirates,
        loading: false
      }));
    } catch (error) {
      console.error('Failed to load all pirates:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load pirate names. Please try again.'
      }));
    }
  };

  const loadExpeditions = async () => {
    try {
      const expeditions = await expeditionService.getAll();
      setState(prev => ({
        ...prev,
        expeditions: expeditions.filter((e: Expedition) => e.status === 'active')
      }));
    } catch (error) {
      console.error('Failed to load expeditions:', error);
    }
  };

  const handleToggleDisplay = () => {
    hapticFeedback('light');
    // For maintenance page, we just toggle the display
    // Original names come directly from the API if user has permission
    setState(prev => ({
      ...prev,
      showOriginalNames: !prev.showOriginalNames
    }));
  };

  const handleStartEdit = (pirate: BramblerMaintenanceItem) => {
    hapticFeedback('light');
    setState(prev => ({
      ...prev,
      editingId: pirate.id,
      editValue: pirate.pirate_name
    }));
  };

  const handleCancelEdit = () => {
    hapticFeedback('light');
    setState(prev => ({
      ...prev,
      editingId: null,
      editValue: ''
    }));
  };

  const handleSaveEdit = async (pirateId: number) => {
    if (!state.editValue.trim()) {
      setState(prev => ({ ...prev, error: 'Pirate name cannot be empty' }));
      return;
    }

    setState(prev => ({ ...prev, saving: true, error: null }));
    hapticFeedback('medium');

    try {
      await bramblerService.updatePirateName(pirateId, state.editValue.trim());

      // Update local state
      setState(prev => ({
        ...prev,
        pirates: prev.pirates.map(p =>
          p.id === pirateId ? { ...p, pirate_name: state.editValue.trim() } : p
        ),
        editingId: null,
        editValue: '',
        saving: false
      }));

      hapticFeedback('success');
    } catch (error) {
      console.error('Failed to update pirate name:', error);
      setState(prev => ({
        ...prev,
        saving: false,
        error: 'Failed to update pirate name. Please try again.'
      }));
    }
  };

  const getDisplayName = (pirate: BramblerMaintenanceItem): string => {
    if (state.showOriginalNames && pirate.original_name) {
      return pirate.original_name;
    }
    return pirate.pirate_name;
  };

  const handleOpenCreateModal = () => {
    hapticFeedback('light');
    setState(prev => ({
      ...prev,
      showCreateModal: true,
      error: null,
      createForm: {
        expedition_id: null,
        original_name: '',
        pirate_name: '',
      }
    }));
  };

  const handleCloseCreateModal = () => {
    hapticFeedback('light');
    setState(prev => ({
      ...prev,
      showCreateModal: false,
      createForm: {
        expedition_id: null,
        original_name: '',
        pirate_name: '',
      }
    }));
  };

  const handleCreatePirate = async () => {
    if (!state.createForm.expedition_id) {
      setState(prev => ({ ...prev, error: 'Please select an expedition' }));
      return;
    }

    if (!state.createForm.original_name.trim()) {
      setState(prev => ({ ...prev, error: 'Original name is required' }));
      return;
    }

    setState(prev => ({ ...prev, creating: true, error: null }));
    hapticFeedback('medium');

    try {
      const result = await bramblerService.createPirate({
        expedition_id: state.createForm.expedition_id,
        original_name: state.createForm.original_name.trim(),
        pirate_name: state.createForm.pirate_name.trim() || undefined,
      });

      // Add the new pirate to the list
      setState(prev => ({
        ...prev,
        pirates: [...prev.pirates, result.pirate],
        showCreateModal: false,
        creating: false,
        createForm: {
          expedition_id: null,
          original_name: '',
          pirate_name: '',
        }
      }));

      hapticFeedback('success');
    } catch (error: any) {
      console.error('Failed to create pirate:', error);
      setState(prev => ({
        ...prev,
        creating: false,
        error: error.response?.data?.error || 'Failed to create pirate. Please try again.'
      }));
    }
  };

  return (
    <>
      <LoadingOverlay show={state.loading} message="Loading pirate names..." />

    <CaptainLayout
      title="Brambler Maintenance"
      subtitle="Manage all pirate names across expeditions"
    >
      <MaintenanceContainer>
        <HeaderSection>
          <MaintenanceTitle>
            🎭 Brambler Maintenance
          </MaintenanceTitle>
          <MaintenanceDescription>
            Global management interface for all pirate names across all expeditions.
            Edit pirate aliases and manage anonymization settings.
          </MaintenanceDescription>
        </HeaderSection>

        {state.showOriginalNames && (
          <WarningBanner
            type="warning"
            message="Original names are currently visible. Make sure you're in a secure environment."
          />
        )}

        <ControlsSection>
          <ViewToggle>
            <span style={{ color: pirateColors.muted, fontSize: pirateTypography.sizes.sm }}>
              Display Mode:
            </span>
            <PirateButton
              variant={state.showOriginalNames ? "danger" : "primary"}
              onClick={handleToggleDisplay}
            >
              {state.showOriginalNames ? <><EyeOff size={16} /> Hide Original Names</> : <><Eye size={16} /> Show Original Names</>}
            </PirateButton>
          </ViewToggle>

          <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md }}>
            <div style={{ color: pirateColors.muted, fontSize: pirateTypography.sizes.sm }}>
              Total: {state.pirates.length} pirates
            </div>
            <PirateButton
              variant="success"
              onClick={handleOpenCreateModal}
            >
              <Plus size={16} /> Create Pirate
            </PirateButton>
          </div>
        </ControlsSection>

        {state.error && (
          <WarningBanner
            type="error"
            message={state.error}
          />
        )}

        {state.pirates.length === 0 ? (
          <EmptyState>
            <EmptyIcon>🏴‍☠️</EmptyIcon>
            <EmptyTitle>No pirate names found</EmptyTitle>
            <p>No pirate names have been created yet across any expeditions.</p>
          </EmptyState>
        ) : (
          <PiratesTable>
            <TableRow $isHeader>
              <TableCell>Pirate Name</TableCell>
              <TableCell>Expedition</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>

            <AnimatePresence>
              {state.pirates.map((pirate) => (
                <TableRow
                  key={pirate.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                >
                  <TableCell>
                    {state.editingId === pirate.id ? (
                      <EditInput
                        type="text"
                        value={state.editValue}
                        onChange={(e) => setState(prev => ({ ...prev, editValue: e.target.value }))}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(pirate.id);
                          if (e.key === 'Escape') handleCancelEdit();
                        }}
                        autoFocus
                      />
                    ) : (
                      <PirateNameDisplay $showingOriginal={state.showOriginalNames && !!pirate.original_name}>
                        {state.showOriginalNames && pirate.original_name ? '👤' : '🏴‍☠️'}
                        {getDisplayName(pirate)}
                      </PirateNameDisplay>
                    )}
                  </TableCell>

                  <TableCell>
                    {pirate.expedition_name}
                  </TableCell>

                  <TableCell>
                    {!state.showOriginalNames && !pirate.original_name && (
                      <span style={{ fontSize: pirateTypography.sizes.xs, color: pirateColors.muted }}>
                        🔒 Encrypted
                      </span>
                    )}
                    {state.showOriginalNames && pirate.original_name && (
                      <TableCell $warning>
                        <Key size={14} style={{ marginRight: spacing.xs }} />
                        Revealed
                      </TableCell>
                    )}
                  </TableCell>

                  <TableCell>
                    <ActionButtons>
                      {state.editingId === pirate.id ? (
                        <>
                          <PirateButton
                            size="sm"
                            onClick={() => handleSaveEdit(pirate.id)}
                            disabled={state.saving}
                          >
                            <Save size={14} />
                          </PirateButton>
                          <PirateButton
                            size="sm"
                            variant="secondary"
                            onClick={handleCancelEdit}
                            disabled={state.saving}
                          >
                            <X size={14} />
                          </PirateButton>
                        </>
                      ) : (
                        <PirateButton
                          size="sm"
                          variant="outline"
                          onClick={() => handleStartEdit(pirate)}
                        >
                          <Edit2 size={14} /> Edit
                        </PirateButton>
                      )}
                    </ActionButtons>
                  </TableCell>
                </TableRow>
              ))}
            </AnimatePresence>
          </PiratesTable>
        )}

        {/* Create Pirate Modal */}
        <Modal
          isOpen={state.showCreateModal}
          onClose={handleCloseCreateModal}
          title="Create New Pirate"
          titleIcon={<Users size={24} />}
          footer={
            <>
              <PirateButton
                variant="secondary"
                onClick={handleCloseCreateModal}
                disabled={state.creating}
              >
                Cancel
              </PirateButton>
              <PirateButton
                variant="primary"
                onClick={handleCreatePirate}
                disabled={state.creating}
              >
                {state.creating ? 'Creating...' : 'Create Pirate'}
              </PirateButton>
            </>
          }
        >
          <FormGroup
            label="Expedition"
            htmlFor="expedition"
            required
            helpText="Choose which expedition this pirate will join"
          >
            <Select
              id="expedition"
              value={state.createForm.expedition_id || ''}
              onChange={(e) => setState(prev => ({
                ...prev,
                createForm: {
                  ...prev.createForm,
                  expedition_id: e.target.value ? parseInt(e.target.value) : null
                }
              }))}
            >
              <option value="">Select an expedition...</option>
              {state.expeditions.map(exp => (
                <option key={exp.id} value={exp.id}>
                  {exp.name}
                </option>
              ))}
            </Select>
          </FormGroup>

          <FormGroup
            label="Original Name"
            htmlFor="original_name"
            required
            helpText="The actual name of the buyer/consumer (required)"
          >
            <Input
              id="original_name"
              type="text"
              placeholder="Enter the real buyer/consumer name"
              value={state.createForm.original_name}
              onChange={(e) => setState(prev => ({
                ...prev,
                createForm: {
                  ...prev.createForm,
                  original_name: e.target.value
                }
              }))}
            />
          </FormGroup>

          <FormGroup
            label="Pirate Name (Optional)"
            htmlFor="pirate_name"
            helpText="Leave blank to auto-generate, or enter a custom pirate name"
          >
            <Input
              id="pirate_name"
              type="text"
              placeholder="Leave empty for auto-generated name"
              value={state.createForm.pirate_name}
              onChange={(e) => setState(prev => ({
                ...prev,
                createForm: {
                  ...prev.createForm,
                  pirate_name: e.target.value
                }
              }))}
            />
          </FormGroup>

          {state.error && (
            <WarningBanner
              type="error"
              message={state.error}
              style={{ marginBottom: spacing.lg }}
            />
          )}
        </Modal>
      </MaintenanceContainer>
    </CaptainLayout>
    </>
  );
};
