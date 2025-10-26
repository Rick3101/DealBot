import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useExpeditions } from '@/hooks/useExpeditions';
import { useDashboardStats } from '@/hooks/useDashboardStats';
import { useTimelineExpeditions } from '@/hooks/useTimelineExpeditions';
import { useDashboardActions } from '@/hooks/useDashboardActions';
import { DashboardPresenter } from '@/components/dashboard/DashboardPresenter';

/**
 * Container component for Dashboard
 *
 * Responsible for:
 * - Data fetching via useExpeditions hook
 * - Statistics calculation via useDashboardStats hook
 * - Timeline transformation via useTimelineExpeditions hook
 * - Action handlers via useDashboardActions hook
 * - Delegation to DashboardPresenter for rendering
 *
 * This component has NO UI logic - only hook composition and orchestration
 */
export const DashboardContainer: React.FC = () => {
  const navigate = useNavigate();

  // Data fetching
  const {
    expeditions,
    timelineData,
    loading,
    error,
    refreshing,
    refreshExpeditions,
  } = useExpeditions({
    autoRefresh: true,
    refreshInterval: 30000,
    realTimeUpdates: true,
  });

  // Calculation hooks
  const stats = useDashboardStats(expeditions, timelineData);
  const timelineExpeditions = useTimelineExpeditions(expeditions, timelineData);

  // Action hooks
  const actions = useDashboardActions(navigate, refreshExpeditions);

  // Delegate to presenter
  return (
    <DashboardPresenter
      loading={loading}
      error={error}
      stats={stats}
      expeditions={timelineExpeditions}
      actions={actions}
      refreshing={refreshing}
    />
  );
};
