import React, { useState } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, EyeOff, AlertTriangle, Key } from 'lucide-react';
import { PirateCard } from '@/components/ui/PirateCard';
import { PirateButton as Button } from '@/components/ui/PirateButton';
import { EmptyState } from '@/components/ui/EmptyState';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';
import { formatCurrency, formatDateTime } from '@/utils/formatters';
import { ItemConsumption } from '@/types/expedition';
import { useConsumptionPayment } from '@/hooks/useConsumptionPayment';
import { hapticFeedback } from '@/utils/telegram';

interface ConsumptionsTabProps {
  consumptions: ItemConsumption[];
  onPaymentSuccess?: () => void;
  isOwner?: boolean;
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

const ConsumptionsList = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.md};
`;

const ConsumptionCard = styled(PirateCard)`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: ${spacing.md} ${spacing.lg};
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(139, 69, 19, 0.15);
  }
`;

const ConsumptionInfo = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.md};
  flex: 1;
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

const ConsumptionDetails = styled.div`
  flex: 1;
`;

const ConsumptionPirate = styled.div`
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.xs};
`;

const ConsumptionItem = styled.div`
  color: ${pirateColors.muted};
  font-size: ${pirateTypography.sizes.sm};
`;

const ConsumptionValue = styled.div`
  text-align: right;
`;

const ConsumptionPrice = styled.div`
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.secondary};
  font-size: ${pirateTypography.sizes.lg};
`;

const ConsumptionDate = styled.div`
  color: ${pirateColors.muted};
  font-size: ${pirateTypography.sizes.xs};
  margin-top: ${spacing.xs};
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

const PaymentActions = styled.div`
  display: flex;
  flex-direction: column;
  gap: ${spacing.sm};
  margin-top: ${spacing.sm};
`;

const PaymentInput = styled.input`
  padding: ${spacing.sm};
  border: 2px solid ${pirateColors.lightGold};
  border-radius: 8px;
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.sm};
  width: 120px;

  &:focus {
    outline: none;
    border-color: ${pirateColors.primary};
  }
`;

const PaymentInfo = styled.div`
  font-size: ${pirateTypography.sizes.xs};
  color: ${pirateColors.muted};
  margin-top: ${spacing.xs};
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: ${spacing.sm};
`;

