import { useState, useCallback, useMemo } from 'react';
import { hapticFeedback } from '@/utils/telegram';

export interface WizardStep {
  id: number;
  title: string;
  icon: string;
  description: string;
}

export interface UseExpeditionWizardOptions {
  initialStep?: number;
  totalSteps: number;
  onStepChange?: (step: number) => void;
}

export interface UseExpeditionWizardReturn {
  currentStep: number;
  isFirstStep: boolean;
  isLastStep: boolean;
  canGoNext: boolean;
  canGoPrevious: boolean;
  goToNextStep: () => void;
  goToPreviousStep: () => void;
  goToStep: (step: number) => void;
  canNavigateToStep: (step: number) => boolean;
}

/**
 * Hook for managing multi-step wizard navigation
 * Single Responsibility: Step navigation logic only
 *
 * @param options - Configuration options for the wizard
 * @returns Wizard navigation state and methods
 */
export const useExpeditionWizard = ({
  initialStep = 1,
  totalSteps,
  onStepChange,
}: UseExpeditionWizardOptions): UseExpeditionWizardReturn => {
  const [currentStep, setCurrentStep] = useState(initialStep);

  // Derived state
  const isFirstStep = useMemo(() => currentStep === 1, [currentStep]);
  const isLastStep = useMemo(() => currentStep === totalSteps, [currentStep, totalSteps]);
  const canGoPrevious = useMemo(() => currentStep > 1, [currentStep]);
  const canGoNext = useMemo(() => currentStep < totalSteps, [currentStep, totalSteps]);

  /**
   * Navigate to the next step
   */
  const goToNextStep = useCallback(() => {
    if (canGoNext) {
      const nextStep = currentStep + 1;
      setCurrentStep(nextStep);
      hapticFeedback('medium');
      onStepChange?.(nextStep);
    }
  }, [currentStep, canGoNext, onStepChange]);

  /**
   * Navigate to the previous step
   */
  const goToPreviousStep = useCallback(() => {
    if (canGoPrevious) {
      const prevStep = currentStep - 1;
      setCurrentStep(prevStep);
      hapticFeedback('light');
      onStepChange?.(prevStep);
    }
  }, [currentStep, canGoPrevious, onStepChange]);

  /**
   * Navigate to a specific step
   * Only allows navigation to previous steps or current step
   */
  const goToStep = useCallback((step: number) => {
    if (step >= 1 && step <= currentStep && step <= totalSteps) {
      setCurrentStep(step);
      hapticFeedback('light');
      onStepChange?.(step);
    }
  }, [currentStep, totalSteps, onStepChange]);

  /**
   * Check if navigation to a specific step is allowed
   * Users can only navigate to completed steps (previous steps)
   */
  const canNavigateToStep = useCallback((step: number) => {
    return step >= 1 && step <= currentStep && step <= totalSteps;
  }, [currentStep, totalSteps]);

  return {
    currentStep,
    isFirstStep,
    isLastStep,
    canGoNext,
    canGoPrevious,
    goToNextStep,
    goToPreviousStep,
    goToStep,
    canNavigateToStep,
  };
};
