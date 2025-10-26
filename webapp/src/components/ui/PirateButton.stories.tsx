import type { Meta, StoryObj } from '@storybook/react';
import { PirateButton } from './PirateButton';

const meta = {
  title: 'UI/PirateButton',
  component: PirateButton,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'danger'],
      description: 'Button variant style',
    },
    size: {
      control: 'select',
      options: ['small', 'medium', 'large'],
      description: 'Button size',
    },
    disabled: {
      control: 'boolean',
      description: 'Disable the button',
    },
    onClick: { action: 'clicked' },
  },
} satisfies Meta<typeof PirateButton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    children: 'Set Sail',
    variant: 'primary',
  },
};

export const Secondary: Story = {
  args: {
    children: 'Cancel',
    variant: 'secondary',
  },
};

export const Danger: Story = {
  args: {
    children: 'Delete',
    variant: 'danger',
  },
};

export const Small: Story = {
  args: {
    children: 'Small Button',
    variant: 'primary',
    size: 'small',
  },
};

export const Large: Story = {
  args: {
    children: 'Large Button',
    variant: 'primary',
    size: 'large',
  },
};

export const Disabled: Story = {
  args: {
    children: 'Disabled',
    variant: 'primary',
    disabled: true,
  },
};

export const WithIcon: Story = {
  args: {
    children: '⚓ Anchor',
    variant: 'primary',
  },
};

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <PirateButton variant="primary">Primary</PirateButton>
      <PirateButton variant="secondary">Secondary</PirateButton>
      <PirateButton variant="danger">Danger</PirateButton>
      <PirateButton variant="primary" disabled>Disabled</PirateButton>
    </div>
  ),
};
