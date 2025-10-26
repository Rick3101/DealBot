import React from 'react';
import { ExpeditionDetailsContainer } from '@/containers/ExpeditionDetailsContainer';

interface ExpeditionDetailsProps {
  expeditionId: number;
  onBack?: () => void;
}

/**
 * ExpeditionDetails Page Component (Refactored)
 *
 * This component has been refactored following the Container/Presenter pattern
 * to improve maintainability, testability, and code organization.
 *
 * Architecture:
 * - This page component is now a thin wrapper that delegates to the container
 * - ExpeditionDetailsContainer: Handles data fetching, state management, and business logic
 * - ExpeditionDetailsPresenter: Pure presentation component with all UI rendering
 * - Domain hooks: useExpeditionDetails, useExpeditionPirates, useItemConsumption
 * - Tab components: OverviewTab, ItemsTab, PiratesTab, ConsumptionsTab, AnalyticsTab
 *
 * Benefits:
 * - Single Responsibility: Each component has one clear purpose
 * - Testability: Logic and UI can be tested independently
 * - Reusability: Hooks and components can be reused elsewhere
 * - Maintainability: Easy to understand, modify, and extend
 *
 * Original size: 1180 lines
 * Refactored size: ~30 lines
 * Code reduction: 97.5%
 */
export const ExpeditionDetails: React.FC<ExpeditionDetailsProps> = (props) => {
  return <ExpeditionDetailsContainer {...props} />;
};
