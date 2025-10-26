import React from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { CaptainLayout } from '@/layouts/CaptainLayout';
import { PirateButton } from '@/components/ui/PirateButton';
import { StepWizard, Step } from '@/components/expedition/wizard/StepWizard';
import { ExpeditionDetailsStep } from '@/components/expedition/wizard/ExpeditionDetailsStep';
import { ProductSelectionStep } from '@/components/expedition/wizard/ProductSelectionStep';
import { ProductConfigurationStep, SelectedProductItem } from '@/components/expedition/wizard/ProductConfigurationStep';
import { ReviewStep } from '@/components/expedition/wizard/ReviewStep';
import { spacing, pirateTypography, pirateColors, mixins } from '@/utils/pirateTheme';
import { Product, QualityGrade } from '@/types/expedition';

const CreateContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
`;

const StepContent = styled(motion.div)`
  ${mixins.pirateCard}
  padding: ${spacing.xl};
  min-height: 400px;
`;

const NavigationButtons = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: ${spacing.xl};
  gap: ${spacing.md};

  @media (min-width: 640px) {
    flex-direction: column;
    gap: ${spacing.lg};
  }
`;

const StepIndicator = styled.div`
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.muted};
  font-weight: ${pirateTypography.weights.medium};
`;

const steps: Step[] = [
  { id: 1, title: 'Expedition Name', icon: '🗺️', description: 'Give your expedition a name' },
  { id: 2, title: 'Select Items', icon: '📦', description: 'Choose items for your expedition' },
  { id: 3, title: 'Set Qualities & Prices', icon: '💰', description: 'Configure quality grades and pricing' },
  { id: 4, title: 'Launch Expedition', icon: '⛵', description: 'Review and launch your expedition' },
];

export interface CreateExpeditionPresenterProps {
  // Wizard state
  currentStep: number;
  isFirstStep: boolean;
  isLastStep: boolean;
  totalSteps: number;

  // Expedition data
  name: string;
  selectedProducts: SelectedProductItem[];
  availableProducts: Product[];

  // Loading state
  loading: boolean;

  // Validation
  isStepValid: boolean;
  canNavigateToStep: (step: number) => boolean;

  // Event handlers
  onNameChange: (name: string) => void;
  onProductToggle: (product: Product) => void;
  onQuantityChange: (productId: number, quantity: number) => void;
  onQualityChange: (productId: number, qualityGrade: QualityGrade) => void;
  onPriceChange: (productId: number, unitPrice: number) => void;
  onNext: () => void;
  onPrevious: () => void;
  onStepClick: (step: number) => void;
  onSubmit: () => void;
}

/**
 * CreateExpeditionPresenter component
 * Pure presentation component for the expedition creation wizard
 */
export const CreateExpeditionPresenter: React.FC<CreateExpeditionPresenterProps> = ({
  currentStep,
  isFirstStep,
  isLastStep,
  totalSteps,
  name,
  selectedProducts,
  availableProducts,
  loading,
  isStepValid,
  canNavigateToStep,
  onNameChange,
  onProductToggle,
  onQuantityChange,
  onQualityChange,
  onPriceChange,
  onNext,
  onPrevious,
  onStepClick,
  onSubmit,
}) => {
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <StepContent
            key="step1"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            <ExpeditionDetailsStep
              name={name}
              onNameChange={onNameChange}
            />
          </StepContent>
        );

      case 2:
        return (
          <StepContent
            key="step2"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            <ProductSelectionStep
              availableProducts={availableProducts}
              selectedProductIds={selectedProducts.map(p => p.product_id)}
              onProductToggle={onProductToggle}
            />
          </StepContent>
        );

      case 3:
        return (
          <StepContent
            key="step3"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            <ProductConfigurationStep
              selectedProducts={selectedProducts}
              onQuantityChange={onQuantityChange}
              onQualityChange={onQualityChange}
              onPriceChange={onPriceChange}
            />
          </StepContent>
        );

      case 4:
        return (
          <StepContent
            key="step4"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            <ReviewStep
              name={name}
              selectedProducts={selectedProducts}
              loading={loading}
              onSubmit={onSubmit}
            />
          </StepContent>
        );

      default:
        return null;
    }
  };

  return (
    <CaptainLayout
      title="Create New Expedition"
      subtitle="Set sail on a new adventure"
    >
      <CreateContainer>
        <StepWizard
          steps={steps}
          currentStep={currentStep}
          onStepClick={onStepClick}
          canNavigateToStep={canNavigateToStep}
        />

        <AnimatePresence mode="wait">
          {renderStepContent()}
        </AnimatePresence>

        <NavigationButtons>
          <PirateButton
            variant="outline"
            onClick={onPrevious}
            disabled={isFirstStep}
          >
            <ChevronLeft size={16} /> Previous
          </PirateButton>

          <StepIndicator>
            Step {currentStep} of {totalSteps}
          </StepIndicator>

          {!isLastStep ? (
            <PirateButton
              variant="primary"
              onClick={onNext}
              disabled={!isStepValid}
            >
              Next <ChevronRight size={16} />
            </PirateButton>
          ) : (
            <div />
          )}
        </NavigationButtons>
      </CreateContainer>
    </CaptainLayout>
  );
};
