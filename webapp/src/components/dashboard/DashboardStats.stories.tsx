import type { Meta, StoryObj } from '@storybook/react';
import { DashboardStats } from './DashboardStats';
import { DashboardStats as DashboardStatsType } from '@/hooks/useDashboardStats';

const meta = {
  title: 'Dashboard/DashboardStats',
  component: DashboardStats,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof DashboardStats>;

export default meta;
type Story = StoryObj<typeof meta>;

const defaultStats: DashboardStatsType = {
  total_expeditions: 25,
  active_expeditions: 8,
  completed_expeditions: 15,
  overdue_expeditions: 2,
};

export const Default: Story = {
  args: {
    stats: defaultStats,
  },
};

export const NoExpeditions: Story = {
  args: {
    stats: {
      total_expeditions: 0,
      active_expeditions: 0,
      completed_expeditions: 0,
      overdue_expeditions: 0,
    },
  },
};

export const HighActivity: Story = {
  args: {
    stats: {
      total_expeditions: 150,
      active_expeditions: 45,
      completed_expeditions: 105,
      overdue_expeditions: 5,
    },
  },
};

export const LowMargin: Story = {
  args: {
    stats: {
      total_expeditions: 20,
      active_expeditions: 5,
      completed_expeditions: 15,
      overdue_expeditions: 1,
    },
  },
};

export const HighMargin: Story = {
  args: {
    stats: {
      total_expeditions: 30,
      active_expeditions: 10,
      completed_expeditions: 20,
      overdue_expeditions: 0,
    },
  },
};

export const MixedActivity: Story = {
  args: {
    stats: {
      total_expeditions: 50,
      active_expeditions: 30,
      completed_expeditions: 18,
      overdue_expeditions: 3,
    },
  },
};
