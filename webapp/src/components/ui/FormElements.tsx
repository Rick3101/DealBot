import React from 'react';
import styled from 'styled-components';
import { pirateColors, spacing, pirateTypography } from '@/utils/pirateTheme';

// ========================================
// FormGroup Component
// ========================================

export interface FormGroupProps {
  /**
   * Form group label
   */
  label: string;

  /**
   * HTML for attribute (links label to input)
   */
  htmlFor?: string;

  /**
   * Whether the field is required
   */
  required?: boolean;

  /**
   * Error message to display
   */
  error?: string;

  /**
   * Help text to display below input
   */
  helpText?: string;

  /**
   * Form input or other child elements
   */
  children: React.ReactNode;

  /**
   * Additional CSS styles
   */
  style?: React.CSSProperties;
}

const FormGroupContainer = styled.div`
  margin-bottom: ${spacing.lg};
`;

export const Label = styled.label<{ $required?: boolean }>`
  display: block;
  color: ${pirateColors.primary};
  font-weight: ${pirateTypography.weights.bold};
  margin-bottom: ${spacing.sm};
  font-size: ${pirateTypography.sizes.sm};
  font-family: ${pirateTypography.body};

  ${props => props.$required && `
    &::after {
      content: ' *';
      color: ${pirateColors.danger};
    }
  `}
`;

export const HelpText = styled.p<{ $error?: boolean }>`
  color: ${props => props.$error ? pirateColors.danger : pirateColors.muted};
  font-size: ${pirateTypography.sizes.xs};
  margin-top: ${spacing.xs};
  margin-bottom: 0;
  line-height: 1.4;
`;

/**
 * FormGroup Component
 *
 * Wraps form inputs with label, help text, and error handling.
 *
 * @example
 * ```tsx
 * <FormGroup
 *   label="Email Address"
 *   htmlFor="email"
 *   required
 *   helpText="We'll never share your email"
 *   error={errors.email}
 * >
 *   <Input
 *     id="email"
 *     type="email"
 *     placeholder="you@example.com"
 *   />
 * </FormGroup>
 * ```
 */
export const FormGroup: React.FC<FormGroupProps> = ({
  label,
  htmlFor,
  required,
  error,
  helpText,
  children,
  style,
}) => {
  return (
    <FormGroupContainer style={style}>
      <Label htmlFor={htmlFor} $required={required}>
        {label}
      </Label>
      {children}
      {error && <HelpText $error>{error}</HelpText>}
      {!error && helpText && <HelpText>{helpText}</HelpText>}
    </FormGroupContainer>
  );
};

// ========================================
// Input Component
// ========================================

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /**
   * Whether the input has an error
   */
  hasError?: boolean;
}

export const Input = styled.input<InputProps>`
  width: 100%;
  padding: ${spacing.md};
  border: 2px solid ${props => props.hasError ? pirateColors.danger : pirateColors.lightGold};
  border-radius: 8px;
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.base};
  background: ${pirateColors.white};
  color: ${pirateColors.primary};
  transition: all 0.3s ease;

  &:focus {
    outline: none;
    border-color: ${props => props.hasError ? pirateColors.danger : pirateColors.secondary};
    box-shadow: 0 0 0 3px ${props => props.hasError
      ? `${pirateColors.danger}20`
      : `${pirateColors.secondary}20`
    };
  }

  &::placeholder {
    color: ${pirateColors.muted};
  }

  &:disabled {
    background: ${pirateColors.lightGold}40;
    cursor: not-allowed;
    opacity: 0.6;
  }
`;

// ========================================
// Textarea Component
// ========================================

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /**
   * Whether the textarea has an error
   */
  hasError?: boolean;
}

