import type { Meta, StoryObj } from '@storybook/react';
import { ExpeditionCard } from './ExpeditionCard';

const meta = {
  title: 'Expedition/ExpeditionCard',
  component: ExpeditionCard,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    onView: { action: 'view clicked' },
    onManage: { action: 'manage clicked' },
  },
} satisfies Meta<typeof ExpeditionCard>;

export default meta;
type Story = StoryObj<typeof meta>;

const baseExpedition = {
  id: 1,
  name: 'Treasure Island Hunt',
  description: 'Search for buried treasure on a mysterious island',
  status: 'active' as const,
  deadline: new Date(Date.now() + 1000 * 60 * 60 * 24 * 10).toISOString(),
  created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
  owner_chat_id: 123456,
};

export const Active: Story = {
  args: {
    expedition: {
      ...baseExpedition,
      status: 'active',
      progress_percentage: 65,
      total_revenue: 1250,
      total_profit: 450,
    },
  },
};

export const JustStarted: Story = {
  args: {
    expedition: {
      ...baseExpedition,
      name: 'New Caribbean Expedition',
      status: 'active',
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
      progress_percentage: 5,
      total_revenue: 0,
      total_profit: 0,
    },
  },
};

export const NearlyComplete: Story = {
  args: {
    expedition: {
      ...baseExpedition,
      name: 'Almost Done Quest',
      status: 'active',
      progress_percentage: 95,
      total_revenue: 4800,
      total_profit: 1680,
    },
  },
};

export const Completed: Story = {
  args: {
    expedition: {
      ...baseExpedition,
      name: 'Successfully Completed',
      status: 'completed',
      deadline: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
      progress_percentage: 100,
      total_revenue: 5000,
      total_profit: 2000,
    },
  },
};

export const Overdue: Story = {
  args: {
    expedition: {
      ...baseExpedition,
      name: 'Overdue Expedition',
      status: 'active',
      deadline: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
      progress_percentage: 45,
      total_revenue: 800,
      total_profit: 200,
    },
  },
};

export const UrgentDeadline: Story = {
  args: {
    expedition: {
      ...baseExpedition,
      name: 'Urgent Mission',
      status: 'active',
      deadline: new Date(Date.now() + 1000 * 60 * 60 * 12).toISOString(),
      progress_percentage: 30,
      total_revenue: 600,
      total_profit: 150,
    },
  },
};

export const HighRevenue: Story = {
  args: {
    expedition: {
      ...baseExpedition,
      name: 'Major Treasure Hunt',
      status: 'active',
      progress_percentage: 80,
      total_revenue: 25000,
      total_profit: 10000,
    },
  },
};

export const NoRevenue: Story = {
  args: {
    expedition: {
      ...baseExpedition,
      name: 'Fresh Start',
      status: 'active',
      progress_percentage: 0,
      total_revenue: 0,
      total_profit: 0,
    },
  },
};

export const LongDescription: Story = {
  args: {
    expedition: {
      ...baseExpedition,
      name: 'Complex Multi-Phase Expedition',
      description:
        'This is a very long description that explains all the details of this complex expedition. It involves multiple phases, various locations, and requires careful coordination among all crew members. The treasure is said to be hidden in a series of caves across three different islands.',
      status: 'active',
      progress_percentage: 40,
      total_revenue: 3000,
      total_profit: 900,
    },
  },
};
