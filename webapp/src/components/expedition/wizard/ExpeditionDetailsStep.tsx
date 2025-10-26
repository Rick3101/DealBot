import React from 'react';
import styled from 'styled-components';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';

const FormSection = styled.div`
  margin-bottom: ${spacing.xl};
`;

const FormLabel = styled.label`
  display: block;
  font-family: ${pirateTypography.headings};
  font-weight: ${pirateTypography.weights.bold};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.sm};
  font-size: ${pirateTypography.sizes.base};
`;

const FormInput = styled.input`
  width: 100%;
  padding: ${spacing.md};
  border: 2px solid ${pirateColors.lightGold};
  border-radius: 8px;
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.base};
  background: ${pirateColors.white};
  color: ${pirateColors.primary};
  transition: all 0.3s ease;

  &:focus {
    outline: none;
    border-color: ${pirateColors.secondary};
    box-shadow: 0 0 0 3px rgba(218, 165, 32, 0.1);
  }

  &::placeholder {
    color: ${pirateColors.muted};
  }
`;

const HelpText = styled.p`
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.muted};
  margin-top: ${spacing.sm};
  font-family: ${pirateTypography.body};
`;

export interface ExpeditionDetailsStepProps {
  name: string;
  onNameChange: (name: string) => void;
}

/**
 * Step 1: Expedition Details
 * Pure presentation component for expedition name only
 * Description and deadline can be added later in expedition details
 */
export const ExpeditionDetailsStep: React.FC<ExpeditionDetailsStepProps> = ({
  name,
  onNameChange,
}) => {
  return (
    <>
      <FormSection>
        <FormLabel htmlFor="expedition-name">
          ⛵ Expedition Name *
        </FormLabel>
        <FormInput
          id="expedition-name"
          type="text"
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder="Enter expedition name..."
          maxLength={100}
          autoFocus
        />
        <HelpText>
          Give your expedition a memorable name. You can add description, deadline, and other details later from the expedition page.
        </HelpText>
      </FormSection>
    </>
  );
};
