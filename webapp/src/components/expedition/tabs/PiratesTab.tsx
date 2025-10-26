import React, { useState } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { Users, Eye, EyeOff, Key, AlertTriangle } from 'lucide-react';
import { PirateButton } from '@/components/ui/PirateButton';
import { PirateCard } from '@/components/ui/PirateCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { formatCurrency } from '@/utils/formatters';
import { hapticFeedback } from '@/utils/telegram';
import { bramblerService } from '@/services/api/bramblerService';

interface PirateStats {
  total_items: number;
  items_consumed: number;
  total_spent: number;
  total_paid: number;
  debt: number;
}

interface RecentItem {
  name: string;
  emoji: string;
  quantity: number;
  consumed_at: string | null;
}

interface PirateName {
  id: number;
  pirate_name: string;
  original_name?: string;
  stats: PirateStats;
  recent_items: RecentItem[];
}

interface PiratesTabProps {
  pirateNames: PirateName[];
  onAddPirate: () => void;
  expeditionId: number;
  isOwner: boolean;
  ownerChatId: number;
}

const TabContent = styled(motion.div)`
  min-height: 400px;
`;

const SectionTitle = styled.h3`
  font-family: ${pirateTypography.headings};
  font-size: 1.25rem;
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.lg};
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
`;

const ConsumptionIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: ${pirateColors.lightGold};
  color: ${pirateColors.primary};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
`;

const PaymentStatusBadge = styled.span<{ $status: string }>`
  background: ${props =>
    props.$status === 'paid' ? pirateColors.success :
    props.$status === 'partial' ? pirateColors.warning :
    pirateColors.danger
  };
  color: ${pirateColors.white};
  padding: ${spacing.xs} ${spacing.sm};
  border-radius: 12px;
  font-size: ${pirateTypography.sizes.xs};
  font-weight: ${pirateTypography.weights.bold};
  text-transform: uppercase;
  margin-top: ${spacing.xs};
`;

const DecryptionSection = styled.div`
  background: linear-gradient(135deg, ${pirateColors.warning}15, ${pirateColors.secondary}10);
  border: 2px solid ${pirateColors.lightGold};
  border-radius: 12px;
  padding: ${spacing.lg};
  margin-bottom: ${spacing.lg};
`;

const DecryptionHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing.md};
  flex-wrap: wrap;
  gap: ${spacing.md};
`;

const DecryptionTitle = styled.h4`
  font-family: ${pirateTypography.headings};
  color: ${pirateColors.primary};
  margin: 0;
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
`;

const DecryptionControls = styled.div`
  display: flex;
  gap: ${spacing.sm};
  align-items: center;
  flex-wrap: wrap;
`;

const WarningBanner = styled(motion.div)`
  background: linear-gradient(135deg, ${pirateColors.warning}20, ${pirateColors.danger}10);
  border: 2px solid ${pirateColors.warning};
  border-radius: 12px;
  padding: ${spacing.md};
  margin-bottom: ${spacing.md};
  display: flex;
  align-items: center;
  gap: ${spacing.md};
`;

const WarningText = styled.p`
  color: ${pirateColors.muted};
  margin: 0;
  font-size: ${pirateTypography.sizes.sm};
  line-height: 1.5;
`;

const OriginalNameBadge = styled.div`
  background: ${pirateColors.warning}20;
  border: 1px solid ${pirateColors.warning};
  color: ${pirateColors.warning};
  padding: ${spacing.xs} ${spacing.sm};
  border-radius: 8px;
  font-size: ${pirateTypography.sizes.xs};
  font-weight: ${pirateTypography.weights.bold};
  margin-top: ${spacing.xs};
  display: flex;
  align-items: center;
  gap: ${spacing.xs};
`;

