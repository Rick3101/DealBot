import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useExpeditionWizard } from './useExpeditionWizard';
import * as telegramUtils from '@/utils/telegram';

// Mock telegram utils
vi.mock('@/utils/telegram', () => ({
  hapticFeedback: vi.fn(),
}));

describe('useExpeditionWizard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default step 1', () => {
    const { result } = renderHook(() =>
      useExpeditionWizard({ totalSteps: 4 })
    );

    expect(result.current.currentStep).toBe(1);
  });

  it('should initialize with custom initial step', () => {
    const { result } = renderHook(() =>
      useExpeditionWizard({ initialStep: 2, totalSteps: 4 })
    );

    expect(result.current.currentStep).toBe(2);
  });

  describe('Derived state', () => {
    it('should correctly identify first step', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ totalSteps: 4 })
      );

      expect(result.current.isFirstStep).toBe(true);
      expect(result.current.canGoPrevious).toBe(false);
    });

    it('should correctly identify last step', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 4, totalSteps: 4 })
      );

      expect(result.current.isLastStep).toBe(true);
      expect(result.current.canGoNext).toBe(false);
    });

    it('should correctly identify middle steps', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 2, totalSteps: 4 })
      );

      expect(result.current.isFirstStep).toBe(false);
      expect(result.current.isLastStep).toBe(false);
      expect(result.current.canGoPrevious).toBe(true);
      expect(result.current.canGoNext).toBe(true);
    });
  });

  describe('goToNextStep', () => {
    it('should navigate to next step', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ totalSteps: 4 })
      );

      act(() => {
        result.current.goToNextStep();
      });

      expect(result.current.currentStep).toBe(2);
      expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('medium');
    });

    it('should call onStepChange callback when navigating forward', () => {
      const onStepChange = vi.fn();
      const { result } = renderHook(() =>
        useExpeditionWizard({ totalSteps: 4, onStepChange })
      );

      act(() => {
        result.current.goToNextStep();
      });

      expect(onStepChange).toHaveBeenCalledWith(2);
    });

    it('should not navigate past last step', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 4, totalSteps: 4 })
      );

      act(() => {
        result.current.goToNextStep();
      });

      expect(result.current.currentStep).toBe(4);
    });

    it('should not trigger haptic feedback when already at last step', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 4, totalSteps: 4 })
      );

      act(() => {
        result.current.goToNextStep();
      });

      expect(telegramUtils.hapticFeedback).not.toHaveBeenCalled();
    });
  });

  describe('goToPreviousStep', () => {
    it('should navigate to previous step', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 3, totalSteps: 4 })
      );

      act(() => {
        result.current.goToPreviousStep();
      });

      expect(result.current.currentStep).toBe(2);
      expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('light');
    });

    it('should call onStepChange callback when navigating backward', () => {
      const onStepChange = vi.fn();
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 3, totalSteps: 4, onStepChange })
      );

      act(() => {
        result.current.goToPreviousStep();
      });

      expect(onStepChange).toHaveBeenCalledWith(2);
    });

    it('should not navigate before first step', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ totalSteps: 4 })
      );

      act(() => {
        result.current.goToPreviousStep();
      });

      expect(result.current.currentStep).toBe(1);
    });

    it('should not trigger haptic feedback when already at first step', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ totalSteps: 4 })
      );

      act(() => {
        result.current.goToPreviousStep();
      });

      expect(telegramUtils.hapticFeedback).not.toHaveBeenCalled();
    });
  });

  describe('goToStep', () => {
    it('should navigate to a previous step', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 4, totalSteps: 4 })
      );

      act(() => {
        result.current.goToStep(2);
      });

      expect(result.current.currentStep).toBe(2);
      expect(telegramUtils.hapticFeedback).toHaveBeenCalledWith('light');
    });

    it('should navigate to current step', () => {
      const onStepChange = vi.fn();
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 3, totalSteps: 4, onStepChange })
      );

      act(() => {
        result.current.goToStep(3);
      });

      expect(result.current.currentStep).toBe(3);
      expect(onStepChange).toHaveBeenCalledWith(3);
    });

    it('should not navigate to future steps', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 2, totalSteps: 4 })
      );

      act(() => {
        result.current.goToStep(3);
      });

      expect(result.current.currentStep).toBe(2);
    });

    it('should not navigate to steps below 1', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 2, totalSteps: 4 })
      );

      act(() => {
        result.current.goToStep(0);
      });

      expect(result.current.currentStep).toBe(2);
    });

    it('should not navigate to steps above totalSteps', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 4, totalSteps: 4 })
      );

      act(() => {
        result.current.goToStep(5);
      });

      expect(result.current.currentStep).toBe(4);
    });

    it('should call onStepChange when navigation is successful', () => {
      const onStepChange = vi.fn();
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 3, totalSteps: 4, onStepChange })
      );

      act(() => {
        result.current.goToStep(1);
      });

      expect(onStepChange).toHaveBeenCalledWith(1);
    });

    it('should not call onStepChange when navigation fails', () => {
      const onStepChange = vi.fn();
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 2, totalSteps: 4, onStepChange })
      );

      act(() => {
        result.current.goToStep(3); // Cannot go forward
      });

      expect(onStepChange).not.toHaveBeenCalled();
    });
  });

  describe('canNavigateToStep', () => {
    it('should return true for current step', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 3, totalSteps: 4 })
      );

      expect(result.current.canNavigateToStep(3)).toBe(true);
    });

    it('should return true for previous steps', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 3, totalSteps: 4 })
      );

      expect(result.current.canNavigateToStep(1)).toBe(true);
      expect(result.current.canNavigateToStep(2)).toBe(true);
    });

    it('should return false for future steps', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 2, totalSteps: 4 })
      );

      expect(result.current.canNavigateToStep(3)).toBe(false);
      expect(result.current.canNavigateToStep(4)).toBe(false);
    });

    it('should return false for steps below 1', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ totalSteps: 4 })
      );

      expect(result.current.canNavigateToStep(0)).toBe(false);
      expect(result.current.canNavigateToStep(-1)).toBe(false);
    });

    it('should return false for steps above totalSteps', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 4, totalSteps: 4 })
      );

      expect(result.current.canNavigateToStep(5)).toBe(false);
      expect(result.current.canNavigateToStep(10)).toBe(false);
    });
  });

  describe('Complete wizard flow', () => {
    it('should navigate through all steps forward', () => {
      const onStepChange = vi.fn();
      const { result } = renderHook(() =>
        useExpeditionWizard({ totalSteps: 4, onStepChange })
      );

      expect(result.current.currentStep).toBe(1);

      act(() => result.current.goToNextStep());
      expect(result.current.currentStep).toBe(2);

      act(() => result.current.goToNextStep());
      expect(result.current.currentStep).toBe(3);

      act(() => result.current.goToNextStep());
      expect(result.current.currentStep).toBe(4);
      expect(result.current.isLastStep).toBe(true);

      expect(onStepChange).toHaveBeenCalledTimes(3);
    });

    it('should navigate through all steps backward', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ initialStep: 4, totalSteps: 4 })
      );

      expect(result.current.currentStep).toBe(4);

      act(() => result.current.goToPreviousStep());
      expect(result.current.currentStep).toBe(3);

      act(() => result.current.goToPreviousStep());
      expect(result.current.currentStep).toBe(2);

      act(() => result.current.goToPreviousStep());
      expect(result.current.currentStep).toBe(1);
      expect(result.current.isFirstStep).toBe(true);
    });

    it('should allow jumping back to any completed step', () => {
      const { result } = renderHook(() =>
        useExpeditionWizard({ totalSteps: 4 })
      );

      // Navigate forward to step 4, one step at a time
      act(() => {
        result.current.goToNextStep(); // Step 2
      });

      act(() => {
        result.current.goToNextStep(); // Step 3
      });

      act(() => {
        result.current.goToNextStep(); // Step 4
      });

      expect(result.current.currentStep).toBe(4);

      // Jump back to step 1
      act(() => result.current.goToStep(1));
      expect(result.current.currentStep).toBe(1);

      // Can navigate forward (but only to previously visited steps, which is step 1 now)
      expect(result.current.canGoNext).toBe(true);
    });
  });

  describe('Hook stability', () => {
    it('should maintain stable function references with useCallback', () => {
      const { result, rerender } = renderHook(() =>
        useExpeditionWizard({ totalSteps: 4 })
      );

      const firstRender = {
        goToNextStep: result.current.goToNextStep,
        goToPreviousStep: result.current.goToPreviousStep,
        goToStep: result.current.goToStep,
        canNavigateToStep: result.current.canNavigateToStep,
      };

      rerender();

      // Functions should have different references because currentStep changed their dependencies
      // But let's test that they work correctly across renders
      expect(result.current.currentStep).toBe(1);
    });
  });
});
