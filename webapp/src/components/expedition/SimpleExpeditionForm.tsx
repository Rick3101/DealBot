import React from 'react';
import styled from 'styled-components';
import { CaptainLayout } from '@/layouts/CaptainLayout';
import { PirateButton } from '@/components/ui/PirateButton';
import { pirateColors, spacing, pirateTypography, mixins } from '@/utils/pirateTheme';

const FormContainer = styled.div`
  ${mixins.pirateCard}
  padding: ${spacing.xl};
  max-width: 600px;
  margin: 0 auto;
`;

const FormTitle = styled.h2`
  font-family: ${pirateTypography.headings};
  font-size: ${pirateTypography.sizes.xl};
  color: ${pirateColors.primary};
  margin-bottom: ${spacing.md};
  text-align: center;
`;

const FormSubtitle = styled.p`
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.base};
  color: ${pirateColors.muted};
  margin-bottom: ${spacing.xl};
  text-align: center;
`;

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

  &:disabled {
    background: #f3f4f6;
    cursor: not-allowed;
  }
`;

const HelpText = styled.p`
  font-size: ${pirateTypography.sizes.sm};
  color: ${pirateColors.muted};
  margin-top: ${spacing.sm};
  font-family: ${pirateTypography.body};
`;

const ButtonContainer = styled.div`
  display: flex;
  gap: ${spacing.md};
  justify-content: flex-end;
  margin-top: ${spacing.xl};
`;

const ErrorMessage = styled.div`
  background: rgba(220, 38, 38, 0.1);
  border: 1px solid rgba(220, 38, 38, 0.3);
  color: #dc2626;
  padding: ${spacing.md};
  border-radius: 8px;
  margin-bottom: ${spacing.lg};
  font-size: ${pirateTypography.sizes.sm};
`;

export interface SimpleExpeditionFormProps {
  name: string;
  onNameChange: (name: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  loading?: boolean;
  error?: string | null;
}

/**
 * SimpleExpeditionForm component
 * Pure presentation component for quick expedition creation
 * Only requires a name - items can be added later from the expedition details page
 */
export const SimpleExpeditionForm: React.FC<SimpleExpeditionFormProps> = ({
  name,
  onNameChange,
  onSubmit,
  onCancel,
  loading = false,
  error = null,
}) => {
  const handleSubmit = () => {
    if (name.trim() && !loading) {
      onSubmit();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && name.trim() && !loading) {
      e.preventDefault();
      onSubmit();
    }
  };

  const isValid = name.trim().length > 0;

  return (
    <CaptainLayout
      title="Create New Expedition"
      subtitle="Set sail on a new adventure"
    >
      <FormContainer>
        <FormTitle>Quick Start</FormTitle>
        <FormSubtitle>
          Start your journey with a name. Add items and details later!
        </FormSubtitle>

        {error && <ErrorMessage>{error}</ErrorMessage>}

        <FormSection>
          <FormLabel htmlFor="expedition-name">
            Expedition Name *
          </FormLabel>
          <FormInput
            id="expedition-name"
            type="text"
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter expedition name..."
            maxLength={100}
            autoFocus
            disabled={loading}
          />
          <HelpText>
            Give your expedition a memorable name. You can add items, pirates, and other details from the expedition page.
          </HelpText>
        </FormSection>

        <ButtonContainer>
          <PirateButton
            variant="outline"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </PirateButton>
          <PirateButton
            variant="primary"
            onClick={handleSubmit}
            disabled={!isValid || loading}
          >
            {loading ? 'Creating...' : 'Create Expedition'}
          </PirateButton>
        </ButtonContainer>
      </FormContainer>
    </CaptainLayout>
  );
};
