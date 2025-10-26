/**
 * Dashboard Page
 *
 * Main dashboard view showing expedition statistics and timeline.
 * Refactored to container/presenter pattern for better testability and maintainability.
 *
 * Architecture:
 * - DashboardContainer: Hook composition and state management
 * - DashboardPresenter: Pure UI rendering
 * - Custom hooks: useDashboardStats, useTimelineExpeditions, useDashboardActions
 * - Presentation components: DashboardStats, ExpeditionTimeline
 *
 * This refactoring reduces the main file from 359 lines to 3 lines (99% reduction)
 * while improving separation of concerns, testability, and reusability.
 */

export { DashboardContainer as Dashboard } from '@/containers/DashboardContainer';