const PayButton = styled(Button)`
  margin-top: ${spacing.sm};
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

export const ConsumptionsTab: React.FC<ConsumptionsTabProps> = ({
  consumptions,
  onPaymentSuccess,
  isOwner = false,
}) => {
  console.log('[ConsumptionsTab] Component rendering with', consumptions.length, 'consumptions');
  consumptions.forEach(c => {
    console.log(`  [ConsumptionsTab] ID ${c.id}: Status ${c.payment_status}, Paid ${c.amount_paid}/${c.total_price}`);
  });

  const [showOriginalNames, setShowOriginalNames] = useState(false);
  const {
    payingConsumptionId,
    paymentAmount,
    processing,
    startPayment,
    processPayment,
    cancelPayment,
    setPaymentAmount,
    calculatePaymentDetails,
    validatePaymentAmount,
  } = useConsumptionPayment(onPaymentSuccess);

  const handleToggleDisplay = () => {
    hapticFeedback('light');
    setShowOriginalNames(!showOriginalNames);
  };

  const getDisplayName = (consumption: ItemConsumption): string => {
    return showOriginalNames ? consumption.consumer_name : consumption.pirate_name;
  };

  return (
    <TabContent
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      {/* Owner-only decryption section */}
      {isOwner && consumptions.length > 0 && (
        <DecryptionSection>
          <DecryptionHeader>
            <DecryptionTitle>
              <Key size={20} />
              Owner Identity Access
            </DecryptionTitle>
            <DecryptionControls>
              <Button
                variant={showOriginalNames ? 'danger' : 'secondary'}
                size="sm"
                onClick={handleToggleDisplay}
              >
                {showOriginalNames ? (
                  <><EyeOff size={16} /> Hide Original Names</>
                ) : (
                  <><Eye size={16} /> Show Original Names</>
                )}
              </Button>
            </DecryptionControls>
          </DecryptionHeader>

          {showOriginalNames && (
            <WarningBanner
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <AlertTriangle size={20} color={pirateColors.warning} />
              <WarningText>
                Original names are currently visible. Make sure you're in a secure environment.
              </WarningText>
            </WarningBanner>
          )}
        </DecryptionSection>
      )}

      <SectionTitle>🏴‍☠️ Recent Consumptions</SectionTitle>
      {consumptions.length === 0 ? (
        <EmptyState
          icon="🍽️"
          title="No consumptions yet"
          description="Pirates haven't started consuming items from this expedition."
        />
      ) : (
        <ConsumptionsList>
          <AnimatePresence>
            {consumptions.map(consumption => (
              <motion.div
                key={consumption.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <ConsumptionCard>
                  <ConsumptionInfo>
                    <ConsumptionIcon>
                      🏴‍☠️
                    </ConsumptionIcon>
                    <ConsumptionDetails>
                      <ConsumptionPirate style={{
                        color: showOriginalNames ? pirateColors.warning : pirateColors.primary
                      }}>
                        {showOriginalNames && isOwner && '👤 '}
                        {getDisplayName(consumption)}
                      </ConsumptionPirate>
                      <ConsumptionItem>
                        {consumption.quantity}x {consumption.product_name}
                      </ConsumptionItem>
                      <PaymentStatusBadge $status={consumption.payment_status}>
                        {consumption.payment_status}
                      </PaymentStatusBadge>
                      {consumption.payment_status !== 'paid' && payingConsumptionId === consumption.id && (
                        <PaymentActions>
                          <PaymentInput
                            type="number"
                            step="0.01"
                            min="0.01"
                            max={calculatePaymentDetails(consumption).remainingAmount}
                            value={paymentAmount}
                            onChange={(e) => {
                              const value = parseFloat(e.target.value);
                              const { remainingAmount } = calculatePaymentDetails(consumption);
                              if (value > remainingAmount) {
                                setPaymentAmount(remainingAmount.toFixed(2));
                              } else {
                                setPaymentAmount(e.target.value);
                              }
                            }}
                            placeholder={`Max: ${formatCurrency(calculatePaymentDetails(consumption).remainingAmount)}`}
                          />
                          <ButtonGroup>
                            <Button
                              size="sm"
                              onClick={() => processPayment(consumption.id, parseFloat(paymentAmount))}
                              disabled={
                                processing ||
                                !validatePaymentAmount(
                                  paymentAmount,
                                  calculatePaymentDetails(consumption).remainingAmount
                                )
                              }
                            >
                              {processing ? 'Processing...' : 'Confirm'}
                            </Button>
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={cancelPayment}
                              disabled={processing}
                            >
                              Cancel
                            </Button>
                          </ButtonGroup>
                        </PaymentActions>
                      )}
                    </ConsumptionDetails>
                  </ConsumptionInfo>
                  <ConsumptionValue>
                    <ConsumptionPrice>
                      {formatCurrency(consumption.total_price)}
                    </ConsumptionPrice>
                    {consumption.amount_paid > 0 && (
                      <PaymentInfo>
                        Paid: {formatCurrency(consumption.amount_paid)} |
                        Due: {formatCurrency(consumption.total_price - consumption.amount_paid)}
                      </PaymentInfo>
                    )}
                    <ConsumptionDate>
                      {formatDateTime(consumption.consumed_at || '')}
                    </ConsumptionDate>
                    {consumption.payment_status !== 'paid' && payingConsumptionId !== consumption.id && (
                      <PayButton
                        size="sm"
                        onClick={() => startPayment(consumption)}
                      >
                        Pay
                      </PayButton>
                    )}
                  </ConsumptionValue>
                </ConsumptionCard>
              </motion.div>
            ))}
          </AnimatePresence>
        </ConsumptionsList>
      )}
    </TabContent>
  );
};