export const PiratesTab: React.FC<PiratesTabProps> = ({
  pirateNames,
  onAddPirate,
  expeditionId,
  isOwner,
}) => {
  const [showOriginalNames, setShowOriginalNames] = useState(false);
  const [decryptedMappings, setDecryptedMappings] = useState<Record<string, string>>({});
  const [isDecrypting, setIsDecrypting] = useState(false);
  const [decryptError, setDecryptError] = useState<string | null>(null);
  const [ownerKey, setOwnerKey] = useState<string | null>(null);

  // Get the display name for a pirate (decrypted if available and showOriginalNames is true)
  const getDisplayName = (pirate: PirateName): string => {
    if (showOriginalNames) {
      // Check decrypted mappings first
      if (decryptedMappings[pirate.pirate_name]) {
        return decryptedMappings[pirate.pirate_name];
      }
      // Fall back to API-provided original name (for backward compatibility)
      if (pirate.original_name) {
        return pirate.original_name;
      }
    }
    return pirate.pirate_name;
  };

  // Check if pirate has original name (either from API or decrypted)
  const hasOriginalName = (pirate: PirateName): boolean => {
    return Boolean(pirate.original_name || decryptedMappings[pirate.pirate_name]);
  };

  // Check if any pirates need decryption (have no original_name from API)
  const hasEncryptedPirates = pirateNames.some(p => !p.original_name);

  // Check if owner can see original names directly from API
  const hasDirectOriginalNames = pirateNames.some(p => p.original_name);

  const handleDecryptNames = async () => {
    if (!isOwner) {
      setDecryptError('Only the expedition owner can decrypt pirate names');
      return;
    }

    setIsDecrypting(true);
    setDecryptError(null);
    hapticFeedback('medium');

    try {
      // First, get the owner key if we don't have it
      let keyToUse = ownerKey;

      if (!keyToUse) {
        try {
          keyToUse = await bramblerService.getOwnerKey(expeditionId);
          setOwnerKey(keyToUse);
        } catch (error: any) {
          console.error('Failed to get owner key:', error);
          const errorMsg = error?.message || 'Failed to retrieve owner key';
          setDecryptError(`Owner key error: ${errorMsg}. Make sure you are the expedition owner.`);
          return;
        }
      }

      // Now decrypt with the owner key
      try {
        const decrypted = await bramblerService.decryptNames(expeditionId, {
          owner_key: keyToUse
        });

        setDecryptedMappings(decrypted);
        setShowOriginalNames(true);
      } catch (error: any) {
        console.error('Failed to decrypt names:', error);
        const errorMsg = error?.message || 'Decryption failed';
        setDecryptError(`Decryption error: ${errorMsg}. The owner key may be invalid or data may be corrupted.`);
      }
    } catch (error: any) {
      console.error('Unexpected decryption error:', error);
      setDecryptError('An unexpected error occurred. Please try again.');
    } finally {
      setIsDecrypting(false);
    }
  };

  const handleToggleDisplay = () => {
    hapticFeedback('light');
    if (!showOriginalNames) {
      // If there are direct original names from API (no encryption), just toggle
      if (hasDirectOriginalNames && !hasEncryptedPirates) {
        setShowOriginalNames(true);
      } else if (hasEncryptedPirates) {
        // Try to decrypt encrypted names
        handleDecryptNames();
      } else {
        // Fallback: just toggle
        setShowOriginalNames(true);
      }
    } else {
      // Hide original names
      setShowOriginalNames(false);
    }
  };

  return (
    <TabContent
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      {/* Owner-only decryption section */}
      {isOwner && (hasEncryptedPirates || hasDirectOriginalNames) && (
        <DecryptionSection>
          <DecryptionHeader>
            <DecryptionTitle>
              <Key size={20} />
              Owner Decryption Access
            </DecryptionTitle>
            <DecryptionControls>
              <PirateButton
                variant={showOriginalNames ? 'danger' : 'secondary'}
                size="sm"
                onClick={handleToggleDisplay}
                disabled={isDecrypting || (!hasEncryptedPirates && !hasDirectOriginalNames)}
              >
                {isDecrypting ? (
                  'Decrypting...'
                ) : showOriginalNames ? (
                  <><EyeOff size={16} /> Hide Original Names</>
                ) : (
                  <><Eye size={16} /> Show Original Names</>
                )}
              </PirateButton>
            </DecryptionControls>
          </DecryptionHeader>

          {!hasEncryptedPirates && !hasDirectOriginalNames && (
            <WarningBanner
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <AlertTriangle size={20} color={pirateColors.warning} />
              <WarningText>
                No encrypted pirate names found for this expedition.
                Original names will be shown by default as the expedition owner.
              </WarningText>
            </WarningBanner>
          )}

          {decryptError && (
            <WarningBanner
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <AlertTriangle size={20} color={pirateColors.warning} />
              <WarningText>{decryptError}</WarningText>
            </WarningBanner>
          )}

          {showOriginalNames && (hasDirectOriginalNames || Object.keys(decryptedMappings).length > 0) && (
            <WarningBanner
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <AlertTriangle size={20} color={pirateColors.warning} />
              <WarningText>
                Original names are currently visible. Make sure you're in a secure environment.
                {hasEncryptedPirates ? ' These names were decrypted using your owner key.' : ' These names are stored in plain text.'}
              </WarningText>
            </WarningBanner>
          )}
        </DecryptionSection>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.lg }}>
        <SectionTitle style={{ marginBottom: 0 }}>🏴‍☠️ Pirate Crew</SectionTitle>
        <PirateButton
          variant="primary"
          size="sm"
          onClick={() => {
            hapticFeedback('medium');
            onAddPirate();
          }}
        >
          <Users size={16} /> Add Pirate
        </PirateButton>
      </div>

      {pirateNames.length === 0 ? (
        <EmptyState
          icon="🏴‍☠️"
          title="No pirates yet"
          description="No pirates have joined this expedition yet."
        />
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: spacing.lg
        }}>
          {pirateNames.map(pirate => {
            // Use stats directly from API response
            const { stats, recent_items } = pirate;
            const hasPaid = stats.total_paid > 0;
            const hasPending = stats.debt > 0;

            return (
              <motion.div
                key={pirate.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
              >
                <PirateCard>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: spacing.md,
                    marginBottom: spacing.lg
                  }}>
                    <ConsumptionIcon style={{ width: '50px', height: '50px', fontSize: '1.5rem' }}>
                      {showOriginalNames && hasOriginalName(pirate) ? '👤' : '🏴‍☠️'}
                    </ConsumptionIcon>
                    <div style={{ flex: 1 }}>
                      <h4 style={{
                        fontFamily: pirateTypography.headings,
                        color: showOriginalNames && hasOriginalName(pirate) ? pirateColors.warning : pirateColors.primary,
                        margin: 0,
                        fontSize: pirateTypography.sizes.lg
                      }}>
                        {getDisplayName(pirate)}
                      </h4>
                      {showOriginalNames && hasOriginalName(pirate) && (
                        <OriginalNameBadge>
                          <Key size={12} />
                          Decrypted Identity
                        </OriginalNameBadge>
                      )}
                      {!showOriginalNames && !pirate.original_name && (
                        <div style={{
                          fontSize: pirateTypography.sizes.xs,
                          color: pirateColors.muted,
                          marginTop: spacing.xs,
                          fontStyle: 'italic'
                        }}>
                          🔒 Original name encrypted
                        </div>
                      )}
                      <div style={{
                        fontSize: pirateTypography.sizes.sm,
                        color: pirateColors.muted,
                        marginTop: spacing.xs
                      }}>
                        {stats.total_items} consumption{stats.total_items !== 1 ? 's' : ''}
                      </div>
                    </div>
                  </div>

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: spacing.md,
                    marginBottom: spacing.md
                  }}>
                    <div>
                      <div style={{
                        fontSize: pirateTypography.sizes.xs,
                        color: pirateColors.muted,
                        marginBottom: spacing.xs
                      }}>
                        Total Spent
                      </div>
                      <div style={{
                        fontFamily: pirateTypography.headings,
                        fontSize: pirateTypography.sizes.lg,
                        color: pirateColors.secondary,
                        fontWeight: pirateTypography.weights.bold
                      }}>
                        {formatCurrency(stats.total_spent)}
                      </div>
                    </div>

                    <div>
                      <div style={{
                        fontSize: pirateTypography.sizes.xs,
                        color: pirateColors.muted,
                        marginBottom: spacing.xs
                      }}>
                        Items Consumed
                      </div>
                      <div style={{
                        fontFamily: pirateTypography.headings,
                        fontSize: pirateTypography.sizes.lg,
                        color: pirateColors.primary,
                        fontWeight: pirateTypography.weights.bold
                      }}>
                        {stats.items_consumed}
                      </div>
                    </div>
                  </div>

                  <div style={{
                    display: 'flex',
                    gap: spacing.sm,
                    flexWrap: 'wrap'
                  }}>
                    {hasPaid && (
                      <PaymentStatusBadge $status="paid">
                        ✓ Paid {formatCurrency(stats.total_paid)}
                      </PaymentStatusBadge>
                    )}
                    {hasPending && (
                      <PaymentStatusBadge $status="pending">
                        ⏳ Debt {formatCurrency(stats.debt)}
                      </PaymentStatusBadge>
                    )}
                  </div>

                  <div style={{
                    marginTop: spacing.md,
                    paddingTop: spacing.md,
                    borderTop: `1px solid ${pirateColors.lightGold}`
                  }}>
                    <div style={{
                      fontSize: pirateTypography.sizes.xs,
                      color: pirateColors.muted,
                      marginBottom: spacing.xs
                    }}>
                      Recent Items
                    </div>
                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: spacing.xs
                    }}>
                      {recent_items.map((item, index) => (
                        <span
                          key={index}
                          style={{
                            background: pirateColors.lightGold,
                            color: pirateColors.primary,
                            padding: `${spacing.xs} ${spacing.sm}`,
                            borderRadius: '12px',
                            fontSize: pirateTypography.sizes.xs,
                            fontWeight: pirateTypography.weights.medium
                          }}
                        >
                          {item.emoji} {item.name} x{item.quantity}
                        </span>
                      ))}
                    </div>
                  </div>
                </PirateCard>
              </motion.div>
            );
          })}
        </div>
      )}
    </TabContent>
  );
};
