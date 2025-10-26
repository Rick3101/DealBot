import type { Meta, StoryObj } from '@storybook/react';
import { DeadlineTimer } from './DeadlineTimer';

const meta = {
  title: 'UI/DeadlineTimer',
  component: DeadlineTimer,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    deadline: {
      control: 'text',
      description: 'ISO date string for the deadline',
    },
    variant: {
      control: 'select',
      options: ['normal', 'warning', 'danger'],
      description: 'Timer variant based on urgency',
    },
  },
} satisfies Meta<typeof DeadlineTimer>;

export default meta;
type Story = StoryObj<typeof meta>;

const futureDate = new Date();
futureDate.setDate(futureDate.getDate() + 15);

const soonDate = new Date();
soonDate.setDate(soonDate.getDate() + 2);

const pastDate = new Date();
pastDate.setDate(pastDate.getDate() - 5);

export const Normal: Story = {
  args: {
    deadline: futureDate.toISOString(),
  },
};

export const Warning: Story = {
  args: {
    deadline: soonDate.toISOString(),
    variant: 'warning',
  },
};

export const Danger: Story = {
  args: {
    deadline: new Date(Date.now() + 1000 * 60 * 60 * 12).toISOString(), // 12 hours
    variant: 'danger',
  },
};

export const Overdue: Story = {
  args: {
    deadline: pastDate.toISOString(),
    variant: 'danger',
  },
};

export const LongDeadline: Story = {
  args: {
    deadline: new Date(Date.now() + 1000 * 60 * 60 * 24 * 90).toISOString(), // 90 days
  },
};

export const VeryShort: Story = {
  args: {
    deadline: new Date(Date.now() + 1000 * 60 * 30).toISOString(), // 30 minutes
    variant: 'danger',
  },
};
