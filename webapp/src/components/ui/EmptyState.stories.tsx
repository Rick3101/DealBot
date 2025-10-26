import type { Meta, StoryObj } from '@storybook/react';
import { EmptyState } from './EmptyState';
import { PirateButton } from './PirateButton';
import { Plus, Users } from 'lucide-react';

const meta = {
  title: 'UI/EmptyState',
  component: EmptyState,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A reusable empty state component with pirate-themed styling for displaying when content is not available.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    icon: {
      control: 'text',
      description: 'Emoji or icon to display',
    },
    title: {
      control: 'text',
      description: 'Main title of the empty state',
    },
    description: {
      control: 'text',
      description: 'Descriptive text explaining the empty state',
    },
    action: {
      control: false,
      description: 'Optional action button or custom content',
    },
  },
} satisfies Meta<typeof EmptyState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    icon: '🏴‍☠️',
    title: 'No data available',
    description: 'There is currently no data to display.',
  },
};

export const NoPirates: Story = {
  args: {
    icon: '🏴‍☠️',
    title: 'No pirates yet',
    description: 'No pirates have joined this expedition yet.',
  },
};

export const NoItems: Story = {
  args: {
    icon: '📦',
    title: 'No items',
    description: 'This expedition has no items yet. Add some items to get started!',
  },
};

export const NoConsumptions: Story = {
  args: {
    icon: '🍽️',
    title: 'No consumptions yet',
    description: 'Pirates haven\'t started consuming items from this expedition.',
  },
};

export const NoExpeditions: Story = {
  args: {
    icon: '🗺️',
    title: 'No expeditions',
    description: 'You haven\'t created any expeditions yet. Start your first voyage!',
  },
};

export const WithAction: Story = {
  args: {
    icon: '🏴‍☠️',
    title: 'No pirates yet',
    description: 'No pirates have joined this expedition yet.',
    action: (
      <PirateButton variant="primary" size="md" onClick={() => alert('Add Pirate clicked')}>
        <Users size={16} /> Add Pirate
      </PirateButton>
    ),
  },
};

export const WithMultipleActions: Story = {
  args: {
    icon: '📦',
    title: 'No items',
    description: 'This expedition has no items yet.',
    action: (
      <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
        <PirateButton variant="primary" size="sm" onClick={() => alert('Add Item clicked')}>
          <Plus size={16} /> Add Item
        </PirateButton>
        <PirateButton variant="secondary" size="sm" onClick={() => alert('Import clicked')}>
          Import Items
        </PirateButton>
      </div>
    ),
  },
};

export const CustomIcon: Story = {
  args: {
    icon: '⚓',
    title: 'Anchored',
    description: 'This expedition is currently on hold. Resume to continue your journey.',
  },
};

export const LongDescription: Story = {
  args: {
    icon: '🧭',
    title: 'Lost at sea',
    description: 'It looks like you\'ve wandered off the map! This section doesn\'t have any content yet, but you can create some by clicking the button below to start your adventure.',
    action: (
      <PirateButton variant="primary" size="md">
        Start Adventure
      </PirateButton>
    ),
  },
};

export const MobileView: Story = {
  args: {
    icon: '🏴‍☠️',
    title: 'No pirates yet',
    description: 'No pirates have joined this expedition yet.',
    action: (
      <PirateButton variant="primary" size="md">
        <Users size={16} /> Add Pirate
      </PirateButton>
    ),
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
};