export const Textarea = styled.textarea<TextareaProps>`
  width: 100%;
  padding: ${spacing.md};
  border: 2px solid ${props => props.hasError ? pirateColors.danger : pirateColors.lightGold};
  border-radius: 8px;
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.base};
  background: ${pirateColors.white};
  color: ${pirateColors.primary};
  transition: all 0.3s ease;
  resize: vertical;
  min-height: 100px;

  &:focus {
    outline: none;
    border-color: ${props => props.hasError ? pirateColors.danger : pirateColors.secondary};
    box-shadow: 0 0 0 3px ${props => props.hasError
      ? `${pirateColors.danger}20`
      : `${pirateColors.secondary}20`
    };
  }

  &::placeholder {
    color: ${pirateColors.muted};
  }

  &:disabled {
    background: ${pirateColors.lightGold}40;
    cursor: not-allowed;
    opacity: 0.6;
  }

  /* Custom scrollbar for webkit browsers */
  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: ${pirateColors.lightGold};
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: ${pirateColors.secondary};
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: ${pirateColors.primary};
  }
`;

// ========================================
// Select Component
// ========================================

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  /**
   * Whether the select has an error
   */
  hasError?: boolean;
}

export const Select = styled.select<SelectProps>`
  width: 100%;
  padding: ${spacing.md};
  border: 2px solid ${props => props.hasError ? pirateColors.danger : pirateColors.lightGold};
  border-radius: 8px;
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.base};
  background: ${pirateColors.white};
  color: ${pirateColors.primary};
  transition: all 0.3s ease;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: ${props => props.hasError ? pirateColors.danger : pirateColors.secondary};
    box-shadow: 0 0 0 3px ${props => props.hasError
      ? `${pirateColors.danger}20`
      : `${pirateColors.secondary}20`
    };
  }

  &:disabled {
    background: ${pirateColors.lightGold}40;
    cursor: not-allowed;
    opacity: 0.6;
  }

  /* Style for select arrow */
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%238B4513' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right ${spacing.md} center;
  background-size: 1.25em;
  padding-right: calc(${spacing.md} * 2 + 1.25em);
`;

// ========================================
// Checkbox Component
// ========================================

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /**
   * Label text for checkbox
   */
  label?: string;
}

const CheckboxContainer = styled.div`
  display: flex;
  align-items: center;
  gap: ${spacing.sm};
  cursor: pointer;
`;

const CheckboxInput = styled.input`
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: ${pirateColors.secondary};

  &:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
`;

const CheckboxLabel = styled.label`
  color: ${pirateColors.primary};
  font-size: ${pirateTypography.sizes.sm};
  cursor: pointer;
  user-select: none;
  line-height: 1.4;

  &:has(input:disabled) {
    cursor: not-allowed;
    opacity: 0.5;
  }
`;

/**
 * Checkbox Component
 *
 * Styled checkbox with optional label.
 *
 * @example
 * ```tsx
 * <Checkbox
 *   id="terms"
 *   label="I agree to the terms and conditions"
 *   checked={agreed}
 *   onChange={(e) => setAgreed(e.target.checked)}
 * />
 * ```
 */
export const Checkbox: React.FC<CheckboxProps> = ({ label, id, ...props }) => {
  if (label) {
    return (
      <CheckboxContainer>
        <CheckboxInput type="checkbox" id={id} {...props} />
        <CheckboxLabel htmlFor={id}>{label}</CheckboxLabel>
      </CheckboxContainer>
    );
  }

  return <CheckboxInput type="checkbox" id={id} {...props} />;
};

// ========================================
// EditInput (inline editing)
// ========================================

export interface EditInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /**
   * Whether the input has an error
   */
  hasError?: boolean;
}

export const EditInput = styled.input<EditInputProps>`
  padding: ${spacing.sm} ${spacing.md};
  border: 2px solid ${props => props.hasError ? pirateColors.danger : pirateColors.lightGold};
  border-radius: 8px;
  font-family: ${pirateTypography.body};
  font-size: ${pirateTypography.sizes.sm};
  background: ${pirateColors.white};
  color: ${pirateColors.primary};
  width: 100%;
  max-width: 300px;
  transition: all 0.3s ease;

  &:focus {
    outline: none;
    border-color: ${props => props.hasError ? pirateColors.danger : pirateColors.secondary};
    box-shadow: 0 0 0 3px ${props => props.hasError
      ? `${pirateColors.danger}20`
      : `${pirateColors.secondary}20`
    };
  }

  &::placeholder {
    color: ${pirateColors.muted};
  }
`;
