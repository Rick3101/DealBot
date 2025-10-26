import type { Meta, StoryObj } from '@storybook/react';
import { DashboardPresenter } from './DashboardPresenter';
import { DashboardStats } from '@/hooks/useDashboardStats';
import { ExpeditionTimelineEntry } from '@/types/expedition';
import { DashboardActions } from '@/hooks/useDashboardActions';

const meta = {
  title: 'Dashboard/DashboardPresenter',
  component: DashboardPresenter,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof DashboardPresenter>;

export default meta;
type Story = StoryObj<typeof meta>;

const mockStats: DashboardStats = {
  totalExpeditions: 25,
  activeExpeditions: 8,
  completedExpeditions: 15,
  totalRevenue: 12500,
  totalProfit: 4250,
  profitMargin: 34,
};

const mockExpeditions: ExpeditionTimelineEntry[] = [
  {
    id: 1,
    name: 'Treasure Island Hunt',
    status: 'active',
    deadline: new Date(Date.now() + 1000 * 60 * 60 * 24 * 10).toISOString(),
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
    progress_percentage: 65,
    total_revenue: 1250,
    total_profit: 450,
  },
  {
    id: 2,
    name: 'Caribbean Expedition',
    status: 'active',
    deadline: new Date(Date.now() + 1000 * 60 * 60 * 24 * 3).toISOString(),
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 8).toISOString(),
    progress_percentage: 85,
    total_revenue: 2100,
    total_profit: 780,
  },
  {
    id: 3,
    name: 'Lost Gold Search',
    status: 'completed',
    deadline: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 15).toISOString(),
    progress_percentage: 100,
    total_revenue: 3200,
    total_profit: 1200,
  },
];

const mockActions: DashboardActions = {
  handleViewExpedition: (id: number) => console.log('View expedition:', id),
  handleManageExpedition: (id: number) => console.log('Manage expedition:', id),
  handleCreateExpedition: () => console.log('Create expedition'),
  handleRefresh: async () => console.log('Refresh'),
  refreshing: false,
};

export const Default: Story = {
  args: {
    loading: false,
    error: null,
    stats: mockStats,
    expeditions: mockExpeditions,
    actions: mockActions,
    refreshing: false,
  },
};

export const Loading: Story = {
  args: {
    loading: true,
    error: null,
    stats: mockStats,
    expeditions: [],
    actions: mockActions,
    refreshing: false,
  },
};

export const Error: Story = {
  args: {
    loading: false,
    error: 'Failed to load expeditions. Please check your connection.',
    stats: mockStats,
    expeditions: [],
    actions: mockActions,
    refreshing: false,
  },
};

export const Empty: Story = {
  args: {
    loading: false,
    error: null,
    stats: {
      totalExpeditions: 0,
      activeExpeditions: 0,
      completedExpeditions: 0,
      totalRevenue: 0,
      totalProfit: 0,
      profitMargin: 0,
    },
    expeditions: [],
    actions: mockActions,
    refreshing: false,
  },
};

export const Refreshing: Story = {
  args: {
    loading: false,
    error: null,
    stats: mockStats,
    expeditions: mockExpeditions,
    actions: { ...mockActions, refreshing: true },
    refreshing: true,
  },
};

export const ManyExpeditions: Story = {
  args: {
    loading: false,
    error: null,
    stats: {
      totalExpeditions: 50,
      activeExpeditions: 20,
      completedExpeditions: 30,
      totalRevenue: 50000,
      totalProfit: 18000,
      profitMargin: 36,
    },
    expeditions: Array.from({ length: 10 }, (_, i) => ({
      id: i + 1,
      name: `Expedition ${i + 1}`,
      status: i % 3 === 0 ? 'completed' : 'active',
      deadline: new Date(Date.now() + 1000 * 60 * 60 * 24 * (10 - i)).toISOString(),
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * i).toISOString(),
      progress_percentage: Math.min(100, (i + 1) * 10),
      total_revenue: (i + 1) * 500,
      total_profit: (i + 1) * 180,
    })),
    actions: mockActions,
    refreshing: false,
  },
};
