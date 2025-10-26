import type { Meta, StoryObj } from '@storybook/react';
import { PirateCard } from './PirateCard';

const meta = {
  title: 'UI/PirateCard',
  component: PirateCard,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'highlighted', 'danger'],
      description: 'Card variant style',
    },
    onClick: { action: 'clicked' },
  },
} satisfies Meta<typeof PirateCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: (
      <div>
        <h3>Expedition Card</h3>
        <p>This is a default pirate card with some content inside.</p>
      </div>
    ),
  },
};

export const Highlighted: Story = {
  args: {
    variant: 'highlighted',
    children: (
      <div>
        <h3>Active Expedition</h3>
        <p>This card stands out to show importance.</p>
      </div>
    ),
  },
};

export const Danger: Story = {
  args: {
    variant: 'danger',
    children: (
      <div>
        <h3>Overdue Expedition</h3>
        <p>This card indicates a problem or warning.</p>
      </div>
    ),
  },
};

export const WithStats: Story = {
  args: {
    children: (
      <div style={{ padding: '1rem' }}>
        <h3 style={{ marginTop: 0 }}>Treasure Hunt</h3>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.875rem', opacity: 0.7 }}>Progress</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>75%</div>
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', opacity: 0.7 }}>Revenue</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>$1,250</div>
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', opacity: 0.7 }}>Profit</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>$450</div>
          </div>
        </div>
      </div>
    ),
  },
};

export const Interactive: Story = {
  args: {
    onClick: () => alert('Card clicked!'),
    children: (
      <div style={{ padding: '1rem' }}>
        <h3 style={{ marginTop: 0 }}>Clickable Card</h3>
        <p>Click this card to trigger an action</p>
      </div>
    ),
  },
};
