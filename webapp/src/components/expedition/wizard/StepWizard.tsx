import React from 'react';
import styled, { css } from 'styled-components';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';

const WizardContainer = styled.div`
  margin-bottom: ${spacing['2xl']};
`;

const StepsContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${spacing.xl};
  overflow-x: auto;
  padding: ${spacing.sm} 0;

  @media (min-width: 640px) {
    flex-direction: column;
    gap: ${spacing.lg};
    align-items: stretch;
  }
`;

const StepItem = styled.div<{ $active: boolean; $completed: boolean; $clickable: boolean }>`
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 120px;
  position: relative;
  cursor: ${props => props.$clickable ? 'pointer' : 'default'};
  transition: all 0.3s ease;

  ${props => props.$active && css`
    transform: scale(1.05);
  `}

  @media (min-width: 640px) {
    min-width: 150px;
  }
`;

const StepCircle = styled.div<{ $active: boolean; $completed: boolean }>`
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: ${spacing.sm};
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;

  ${props => props.$completed && css`
    background: ${pirateColors.success};
    color: ${pirateColors.white};
    box-shadow: 0 4px 12px rgba(34, 139, 34, 0.3);
  `}

  ${props => props.$active && !props.$completed && css`
    background: ${pirateColors.secondary};
    color: ${pirateColors.white};
    box-shadow: 0 4px 12px rgba(218, 165, 32, 0.3);
    animation: pulse 2s infinite;

    @keyframes pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.1); }
    }
  `}

  ${props => !props.$active && !props.$completed && css`
    background: ${pirateColors.lightGold};
    color: ${pirateColors.primary};
    border: 2px solid ${pirateColors.primary};
  `}
`;

const StepConnector = styled.div<{ $completed: boolean }>`
  position: absolute;
  top: 30px;
  left: 50%;
  right: -50%;
  height: 2px;
  background: ${props => props.$completed ? pirateColors.success : pirateColors.lightGold};
  z-index: 1;
  transition: background 0.3s ease;

  &:last-child {
    display: none;
  }
`;

const StepTitle = styled.h4<{ $active: boolean }>`
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.sm};
  color: ${props => props.$active ? pirateColors.primary : pirateColors.muted};
  margin: 0 0 ${spacing.xs} 0;
  text-align: center;
  transition: color 0.3s ease;

  @media (min-width: 640px) {
    font-size: ${pirateTypography.sizes.base};
  }
`;

const StepDescription = styled.p`
  font-size: ${pirateTypography.sizes.xs};
  color: ${pirateColors.muted};
  margin: 0;
  text-align: center;
  line-height: 1.3;

  @media (min-width: 640px) {
    font-size: ${pirateTypography.sizes.sm};
  }
`;

export interface Step {
  id: number;
  title: string;
  icon: string;
  description: string;
}

export interface StepWizardProps {
  steps: Step[];
  currentStep: number;
  onStepClick: (stepId: number) => void;
  canNavigateToStep: (stepId: number) => boolean;
}

/**
 * StepWizard component
 * Reusable progress indicator for multi-step forms
 */
export const StepWizard: React.FC<StepWizardProps> = ({
  steps,
  currentStep,
  onStepClick,
  canNavigateToStep,
}) => {
  return (
    <WizardContainer>
      <StepsContainer>
        {steps.map((step, index) => {
          const isActive = currentStep === step.id;
          const isCompleted = currentStep > step.id;
          const clickable = canNavigateToStep(step.id);

          return (
            <StepItem
              key={step.id}
              $active={isActive}
              $completed={isCompleted}
              $clickable={clickable}
              onClick={() => clickable && onStepClick(step.id)}
            >
              {index < steps.length - 1 && (
                <StepConnector $completed={isCompleted} />
              )}

              <StepCircle $active={isActive} $completed={isCompleted}>
                {isCompleted ? '✓' : step.icon}
              </StepCircle>

              <StepTitle $active={isActive}>
                {step.title}
              </StepTitle>

              <StepDescription>
                {step.description}
              </StepDescription>
            </StepItem>
          );
        })}
      </StepsContainer>
    </WizardContainer>
  );
};
